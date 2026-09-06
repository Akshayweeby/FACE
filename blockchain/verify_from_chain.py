"""Re-hash Person 2 post data and verify it against the chain."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .hashing import post_hash


def _hex_with_prefix(value: Any) -> str:
    rendered = value.hex() if hasattr(value, "hex") else str(value)
    return rendered if rendered.startswith("0x") else "0x" + rendered


class BlockchainVerifier:
    def __init__(self, contract_address: str | None = None, private_key: str | None = None,
                 rpc_url: str | None = None, abi_path: str | Path | None = None):
        from web3 import Web3
        self.w3 = Web3(Web3.HTTPProvider(rpc_url or os.getenv("RPC_URL", "http://127.0.0.1:8545")))
        self.private_key = private_key or os.getenv("PRIVATE_KEY")
        self.contract_address = contract_address or os.getenv("CONTRACT_ADDRESS")
        if not self.private_key or not self.contract_address:
            raise ValueError("PRIVATE_KEY and CONTRACT_ADDRESS are required")
        abi_file = Path(abi_path or Path(__file__).parent / "abi" / "PostVerification.json")
        self.contract = self.w3.eth.contract(address=Web3.to_checksum_address(self.contract_address),
                                              abi=json.loads(abi_file.read_text(encoding="utf-8")))

    def retrieve_post(self, post_id: int) -> dict[str, Any]:
        record = self.contract.functions.getPost(post_id).call()
        stored_hash = record[1].hex() if hasattr(record[1], "hex") else str(record[1])
        if not stored_hash.startswith("0x"):
            stored_hash = "0x" + stored_hash
        return {"id": int(record[0]), "post_hash": stored_hash, "post_url": record[2],
                "original_timestamp": int(record[3]), "uploader": record[4],
                "uploaded_at": int(record[5]), "verified": bool(record[6])}

    def verify_post(self, post_data: dict[str, Any], post_id: int) -> dict[str, Any]:
        calculated = post_hash(post_data)
        try:
            stored = self.retrieve_post(post_id)
            matches = stored["post_hash"].lower() == calculated.lower()
            account = self.w3.eth.account.from_key(self.private_key)
            tx = self.contract.functions.verifyPost(post_id, calculated).build_transaction({
                "from": account.address, "nonce": self.w3.eth.get_transaction_count(account.address),
                "chainId": self.w3.eth.chain_id, "gas": 150000, "gasPrice": self.w3.eth.gas_price,
            })
            signed = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            return {"success": receipt["status"] == 1, "verified": matches, "post_id": post_id,
                    "stored_hash": stored["post_hash"], "calculated_hash": calculated,
                    "hashes_match": matches, "transaction_hash": _hex_with_prefix(tx_hash)}
        except Exception as exc:
            return {"success": False, "verified": False, "post_id": post_id,
                    "stored_hash": None, "calculated_hash": calculated, "hashes_match": False, "error": str(exc)}
