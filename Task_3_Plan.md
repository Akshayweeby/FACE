# HH Goa 2026 Task 3: Project Plan & Work Division
## Face Identification & Blockchain Verification Pipeline

---

## Executive Summary

**Project**: Build an end-to-end pipeline that identifies faces in images, searches for matching content on social media, and verifies the discovered data using blockchain.

**Timeline**: August 31, 2026 → September 7, 2026, 11:59 PM (7 days)

**Team Size**: 3 developers (parallel workstreams)

**Deliverables**:
- GitHub repository with complete source code
- Screen recording of working pipeline (end-to-end demo)
- Submission via form: https://forms.gle/oZbQGuwiNeHVcHWo8

---

## Part 1: Task Requirements Breakdown

### Input → Process → Output

| Stage | Input | Process | Output |
|-------|-------|---------|--------|
| **Stage 1** | Face image (JPG/PNG) | Detect face, extract embedding vector | Face embedding + confidence score |
| **Stage 2** | Face embedding | Search web/social media for matches | Social media post (URL, image, metadata) |
| **Stage 3** | Post data | Hash data, upload to blockchain, verify | Transaction hash, on-chain proof of verification |

### Technical Requirements (Must-Haves)

1. **Face Detection & Encoding** ✓
   - Any face detection library acceptable (dlib, MediaPipe, OpenCV, AWS Rekognition, Google Vision)
   - Output: face embedding (vector representation)
   - Handle: single/multiple faces, no faces, edge cases

2. **Social Media / Web Search** ✓
   - REAL search, not hardcoded results
   - Find at least ONE matching social media post
   - Methods: Reverse image search API, scripted search, web scraping
   - Platforms: Instagram, Twitter/X, Facebook, LinkedIn, TikTok (any 2+)

3. **Blockchain Verification** ✓
   - Upload post data (or hash) to blockchain
   - Create tamper-evident record
   - Re-verify data against on-chain record
   - Blockchain choice: Any (public testnet, mainnet, local)
   - Recommended: Sepolia Testnet, Polygon Mumbai, or Hardhat

4. **No Website Required** ✓
   - CLI tool or Python script sufficient
   - All time spent on backend pipeline

5. **GitHub Repository** ✓
   - README: What it does, how to run, blockchain used, limitations
   - Clean code organization
   - requirements.txt / package.json for dependencies

6. **Screen Recording** ✓
   - Plain, no editing needed
   - Show: image input → post found → blockchain confirmation
   - Upload to YouTube (unlisted), Google Drive, Loom, etc.

---

## Part 2: Work Division for 3 People

### Team Structure & Responsibilities

```
┌─────────────────────────────────────────────────────────┐
│     HH Goa Task 3 - Pipeline Architecture               │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  [Input Image] ─────────────────────────────────────>  │
│                      ↓                                    │
│  ┌──────────────────────────────────────────────┐       │
│  │ PERSON 1: Face Detection & Encoding         │       │
│  │ (Face → Embedding)                          │       │
│  └──────────────────────────────────────────────┘       │
│                      ↓                                    │
│               [Face Embedding]                           │
│                      ↓                                    │
│  ┌──────────────────────────────────────────────┐       │
│  │ PERSON 2: Social Media Search & Matching    │       │
│  │ (Embedding → Post Data)                     │       │
│  └──────────────────────────────────────────────┘       │
│                      ↓                                    │
│           [Social Post + Metadata]                       │
│                      ↓                                    │
│  ┌──────────────────────────────────────────────┐       │
│  │ PERSON 3: Blockchain Upload & Verification │       │
│  │ (Post → Blockchain Proof)                   │       │
│  └──────────────────────────────────────────────┘       │
│                      ↓                                    │
│        [On-Chain Verification Record]                    │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

---

## Part 3: Person 1 - Face Detection & Encoding Specialist

### Role Definition
Responsible for the **first stage** of the pipeline: detect faces in input images and generate embeddings.

### Key Responsibilities

1. **Face Detection**
   - Accept JPG/PNG images as input
   - Use face detection library:
     - **Option A (Recommended)**: MediaPipe or Dlib (open-source, fast)
     - **Option B**: OpenCV (widely documented)
     - **Option C**: Cloud API (AWS Rekognition, Google Vision, Azure Face)
   - Detect all faces in image
   - Return bounding box for each face

2. **Face Embedding Generation**
   - Extract deep learning face embeddings (typically 128-512 dimensional vector)
   - Use pre-trained model:
     - **Option A (Recommended)**: FaceNet or VGGFace2 (via dlib)
     - **Option B**: OpenFace
     - **Option C**: Cloud API embeddings
   - Normalize embeddings for comparison
   - Calculate confidence score (0.0-1.0)

3. **Error Handling**
   - No faces detected → return clear error message
   - Multiple faces → detect largest/most prominent face (or return all)
   - Blurry/low-quality image → return low confidence flag
   - Invalid input → validate file type and size

4. **Testing & Documentation**
   - Create unit tests with sample images (5-10 test cases)
   - Document: model used, accuracy metrics, processing time
   - Specify system requirements (GPU optional, CPU sufficient)

### Deliverables

```
face_detection/
├── detector.py                 # Main module
├── models/                     # Pre-trained model files
│   └── face_recognition_model.pth  (if needed)
├── requirements.txt            # Dependencies
├── config.py                   # Configuration (model path, etc.)
└── utils.py                    # Helper functions (bbox drawing, etc.)

