from pathlib import Path

import cv2
import numpy as np

from face_detection.detector import FaceDetector


def write_image(path: Path, kind: str) -> None:
    image = np.zeros((240, 320, 3), dtype=np.uint8)
    if kind == "single":
        cv2.rectangle(image, (90, 45), (230, 205), (255, 255, 255), -1)
    elif kind == "multiple":
        cv2.rectangle(image, (20, 55), (135, 205), (255, 255, 255), -1)
        cv2.rectangle(image, (185, 35), (305, 215), (255, 255, 255), -1)
    elif kind == "poor":
        image[:] = 128
    cv2.imwrite(str(path), image)


class FakeDetector:
    def setInputSize(self, size):
        self.size = size

    def detect(self, image):
        if image.max() == 0:
            return None, None
        if image.mean() < 1:
            return None, None
        rows = [[20, 55, 115, 150, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.91]]
        if image[35, 185, 0] > 0:
            rows.append([185, 35, 120, 180, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.96])
        return None, np.array(rows, dtype=np.float32)


class FakeRecognizer:
    def alignCrop(self, image, face):
        return image

    def feature(self, image):
        return np.ones((1, 128), dtype=np.float32)


def detector(tmp_path, image_kind):
    path = tmp_path / f"{image_kind}.png"
    write_image(path, image_kind)
    instance = FaceDetector(auto_download=False, min_blur_variance=0)
    instance._detector = FakeDetector()
    instance._recognizer = FakeRecognizer()
    return instance, path


def test_single_face_image(tmp_path):
    instance, path = detector(tmp_path, "single")
    result = instance.detect_and_encode(path)
    assert result["success"] is True
    assert result["faces_detected"] == 1
    assert result["embedding_dimension"] == 128
    assert len(result["embedding"]) == 128


def test_multiple_face_image_encodes_largest(tmp_path):
    instance, path = detector(tmp_path, "multiple")
    result = instance.detect_and_encode(path)
    assert result["success"] is True
    assert result["faces_detected"] == 2
    assert result["bounding_box"]["width"] == 120


def test_no_face_image(tmp_path):
    instance, path = detector(tmp_path, "none")
    result = instance.detect_and_encode(path)
    assert result["success"] is False
    assert result["error_code"] == "no_face"


def test_poor_quality_image(tmp_path):
    path = tmp_path / "poor.png"
    write_image(path, "poor")
    instance = FaceDetector(auto_download=False, min_blur_variance=25)
    result = instance.detect_and_encode(path)
    assert result["success"] is False
    assert result["error_code"] == "low_quality"


def test_invalid_file_is_structured(tmp_path):
    path = tmp_path / "not-an-image.txt"
    path.write_text("not an image")
    result = FaceDetector(auto_download=False).detect_and_encode(path)
    assert result["success"] is False
    assert result["error_code"] == "invalid_type"
