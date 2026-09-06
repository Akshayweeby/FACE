"""Upload canonical Person 2 post hashes to PostVerification."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .hashing import post_hash


def _hex_with_prefix(value: Any) -> str:
    rendered = value.hex() if hasattr(value, "hex") else str(value)
    return rendered if rendered.startswith("0x") else "0x" + rendered


class BlockchainUploader:
    def __init__(self, contract_address: str | None = None, private_key: str | None = None,
                 rpc_url: str | None = None, abi_path: str | Path | None = None):
        try:
            from web3 import Web3
        except ImportError as exc:
            raise ImportError("Install blockchain dependencies with: pip install -r blockchain/requirements.txt") from exc
        self.w3 = Web3(Web3.HTTPProvider(rpc_url or os.getenv("RPC_URL", "http://127.0.0.1:8545")))
        self.private_key = private_key or os.getenv("PRIVATE_KEY")
        self.contract_address = contract_address or os.getenv("CONTRACT_ADDRESS")
        if not self.private_key or not self.contract_address:
            raise ValueError("PRIVATE_KEY and CONTRACT_ADDRESS are required")
        abi_file = Path(abi_path or Path(__file__).parent / "abi" / "PostVerification.json")
        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.contract_address), abi=json.loads(abi_file.read_text(encoding="utf-8"))
        )

    def upload_post(self, post_data: dict[str, Any]) -> dict[str, Any]:
        digest = post_hash(post_data)
        try:
            account = self.w3.eth.account.from_key(self.private_key)
            nonce = self.w3.eth.get_transaction_count(account.address)
            tx = self.contract.functions.uploadPost(
                digest, str(post_data.get("url", "")), int(post_data.get("timestamp", 0) or 0)
            ).build_transaction({
                "from": account.address, "nonce": nonce,
                "chainId": self.w3.eth.chain_id,
                "gas": 300000,
                "gasPrice": self.w3.eth.gas_price,
            })
            signed = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            events = self.contract.events.PostUploaded().process_receipt(receipt)
            post_id = int(events[0]["args"]["postId"]) if events else None
            if post_id is None:
                raise RuntimeError("Upload transaction emitted no PostUploaded event")
            return {"success": receipt["status"] == 1, "transaction_hash": _hex_with_prefix(tx_hash),
                    "contract_address": self.contract.address, "post_id": post_id,
                    "block_number": receipt["blockNumber"], "status": "confirmed" if receipt["status"] == 1 else "failed",
                    "post_hash": digest}
        except Exception as exc:
            return {"success": False, "transaction_hash": None, "contract_address": self.contract.address,
                    "post_id": None, "block_number": None, "status": "failed", "error": str(exc), "post_hash": digest}
