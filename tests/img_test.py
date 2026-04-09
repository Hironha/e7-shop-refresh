import os

import cv2
import pytest

from src.img.processor import ImageProcessor


def test_match():
    templ = cv2.imread(os.path.join("assets", "shop-with-covenant.png"))
    if templ is None:
        pytest.fail("should be able to load shop image")

    covenant = cv2.imread(os.path.join("assets", "covenant.png"))
    if covenant is None:
        pytest.fail("should be able to load covenant image")

    mystic = cv2.imread(os.path.join("assets", "mystic.png"))
    if mystic is None:
        pytest.fail("should be able to load covenant image")

    processor = ImageProcessor(templ)
    result = processor.match_loc(covenant)
    assert result is not None, "covenant should match image in template"

    result = processor.match_loc(mystic)
    assert result is None, "mystic should not match image in template"
