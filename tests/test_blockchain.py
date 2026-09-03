from blockchain.hashing import canonical_json, post_hash


POST = {"url": "https://example.test/post", "caption": "hello", "timestamp": 1700000000}


def test_canonical_hash_is_order_independent():
    assert canonical_json(POST) == canonical_json({"timestamp": 1700000000, "caption": "hello", "url": "https://example.test/post"})
    assert post_hash(POST) == post_hash({"caption": "hello", "url": "https://example.test/post", "timestamp": 1700000000})


def test_caption_url_and_timestamp_changes_change_hash():
    assert post_hash({**POST, "caption": "changed"}) != post_hash(POST)
    assert post_hash({**POST, "url": "https://example.test/other"}) != post_hash(POST)
    assert post_hash({**POST, "timestamp": 1700000001}) != post_hash(POST)