tests/
├── test_face_detection.py     # Unit tests
├── sample_images/
│   ├── single_face.jpg
│   ├── multiple_faces.jpg
│   ├── no_face.jpg
│   └── blurry_face.jpg
└── expected_outputs/
    └── embeddings.json

docs/
└── FACE_DETECTION.md          # Technical documentation
```

### Output Specification

**Input**: `image_path: str`

**Output JSON**:
```json
{
  "success": true,
  "faces_detected": 1,
  "embedding": [0.124, 0.456, ..., 0.789],
  "embedding_dimension": 128,
  "confidence": 0.97,
  "bounding_box": {
    "x": 50,
    "y": 60,
    "width": 200,
    "height": 220
  },
  "model_used": "facenet_vggface2",
  "processing_time_ms": 245
}
```

### Interface Contract (For Person 2)

```python
from face_detection.detector import FaceDetector

detector = FaceDetector(model_name="facenet")
result = detector.detect_and_encode(image_path="path/to/image.jpg")

# result["embedding"] → passed to Person 2
```

### Technology Recommendations

| Component | Recommendation | Alternative |
|-----------|-----------------|-------------|
| Face Detection | MediaPipe / Dlib | OpenCV Cascade |
| Face Embedding | FaceNet (VGGFace2) | OpenFace |
| Language | Python 3.9+ | Node.js (TensorFlow.js) |
| Framework | PyTorch / TensorFlow | OpenCV (C++) |
| Deployment | CPU sufficient | GPU optional (for speed) |

### Timeline
- **Day 1-2**: Set up library, test with sample images
- **Day 3**: Implement embedding generation, test accuracy
- **Day 4**: Error handling, edge cases, unit tests
- **Day 5**: Documentation, pass to Person 2 for integration

---

## Part 4: Person 2 - Social Media Search & Matching Specialist

### Role Definition
Responsible for the **second stage**: find real social media posts matching the detected face.

### Key Responsibilities

1. **Reverse Image Search**
   - Accept face embedding from Person 1
   - Use reverse image search service:
     - **Option A (Recommended)**: Google Images API or TinEye API
     - **Option B**: Custom web scraping (Google Images, Bing Images)
     - **Option C**: Facebook/Instagram built-in reverse search
   - Convert embedding → image or use original image file
   - Return list of potential matches

2. **Social Media Scraping & Discovery**
   - Search platforms:
     - Instagram (via Instagram API, Instagrapi, or web scraping)
     - Twitter/X (via Twitter API v2)
     - Facebook (via Facebook Graph API)
     - LinkedIn (web scraping, API may be limited)
     - TikTok (via unofficial API or web scraping)
   - For each match, extract:
     - **URL**: Direct link to post
     - **Image URL**: Link to the image
     - **Caption**: Post text/description
     - **Timestamp**: Date/time posted
     - **User**: Profile handle, name, followers
     - **Engagement**: Likes, comments, shares (optional)
     - **Platform**: Which social media

3. **Matching & Scoring**
   - Compare discovered images against original embedding
   - Calculate confidence score (0.0-1.0)
   - Return top 1-3 matches with scores
   - **Requirement**: Must find at least ONE real match (not hardcoded)

4. **Mock Data Fallback**
   - Create mock social posts for testing if APIs fail
   - Use real but publicly available data
   - Format same as actual discovery output

5. **Testing & Documentation**
   - Test with 3-5 real celebrity/public figure images
   - Document API keys needed, rate limits, authentication
   - Specify which platforms are easiest to search

### Deliverables

```
social_search/
├── search_engine.py           # Main module
├── scrapers/
│   ├── instagram_scraper.py
│   ├── twitter_scraper.py
│   ├── facebook_scraper.py
│   └── reverse_image_search.py
├── requirements.txt           # Dependencies
├── config.py                  # API keys, settings
├── secrets.example.py         # Example for API keys (NEVER commit actual keys!)
└── utils.py                   # Helper functions

