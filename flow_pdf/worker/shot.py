from .common import PageWorker, Block, Range
from .common import (
    DocInputParams,
    PageInputParams,
    DocOutputParams,
    PageOutputParams,
    LocalPageOutputParams,
)


from dataclasses import dataclass


@dataclass
class DocInParams(DocInputParams):
    big_text_columns: list[Range]

    core_y: Range


@dataclass
class PageInParams(PageInputParams):
    big_blocks: list
    raw_dict: dict
    drawings: list


@dataclass
class DocOutParams(DocOutputParams):
    pass


@dataclass
class PageOutParams(PageOutputParams):
    shot_rects: list


@dataclass
class LocalPageOutParams(LocalPageOutputParams):
    pass


def rectangle_relation(rect1, rect2):
    x1, y2, x2, y1 = rect1
    x3, y4, x4, y3 = rect2

    if x1 >= x4 or x2 <= x3 or y1 <= y4 or y2 >= y3:
        return "not intersect"  # 不相交

    elif x1 >= x3 and x2 <= x4 and y1 <= y3 and y2 >= y4:
        return "contains"  # 包含

    elif x1 <= x3 and x2 >= x4 and y1 >= y3 and y2 <= y4:
        return "contained by"  # 被包含

    else:
        return "intersect"  # 相交


class ShotWorker(PageWorker):
    def run_page(  # type: ignore[override]
        self, page_index: int, doc_in: DocInParams, page_in: PageInParams
    ) -> tuple[PageOutParams, LocalPageOutParams]:
        column_rects: list[list[tuple[float, float, float, float]]] = []

        for column in doc_in.big_text_columns:
            rects: list[tuple[float, float, float, float]] = []

            elements_rect = [
                b
                for b in page_in.big_blocks
                if b["bbox"][0] >= column.min and b["bbox"][2] <= column.max
            ]
            elements_rect.sort(key=lambda x: x["bbox"][1])
            last_y = doc_in.core_y.min
            for block in elements_rect:
                r = (column.min, last_y, column.max, block["bbox"][1])
                if r[3] - r[1] > 0:
                    rects.append(r)
                else:
                    self.logger.warning(f"r.y1 <= r.y0, r = {r}")
                last_y = block["bbox"][3]
            rects.append((column.min, last_y, column.max, doc_in.core_y.max))

            column_rects.append(rects)

        def is_near(rect1, rect2):
            return abs(rect1[1] - rect2[1]) < 10 and abs(rect2[3] - rect1[3]) < 10

        # merge shot in different columns
        for i, rects in enumerate(column_rects):
            if i == len(column_rects) - 1:
                # The last column does not need to be merged
                break

            for j in range(len(rects)):
                rect = rects[j]

                # TODO ZmICE1 - 2.png
                for other_c_index in range(i + 1, len(column_rects)):
                    is_find_near = False
                    next_c = column_rects[other_c_index]
                    for k in range(len(next_c)):
                        next_rect = next_c[k]
                        if is_near(rect, next_rect):
                            is_find_near = True
                            rects[j] = (rect[0], rect[1], next_rect[2], rect[3])
                            del next_c[k]
                            break
                    if not is_find_near:
                        break

        elements_rect = []
        for block in page_in.raw_dict["blocks"]:
            elements_rect.append(block["bbox"])
        for draw in page_in.drawings:
            elements_rect.append(draw["rect"])

        BORDER_WIDTH = 4

        # delete empty rects
        for rects in column_rects:
            for i in reversed(range(len(rects))):
                rect = rects[i]
                # delete height too small
                if rect[3] - rect[1] <= BORDER_WIDTH * 2:
                    del rects[i]
                    continue

                inner_rect = (
                    rect[0] + BORDER_WIDTH,
                    rect[1] + BORDER_WIDTH,
                    rect[2] - BORDER_WIDTH,
                    rect[3] - BORDER_WIDTH,
                )
                is_found = False
                for r in elements_rect:
                    if rectangle_relation(inner_rect, r) != "not intersect":
                        is_found = True
                        break
                if not is_found:
                    del rects[i]

        # extend first rect in each column
        for rects in column_rects:
            if len(rects) == 0:
                continue
            rect = rects[0]

            intersect_rects = []  # elements intersect with rect
            for r in elements_rect:
                if rectangle_relation(rect, r) == "intersect":
                    intersect_rects.append(r)

            if not elements_rect:
                continue

            min_y0 = min([r[1] for r in elements_rect])
            min_y0 = min(min_y0, rect[1])
            rects[0] = (rect[0], min_y0, rect[2], rect[3])

        rects = []
        for c in column_rects:
            rects.extend(c)

        return PageOutParams(rects), LocalPageOutParams()