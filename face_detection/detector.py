"""Face detection and 128-dimensional face embeddings.

The implementation uses OpenCV Zoo's YuNet detector and SFace recognizer.
Models are downloaded on first use into a local cache, or can be supplied
explicitly through ``model_dir``.
"""

from __future__ import annotations

import hashlib
import time
import urllib.request
from pathlib import Path
from typing import Any

try:
    import cv2
except ImportError as exc:  # pragma: no cover - exercised in installation environments
    raise ImportError(
        "OpenCV is required. Install dependencies with: pip install -r requirements.txt"
    ) from exc


class FaceDetector:
    """Detect faces and return a normalized SFace embedding.

    The largest detected face is encoded. All detections are reported in the
    ``faces`` field, while ``bounding_box`` describes the encoded face.
    """

    MODEL_NAME = "opencv_yunet_sface"
    EMBEDDING_DIMENSION = 128
    _MODELS = {
        "detector": {
            "filename": "face_detection_yunet_2023mar.onnx",
            "url": "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx",
            "sha256": "",
        },
        "recognizer": {
            "filename": "face_recognition_sface_2021dec.onnx",
            "url": "https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx",
            "sha256": "",
        },
    }

    def __init__(
        self,
        model_dir: str | Path | None = None,
        score_threshold: float = 0.6,
        nms_threshold: float = 0.3,
        min_face_size: int = 20,
        min_blur_variance: float = 25.0,
        auto_download: bool = True,
    ) -> None:
        self.model_dir = Path(model_dir or Path.home() / ".cache" / "face_detection_models")
        self.score_threshold = score_threshold
        self.nms_threshold = nms_threshold
        self.min_face_size = min_face_size
        self.min_blur_variance = min_blur_variance
        self.auto_download = auto_download
        self._detector = None
        self._recognizer = None

    def _model_path(self, key: str) -> Path:
        info = self._MODELS[key]
        path = self.model_dir / info["filename"]
        if not path.exists():
            if not self.auto_download:
                raise FileNotFoundError(f"Missing model file: {path}")
            self.model_dir.mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(info["url"], path)
        expected = info.get("sha256")
        if expected:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != expected:
                path.unlink(missing_ok=True)
                raise ValueError(f"SHA-256 mismatch for model {path.name}")
        return path

    def _load_models(self) -> None:
        if self._detector is not None and self._recognizer is not None:
            return
        detector_path = self._model_path("detector")
        recognizer_path = self._model_path("recognizer")
        self._detector = cv2.FaceDetectorYN.create(
            str(detector_path), "", (320, 320), self.score_threshold,
            self.nms_threshold, 5000
        )
        self._recognizer = cv2.FaceRecognizerSF.create(str(recognizer_path), "")

    @staticmethod
    def _error(start: float, message: str, code: str) -> dict[str, Any]:
        return {
            "success": False,
            "faces_detected": 0,
            "embedding": None,
            "embedding_dimension": 128,
            "confidence": 0.0,
            "bounding_box": None,
            "model_used": FaceDetector.MODEL_NAME,
            "processing_time_ms": round((time.perf_counter() - start) * 1000, 2),
            "error": message,
            "error_code": code,
        }

    def detect_and_encode(self, image_path: str | Path) -> dict[str, Any]:
        """Return a JSON-serializable result for a JPG or PNG image path."""
        start = time.perf_counter()
        path = Path(image_path)
        if path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
            return self._error(start, "Only JPG and PNG images are supported", "invalid_type")
        if not path.is_file():
            return self._error(start, f"Image file does not exist: {path}", "file_not_found")
        image = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if image is None or image.size == 0:
            return self._error(start, "The image could not be decoded", "invalid_image")
        height, width = image.shape[:2]
        if min(height, width) < self.min_face_size:
            return self._error(start, "Image is too small to contain a usable face", "low_quality")
        quality = float(cv2.Laplacian(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var())
        if quality < self.min_blur_variance:
            return self._error(start, "Image is too blurry or low quality", "low_quality")

        try:
            self._load_models()
            self._detector.setInputSize((width, height))
            _, detections = self._detector.detect(image)
        except Exception as exc:
            return self._error(start, f"Model inference failed: {exc}", "inference_error")
        if detections is None or len(detections) == 0:
            return self._error(start, "No face detected", "no_face")

        detected_faces = []
        for row in detections:
            x, y, w, h = [int(round(value)) for value in row[:4]]
            x, y = max(0, x), max(0, y)
            w, h = min(w, width - x), min(h, height - y)
            if w >= self.min_face_size and h >= self.min_face_size:
                detected_faces.append(({"x": x, "y": y, "width": w, "height": h,
                                        "confidence": round(float(row[14]), 6)}, row))
        if not detected_faces:
            return self._error(start, "No usable face detected", "no_face")

        selected, face_row = max(
            detected_faces, key=lambda item: item[0]["width"] * item[0]["height"]
        )
        try:
            def encode(row):
                aligned = self._recognizer.alignCrop(image, row)
                feature = self._recognizer.feature(aligned)
                vector = feature.reshape(-1).astype("float32")
                norm = float((vector @ vector) ** 0.5)
                if norm == 0:
                    raise ValueError("model returned a zero embedding")
                return [round(float(value), 8) for value in (vector / norm).tolist()]

            for face, row in detected_faces:
                face["embedding"] = encode(row)
            embedding = selected["embedding"]
        except Exception as exc:
            return self._error(start, f"Embedding extraction failed: {exc}", "embedding_error")

        confidence = selected["confidence"]
        quality_factor = (1.0 if self.min_blur_variance == 0 else
                         min(1.0, max(0.0, quality / (self.min_blur_variance * 10))))
        confidence = round(confidence * (0.7 + 0.3 * quality_factor), 6)
        return {
            "success": True,
            "faces_detected": len(detected_faces),
            "embedding": embedding,
            "embedding_dimension": len(embedding),
            "confidence": confidence,
            "bounding_box": {key: selected[key] for key in ("x", "y", "width", "height")},
            "model_used": self.MODEL_NAME,
            "processing_time_ms": round((time.perf_counter() - start) * 1000, 2),
            "faces": [face for face, _ in detected_faces],
        }
