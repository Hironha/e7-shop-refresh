from typing import Any

import cv2
import numpy as np
from cv2.typing import MatLike

FLANN_INDEX_KDTREE = 1


class ImageProcessor:
    def __init__(self, templ: MatLike):
        self.__templ = templ
        self.__sift = cv2.SIFT.create()

        index_params: dict[str, bool | int | float | str] = {
            "algorithm": FLANN_INDEX_KDTREE,
            "trees": 5,
        }
        search_params: dict[str, bool | int | float | str] = {"checks": 50}
        self.__flann = cv2.FlannBasedMatcher(index_params, search_params)

    # Match image location using SIFT algorithm
    def match_loc_sift(self, target: MatLike) -> tuple[int, int] | None:
        templ_gray = cv2.cvtColor(self.__templ, cv2.COLOR_BGR2GRAY)
        kp_templ, des_templ = self.__sift.detectAndCompute(templ_gray, None)

        target_gray = cv2.cvtColor(target, cv2.COLOR_BGR2GRAY)
        kp_target, des_target = self.__sift.detectAndCompute(target_gray, None)

        if des_templ is None or len(des_templ) < 2:
            return None

        matches = self.__flann.knnMatch(des_target, des_templ, k=2)

        # Lowe's ratio test to filter noise
        good_matches: list[cv2.DMatch] = []
        for m, n in matches:
            if m.distance < 0.5 * n.distance:
                good_matches.append(m)

        if len(good_matches) <= 10:
            return None

        # Get coordinates of matched points
        target_pts: Any = [kp_target[m.queryIdx].pt for m in good_matches]
        src_pts = np.float32(target_pts).reshape(-1, 1, 2)

        templ_pts: Any = [kp_templ[m.trainIdx].pt for m in good_matches]
        dst_pts = np.float32(templ_pts).reshape(-1, 1, 2)

        # Find the perspective transform (the "location")
        M, _mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

        # Calculate the center point of the item in the screenshot
        h, w = target_gray.shape
        pts: Any = [[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]
        pts = np.float32(pts).reshape(-1, 1, 2)
        dst = cv2.perspectiveTransform(pts, M)

        # Calculate center X, Y
        center = np.mean(dst, axis=0)[0]
        return int(center[0]), int(center[1])

    def match_loc(self, target: MatLike, threshold=0.675) -> tuple[int, int] | None:
        templ_gray = cv2.cvtColor(self.__templ, cv2.COLOR_BGR2GRAY)
        target_gray = cv2.cvtColor(target, cv2.COLOR_BGR2GRAY)
        w, h = target_gray.shape[::-1]

        result = cv2.matchTemplate(target_gray, templ_gray, cv2.TM_CCOEFF_NORMED)
        # For TM_CCOEFF_NORMED, max_loc is the top-left corner of the best match
        _min_val, max_val, _min_loc, max_loc = cv2.minMaxLoc(result)
        if max_val < threshold:
            return None

        middle = (max_loc[0] + w / 2, max_loc[1] + h / 2)
        return middle
