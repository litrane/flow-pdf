from pathlib import Path
import inspect
import time
import fitz
from typing import NamedTuple
import concurrent.futures
from htutil import file


class DocInputParams(NamedTuple):
    file_input: Path
    page_count: int


class PageInputParams(NamedTuple):
    pass


class DocOutputParams(NamedTuple):
    pass


class PageOutputParams(NamedTuple):
    pass


class Worker:
    def post_run(
        self, doc_in: DocInputParams, page_in: list[PageInputParams]
    ) -> tuple[DocOutputParams, list[PageOutputParams]]:
        success, result = self.load_cache(doc_in, page_in)
        if success:
            return result

        doc_out, page_out = self.run(doc_in, page_in)

        self.save_cache(doc_in, page_in, doc_out, page_out)
        return doc_out, page_out

    def run(
        self, doc_in: DocInputParams, page_in: list[PageInputParams]
    ) -> tuple[DocOutputParams, list[PageOutputParams]]:
        return (DocOutputParams(), [])

    def load_cache(
        self, doc_in: DocInputParams, page_in: list[PageInputParams]
    ) -> tuple[bool, tuple[DocOutputParams, list[PageOutputParams]]]:
        if self.__dict__.get("disable_cache"):
            return False, (DocOutputParams(), [])
        # print(inspect.getsource(self.__class__))

        file_pkl = (
            Path("/tmp")
            / "flow-pdf"
            / doc_in.file_input.name
            / f"{self.__class__.__name__}.pkl"
        )
        if not file_pkl.exists():
            return False, (DocOutputParams(), [])
        
        d = file.read_pkl(file_pkl)
        if d["src"] != inspect.getsource(self.__class__) or d["doc_in"] != doc_in or d["page_in"] != page_in:
            return False, (DocOutputParams(), [])
        
        return True, (d["doc_out"], d["page_out"])

    def save_cache(
        self,
        doc_in: DocInputParams,
        page_in: list[PageInputParams],
        doc_out: DocOutputParams,
        page_out: list[PageOutputParams],
    ):
        if self.__dict__.get("disable_cache"):
            return

        file_pkl = (
            Path("/tmp")
            / "flow-pdf"
            / doc_in.file_input.name
            / f"{self.__class__.__name__}.pkl"
        )
        file_pkl.parent.mkdir(parents=True, exist_ok=True)

        file.write_pkl(
            file_pkl,
            {
                "src": inspect.getsource(self.__class__),
                "doc_in": doc_in,
                "page_in": page_in,
                "doc_out": doc_out,
                "page_out": page_out,
            },
        )


class PageWorker(Worker):
    def run(
        self, doc_in: DocInputParams, page_in: list[PageInputParams]
    ) -> tuple[DocOutputParams, list[PageOutputParams]]:
        page_result = self.run_page_parallel(doc_in, page_in)

        doc_result = self.after_run_page(doc_in, page_in, page_result)

        return (doc_result, page_result)

    def run_page_parallel(
        self, doc_in: DocInputParams, page_in: list[PageInputParams]
    ) -> list[PageOutputParams]:
        with concurrent.futures.ProcessPoolExecutor() as executor:
            futures = [
                executor.submit(self.run_page, page_index, doc_in, page_in[page_index])
                for page_index in range(doc_in.page_count)
            ]
            results = [future.result() for future in futures]
            return results

    # def post_run_page(self):
    #     pass

    def run_page(
        self, page_index: int, doc_in: DocInputParams, page_in: PageInputParams
    ) -> PageOutputParams:
        raise NotImplementedError()

    def after_run_page(
        self,
        doc_in: DocInputParams,
        page_in: list[PageInputParams],
        page_out: list[PageOutputParams],
    ) -> DocOutputParams:
        return DocOutputParams()


class Executer:
    def __init__(self, file_input: Path, dir_output: Path):
        with fitz.open(file_input) as doc:  # type: ignore
            page_count = doc.page_count

        self.store = ParamsStore(page_count)
        self.store.doc_set("file_input", file_input)
        self.store.doc_set("dir_output", dir_output)

    def register(self, workers: list[type]):
        self.workers = workers

    def execute(self):
        for w in self.workers:
            print(f"{w.__name__} start")
            start = time.perf_counter()

            if issubclass(w, PageWorker):
                w_method = w.run_page
            elif issubclass(w, Worker):
                w_method = w.run
            else:
                print(f"warning: {w.__name__} is not a worker")
                continue

            k = "doc_in"
            k_class = w_method.__annotations__[k]  # type: ignore
            param_names = k_class._fields
            params = [self.store.doc_get(n) for n in param_names]
            doc_in = k_class(*params)

            k = "page_in"
            if issubclass(w, PageWorker):
                k_class = w_method.__annotations__[k]  # type: ignore
            elif issubclass(w, Worker):
                k_class = w_method.__annotations__[k].__args__[0]  # type: ignore

            param_names = k_class._fields
            page_in = []
            for i in range(self.store.doc_get("page_count")):
                params = [self.store.page_get(n, i) for n in param_names]
                page_in.append(k_class(*params))

            doc_out, page_out = w().post_run(doc_in, page_in)
            for k, v in doc_out._asdict().items():
                self.store.doc_set(k, v)
            for i, p in enumerate(page_out):
                for k, v in p._asdict().items():
                    self.store.page_set(k, i, v)
            print(f"{w.__name__} finished, time = {(time.perf_counter() - start):.2f}s")


class ParamsStore:
    def __init__(self, page_count: int):
        self.doc_params = {"page_count": page_count}
        self.page_params = [{}] * page_count

    def doc_get(self, name: str):
        return self.doc_params[name]

    def doc_set(self, name: str, value):
        self.doc_params[name] = value

    def page_get(self, name: str, page_index: int):
        return self.page_params[page_index][name]

    def page_set(self, name: str, page_index: int, value):
        self.page_params[page_index][name] = value