tests/
├── test_social_search.py      # Unit tests
├── test_images/
│   ├── celebrity_1.jpg
│   ├── public_figure_2.jpg
│   └── test_embedding.npy
└── mock_data/
    └── expected_posts.json

docs/
└── SOCIAL_SEARCH.md           # Setup guide, API keys, limitations
```

### Output Specification

**Input**: `face_embedding: list[float]` (from Person 1)

**Output JSON**:
```json
{
  "success": true,
  "posts_found": 2,
  "search_method": "reverse_image_search + instagram_api",
  "matches": [
    {
      "rank": 1,
      "platform": "instagram",
      "url": "https://instagram.com/p/ABC123XYZ/",
      "image_url": "https://instagram.cdninstagram.com/...",
      "caption": "Beach day! #summer #travel",
      "timestamp": "2024-08-15T14:30:00Z",
      "user": {
        "handle": "jane_doe",
        "name": "Jane Doe",
        "followers": 15420
      },
      "engagement": {
        "likes": 342,
        "comments": 28,
        "shares": 5
      },
      "match_confidence": 0.94
    }
  ],
  "best_match_confidence": 0.94,
  "search_time_ms": 3200
}
```

### Interface Contract (From Person 1, To Person 3)

```python
from social_search.search_engine import SocialMediaSearchEngine

search_engine = SocialMediaSearchEngine(
    google_api_key="YOUR_KEY",
    instagram_api_key="YOUR_KEY"
)
result = search_engine.find_posts(face_embedding)

