<div align="center">

# 🔎 Hacker House Goa Task 3

### Face → Live Web Discovery → Blockchain Verification

<p><strong>A terminal-first identity discovery and tamper-evident verification pipeline for publicly indexed images.</strong></p>

<p>
  <a href="#quick-start">🚀 Quick Start</a> ·
  <a href="#architecture">🏗️ Architecture</a> ·
  <a href="#live-search-guarantee">🌐 Live Search</a> ·
  <a href="#blockchain-verification-details">⛓️ Blockchain</a>
</p>
<p>
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/OpenCV-YuNet%20%2B%20SFace-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white" alt="OpenCV">
  <img src="https://img.shields.io/badge/SerpApi-Live%20Google%20Lens-4285F4?style=for-the-badge&logo=google&logoColor=white" alt="SerpApi">
  <img src="https://img.shields.io/badge/Solidity-0.8.20-363636?style=for-the-badge&logo=solidity&logoColor=white" alt="Solidity">
  <img src="https://img.shields.io/badge/Hardhat-Local%20Chain-FFF100?style=for-the-badge&logo=ethereum&logoColor=black" alt="Hardhat">
  <img src="https://img.shields.io/badge/Tests-Pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white" alt="Pytest">
</p>

</div>

<hr>

## ✨ Overview

This project turns an input JPG/PNG image into a structured, evidence-oriented result. It detects faces, creates CPU-compatible embeddings, performs genuine live reverse-image discovery, retrieves public post/profile candidates, verifies candidate faces locally, and records the selected post fingerprint on a local Hardhat blockchain. The final stage recalculates the fingerprint and proves whether the on-chain record still matches.

> **Pipeline:** `IMAGE → FACE EMBEDDING → LIVE SEARCH → MATCHED POST/PROFILE → SHA-256 → BLOCKCHAIN → VERIFIED`

The system does not train a model from scratch. Face detection and embeddings use pretrained OpenCV models and run on the CPU.

## 🧰 Technology stack

- **Python 3.10+** — application orchestration and integration.
- **OpenCV YuNet** — CPU-compatible face detection.
- **OpenCV SFace** — pretrained 128-dimensional face embeddings.
- **NumPy** — embedding normalization and cosine similarity.
- **SerpApi Google Lens** — live reverse-image discovery using the original image.
- **Requests** — provider and candidate-image HTTP requests.
- **python-dotenv** — local environment configuration.
- **web3.py** — Python-to-Ethereum communication and transaction handling.
- **Solidity 0.8.20** — `PostVerification` smart contract.
- **Hardhat** — local Ethereum development network, deployment, and contract testing.
- **Ethers.js / Hardhat Toolbox** — JavaScript deployment and Solidity test support.
- **Pytest** — Python unit and integration testing.

The project does not train a model from scratch. Face detection and embeddings use pretrained OpenCV models and run on the CPU.

## 🏗️ Architecture

```text
                    ┌──────────────────────────┐
                    │        Input image        │
                    │       JPG / PNG file      │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │ Face detection + SFace    │
                    │ 128D embedding per face  │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │ Live SerpApi Google Lens  │
                    │ image upload + discovery  │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │ Candidate image retrieval │
                    │ local face comparison     │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │ Best public post/profile  │
                    │ name, handle, URL, score  │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │ Canonical JSON + SHA-256  │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │ Hardhat smart contract    │
                    │ upload → retrieve → verify│
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │ FINAL BLOCKCHAIN RESULT:  │
                    │ VERIFIED / NOT VERIFIED   │
                    └──────────────────────────┘
```

## Project structure

```text
Face Detection/
├── main.py                         # End-to-end terminal orchestrator
├── start.bat                       # Automatic launcher for Windows
├── face_detection/
│   └── detector.py                 # YuNet detection + SFace embedding
├── social_search/
│   ├── discovery.py                # SerpApi/Bing provider adapters
│   └── search_engine.py            # Candidate ranking and profile lookup
├── blockchain/
│   ├── contracts/PostVerification.sol
│   ├── upload_to_chain.py
│   ├── verify_from_chain.py
│   ├── hashing.py
│   └── scripts/deploy.js
├── Images/                         # Local demo images
├── tests/                          # Python tests
└── docs/                           # Stage documentation
```

## How the pipeline works

1. The input image is loaded and validated.
2. YuNet detects one or more faces and returns bounding boxes and confidence scores.
3. SFace creates a normalized 128-dimensional embedding for each detected face.
4. SerpApi uploads the image and performs a genuine Google Lens search. No social result is hardcoded.
5. Candidate images returned by the provider are downloaded and encoded locally.
6. Cosine similarity ranks candidate faces. Social posts/profiles are preferred over generic web pages when the match is sufficiently strong.
7. Provider identity metadata and trusted result titles are used for the displayed name. A post uploader is kept separate from the person shown in the image.
8. A public social profile is retrieved through a separate live Google search when a provider-derived name is available.
9. The selected post object is serialized deterministically and hashed with SHA-256.
10. The hash, URL, and timestamp are uploaded to `PostVerification.sol`.
11. The same post object is hashed again, compared with the on-chain hash, and submitted to the contract for verification.

