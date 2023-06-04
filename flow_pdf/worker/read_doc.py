from .common import PageWorker, Block
from .common import (
    DocInputParams,
    PageInputParams,
    DocOutputParams,
    PageOutputParams,
    LocalPageOutputParams,
)


import fitz
from fitz import Page
from dataclasses import dataclass


@dataclass
class DocInParams(DocInputParams):
    pass


@dataclass
class PageInParams(PageInputParams):
    pass


@dataclass
class DocOutParams(DocOutputParams):
    pass


@dataclass
class PageOutParams(PageOutputParams):
    raw_dict: dict
    drawings: list
    blocks: list[Block]
    images: list


@dataclass
class LocalPageOutParams(LocalPageOutputParams):
    pass


class ReadDocWorker(PageWorker):
    def run_page(  # type: ignore[override]
        self, page_index: int, doc_in: DocInParams, page_in: PageInParams
    ) -> tuple[PageOutParams, LocalPageOutParams]:
        with fitz.open(doc_in.file_input) as doc:  # type: ignore
            page: Page = doc.load_page(page_index)
            raw_dict = page.get_text("rawdict")  # type: ignore
            drawings = page.get_drawings()
            blocks = [Block(b) for b in page.get_text("blocks")]  # type: ignore
            images = page.get_image_info()# type: ignore

            return PageOutParams(raw_dict, drawings, blocks, images), LocalPageOutParams()
