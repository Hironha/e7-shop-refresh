import argparse
import datetime as dt
import os
import pathlib
import random
import sys
import time
from typing import Any

import cv2
import numpy as np
import pyautogui
import pygetwindow as pgw
from mss import mss

import ascii
from img.processor import ImageProcessor
from log import Logger, LogLevel
from metrics import (
    MetricsOverview,
    MetricsProcessor,
    MetricsStorage,
    MetricsSummary,
    RefreshMetric,
)
from result import Error, Ok

PROGRAM_NAME = "e7-shop-refresh"
EPIC7_TITLES = ["Epic Seven"]
COVENANT_MEDALS = "Covenant Medals"
MYSTIC_MEDALS = "Mystic Medals"


class Window:
    def __init__(self, left: int, top: int, width: int, height: int):
        self.__left = left
        self.__top = top
        self.__width = width
        self.__height = height

    @property
    def left(self) -> int:
        return self.__left

    @property
    def top(self) -> int:
        return self.__top

    @property
    def width(self) -> int:
        return self.__width

    @property
    def height(self) -> int:
        return self.__height

    def to_string(self) -> str:
        return f"w:{self.width},h:{self.height},l:{self.left},t:{self.top}"


class GameTitle:
    def __init__(self, options: list[str]):
        self.__options = options

    def match(self, title: str) -> bool:
        for opt in self.__options:
            if self.__normalize(opt) == self.__normalize(title):
                return True
        return False

    def __normalize(self, title: str) -> str:
        return title.replace(" ", "").lower()


class ShopItem:
    def __init__(self, image: np.ndarray, name: str):
        self.__image = image
        self.__name = name

    @property
    def image(self) -> np.ndarray:
        return self.__image

    @property
    def name(self) -> str:
        return self.__name


class RefreshStats:
    def __init__(self):
        self.__iterations: int = 0
        self.__count: dict[str, int] = {}

    @property
    def iterations(self) -> int:
        return self.__iterations

    def incr_iterations(self) -> None:
        self.__iterations += 1

    def incr_item(self, item_name: str) -> None:
        if item_name in self.__count:
            self.__count[item_name] += 1
        else:
            self.__count[item_name] = 1

    def count(self, item_name: str) -> int:
        if item_name in self.__count:
            return self.__count[item_name]
        return 0

    def rate(self, item_name: str) -> float:
        if self.__iterations == 0 or item_name not in self.__count:
            return 0
        return self.__count[item_name] / self.__iterations


