from main import run_pipeline


class FakeDetector:
    def detect_and_encode(self, image_path):
        assert image_path == "input.jpg"
        return {"success": True, "embedding": [0.1, 0.2], "confidence": 0.95}


class FakeSearch:
    def find_posts(self, *, image_path, image_url, face_embedding):
        assert image_path == "input.jpg"
        assert image_url == "https://cdn.example/input.jpg"
        assert face_embedding == [0.1, 0.2]
        return {"success": True, "posts_found": 1, "matches": [{
            "rank": 1, "url": "https://example.test/post", "image_url": "https://example.test/post.jpg",
            "caption": "A real provider-shaped candidate", "timestamp": None,
            "user": {"handle": None, "name": None}, "match_confidence": 0.91,
        }]}


class FakeUploader:
    def upload_post(self, post_data):
        self.post_data = post_data
        return {"success": True, "contract_address": "0xcontract", "post_id": 7,
                "transaction_hash": "0xtx", "block_number": 12, "status": "confirmed"}


class FakeVerifier:
    def verify_post(self, post_data, post_id):
        self.post_data, self.post_id = post_data, post_id
        return {"success": True, "verified": True, "post_id": post_id,
                "stored_hash": "0xhash", "calculated_hash": "0xhash", "hashes_match": True}


def test_pipeline_passes_each_stage_contract_unchanged():
    uploader, verifier = FakeUploader(), FakeVerifier()
    result = run_pipeline("input.jpg", "https://cdn.example/input.jpg", detector=FakeDetector(),
                          search_engine=FakeSearch(), uploader=uploader, verifier=verifier)
    assert result["success"] is True
    assert result["best_match"] is uploader.post_data is verifier.post_data
    assert verifier.post_id == 7


def test_pipeline_stops_before_blockchain_when_search_fails():
    class EmptySearch:
        def find_posts(self, **kwargs):
            return {"success": False, "posts_found": 0, "matches": [], "error": "provider unavailable"}

    result = run_pipeline("input.jpg", detector=FakeDetector(), search_engine=EmptySearch())
    assert result["success"] is False
    assert result["failed_stage"] == "social_search"
