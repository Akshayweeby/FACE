"""Adapters for image-search providers.

These adapters only return data received from the provider. They never create
or infer a result URL.
"""

from __future__ import annotations

from typing import Any

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
        return [
            {
                "url": item.get("link"),
                "image_url": item.get("image") or item.get("thumbnail"),
                "title": item.get("title", ""),
                "source": "google_lens_serpapi",
            }
            for item in payload.get("visual_matches", [])
            if item.get("link") and (item.get("image") or item.get("thumbnail"))
        ]
