from pathlib import Path

import numpy as np

from social_search.discovery import BingVisualSearch, SerpApiGoogleLens
from social_search.search_engine import SocialMediaSearchEngine


class FakeDetector:
    def detect_and_encode(self, path):
        return {"success": True, "embedding": [1.0, 0.0], "confidence": 0.9}


def test_bing_parser_returns_only_provider_urls():
    payload = {"tags": [{"actions": [{"actionType": "PagesIncluding", "data": {"value": [
        {"hostPageUrl": "https://example.test/post", "contentUrl": "https://example.test/image.jpg", "name": "A post"}
    ]}}]}]}
    result = BingVisualSearch._parse(payload)
    assert result[0]["url"] == "https://example.test/post"


def test_lens_parser_ignores_incomplete_results():
    result = SerpApiGoogleLens._parse({"visual_matches": [{"title": "missing"}, {
        "link": "https://example.test/post", "image": "https://example.test/image.jpg"
    }]})
    assert len(result) == 1


def test_real_provider_candidates_are_ranked_and_limited(monkeypatch):
    engine = SocialMediaSearchEngine(face_detector=FakeDetector(), bing_api_key="key", max_candidates=5)
    candidates = [
        {"url": "https://example.test/second", "image_url": "https://example.test/2.jpg", "title": "second"},
        {"url": "https://example.test/first", "image_url": "https://example.test/1.jpg", "title": "first"},
    ]
    monkeypatch.setattr("social_search.search_engine.BingVisualSearch.search", lambda self, path: candidates)
    monkeypatch.setattr(engine, "_download_and_encode", lambda url: {
        "success": True, "embedding": [1.0, 0.0] if url.endswith("1.jpg") else [0.0, 1.0], "confidence": 0.8
    })
    result = engine.find_posts(image_path="input.jpg", face_embedding=[1.0, 0.0])
    assert result["success"] is True
    assert result["matches"][0]["url"] == "https://example.test/first"
    assert result["matches"][0]["match_confidence"] == 1.0


def test_no_credentials_is_graceful():
    result = SocialMediaSearchEngine(face_detector=FakeDetector(), bing_api_key=None, serpapi_api_key=None).find_posts(
        face_embedding=[1.0, 0.0]
    )
    assert result["success"] is False
    assert result["matches"] == []