## 🚀 Quick start

From the project root:

```powershell
python -m pip install -r requirements.txt
cd blockchain
npm install
cd ..
```

Copy the environment template if needed:

```powershell
copy .env.example .env
```

Set the values in `.env`:

```env
SERPAPI_KEY=your_serpapi_key
BING_VISUAL_SEARCH_KEY=
RPC_URL=http://127.0.0.1:8545
CONTRACT_ADDRESS=
PRIVATE_KEY=your_local_hardhat_account_private_key
FACE_MATCH_THRESHOLD=0.55
FACE_EARLY_MATCH_THRESHOLD=0.90
```

Never commit `.env`, API keys, private keys, wallet credentials, or RPC secrets.

## Running the application

The recommended Windows workflow is now one command:

```powershell
.\start.bat
```

The launcher automatically:

- checks for a local Hardhat node;
- starts it in a minimized window when necessary;
- waits for RPC readiness;
- reuses a valid configured contract;
- deploys and records a new contract address when required;
- starts the interactive face-search program.

When prompted, enter:

```text
Search M.jpg
```

or any other image name inside the `Images` folder, for example:

```text
Search images.jpg
```

The Hardhat window must remain open while the application is running. The launcher handles the setup automatically; do not manually use a production wallet key with the local network.

## Manual blockchain commands

If manual operation is needed:

```powershell
cd blockchain
npm.cmd run node
```

In another terminal:

```powershell
cd blockchain
npx.cmd hardhat run scripts/deploy.js --network localhost
```

Then run the application from the project root:

```powershell
python main.py --interactive
```

## Live search guarantee

Normal application execution uses the configured SerpApi provider. The image is uploaded to the provider and the returned Lens candidates are retrieved dynamically. The application does not hardcode a final person, post, profile, or URL.

`mock_candidates` exists only for unit tests and development. It is never used by the normal terminal flow unless explicitly passed by code.

The terminal report identifies the live provider method, retrieved candidate count, retrieved source URL, social profile URL when available, and whether the source is a social post/profile or generic web page.

## Blockchain verification details

The canonical post hash is generated with:

```python
json.dumps(
    post_data,
    ensure_ascii=False,
    sort_keys=True,
    separators=(",", ":"),
    allow_nan=False,
).encode("utf-8")
```

That UTF-8 byte sequence is hashed with SHA-256 and stored as Solidity `bytes32`. The terminal displays:

- upload transaction hash;
- contract address;
- on-chain post ID;
- block number;
- uploaded hash;
- stored on-chain hash;
- recalculated hash;
- hash comparison result;
- verification transaction hash;
- final `VERIFIED` or `NOT VERIFIED` result.

## Example final terminal evidence

```text
Live provider search: YES
Retrieved source type: social_post_or_profile
Blockchain upload: CONFIRMED
  Upload transaction: 0x...
  Contract address: 0x...
  On-chain post ID: 1
  Uploaded post hash: 0x...
On-chain stored hash: 0x...
Recalculated hash: 0x...
Hashes match: True
Verification transaction: 0x...
FINAL BLOCKCHAIN RESULT: VERIFIED
```

## Testing

Run the Python suite:

```powershell
$env:PYTHONPATH='.'
pytest -q
```

The tests cover face detection behavior, multiple/no-face cases, social provider parsing, profile filtering, candidate matching, integration contracts, canonical hashing, and terminal blockchain evidence output.

Run Hardhat contract tests:

```powershell
cd blockchain
npm.cmd test
```

## Limitations and responsible use

- A face embedding is a biometric representation, not a legal identity proof.
- Reverse-image search coverage depends on what is publicly indexed by the provider.
- A social post account may be the uploader and not the person shown; the application labels these separately.
- A provider-derived profile may not exist or may not be publicly accessible.
- Search results, rate limits, API behavior, robots rules, and authentication requirements can change.
- Local Hardhat is for development and demonstration. A testnet deployment requires a funded wallet, RPC endpoint, and separate environment configuration.
- Do not process images or publish results without appropriate permission and compliance with applicable privacy, biometric, and platform rules.

<div align="center">

## 👥 Creators

<table>
  <tr>
    <th>Creator</th>
    <th>Email</th>
  </tr>
  <tr>
    <td><strong>Akshay V B</strong></td>
    <td><a href="mailto:aksh.techie@gmail.com">aksh.techie@gmail.com</a></td>
  </tr>
  <tr>
    <td><strong>Shraddha K</strong></td>
    <td><a href="mailto:shraddhakurakuri24@gmail.com">shraddhakurakuri24@gmail.com</a></td>
  </tr>
  <tr>
    <td><strong>Aditya Vikram</strong></td>
    <td><a href="mailto:1dt24cy003@dsatm.edu.in">1dt24cy003@dsatm.edu.in</a></td>
  </tr>
</table>

</div>