# result["matches"][0] → passed to Person 3
```

### Technology Recommendations

| Component | Recommendation | Alternative |
|-----------|-----------------|-------------|
| Reverse Image | TinEye API or Google Images | Bing Images |
| Instagram | Instagrapi (unofficial) | Instagram Graph API |
| Twitter | Tweepy + Twitter API v2 | Manual scraping |
| Facebook | Selenium + scraping | Facebook Graph API |
| Language | Python 3.9+ | Node.js (Puppeteer) |
| Async | AIOHTTP or asyncio | Requests (slower) |

### API Keys Needed
- **Google Images API**: ~$0-5 per 1000 requests (set up in Google Cloud Console)
- **Instagram**: Instagrapi is free but unofficial; official API is limited
- **Twitter/X**: Free tier available (Twitter Developer Portal)
- **TinEye**: Free tier available (25 searches/month)
- **Facebook**: Graph API (free, but restrictive)

### Timeline
- **Day 1-2**: Set up reverse image search, test basic functionality
- **Day 3**: Integrate Instagram scraping
- **Day 4**: Add Twitter, Facebook scraping
- **Day 5**: Testing, mock data, pass to Person 3

---

## Part 5: Person 3 - Blockchain Verification Specialist

### Role Definition
Responsible for the **third stage**: upload post data to blockchain and create tamper-evident verification records.

### Key Responsibilities

1. **Blockchain Selection**
   - Choose one blockchain:
     - **Option A (Recommended)**: Sepolia Testnet (Ethereum testnet, free faucet)
     - **Option B**: Polygon Mumbai (Layer 2 testnet, free faucet)
     - **Option C**: Hardhat (local testnet for testing, no gas fees)
   - Document: chain name, RPC endpoint, faucet link, contract address

2. **Smart Contract Development**
   - Write Solidity smart contract (0.8.x)
   - Contract: `PostVerification.sol`
   - Functions:
     - `uploadPost(bytes32 postHash, string memory postUrl, uint256 timestamp)` → stores on-chain
     - `verifyPost(bytes32 postHash, string memory postUrl, uint256 timestamp)` → returns true/false
     - `getPost(uint256 id)` → retrieves stored data
   - Events:
     - `PostUploaded(uint256 indexed postId, bytes32 postHash, address indexed uploader)`
     - `PostVerified(uint256 indexed postId, bool isValid)`
   - Storage structure:
     ```solidity
     struct Post {
       uint256 id;
       bytes32 postHash;
       string postUrl;
       uint256 timestamp;
       address uploader;
       bool verified;
     }
     ```

3. **Data Upload to Blockchain**
   - Accept post data from Person 2
   - Create SHA-256 hash of post JSON/metadata
   - Sign transaction with private key (or use provided wallet)
   - Submit transaction to blockchain
   - Return:
     - Transaction hash (tx hash)
     - Contract address
     - Block number
     - Gas used

4. **Verification Function**
   - Accept post data + on-chain record reference
   - Re-hash the incoming data
   - Compare hashes: stored == newly calculated
   - Return verification proof
   - Confirmation: block confirmations, timestamp

5. **Testing & Documentation**
   - Deploy contract to testnet (Sepolia or Mumbai)
   - Test upload and verification with 3-5 posts
   - Document: contract address, ABI, how to interact
   - Provide example transactions

### Deliverables

```
blockchain/
├── contracts/
│   └── PostVerification.sol    # Smart contract
├── scripts/
│   ├── deploy.js              # Hardhat deployment
│   └── verify.js              # Verification script
├── upload_to_chain.py         # Python upload module
├── verify_from_chain.py       # Python verification module
├── requirements.txt           # Python dependencies
├── package.json               # Node.js dependencies (for Hardhat)
├── hardhat.config.js          # Hardhat config (if using local chain)
├── .env.example               # Example environment variables
└── config.py                  # Chain config, RPC, contract address

tests/
├── test_blockchain.py         # Unit tests
├── test_contract.js           # Hardhat tests
└── mock_posts.json            # Mock post data for testing

docs/
└── BLOCKCHAIN.md              # Setup guide, contract ABI, deployment info
```

### Solidity Smart Contract (PostVerification.sol)

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract PostVerification {
    struct Post {
        uint256 id;
        bytes32 postHash;
        string postUrl;
        uint256 timestamp;
        address uploader;
        uint256 uploadedAt;
        bool verified;
    }

    mapping(uint256 => Post) public posts;
    uint256 public postCounter;

    event PostUploaded(uint256 indexed postId, bytes32 postHash, address indexed uploader);
    event PostVerified(uint256 indexed postId, bool isValid);

    function uploadPost(
        bytes32 _postHash,
        string memory _postUrl,
        uint256 _timestamp
    ) public returns (uint256) {
        postCounter++;
        posts[postCounter] = Post(
            postCounter,
            _postHash,
            _postUrl,
            _timestamp,
            msg.sender,
            block.timestamp,
            false
        );
        emit PostUploaded(postCounter, _postHash, msg.sender);
        return postCounter;
    }

    function verifyPost(
        uint256 _postId,
        bytes32 _postHash,
        string memory _postUrl,
        uint256 _timestamp
    ) public returns (bool) {
        require(posts[_postId].id != 0, "Post not found");
        bool isValid = (posts[_postId].postHash == _postHash &&
            keccak256(abi.encodePacked(posts[_postId].postUrl)) == keccak256(abi.encodePacked(_postUrl)) &&
            posts[_postId].timestamp == _timestamp);
        
        if (isValid) {
            posts[_postId].verified = true;
        }
        emit PostVerified(_postId, isValid);
        return isValid;
    }

    function getPost(uint256 _postId) public view returns (Post memory) {
        return posts[_postId];
    }
}
```

