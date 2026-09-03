# Stage 2: real web/social discovery and matching

```python
from social_search.search_engine import SocialMediaSearchEngine

engine = SocialMediaSearchEngine()
result = engine.find_posts(image_path="test_image.jpg")
if result["success"]:
    best_match = result["matches"][0]
```

## How it works

1. The original image is sent to Bing Visual Search, or a publicly reachable image URL is sent to Google Lens through SerpApi.
2. Only URLs and image URLs returned by that provider are used; no result is hardcoded.
3. Candidate images are downloaded and passed through the Stage 1 face encoder.
4. Cosine similarity between the input embedding and candidate embedding is used to rank up to three verified matches.

An embedding alone cannot be sent to an image-search service. Use `image_path` with Bing or `image_url` with SerpApi; `face_embedding` is used for local comparison.

## Setup

```bash
pip install -r social_search/requirements.txt
copy .env.example .env  # Windows
```

The current implementation supports:

- Bing Visual Search API: requires an Azure Bing Visual Search subscription key; endpoint quota and pricing depend on the selected Azure tier.
- SerpApi Google Lens: requires a SerpApi account/key; request limits and pricing depend on the account plan.

Provider access, robots rules, authentication, rate limits, and result coverage can change. Only use publicly accessible pages and comply with each provider’s terms and applicable privacy/biometric laws. This is discovery, not proof of identity: `match_confidence` is cosine similarity, not an identity probability.

## Output

`result["matches"][0]` is a provider-derived candidate with `rank`, `url`, `image_url`, `caption`, `timestamp`, `user`, `match_confidence`, and `face_confidence`. `success` is false when the provider fails, no credentials are configured, the input face is invalid, or no candidate image can be locally verified. `mock_candidates` exists only for tests/development and is never used unless explicitly passed.

## Demo/testing

For an end-to-end demo, use a known public-figure image that you have permission to process, configure one provider key, and run `find_posts(image_path=...)`. Integration tests should record provider responses rather than commit personal images or API keys. Unit tests use mocked provider responses and candidate downloads, so normal test execution does not make external requests.
