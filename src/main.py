import os
import time
from typing import Any

import cv2
import numpy as np
import pyautogui
import pygetwindow as pgw
from mss import mss

from img.processor import ImageProcessor
from log import Logger

EPIC7_TITLES = ["Epic Seven"]


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
        return self.__left

    @property
    def width(self) -> int:
        return self.__width

    @property
    def height(self) -> int:
        return self.__height


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


class ShopRefresher:
    def __init__(self, items: list[ShopItem], window: Window, logger: Logger):
        self.__logger = logger
        self.__items = items
        self.__window = window
        self.__delay_secs = 0.35
        self.__move_delay_secs = 0.25

    def start(self, times: int):
        monitor = {
            "left": self.__window.left,
            "top": self.__window.top,
            "width": self.__window.width,
            "height": self.__window.height,
        }
        with mss() as sct:
            while "Automatically refreshing shop":
                # without scroll
                screenshot = np.array(sct.grab(monitor))
                processor = ImageProcessor(screenshot)
                for item in self.__items:
                    loc = processor.match_loc(item.image)
                    if loc is None:
                        self.__logger.warn(f"Could not find {item.name} in screenshot")
                    else:
                        self.__logger.info(f"Found item {item.name} in screenshot")
                        self.__buy(loc)

                self.__scroll()

                # with scroll
                screenshot = np.array(sct.grab(monitor))
                processor = ImageProcessor(screenshot)
                for item in self.__items:
                    loc = processor.match_loc(item.image)
                    if loc is None:
                        self.__logger.warn(f"Could not find {item.name} in screenshot")
                    else:
                        self.__logger.info(f"Found item {item.name} in screenshot")
                        self.__buy(loc)

                self.__refresh()
                # use bigger delay to wait for shop refresh animation
                time.sleep(1.5)

    def __buy(self, item_loc: tuple[int, int]) -> None:
        _item_x, item_y = item_loc
        buy_x = self.__window.left + self.__window.width * 0.84
        buy_y = self.__window.top + item_y * 1.05
        pyautogui.moveTo(buy_x, buy_y, duration=self.__move_delay_secs)
        pyautogui.click(interval=0.5)

        time.sleep(self.__delay_secs)

        confirm_x = self.__window.left + self.__window.width * 0.57
        confirm_y = self.__window.top + self.__window.height * 0.70
        pyautogui.moveTo(confirm_x, confirm_y, duration=self.__move_delay_secs)
        pyautogui.click(interval=0.5)

        time.sleep(self.__delay_secs)
        pass

    def __scroll(self) -> None:
        self.__logger.debug("Starting to scroll shop until the end")
        x = self.__window.left + self.__window.width * 0.59
        y = self.__window.top + self.__window.height * 0.51
        pyautogui.moveTo(x, y, duration=self.__move_delay_secs)
        self.__logger.debug(f"Moved cursor to x: {x} y: {y}")

        time.sleep(0.05)

        pyautogui.mouseDown(button="left")
        scroll_y = self.__window.top + self.__window.height * 0.2
        pyautogui.moveTo(x, scroll_y, duration=0.1)
        pyautogui.mouseUp(button="left")

        # wait for shop scroll animation
        time.sleep(self.__delay_secs)
        self.__logger.debug("Shop scroll finished")

    def __refresh(self):
        self.__logger.debug("Starting to click shop refresh")
        refresh_x = self.__window.left + self.__window.width * 0.17
        refresh_y = self.__window.top + self.__window.height * 0.90
        pyautogui.moveTo(refresh_x, refresh_y, duration=self.__move_delay_secs)
        pyautogui.click(interval=0.5)

        time.sleep(self.__delay_secs)

        confirm_x = self.__window.left + self.__window.width * 0.56
        confirm_y = self.__window.top + self.__window.height * 0.61
        pyautogui.moveTo(confirm_x, confirm_y, duration=self.__move_delay_secs)
        pyautogui.click(interval=0.5)

        time.sleep(self.__delay_secs)
        self.__logger.debug("Finished refreshing shop")


def find_epic_seven_window() -> Any:
    game_title = GameTitle(EPIC7_TITLES)
    windows = pgw.getAllWindows()
    for w in windows:
        title = str(w.title)
        if game_title.match(title):
            return w
    return None


def main():
    logger = Logger(size=2)

    covenant_img = cv2.imread(os.path.join("assets", "covenant.png"))
    assert covenant_img is not None, "Failed loading covenant image"
    covenant = ShopItem(covenant_img, "Covenant Medals")

    mystic_img = cv2.imread(os.path.join("assets", "mystic.png"))
    assert mystic_img is not None, "Failed loading mystic image"
    mystic = ShopItem(mystic_img, "Mystic Medals")

    items = [covenant, mystic]

    window = find_epic_seven_window()
    if window is None:
        raise Exception("Could not detect Epic Seven game open")
    window.activate()
    time.sleep(2)

    window = Window(window.left, window.top, window.width, window.height)
    refresher = ShopRefresher(items, window, logger)
    refresher.start(10)


if __name__ == "__main__":
    main()
