"""Search public web pages and rank them using local face embeddings."""

from __future__ import annotations

import os
import re
import tempfile
import time
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

import cv2
import numpy as np
import requests

from face_detection.detector import FaceDetector
from .discovery import BingVisualSearch, DiscoveryError, SerpApiGoogleIdentity, SerpApiGoogleLens


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
        timeout: float = 15.0,
        max_candidates: int = 8,
        match_threshold: float | None = None,
        early_match_threshold: float | None = None,
    ) -> None:
        self.bing_api_key = os.getenv("BING_VISUAL_SEARCH_KEY") if bing_api_key is None else bing_api_key
        self.serpapi_api_key = os.getenv("SERPAPI_KEY") if serpapi_api_key is None else serpapi_api_key
        self.face_detector = face_detector or FaceDetector()
        self.timeout = timeout
        self.max_candidates = max_candidates
        configured_threshold = os.getenv("FACE_MATCH_THRESHOLD", "0.55")
        self.match_threshold = float(configured_threshold) if match_threshold is None else match_threshold
        configured_early_threshold = os.getenv("FACE_EARLY_MATCH_THRESHOLD", "0.90")
        self.early_match_threshold = (float(configured_early_threshold)
                                      if early_match_threshold is None else early_match_threshold)

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

    @staticmethod
    def _handle_from_url(url: str | None) -> str | None:
        """Extract a handle only when it is present in a real social URL."""
        if not url:
            return None
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        if not any(site in host for site in ("x.com", "twitter.com", "instagram.com", "facebook.com")):
            return None
        parts = [part for part in parsed.path.split("/") if part]
        if not parts or parts[0].lower() in {"status", "p", "posts", "share"}:
            return None
        return "@" + parts[0].lstrip("@")

    @staticmethod
    def _is_social_url(url: str | None) -> bool:
        if not url:
            return False
        host = urlparse(url).netloc.lower()
        return any(site in host for site in (
            "x.com", "twitter.com", "instagram.com", "facebook.com", "linkedin.com",
            "reddit.com", "youtube.com", "tiktok.com",
        ))

    @staticmethod
    def _plausible_person_name(name: str | None) -> bool:
        if not name:
            return False
        words = re.findall(r"[A-Za-z][A-Za-z'-]*", name)
        banned = {"award", "championship", "champion", "race", "racing", "team", "formula",
                  "red", "bull", "embassy", "official", "news", "wikipedia", "instagram", "facebook",
                  "prime", "minister", "president", "honourable", "honorable", "of", "the", "and",
                  "for", "on", "in", "to", "a", "an"}
        normalized = " ".join(word.lower() for word in words)
        generic_titles = {"prime minister", "president", "prime minister of india"}
        return 2 <= len(words) <= 4 and normalized not in generic_titles and not any(word.lower() in banned for word in words)

    @staticmethod
    def _name_from_identity_page_title(candidate: dict[str, Any]) -> str | None:
        """Read a name only from a strong identity-page title, not a headline."""
        url = candidate.get("url") or ""
        host = urlparse(url).netloc.lower()
        trusted_identity_hosts = ("wikipedia.org", "redbull.com", "formula1.com", "f1.com")
        if not any(identity_host in host for identity_host in trusted_identity_hosts):
            return None
        title = candidate.get("title") or ""
        for separator in (" - ", " | ", ": "):
            title = title.split(separator, 1)[0].strip()
            if re.fullmatch(r"(?:[A-Z]\.\s*)?[A-Z][A-Za-z'-]+(?:\s+[A-Z][A-Za-z'-]+){0,2}", title):
                return title
        return None

    def _enrich_identity(self, candidates: list[dict[str, Any]]) -> bool:
        """Use only Lens identity metadata or an explicit Wikipedia title."""
        for candidate in candidates[: self.max_candidates]:
            if self._plausible_person_name(candidate.get("provider_person_name")):
                continue
            name = self._name_from_identity_page_title(candidate)
            if not name or not self._plausible_person_name(name):
                continue
            candidate["provider_person_name"] = name
            candidate["identity_source"] = "google_lens_identity_page_title"
            # Candidates are all returned for this face query, so carry the
            # same provider identity to the ranked result if it wins.
            for other in candidates:
                if not self._plausible_person_name(other.get("provider_person_name")):
                    other["provider_person_name"] = name
                    other["identity_source"] = "google_lens_identity_page_title"
            return True
        if not self.serpapi_api_key:
            return False
        searched_queries: set[str] = set()
        for candidate in candidates[: self.max_candidates]:
            if self._plausible_person_name(candidate.get("provider_person_name")):
                continue
            query = (candidate.get("title") or "").split("|", 1)[0].strip()
            if (len(query) < 4 or query.lower() in {"prime minister", "president", "official"}
                    or query.lower() in searched_queries):
                continue
            searched_queries.add(query.lower())
            try:
                identity = SerpApiGoogleIdentity(self.serpapi_api_key, self.timeout).search_text(query)
            except DiscoveryError:
                continue
            if not identity or not self._plausible_person_name(identity.get("name")):
                continue
            candidate["provider_person_name"] = identity["name"]
            candidate["identity_source"] = identity.get("source")
            for other in candidates:
                if not self._plausible_person_name(other.get("provider_person_name")):
                    other["provider_person_name"] = identity["name"]
                    other["identity_source"] = identity.get("source")
            return True
        return False

    def _enrich_social_profiles(self, matches: list[dict[str, Any]]) -> bool:
        """Attach public profile URLs to matches with a provider identity."""
        if not self.serpapi_api_key:
            return False
        names = [match.get("provider_person_name") for match in matches
                 if self._plausible_person_name(match.get("provider_person_name"))]
        if not names:
            return False
        try:
            profiles = SerpApiGoogleIdentity(self.serpapi_api_key, self.timeout).search_social_profiles(names[0])
        except DiscoveryError:
            return False
        if not profiles:
            return False
        profile = profiles[0]
        for match in matches:
            subject = match.setdefault("subject", {})
            subject["handle"] = profile["handle"]
            subject["profile_url"] = profile["url"]
            subject["profile_source"] = profile["source"]
        return True

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
            if not candidate.get("image_url"):
                continue
            encoded = self._download_and_encode(candidate["image_url"])
            if not encoded:
                continue
            candidate_faces = encoded.get("faces") or []
            candidate_embeddings = [face.get("embedding") for face in candidate_faces if face.get("embedding")]
            if not candidate_embeddings and encoded.get("embedding"):
                candidate_embeddings = [encoded["embedding"]]
            if not candidate_embeddings:
                continue
            similarity = max(self._cosine_similarity(embedding, candidate_embedding)
                             for candidate_embedding in candidate_embeddings)
            if similarity < self.match_threshold:
                continue
            provider_name = candidate.get("provider_person_name")
            if not self._plausible_person_name(provider_name):
                provider_name = None
            post_handle = self._handle_from_url(candidate.get("url"))
            is_social = self._is_social_url(candidate.get("url"))
            ranked.append({
                "url": candidate["url"],
                "image_url": candidate["image_url"],
                "caption": candidate.get("title", ""),
                "timestamp": None,
                "user": {
                    "handle": post_handle,
                    "name": provider_name,
                },
                "subject": {
                    "handle": candidate.get("provider_subject_handle"),
                    "name": provider_name,
                    "identity_source": candidate.get("identity_source"),
                },
                "post_account": {"handle": post_handle},
                "match_confidence": round(similarity, 6),
                "match_threshold": self.match_threshold,
                "face_confidence": encoded["confidence"],
                "verified_match": True,
                "person_name": candidate.get("person_name"),
                "provider_person_name": provider_name,
                "is_social_source": is_social,
                "post_type": "social_post_or_profile" if is_social else "web_page",
                "source": candidate.get("source"),
            })
            # Lens orders candidates by relevance. Once the first strong face
            # match is found, avoid downloading and encoding the remaining
            # images serially.
            if similarity >= self.early_match_threshold and is_social:
                break
        social_matches = [item for item in ranked
                          if item["is_social_source"] and item["match_confidence"] >= max(self.match_threshold, 0.75)]
        if social_matches:
            social_ids = {id(item) for item in social_matches}
            ranked.sort(key=lambda item: (id(item) in social_ids, item["match_confidence"]), reverse=True)
        else:
            ranked.sort(key=lambda item: item["match_confidence"], reverse=True)
        for rank, item in enumerate(ranked[:3], start=1):
            item["rank"] = rank
        return ranked[:3]

    @staticmethod
    def _unverified_entities(candidates: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
        """Expose provider entity results when no image could be verified."""
        entities = []
        seen = set()
        for candidate in candidates:
            name, url = candidate.get("provider_person_name"), candidate.get("url")
            if not candidate.get("unverified") or not name or not url or url in seen:
                continue
            seen.add(url)
            host = urlparse(url).netloc.lower()
            handle = SocialMediaSearchEngine._handle_from_url(url)
            entities.append({
                "rank": len(entities) + 1,
                "url": url,
                "image_url": candidate.get("image_url"),
                "caption": candidate.get("title", ""),
                "timestamp": None,
                "user": {"handle": handle, "name": name},
                "subject": {"handle": candidate.get("provider_subject_handle"), "name": name,
                            "identity_source": candidate.get("identity_source")},
                "match_confidence": 0.0,
                "face_confidence": 0.0,
                "verified_match": False,
                "verification_status": "unverified_provider_entity",
                "provider_person_name": name,
                "source": candidate.get("source"),
            })
            if len(entities) == 3:
                break
        return entities

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
                    candidates.extend(SerpApiGoogleLens(self.serpapi_api_key, self.timeout).search(image_url=image_url))
                    method_parts.append("google_lens_serpapi")
                elif image_path and self.serpapi_api_key:
                    candidates.extend(SerpApiGoogleLens(self.serpapi_api_key, self.timeout).search(image_path=str(image_path)))
                    method_parts.append("google_lens_serpapi_upload")
            except DiscoveryError as exc:
                return self._result(start, [], "+".join(method_parts) or "configured_provider", str(exc))
            if self._enrich_identity(candidates):
                method_parts.append("google_lens_identity_metadata")
        if not method_parts and mock_candidates is None:
            return self._result(start, [], "none", "Configure BING_VISUAL_SEARCH_KEY or SERPAPI_KEY and provide the required image input")
        matches = self._rank(candidates, face_embedding)
        if not matches:
            matches = self._unverified_entities(candidates)
        if matches and self._enrich_social_profiles(matches):
            method_parts.append("google_social_profile_search")
        return self._result(start, matches, "+".join(method_parts) or "mock", None if matches else "No provider candidate could be verified locally")
