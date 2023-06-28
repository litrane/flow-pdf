import yaml
from pathlib import Path
import shutil
import time
from htutil import file
from worker import Executer, ExecuterConfig, workers_dev  # type: ignore
import concurrent.futures
import common  # type: ignore
import traceback
from tqdm import tqdm

from common import version

cfg = yaml.load(Path("./config.yaml").read_text(), Loader=yaml.FullLoader)
disable_pbar = not cfg["processbar"]['enabled']

def get_files_from_cfg():
    dir_input = Path(cfg["path"]["input"])
    dir_output = Path(cfg["path"]["output"])

    for file in cfg["files"]:
        yield (dir_input / f"{file}.pdf"), (dir_output / file)


def get_files_from_dir():
    for file in Path("./data").glob("*.pdf"):
        yield (file, Path("./data") / file.stem)


logger = common.create_main_logger()
logger.info(f"version: {version}")


def create_task(file_input: Path, dir_output: Path):
    # TODO when enable pbar, just write to file
    if disable_pbar:
        logger.info(f"start {file_input.name}")
    t = time.perf_counter()
    if dir_output.exists():
        shutil.rmtree(dir_output)
    dir_output.mkdir(parents=True)

    cfg = ExecuterConfig(version, True)  # type: ignore
    e = Executer(file_input, dir_output, cfg)
    e.register(workers_dev)
    try:
        e.execute()
    except Exception as e:
        if disable_pbar:
            logger.error(f"{file_input.name} failed")
        file.write_text(dir_output / "error.txt", traceback.format_exc())
    if disable_pbar:
        logger.info(f"end {file_input.name}, time = {time.perf_counter() - t:.2f}s")


if __name__ == "__main__":
    files = list(get_files_from_cfg())
    with tqdm(total=len(files), disable=disable_pbar) as progress:
        with concurrent.futures.ProcessPoolExecutor(max_workers=12) as executor:
            futures = [
                executor.submit(create_task, file_input, dir_output)
                for file_input, dir_output in files
            ]
            for future in concurrent.futures.as_completed(futures):
                # future.result()
                progress.update(1)

        if cfg["compare"]["enabled"]:
            dir_target = Path(cfg["compare"]["target"])

            dir_output_list = []
            for _, d in files:
                dir_output_list.append(d)
            dir_output_list.sort()

            for dir_output in dir_output_list:
                dir_t = dir_target / dir_output.stem
                file_t = dir_t / "big_blocks_id" / "big_blocks_id.json"
                if not file_t.exists():
                    logger.warning(f"target file not found: {file_t}")
                    continue

                cur = file.read_json(dir_output / "big_blocks_id.json")
                expect = file.read_json(file_t)

                if cur != expect:
                    logger.debug(f"{dir_output.stem} changed")
                    for i in range(len(cur)):
                        if cur[i] != expect[i]:
                            add_list = []
                            del_list = []
                            for j in range(len(cur[i])):
                                if cur[i][j] not in expect[i]:
                                    add_list.append(cur[i][j])
                            for j in range(len(expect[i])):
                                if expect[i][j] not in cur[i]:
                                    del_list.append(expect[i][j])
                            logger.debug(f"page {i}, add: {add_list}, del: {del_list}")