class ShopRefresher:
    def __init__(
        self,
        items: list[ShopItem],
        window: Window,
        logger: Logger,
        metric_storage: MetricsStorage | None,
    ):
        self.__logger = logger
        self.__items = items
        self.__window = window
        self.__metric_storage = metric_storage
        self.__delay_secs = 0.4
        self.__move_delay_secs = 0.3
        self.__stats = RefreshStats()

    def __del__(self) -> None:
        iterations = self.__stats.iterations
        self.__logger.info("Finished executing shop refresher")
        self.__logger.info(f"Total shop refresh iterations: [{iterations}]")
        for item in self.__items:
            count = self.__stats.count(item.name)
            pct = self.__stats.rate(item.name) * 100
            self.__logger.info(
                f"Stats [{item.name}]: {count}/{iterations} ({pct:.2f}%)"
            )

        # TODO: improve code organization to reduce duplication of calculations
        if self.__metric_storage is not None:
            covenant = next(i for i in self.__items if i.name == COVENANT_MEDALS)
            covenant_count = self.__stats.count(covenant.name)
            mystic = next(i for i in self.__items if i.name == MYSTIC_MEDALS)
            mystic_count = self.__stats.count(mystic.name)

            self.__logger.info("Storing metric into persistent storage...")
            now = dt.datetime.now(dt.UTC)
            metric = RefreshMetric(now, iterations, covenant_count, mystic_count)
            result = self.__metric_storage.store(metric)
            match result:
                case Error(error):
                    self.__logger.info(f"Failed storing metrics: {error}")

    def start(self, times: int):
        monitor = {
            "left": self.__window.left,
            "top": self.__window.top,
            "width": self.__window.width,
            "height": self.__window.height,
        }
        with mss() as sct:
            for i in range(times):
                self.__logger.info(f"Running shop refresh iteration [{i}]")
                self.__stats.incr_iterations()

                found_items: list[str] = []

                # without scroll
                screenshot = np.array(sct.grab(monitor))
                processor = ImageProcessor(screenshot)
                self.__process_screenshot(processor, found_items)

                self.__scroll()

                # with scroll, hopefully someday SG removes the scroll from
                # the secret shop...
                screenshot = np.array(sct.grab(monitor))
                processor = ImageProcessor(screenshot)
                self.__process_screenshot(processor, found_items)

                self.__refresh()
                self.__logger.info(f"Finished shop refresh iteration [{i}]")
                # use bigger delay to wait for shop refresh animation
                time.sleep(self.__rand_time(1.25))

    def __process_screenshot(
        self, processor: ImageProcessor, found_items: list[str]
    ) -> None:
        for item in self.__items:
            loc = processor.match_loc_sift(item.image)
            if loc is None:
                self.__logger.warning(f"Could not find {item.name} in screenshot")
            elif item.name not in found_items:
                self.__logger.info(f"Found item {item.name} in screenshot")
                if self.__buy(loc):
                    found_items.append(item.name)
                    self.__stats.incr_item(item.name)

    def __buy(self, item_loc: tuple[int, int]) -> bool:
        _item_x, item_y = item_loc
        buy_x = self.__window.left + self.__window.width * 0.9
        buy_x = self.__rand(int(buy_x))

        buy_y = self.__window.top + item_y * 1.05
        buy_y = self.__rand(int(buy_y))

        if not self.__is_whithin_window((buy_x, buy_y)):
            return False

        pyautogui.moveTo(buy_x, buy_y, duration=self.__move_delay_secs)
        pyautogui.click(interval=0.5)

        time.sleep(self.__rand_time(self.__delay_secs))

        confirm_x = self.__window.left + self.__window.width * 0.57
        confirm_x = self.__rand(int(confirm_x))

        confirm_y = self.__window.top + self.__window.height * 0.73
        confirm_y = self.__rand(int(confirm_y))

        pyautogui.moveTo(confirm_x, confirm_y, duration=self.__move_delay_secs)
        pyautogui.click(interval=0.5)

        time.sleep(self.__rand_time(self.__delay_secs))
        return True

    def __scroll(self) -> None:
        self.__logger.debug("Starting to scroll shop until the end")
        x = self.__window.left + self.__window.width * 0.59
        x = self.__rand(int(x))

        y = self.__window.top + self.__window.height * 0.51
        y = self.__rand(int(y))

        pyautogui.moveTo(x, y, duration=self.__move_delay_secs)
        self.__logger.debug(f"Moved cursor to x: {x} y: {y}")

        time.sleep(0.05)

        pyautogui.mouseDown(button="left")
        scroll_y = self.__window.top + self.__window.height * 0.2
        self.__rand(int(scroll_y))

        pyautogui.moveTo(x, scroll_y, duration=0.1)
        pyautogui.mouseUp(button="left")

        # wait for shop scroll animation
        time.sleep(self.__rand_time(self.__delay_secs))
        self.__logger.debug("Shop scroll finished")

    def __refresh(self):
        self.__logger.debug("Starting to click shop refresh")
        refresh_x = self.__window.left + self.__window.width * 0.17
        refresh_x = self.__rand(int(refresh_x))

        refresh_y = self.__window.top + self.__window.height * 0.90
        refresh_y = self.__rand(int(refresh_y))

        pyautogui.moveTo(refresh_x, refresh_y, duration=self.__move_delay_secs)
        pyautogui.click(interval=0.5)

        time.sleep(self.__rand_time(self.__delay_secs))

        confirm_x = self.__window.left + self.__window.width * 0.56
        confirm_x = self.__rand(int(confirm_x))

        confirm_y = self.__window.top + self.__window.height * 0.63
        confirm_y = self.__rand(int(confirm_y))

        pyautogui.moveTo(confirm_x, confirm_y, duration=self.__move_delay_secs)
        pyautogui.click(interval=0.5)

        time.sleep(self.__rand_time(self.__delay_secs))
        self.__logger.debug("Finished refreshing shop")

    def __is_whithin_window(self, loc: tuple[int, int]) -> bool:
        x, y = loc
        y_min = self.__window.top
        y_max = self.__window.top + self.__window.height
        x_min = self.__window.left
        x_max = self.__window.left + self.__window.width
        return x_min <= x <= x_max and y_min <= y <= y_max

    def __rand(self, value: int, range: int = 10) -> int:
        rand = random.randint(0, max(range, 1))
        return value + rand

    def __rand_time(self, time: float) -> float:
        rand = self.__rand(15) / 100
        negative = int(rand) % 2 == 0
        if negative:
            return time - rand
        return time + rand


