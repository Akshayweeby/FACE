"""End-to-end Hacker House Goa Task 3 pipeline.

This file orchestrates the existing Stage 1, Stage 2, and Stage 3 modules;
it does not duplicate detection, discovery, matching, hashing, or blockchain
logic.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from face_detection.detector import FaceDetector
from social_search.search_engine import SocialMediaSearchEngine
from blockchain.upload_to_chain import BlockchainUploader
from blockchain.verify_from_chain import BlockchainVerifier


def _failed_pipeline(stage: str, message: str, **details: Any) -> dict[str, Any]:
    return {"success": False, "failed_stage": stage, "error": message, **details}


def run_pipeline(
    image_path: str | Path,
    public_image_url: str | None = None,
    *,
    detector: FaceDetector | None = None,
    search_engine: SocialMediaSearchEngine | None = None,
    uploader: BlockchainUploader | None = None,
    verifier: BlockchainVerifier | None = None,
) -> dict[str, Any]:
    """Run image → face → web match → blockchain verification.

    ``public_image_url`` is optional and is used by Google Lens providers.
    Bing can discover directly from ``image_path``. The optional dependency
    arguments make the flow easy to test without external services.
    """
    load_dotenv()

    detector = detector or FaceDetector()
    face_result = detector.detect_and_encode(image_path)
    if not face_result.get("success"):
        return _failed_pipeline("face_detection", face_result.get("error", "Face detection failed"), face=face_result)

    search_engine = search_engine or SocialMediaSearchEngine(face_detector=detector)
    search_result = search_engine.find_posts(
        image_path=image_path,
        image_url=public_image_url,
        face_embedding=face_result["embedding"],
    )
    if not search_result.get("success") or not search_result.get("matches"):
        return _failed_pipeline("social_search", search_result.get("error", "No verified social/web match found"),
                                face=face_result, search=search_result)

    best_match = search_result["matches"][0]
    uploader = uploader or BlockchainUploader(
        rpc_url=os.getenv("RPC_URL"),
        private_key=os.getenv("PRIVATE_KEY"),
        contract_address=os.getenv("CONTRACT_ADDRESS"),
    )
    upload_result = uploader.upload_post(best_match)
    if not upload_result.get("success") or upload_result.get("post_id") is None:
        return _failed_pipeline("blockchain_upload", upload_result.get("error", "Blockchain upload failed"),
                                face=face_result, search=search_result, best_match=best_match,
                                blockchain_upload=upload_result)

    verifier = verifier or BlockchainVerifier(
        rpc_url=os.getenv("RPC_URL"),
        private_key=os.getenv("PRIVATE_KEY"),
        contract_address=upload_result.get("contract_address") or os.getenv("CONTRACT_ADDRESS"),
    )
    verification = verifier.verify_post(best_match, upload_result["post_id"])
    return {
        "success": bool(verification.get("success") and verification.get("verified")),
        "face": face_result,
        "search": search_result,
        "best_match": best_match,
        "blockchain_upload": upload_result,
        "blockchain_verification": verification,
    }


# Name used by the project plan and convenient for CLI callers.
run_full_pipeline = run_pipeline


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Run the Goa face-to-blockchain pipeline")
    parser.add_argument("image_path", help="Input JPG/PNG image")
    parser.add_argument("--public-image-url", help="Public image URL for Google Lens")
    args = parser.parse_args()
    print(json.dumps(run_pipeline(args.image_path, args.public_image_url), indent=2, ensure_ascii=False))
