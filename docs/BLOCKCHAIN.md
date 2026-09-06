# Stage 3: blockchain verification

Stage 3 stores a SHA-256 hash of the complete Person 2 post object. Canonical serialization is exactly:

```python
json.dumps(post_data, ensure_ascii=False, sort_keys=True,
           separators=(",", ":"), allow_nan=False).encode("utf-8")
```

The resulting SHA-256 hex digest is passed as Solidity `bytes32`. Upload and verification both use `blockchain.hashing.post_hash`, so changing the caption, URL, timestamp, or any other field changes the digest.

## Local Hardhat setup

```bash
cd blockchain
npm install
npx hardhat compile
npx hardhat test
npx hardhat node
npx hardhat run scripts/deploy.js --network localhost
```

Copy the printed contract address into `blockchain/.env`, and set `PRIVATE_KEY` to one of the local Hardhat account keys. Never use those development keys on a public network.

## Python interface

```python
from blockchain.upload_to_chain import BlockchainUploader
from blockchain.verify_from_chain import BlockchainVerifier

uploader = BlockchainUploader()
upload_result = uploader.upload_post(post_data)

verifier = BlockchainVerifier()
verification = verifier.verify_post(post_data, upload_result["post_id"])
```

Install Python dependencies with `pip install -r blockchain/requirements.txt`. Upload returns transaction hash, contract address, post ID, block number, status, and the stored hash. Verification returns stored/calculated hashes, `hashes_match`, `verified`, and its verification transaction hash. `retrieve_post(post_id)` returns the on-chain record.

The contract emits `PostUploaded` and `PostVerified`. It stores the post ID, hash, original post URL/timestamp, uploader, blockchain upload timestamp, and latest verification state. It does not store the full caption or image, which keeps the chain record compact and avoids putting unnecessary personal data on-chain.

## Screen-recording evidence

Run the Hardhat node and deploy the contract before starting the Python pipeline. The terminal report displays the live search method, retrieved post/profile, upload transaction, contract address, on-chain post ID, block number, uploaded hash, stored hash, recalculated hash, verification transaction, and `FINAL BLOCKCHAIN RESULT: VERIFIED`.

## Sepolia

Set `SEPOLIA_RPC_URL`, `PRIVATE_KEY`, and `CONTRACT_ADDRESS` only through environment variables, then deploy with `npx hardhat run scripts/deploy.js --network sepolia`. A real contract address and transaction hash can only be documented after deployment with a funded testnet wallet; no fake address or transaction is included here.

## Security and limitations

Do not commit `.env`, private keys, API keys, or RPC secrets. Keep `blockchain/.env.example` as the template. Hash verification proves that the supplied JSON matches the recorded digest; it does not prove that the social post itself is authentic or that the face match is a legal identity determination. Transactions require gas and RPC availability.