### Output Specification

**Input**: `post_data: dict` (from Person 2)

**Upload Output**:
```json
{
  "success": true,
  "transaction_hash": "0x1a2b3c4d5e6f7g8h9i0j...",
  "contract_address": "0xAbCdEf1234567890AbCdEf1234567890AbCdEf12",
  "post_id": 1,
  "block_number": 5432101,
  "gas_used": 65420,
  "status": "confirmed",
  "confirmation_time": "2024-09-05T10:15:30Z"
}
```

**Verification Output**:
```json
{
  "success": true,
  "verified": true,
  "post_id": 1,
  "stored_hash": "0xabcd1234...",
  "calculated_hash": "0xabcd1234...",
  "hashes_match": true,
  "block_confirmations": 12,
  "verification_time": "2024-09-05T10:20:45Z"
}
```

### Interface Contract (From Person 2)

```python
from blockchain.upload_to_chain import BlockchainUploader
from blockchain.verify_from_chain import BlockchainVerifier

uploader = BlockchainUploader(
    contract_address="0x...",
    private_key="0x...",
    rpc_url="https://sepolia.infura.io/v3/YOUR_KEY"
)
upload_result = uploader.upload_post(post_data)

verifier = BlockchainVerifier(rpc_url="...")
verification = verifier.verify_post(post_data, upload_result["post_id"])
```

### Technology Recommendations

| Component | Recommendation | Alternative |
|-----------|-----------------|-------------|
| Blockchain | Sepolia Testnet | Polygon Mumbai, Hardhat |
| Smart Contract | Solidity 0.8.x | Vyper |
| Deployment Tool | Hardhat | Truffle, Brownie |
| Python Interaction | web3.py | ethers.py |
| Testing | Hardhat tests + pytest | Ganache + truffle |

### Testnet Setup

**Sepolia Testnet**:
- RPC: `https://sepolia.infura.io/v3/YOUR_INFURA_KEY`
- Faucet: https://www.alchemy.com/faucets/ethereum-sepolia
- Block Explorer: https://sepolia.etherscan.io/

**Polygon Mumbai**:
- RPC: `https://rpc-mumbai.maticvigil.com`
- Faucet: https://faucet.polygon.technology/
- Block Explorer: https://mumbai.polygonscan.com/

### Timeline
- **Day 1**: Choose blockchain, set up testnet faucet, understand Solidity
- **Day 2-3**: Write and test smart contract
- **Day 4**: Implement Python upload/verify modules
- **Day 5**: Integration testing with Person 2 data, documentation

---

## Part 6: Integration & Testing

### Integration Workflow

```
1. Person 1 generates embedding → outputs JSON
2. Person 2 takes embedding → finds post → outputs post JSON
3. Person 3 takes post data → uploads to blockchain → outputs tx hash & proof
```

### Integration Testing Checklist

- [ ] Person 1 → Person 2: Embedding format matches
- [ ] Person 2 → Person 3: Post data format matches
- [ ] End-to-end test: image → embedding → social post → blockchain record
- [ ] Error handling: graceful failures at each stage
- [ ] Performance: total pipeline < 2 minutes
- [ ] Data validation: no empty/null values passed between stages

### Main Pipeline Script

```python
# main.py - Orchestrates all three stages

from face_detection.detector import FaceDetector
from social_search.search_engine import SocialMediaSearchEngine
from blockchain.upload_to_chain import BlockchainUploader
from blockchain.verify_from_chain import BlockchainVerifier

def run_full_pipeline(image_path, web3_provider_url):
    # Stage 1: Face Detection
    detector = FaceDetector()
    face_result = detector.detect_and_encode(image_path)
    if not face_result["success"]:
        print("Error: No face detected")
        return
    
    # Stage 2: Social Media Search
    searcher = SocialMediaSearchEngine()
    search_result = searcher.find_posts(face_result["embedding"])
    if not search_result["success"]:
        print("Error: No posts found")
        return
    
    post_data = search_result["matches"][0]
    print(f"Found post: {post_data['url']}")
    
    # Stage 3: Blockchain Upload
    uploader = BlockchainUploader(rpc_url=web3_provider_url)
    upload_result = uploader.upload_post(post_data)
    print(f"Uploaded to blockchain: {upload_result['transaction_hash']}")
    
    # Stage 4: Verification
    verifier = BlockchainVerifier(rpc_url=web3_provider_url)
    verification = verifier.verify_post(post_data, upload_result["post_id"])
    print(f"Verified on-chain: {verification['verified']}")
    
    return {
        "face": face_result,
        "social_post": post_data,
        "blockchain": upload_result,
        "verification": verification
    }

if __name__ == "__main__":
    result = run_full_pipeline("test_image.jpg", "https://sepolia.infura.io/...")
    print(result)
```

