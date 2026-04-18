import os

import cv2
import pytest

from src.img.processor import ImageProcessor


def test_match_covenant():
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


def test_match_mystic():
    templ1 = cv2.imread(os.path.join("assets", "shop-with-mystic-1.png"))
    if templ1 is None:
        pytest.fail("should be able to load shop-with-mystic-1.png")

    templ2 = cv2.imread(os.path.join("assets", "shop-with-mystic-2.png"))
    if templ1 is None:
        pytest.fail("should be able to load shop-with-mystic-2.png")

    mystic = cv2.imread(os.path.join("assets", "mystic.png"))
    if mystic is None:
        pytest.fail("should be able to load mystic image")

    templs = [templ1, templ2]
    matched = False
    for templ in templs:
        processor = ImageProcessor(templ)
        result = processor.match_loc(mystic)
        if result is not None:
            matched = True
            break

    assert matched, "at least some template image should match mystic"
