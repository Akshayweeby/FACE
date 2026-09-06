from pathlib import Path

import numpy as np

from social_search.discovery import BingVisualSearch, SerpApiGoogleIdentity, SerpApiGoogleLens
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


def test_lens_parser_keeps_knowledge_graph_entity():
    result = SerpApiGoogleLens._parse({"knowledge_graph": {
        "title": "Example Person", "link": "https://example.test/person"
    }})
    assert result[0]["provider_person_name"] == "Example Person"
    assert result[0]["unverified"] is True


def test_google_identity_parser_reads_knowledge_graph():
    result = SerpApiGoogleIdentity._parse({"knowledge_graph": {"title": "Example Person", "link": "https://example.test"}}, "@example")
    assert result["name"] == "Example Person"


def test_google_identity_parser_reads_profile_title():
    result = SerpApiGoogleIdentity._parse({"organic_results": [{
        "title": "Example Person (@example) / X", "link": "https://x.com/example"
    }]}, "@example")
    assert result["name"] == "Example Person"


def test_google_identity_parser_reads_provider_title():
    result = SerpApiGoogleIdentity._parse_text({"organic_results": [{
        "title": "Birthday wishes for the Prime Minister Shri Narendra Modi",
        "snippet": "Best wishes to Prime Minister Shri Narendra Modi ji.",
        "link": "https://example.test/post",
    }]})
    assert result["name"] == "Narendra Modi"


def test_generic_job_title_is_not_a_person_name():
    assert not SocialMediaSearchEngine._plausible_person_name("Prime Minister")
    assert SocialMediaSearchEngine._plausible_person_name("Narendra Modi")


def test_trusted_result_title_extracts_max_verstappen():
    assert SocialMediaSearchEngine._name_from_identity_page_title({
        "url": "https://www.redbull.com/us-en/max-verstappen-toughest-title-win",
        "title": "Max Verstappen: How he won his toughest title defense",
    }) == "Max Verstappen"


def test_social_profile_parser_returns_profiles_not_posts():
    result = SerpApiGoogleIdentity._parse_social_profiles({"organic_results": [
        {"title": "Max Verstappen (@max33verstappen) • Instagram", "link": "https://www.instagram.com/max33verstappen/"},
        {"title": "A post", "link": "https://x.com/max33verstappen/status/123"},
    ]})
    assert result == [{
        "url": "https://www.instagram.com/max33verstappen",
        "handle": "@max33verstappen",
        "title": "Max Verstappen (@max33verstappen) • Instagram",
        "snippet": "",
        "source": "google_social_profile_search",
    }]


def test_social_url_provides_handle_and_provider_name(monkeypatch):
    engine = SocialMediaSearchEngine(face_detector=FakeDetector(), bing_api_key="key", serpapi_api_key="")
    monkeypatch.setattr(engine, "_download_and_encode", lambda url: {
        "success": True, "embedding": [1.0, 0.0], "confidence": 0.8
    })
    result = engine.find_posts(
        image_path="input.jpg", face_embedding=[1.0, 0.0],
        mock_candidates=[{
            "url": "https://x.com/example_user/status/123",
            "image_url": "https://example.test/image.jpg",
            "title": "A provider result",
            "provider_person_name": "Example Person",
        }],
    )
    assert result["matches"][0]["user"] == {"handle": "@example_user", "name": "Example Person"}


def test_real_provider_candidates_are_ranked_and_limited(monkeypatch):
    engine = SocialMediaSearchEngine(face_detector=FakeDetector(), bing_api_key="key", serpapi_api_key="", max_candidates=5)
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


def test_low_similarity_candidate_is_not_verified(monkeypatch):
    engine = SocialMediaSearchEngine(
        face_detector=FakeDetector(), bing_api_key="key", serpapi_api_key="", match_threshold=0.8
    )
    monkeypatch.setattr(engine, "_download_and_encode", lambda url: {
        "success": True, "embedding": [0.0, 1.0], "confidence": 0.8
    })
    result = engine.find_posts(
        image_path="input.jpg", face_embedding=[1.0, 0.0],
        mock_candidates=[{
            "url": "https://example.test/wrong", "image_url": "https://example.test/wrong.jpg",
            "title": "Unrelated face",
        }],
    )
    assert result["matches"] == []


def test_strong_match_stops_candidate_processing(monkeypatch):
    engine = SocialMediaSearchEngine(
        face_detector=FakeDetector(), bing_api_key="key", serpapi_api_key="",
        early_match_threshold=0.9,
    )
    checked = []

    def fake_encode(url):
        checked.append(url)
        return {"success": True, "embedding": [1.0, 0.0], "confidence": 0.8}

    monkeypatch.setattr(engine, "_download_and_encode", fake_encode)
    result = engine.find_posts(
        image_path="input.jpg", face_embedding=[1.0, 0.0],
        mock_candidates=[
            {"url": "https://x.com/example/first", "image_url": "https://example.test/1.jpg", "title": "first"},
            {"url": "https://example.test/second", "image_url": "https://example.test/2.jpg", "title": "second"},
        ],
    )
    assert result["matches"][0]["match_confidence"] == 1.0
    assert checked == ["https://example.test/1.jpg"]


def test_social_post_is_preferred_over_stronger_generic_page(monkeypatch):
    engine = SocialMediaSearchEngine(
        face_detector=FakeDetector(), bing_api_key="key", serpapi_api_key="", early_match_threshold=0.99
    )
    monkeypatch.setattr(engine, "_download_and_encode", lambda url: {
        "success": True, "embedding": [1.0, 0.0] if url.endswith("social.jpg") else [0.99, 0.1], "confidence": 0.8
    })
    result = engine.find_posts(
        image_path="input.jpg", face_embedding=[1.0, 0.0],
        mock_candidates=[
            {"url": "https://example.test/page", "image_url": "https://example.test/page.jpg", "title": "page"},
            {"url": "https://x.com/example/status/1", "image_url": "https://example.test/social.jpg", "title": "social"},
        ],
    )
    assert result["matches"][0]["post_type"] == "social_post_or_profile"


def test_no_credentials_is_graceful():
    result = SocialMediaSearchEngine(face_detector=FakeDetector(), bing_api_key="", serpapi_api_key="").find_posts(
        face_embedding=[1.0, 0.0]
    )
    assert result["success"] is False
    assert result["matches"] == []