def find_epic_seven_window() -> Any:
    game_title = GameTitle(EPIC7_TITLES)
    windows = pgw.getAllWindows()
    for w in windows:
        title = str(w.title)
        if game_title.match(title):
            return w
    return None


def handle_shop_refresh(args: argparse.Namespace) -> None:
    verbose = args.verbose is not None
    level = LogLevel.DEBUG if verbose else LogLevel.ERROR
    logger = Logger(size=2, level=level)

    covenant_img = cv2.imread(os.path.join("assets", "covenant.png"))
    assert covenant_img is not None, "Failed loading covenant image"
    covenant = ShopItem(covenant_img, COVENANT_MEDALS)

    mystic_img = cv2.imread(os.path.join("assets", "mystic.png"))
    assert mystic_img is not None, "Failed loading mystic image"
    mystic = ShopItem(mystic_img, MYSTIC_MEDALS)

    items = [covenant, mystic]

    window = find_epic_seven_window()
    if window is None:
        logger.error("Epic Seven game window not found on current screen")
        sys.exit(0)

    window.activate()
    time.sleep(2)

    window = Window(window.left, window.top, window.width, window.height)
    logger.info(
        f"Detected Epic Seven window with following configuration: {window.to_string()}"
    )

    path = pathlib.Path.cwd().joinpath("metrics.csv")
    metric_storage = MetricsStorage(str(path), logger)

    refresher = ShopRefresher(items, window, logger, metric_storage)
    refresher.start(times=1_000)


def build_overview_grid_data(overview: list[MetricsOverview]) -> list[list[str]]:
    headers = [
        "Date",
        "Iterations",
        "Cov.",
        "Cov. BM",
        "Cov. Rating",
        "Mys.",
        "Mys. Medals",
        "Mys. Rating",
        "SS",
        "Gold",
    ]
    data: list[list[str]] = [headers]
    for item in overview:
        row = [
            item.created_at.strftime("%Y-%m-%d"),
            str(item.iterations),
            str(item.covenants),
            str(item.covenant_bookmarks),
            f"{item.covenant_rating:.2f}%",
            str(item.mystics),
            str(item.mystic_medals),
            f"{item.mystic_rating:.2f}%",
            f"{item.skystones:,}",
            f"{item.gold:,}",
        ]
        data.append(row)
    return data


