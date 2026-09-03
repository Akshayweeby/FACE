"""Search public web pages and rank them using local face embeddings."""

from __future__ import annotations

import os
import tempfile
import time
from pathlib import Path
from typing import Any, Iterable

import cv2
import numpy as np
import requests

from face_detection.detector import FaceDetector
from .discovery import BingVisualSearch, DiscoveryError, SerpApiGoogleLens


class SocialMediaSearchEngine:
    """Discover provider-returned candidates and verify faces locally.

    Provide ``BING_VISUAL_SEARCH_KEY`` for local JPG/PNG uploads, or
    ``SERPAPI_KEY`` plus a public ``image_url`` for Google Lens. The provider
    search is always performed in normal mode; ``mock_candidates`` is intended
    only for unit tests/development.
    """

    def __init__(
        self,
        bing_api_key: str | None = None,
        serpapi_api_key: str | None = None,
        face_detector: FaceDetector | None = None,
        timeout: float = 30.0,
        max_candidates: int = 20,
    ) -> None:
        self.bing_api_key = bing_api_key or os.getenv("BING_VISUAL_SEARCH_KEY")
        self.serpapi_api_key = serpapi_api_key or os.getenv("SERPAPI_KEY")
        self.face_detector = face_detector or FaceDetector()
        self.timeout = timeout
        self.max_candidates = max_candidates

    @staticmethod
    def _result(start: float, matches: list[dict[str, Any]], method: str, error: str | None = None) -> dict[str, Any]:
        output = {
            "success": bool(matches),
            "posts_found": len(matches),
            "search_method": method,
            "matches": matches[:3],
            "search_time_ms": round((time.perf_counter() - start) * 1000, 2),
        }
        if error:
            output["error"] = error
        return output

    @staticmethod
    def _cosine_similarity(left: Iterable[float], right: Iterable[float]) -> float:
        a, b = np.asarray(list(left), dtype=np.float32), np.asarray(list(right), dtype=np.float32)
        if a.shape != b.shape or not a.size:
            return 0.0
        denominator = float(np.linalg.norm(a) * np.linalg.norm(b))
        return max(0.0, min(1.0, float(np.dot(a, b) / denominator))) if denominator else 0.0

    def _download_and_encode(self, image_url: str) -> dict[str, Any] | None:
        try:
            response = requests.get(image_url, timeout=self.timeout, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "image/jpeg").split(";", 1)[0]
            suffix = ".png" if content_type == "image/png" else ".jpg"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as handle:
                handle.write(response.content)
                local_path = Path(handle.name)
            try:
                result = self.face_detector.detect_and_encode(local_path)
            finally:
                local_path.unlink(missing_ok=True)
            return result if result.get("success") else None
        except (requests.RequestException, OSError):
            return None

    def _rank(self, candidates: Iterable[dict[str, Any]], embedding: list[float]) -> list[dict[str, Any]]:
        ranked = []
        for candidate in list(candidates)[: self.max_candidates]:
            encoded = self._download_and_encode(candidate["image_url"])
            if not encoded:
                continue
            similarity = self._cosine_similarity(embedding, encoded["embedding"])
            ranked.append({
                "url": candidate["url"],
                "image_url": candidate["image_url"],
                "caption": candidate.get("title", ""),
                "timestamp": None,
                "user": {"handle": None, "name": None},
                "match_confidence": round(similarity, 6),
                "face_confidence": encoded["confidence"],
            })
        ranked.sort(key=lambda item: item["match_confidence"], reverse=True)
        for rank, item in enumerate(ranked[:3], start=1):
            item["rank"] = rank
        return ranked[:3]

    def find_posts(
        self,
        image_path: str | Path | None = None,
        face_embedding: list[float] | None = None,
        image_url: str | None = None,
        mock_candidates: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Search, verify, and return ranked publicly discovered candidates.

        ``image_path`` is required for Bing. ``image_url`` must be publicly
        reachable for Google Lens. An embedding alone is sufficient for local
        verification but cannot be sent to an image-search provider.
        """
        start = time.perf_counter()
        if face_embedding is None:
            if not image_path:
                return self._result(start, [], "none", "Provide image_path or face_embedding")
            encoded = self.face_detector.detect_and_encode(image_path)
            if not encoded.get("success"):
                return self._result(start, [], "face_detection", encoded.get("error", "Face detection failed"))
            face_embedding = encoded["embedding"]

        method_parts = []
        candidates = mock_candidates or []
        if mock_candidates is None:
            try:
                if image_path and self.bing_api_key:
                    candidates.extend(BingVisualSearch(self.bing_api_key, self.timeout).search(str(image_path)))
                    method_parts.append("bing_visual_search")
                if image_url and self.serpapi_api_key:
                    candidates.extend(SerpApiGoogleLens(self.serpapi_api_key, self.timeout).search(image_url))
                    method_parts.append("google_lens_serpapi")
            except DiscoveryError as exc:
                return self._result(start, [], "+".join(method_parts) or "configured_provider", str(exc))
        if not method_parts and mock_candidates is None:
            return self._result(start, [], "none", "Configure BING_VISUAL_SEARCH_KEY or SERPAPI_KEY and provide the required image input")
        matches = self._rank(candidates, face_embedding)
        return self._result(start, matches, "+".join(method_parts) or "mock", None if matches else "No provider candidate could be verified locally")