---

## Part 7: GitHub Repository Structure

```
hh-goa-task3-blockchain-face-verification/
│
├── README.md                      # Main documentation
├── LICENSE
├── .gitignore
├── requirements.txt               # Python dependencies
├── package.json                   # Node.js dependencies (for Hardhat)
├── main.py                        # Main pipeline script
├── config.example.py              # Example configuration
│
├── face_detection/
│   ├── __init__.py
│   ├── detector.py
│   ├── config.py
│   ├── utils.py
│   ├── requirements.txt
│   └── models/
│       └── (pre-trained model files)
│
├── social_search/
│   ├── __init__.py
│   ├── search_engine.py
│   ├── scrapers/
│   │   ├── instagram_scraper.py
│   │   ├── twitter_scraper.py
│   │   └── reverse_image_search.py
│   ├── config.py
│   ├── secrets.example.py
│   ├── utils.py
│   └── requirements.txt
│
├── blockchain/
│   ├── __init__.py
│   ├── contracts/
│   │   └── PostVerification.sol
│   ├── scripts/
│   │   ├── deploy.js
│   │   └── verify.js
│   ├── upload_to_chain.py
│   ├── verify_from_chain.py
│   ├── config.py
│   ├── hardhat.config.js
│   ├── package.json
│   ├── requirements.txt
│   └── .env.example
│
├── tests/
│   ├── test_face_detection.py
│   ├── test_social_search.py
│   ├── test_blockchain.py
│   ├── test_integration.py
│   ├── test_contract.js
│   ├── sample_images/
│   │   ├── single_face.jpg
│   │   ├── multiple_faces.jpg
│   │   └── no_face.jpg
│   └── mock_data/
│       └── expected_posts.json
│
├── docs/
│   ├── FACE_DETECTION.md
│   ├── SOCIAL_SEARCH.md
│   ├── BLOCKCHAIN.md
│   ├── INTEGRATION.md
│   └── SETUP_GUIDE.md
│
└── recording/
    └── pipeline_demo.mp4 (or link in README)
```

### README.md Structure

```markdown
# HH Goa Task 3: Face Identification & Blockchain Verification

## Overview
[Describe project in 2-3 sentences]

## Features
- Face detection and embedding generation
- Reverse image search on social media platforms
- Blockchain-based post verification
- End-to-end pipeline with minimal dependencies

## Architecture
[ASCII diagram of pipeline]

## Prerequisites
- Python 3.9+
- Node.js 16+ (for Hardhat)
- Testnet ETH (free from faucet)
- API keys (Google, Instagram, Twitter)

## Setup & Installation
### 1. Clone Repository
### 2. Install Dependencies
### 3. Configure API Keys
### 4. Deploy Smart Contract
### 5. Run Pipeline

## Usage
### Basic Example
[Code snippet]

### Full End-to-End
[Code snippet]

## Blockchain Details
- **Network**: Sepolia Testnet
- **Contract Address**: 0x...
- **Block Explorer**: https://sepolia.etherscan.io/...

## Known Limitations
- Social media scraping may be rate-limited
- Face detection requires good lighting
- Blockchain verification takes 15-30 seconds
- Some platforms require API authentication

## Team
- Person 1: Face Detection
- Person 2: Social Media Search
- Person 3: Blockchain Verification

## Demo Recording
[Link to YouTube/Google Drive/Loom]

## License
MIT
```

---

## Part 8: Timeline & Milestones

