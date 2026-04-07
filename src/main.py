import pyautogui

import log


def hello_world() -> None:
    logger = log.Logger()
    logger.info("Hello, World")
    logger.warn("Hello, World")
    logger.debug("Hello, World")
    logger.error("Hello, World")


def main() -> None:
    print(pyautogui.position())
    hello_world()


if __name__ == "__main__":
    main()
