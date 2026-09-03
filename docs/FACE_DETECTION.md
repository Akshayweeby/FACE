# Face detection and embedding

Stage 1 exposes `FaceDetector` from `face_detection.detector`:

```python
from face_detection.detector import FaceDetector

result = FaceDetector().detect_and_encode("test_image.jpg")
if result["success"]:
    embedding = result["embedding"]  # normalized list[float], length 128
```

## Libraries and model

- Python 3.9+
- `opencv-contrib-python-headless` for image decoding, YuNet detection, and SFace embeddings
- `numpy` for model output handling
- YuNet (`face_detection_yunet_2023mar.onnx`) detects faces and provides confidence scores.
- SFace (`face_recognition_sface_2021dec.onnx`) produces a normalized 128-dimensional embedding.

Models are downloaded once to `~/.cache/face_detection_models`. For offline deployment, place both ONNX files in a directory and pass `model_dir=...`; set `auto_download=False`.

## Output

Every call returns JSON-serializable data. A successful response contains `success`, `faces_detected`, `embedding`, `embedding_dimension`, `confidence`, `bounding_box`, `model_used`, `processing_time_ms`, and `faces`. The largest face is encoded; `faces` contains every usable detection. Failure responses retain the same core fields and add `error` and `error_code` (`invalid_type`, `file_not_found`, `invalid_image`, `low_quality`, `no_face`, or inference/embedding errors).

## Installation and performance

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

On a typical modern CPU, warm inference is approximately 100–500 ms for a 720p image; the first call also downloads and loads the models. Actual timing depends on CPU and image size. No GPU is required.

## Limitations

The module encodes only the largest face, is sensitive to extreme pose/occlusion and very small faces, and does not identify a person by itself. Confidence is a detection score adjusted by a simple blur-quality check; it is not a probability of identity. Person 2 should compare embeddings using a calibrated distance threshold and treat results as personal biometric data.