### Week of Sept 1-7, 2026

| Date | Day | Milestone | Person 1 | Person 2 | Person 3 |
|------|-----|-----------|----------|----------|----------|
| Sept 1 | Mon | Setup & Planning | ✓ Init repo | ✓ Init repo | ✓ Init repo |
| Sept 2 | Tue | Core Development | ✓ Face detect | ✓ Reverse search | ✓ Smart contract |
| Sept 3 | Wed | Core Development | ✓ Embeddings | ✓ Instagram scraper | ✓ Upload module |
| Sept 4 | Thu | Testing | ✓ Unit tests | ✓ Mock data | ✓ Testnet deploy |
| Sept 5 | Fri | Integration | ✓ Output JSON | ✓ Search tests | ✓ Verification |
| Sept 6 | Sat | Integration + Recording | ✓ Help with demo | ✓ Help with demo | ✓ Help with demo |
| Sept 7 | Sun | Final Polish | ✓ Docs | ✓ Docs | ✓ Docs + SUBMIT |

### Daily Sync Points

- **10:00 AM IST**: 5-min standup (blockers, dependencies)
- **4:00 PM IST**: Integration check (do modules work together?)
- **8:00 PM IST**: End-of-day commit (all code pushed)

### Key Handoff Points

1. **Sept 2 EOD**: Person 1 → Person 2 (embedding format)
2. **Sept 4 EOD**: Person 2 → Person 3 (post data format)
3. **Sept 5 EOD**: Full integration test
4. **Sept 6 EOD**: Screen recording ready

---

## Part 9: Submission Checklist

### Before Submitting

- [ ] GitHub repo public (or shared)
- [ ] README complete with:
  - [ ] What the project does
  - [ ] How to run it
  - [ ] Blockchain used + contract address
  - [ ] Known limitations
- [ ] Code runs end-to-end without errors
- [ ] All dependencies in requirements.txt / package.json
- [ ] API keys in .env.example (NO actual keys in repo)
- [ ] Tests pass: `pytest tests/`
- [ ] Smart contract verified (if on public testnet)
- [ ] Screen recording uploaded (YouTube unlisted / Google Drive / Loom)
- [ ] Screen recording shows:
  - [ ] Input image
  - [ ] Face detected
  - [ ] Social post found
  - [ ] Transaction hash displayed
  - [ ] Blockchain verification confirmed

### Submission Form
- GitHub repo link
- Screen recording link
- Brief 1-2 sentence description

---

## Part 10: Contingency Plans

### If Face Detection Fails
- Use pre-saved embeddings for testing
- Focus on social search + blockchain

### If Social Media Search Fails
- Use mock data (pre-defined posts)
- Skip real search, go to blockchain upload
- Document limitation in README

### If Blockchain Fails
- Use Hardhat local network instead
- Deploy contract to Hardhat, test locally
- Record with local blockchain

### If Time is Short
- **MVP**: Focus on pipeline working, not polish
- **Skip**: Multiple faces, advanced error handling
- **Use**: Mock data at any stage

---

## Roles Summary Table

| Role | Primary Task | Deliverable | Interface Output |
|------|--------------|-------------|-------------------|
| **Person 1** | Face detection & embedding | `detector.py` | Face embedding vector |
| **Person 2** | Social media search | `search_engine.py` | Post data (URL, caption, user) |
| **Person 3** | Blockchain verification | `upload_to_chain.py` + smart contract | Tx hash, verification proof |

---

## Success Criteria

✅ **Technical**
- [x] Face detection works on sample images
- [x] Social media search finds real posts (not hardcoded)
- [x] Data uploaded to blockchain with tx hash
- [x] Verification confirms stored == new hash

✅ **Documentation**
- [x] README explains pipeline
- [x] Each module has inline comments
- [x] API setup documented
- [x] Blockchain contract ABI provided

✅ **Submission**
- [x] GitHub repo with clean code
- [x] Screen recording shows end-to-end flow
- [x] Form submitted before deadline

---

**Document Version**: 1.0  
**Last Updated**: September 2026  
**Team**: 3 developers  
**Deadline**: September 7, 2026, 11:59 PM IST
