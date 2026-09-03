# End-to-end integration

The pipeline entry point is `main.py`:

```python
from main import run_pipeline

result = run_pipeline("input.jpg", public_image_url="https://public.example/input.jpg")
if result["success"]:
    print(result["best_match"]["url"])
```

`run_pipeline` retains the input path, passes only `face_result["embedding"]` to Stage 2, selects `search_result["matches"][0]`, and passes that exact dictionary to Stage 3. Stage 3 canonicalizes and hashes it, uploads the digest, then rehashes the same object for on-chain verification.

Configure the provider variables from `.env.example` and blockchain variables from `blockchain/.env.example`. Start and deploy the local Hardhat contract first, then set `RPC_URL`, `PRIVATE_KEY`, and `CONTRACT_ADDRESS`. For Google Lens, the image URL must be publicly reachable; Bing can use the local image path.

The final result contains `face`, `search`, `best_match`, `blockchain_upload`, and `blockchain_verification`. `success` is true only when the upload succeeds and the on-chain verification reports both a successful transaction and `verified: true`.
