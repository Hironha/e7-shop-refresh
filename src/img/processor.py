import cv2
from cv2.typing import MatLike


class ImageProcessor:
    def __init__(self, templ: MatLike, threshold=0.7):
        self.__templ = templ
        self.__threshold = threshold

    def match_loc(self, target: MatLike) -> tuple[int, int] | None:
        templ_gray = cv2.cvtColor(self.__templ, cv2.COLOR_BGR2GRAY)
        target_gray = cv2.cvtColor(target, cv2.COLOR_BGR2GRAY)
        w, h = target_gray.shape[::-1]

        result = cv2.matchTemplate(target_gray, templ_gray, cv2.TM_CCOEFF_NORMED)
        # For TM_CCOEFF_NORMED, max_loc is the top-left corner of the best match
        _min_val, max_val, _min_loc, max_loc = cv2.minMaxLoc(result)
        if max_val < self.__threshold:
            return None

        middle = (max_loc[0] + w / 2, max_loc[1] + h / 2)
        return middle
        # draw a rectoangle for debugging
        # bottom_right = (max_loc[0] + w, max_loc[1] + h)
        # img = cv2.rectangle(self.__templ, max_loc, bottom_right, (0, 255, 0), 2)

        # cv2.imshow("Detected", img)
        # cv2.waitKey(0)
        # return max_loc[0], max_loc[1]
