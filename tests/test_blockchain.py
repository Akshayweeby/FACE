from blockchain.hashing import canonical_json, post_hash
from blockchain.verify_from_chain import BlockchainVerifier


POST = {"url": "https://example.test/post", "caption": "hello", "timestamp": 1700000000}


def test_canonical_hash_is_order_independent():
    assert canonical_json(POST) == canonical_json({"timestamp": 1700000000, "caption": "hello", "url": "https://example.test/post"})
    assert post_hash(POST) == post_hash({"caption": "hello", "url": "https://example.test/post", "timestamp": 1700000000})


def test_caption_url_and_timestamp_changes_change_hash():
    assert post_hash({**POST, "caption": "changed"}) != post_hash(POST)
    assert post_hash({**POST, "url": "https://example.test/other"}) != post_hash(POST)
    assert post_hash({**POST, "timestamp": 1700000001}) != post_hash(POST)


def test_retrieve_post_normalizes_bytes32_hash():
    class FakeCall:
        def call(self):
            return (1, bytes.fromhex("ab" * 32), "https://example.test", 0, "0xabc", 1, False)

    class FakeFunctions:
        def getPost(self, post_id):
            return FakeCall()

    verifier = object.__new__(BlockchainVerifier)
    verifier.contract = type("Contract", (), {"functions": FakeFunctions()})()
    assert verifier.retrieve_post(1)["post_hash"] == "0x" + "ab" * 32