def build_summary_grid_data(summary: MetricsSummary) -> list[list[str]]:
    covenant_rating_pct = summary.covenant_rating * 100
    mystic_rating_pct = summary.mystic_rating * 100

    return [
        ["Summary", "Covenants", "Mystics", "Total"],
        ["Count", str(summary.covenants), str(summary.mystics), "-"],
        [
            "Currency",
            str(summary.covenant_bookmarks),
            str(summary.msytic_medals),
            "-",
        ],
        ["Rating", f"{covenant_rating_pct:.2f}%", f"{mystic_rating_pct:.2f}%", "_"],
        [
            "Gold",
            f"{summary.covenant_gold:,}",
            f"{summary.mystic_gold:,}",
            f"{summary.gold:,}",
        ],
        ["Skystones", "-", "-", str(summary.skystones)],
        ["Iterations", "-", "-", str(summary.iterations)],
    ]


def handle_metrics_head(storage: MetricsStorage, logger: Logger, head: int) -> None:
    if head <= 0:
        logger.error("Metrics head <n> should be greater than 0")
        return

    head_metrics: list[RefreshMetric]
    match storage.head(head):
        case Ok(m):
            head_metrics = m
        case Error(e):
            logger.error(f"Failed getting first {head} metrics from storage: {e}")
            return

    processor = MetricsProcessor()
    overview = processor.overview(head_metrics)
    grid_data = build_overview_grid_data(overview)

    grid_builder = ascii.GridBuilder()
    grid = grid_builder.build(grid_data)
    print(grid)
    return


def handle_metrics_tail(storage: MetricsStorage, logger: Logger, tail: int) -> None:
    if tail <= 0:
        logger.error("Metrics tail <n> should be greater than 0")
        return
    tail_metrics: list[RefreshMetric]
    match storage.tail(tail):
        case Ok(m):
            tail_metrics = m
        case Error(e):
            logger.error(f"Failed getting last {tail} metrics from storage: {e}")
            return

    processor = MetricsProcessor()
    overview = processor.overview(tail_metrics)
    grid_data = build_overview_grid_data(overview)

    grid_builder = ascii.GridBuilder()
    grid = grid_builder.build(grid_data)
    print(grid)
    return


def handle_calculate_metrics(args: argparse.Namespace) -> None:
    logger = Logger(size=2, level=LogLevel.ERROR)
    filepath = pathlib.Path.cwd().joinpath("metrics.csv")
    storage = MetricsStorage(str(filepath), logger)

    if args.head is not None:
        handle_metrics_head(storage, logger, int(args.head))
        return
    elif args.tail is not None:
        handle_metrics_tail(storage, logger, int(args.tail))
        return

    all_metrics: list[RefreshMetric]
    match storage.get_all_metrics():
        case Ok(metrics):
            all_metrics = metrics
        case Error(error):
            logger.error(f"Failed getting all metrics from storage: {error}")
            return

    processor = MetricsProcessor()
    summary = processor.summarize(all_metrics)
    grid_data = build_summary_grid_data(summary)

    builder = ascii.GridBuilder()
    grid = builder.build(grid_data)
    print(grid)


def main():
    parser = argparse.ArgumentParser(
        prog=PROGRAM_NAME,
        description="Small script to automatically refresh Epic Seven refresh shop",
    )
    subparsers = parser.add_subparsers(
        title="commands", help="Available commands", required=True
    )

    refresh_parser = subparsers.add_parser(
        "refresh",
        help="Start automatically refreshing Epic Seven shop. NOTES: Epic Seven should be running and already be on the Refresh Shop screen.",
    )
    refresh_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output with logs on DEBUG level",
    )
    refresh_parser.set_defaults(func=handle_shop_refresh)

    metrics_parser = subparsers.add_parser(
        "metrics",
        help='Calculate metrics based on the "metrics.csv" file that is automatically generated after a run.',
    )

    tail_head = metrics_parser.add_mutually_exclusive_group()
    tail_head.add_argument(
        "--head",
        nargs="?",
        type=int,
        const=10,
        default=None,
        metavar="N",
        help="Show first <n> refresh metrics.",
    )
    tail_head.add_argument(
        "--tail",
        nargs="?",
        type=int,
        const=10,
        default=None,
        metavar="N",
        help="Show last <n> refresh metrics.",
    )
    metrics_parser.set_defaults(func=handle_calculate_metrics)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
