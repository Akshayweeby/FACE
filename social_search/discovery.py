"""Adapters for image-search providers.

These adapters only return data received from the provider. They never create
or infer a result URL.
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

import requests


class DiscoveryError(RuntimeError):
    """Raised when a provider cannot complete a search."""


class BingVisualSearch:
    endpoint = "https://api.bing.microsoft.com/v7.0/images/visualsearch"

    def __init__(self, api_key: str, timeout: float = 30.0):
        self.api_key = api_key
        self.timeout = timeout

    def search(self, image_path: str) -> list[dict[str, Any]]:
        try:
            with open(image_path, "rb") as image_file:
                response = requests.post(
                    self.endpoint,
                    headers={"Ocp-Apim-Subscription-Key": self.api_key},
                    files={"imageBin": ("image", image_file, "image/jpeg")},
                    params={"mkt": "en-US"},
                    timeout=self.timeout,
                )
            response.raise_for_status()
            payload = response.json()
        except (OSError, requests.RequestException, ValueError) as exc:
            raise DiscoveryError(f"Bing Visual Search failed: {exc}") from exc
        return self._parse(payload)

    @staticmethod
    def _parse(payload: dict[str, Any]) -> list[dict[str, Any]]:
        candidates = []
        for tag in payload.get("tags", []):
            for action in tag.get("actions", []):
                if action.get("actionType") not in {"PagesIncluding", "VisualSearch"}:
                    continue
                data = action.get("data", {})
                for item in data.get("value", []):
                    url = item.get("hostPageUrl") or item.get("webSearchUrl")
                    image_url = item.get("contentUrl") or item.get("thumbnailUrl")
                    if url and image_url:
                        candidates.append({
                            "url": url,
                            "image_url": image_url,
                            "title": item.get("name", ""),
                            "source": "bing_visual_search",
                        })
        return candidates


class SerpApiGoogleLens:
    endpoint = "https://serpapi.com/search.json"
    image_endpoint = "https://serpapi.com/image"

    def __init__(self, api_key: str, timeout: float = 30.0):
        self.api_key = api_key
        self.timeout = timeout

    def search(self, image_url: str | None = None, image_path: str | None = None) -> list[dict[str, Any]]:
        if not image_url and not image_path:
            raise DiscoveryError("Google Lens requires image_url or image_path")
        try:
            params = {"engine": "google_lens", "api_key": self.api_key}
            if image_url:
                params["url"] = image_url
            else:
                with open(image_path, "rb") as image_file:
                    upload = requests.post(
                        self.image_endpoint,
                        data={"api_key": self.api_key},
                        files={"image": ("image", image_file, "application/octet-stream")},
                        timeout=self.timeout,
                    )
                upload.raise_for_status()
                upload_payload = upload.json()
                if not upload_payload.get("image_id"):
                    raise DiscoveryError(upload_payload.get("error", "SerpApi image upload returned no image_id"))
                params["image_id"] = upload_payload["image_id"]
            response = requests.get(
                self.endpoint,
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except (OSError, requests.RequestException, ValueError) as exc:
            raise DiscoveryError(f"Google Lens search failed: {exc}") from exc
        return self._parse(payload)

    @staticmethod
    def _parse(payload: dict[str, Any]) -> list[dict[str, Any]]:
        knowledge_graph = payload.get("knowledge_graph", [])
        if isinstance(knowledge_graph, dict):
            knowledge_graph = [knowledge_graph]
        # A knowledge-graph title is provider identity metadata. A page title
        # may instead describe the post or its author, so keep the two apart.
        provider_person_name = next(
            (item.get("title") for item in knowledge_graph if item.get("title")),
            None,
        )
        candidates = [
            {
                "url": item.get("link"),
                "image_url": item.get("image") or item.get("thumbnail"),
                "title": item.get("title", ""),
                "provider_person_name": provider_person_name,
                "source": "google_lens_serpapi",
            }
            for item in payload.get("visual_matches", [])
            if item.get("link") and (item.get("image") or item.get("thumbnail"))
        ]
        for item in knowledge_graph:
            if item.get("title") and item.get("link"):
                candidates.append({
                    "url": item["link"],
                    "image_url": item.get("image") or item.get("thumbnail"),
                    "title": item.get("description", ""),
                    "provider_person_name": item["title"],
                    "source": "google_lens_knowledge_graph",
                    "unverified": True,
                })
        return candidates


class SerpApiGoogleIdentity:
    """Resolve a provider-mentioned social handle using a real Google search.

    This is deliberately separate from the Lens visual candidates: a post URL
    identifies its uploader, while a handle mentioned in the post may identify
    the person shown in the image.
    """

    endpoint = "https://serpapi.com/search.json"

    def __init__(self, api_key: str, timeout: float = 30.0):
        self.api_key = api_key
        self.timeout = timeout

    def search(self, handle: str) -> dict[str, Any] | None:
        query = handle.lstrip("@")
        try:
            response = requests.get(
                self.endpoint,
                params={"engine": "google", "q": f'"{query}"', "api_key": self.api_key},
                timeout=self.timeout,
            )
            response.raise_for_status()
            return self._parse(response.json(), handle)
        except (requests.RequestException, ValueError) as exc:
            raise DiscoveryError(f"Google identity search failed: {exc}") from exc

    def search_text(self, query: str) -> dict[str, Any] | None:
        """Resolve an identity from a Lens-supplied title using Google."""
        try:
            response = requests.get(
                self.endpoint,
                params={"engine": "google", "q": query, "api_key": self.api_key},
                timeout=self.timeout,
            )
            response.raise_for_status()
            return self._parse_text(response.json())
        except (requests.RequestException, ValueError) as exc:
            raise DiscoveryError(f"Google title identity search failed: {exc}") from exc

    def search_social_profiles(self, name: str) -> list[dict[str, Any]]:
        """Find public social profiles for a provider-derived identity."""
        try:
            response = requests.get(
                self.endpoint,
                params={
                    "engine": "google",
                    "q": f'"{name}" (site:instagram.com OR site:x.com OR site:twitter.com OR site:facebook.com)',
                    "api_key": self.api_key,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            return self._parse_social_profiles(response.json(), name)
        except (requests.RequestException, ValueError) as exc:
            raise DiscoveryError(f"Google social profile search failed: {exc}") from exc

    @staticmethod
    def _parse(payload: dict[str, Any], handle: str) -> dict[str, Any] | None:
        knowledge_graph = payload.get("knowledge_graph", [])
        if isinstance(knowledge_graph, dict):
            knowledge_graph = [knowledge_graph]
        for item in knowledge_graph:
            if item.get("title"):
                return {"name": item["title"], "url": item.get("link"), "source": "google_knowledge_graph"}

        escaped = re.escape(handle.lstrip("@"))
        for item in payload.get("organic_results", []):
            title = item.get("title", "")
            match = re.search(rf"^(.+?)\s*\(@{escaped}\)", title, flags=re.IGNORECASE)
            if match:
                return {"name": match.group(1).strip(), "url": item.get("link"), "source": "google_search"}
        return None

    @staticmethod
    def _parse_text(payload: dict[str, Any]) -> dict[str, Any] | None:
        """Extract a name only from strong provider text such as 'PM Shri X Y'."""
        knowledge_graph = payload.get("knowledge_graph", [])
        if isinstance(knowledge_graph, dict):
            knowledge_graph = [knowledge_graph]
        for item in knowledge_graph:
            if item.get("title"):
                return {"name": item["title"], "url": item.get("link"), "source": "google_knowledge_graph"}

        for item in payload.get("organic_results", [])[:5]:
            patterns = (
                r"(?:prime minister|pm)\s+(?:shri\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})",
                r"\bShri\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})",
            )
            for text in (item.get("title", ""), item.get("snippet", "")):
                for pattern in patterns:
                    match = re.search(pattern, text, flags=re.IGNORECASE)
                    if not match:
                        continue
                    words = [word for word in match.group(1).split()
                             if word.lower() not in {"shri", "ji", "today", "on"}]
                    if len(words) >= 2:
                        return {"name": " ".join(words), "url": item.get("link"), "source": "google_search"}
        return None

    @staticmethod
    def _parse_social_profiles(payload: dict[str, Any], name: str | None = None) -> list[dict[str, Any]]:
        profiles = []
        seen = set()
        required_tokens = [token.lower() for token in re.findall(r"[A-Za-z0-9]+", name or "") if len(token) > 1]
        for item in payload.get("organic_results", []):
            url = item.get("link") or ""
            result_text = f"{item.get('title', '')} {item.get('snippet', '')}".lower()
            if required_tokens and not all(token in result_text for token in required_tokens):
                continue
            parsed = urlparse(url)
            host = parsed.netloc.lower()
            if not any(site in host for site in ("instagram.com", "x.com", "twitter.com", "facebook.com")):
                continue
            parts = [part for part in parsed.path.split("/") if part]
            if (not parts or parts[0].lower() in {"status", "p", "posts", "reel", "reels", "i", "explore", "search"}
                    or (len(parts) > 1 and parts[1].lower() in {"status", "p", "posts", "reel", "reels"})):
                continue
            profile_url = f"{parsed.scheme}://{parsed.netloc}/{parts[0]}"
            if profile_url in seen:
                continue
            seen.add(profile_url)
            profiles.append({
                "url": profile_url,
                "handle": "@" + parts[0].lstrip("@"),
                "title": item.get("title", ""),
                "snippet": item.get("snippet", ""),
                "source": "google_social_profile_search",
            })
            if len(profiles) == 3:
                break
        return profiles
