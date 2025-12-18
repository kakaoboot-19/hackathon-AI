from PIL import Image
from io import BytesIO

import os
import requests

API_URL = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"
API_TOKEN = os.getenv("HF_API")

if not API_TOKEN:
    raise RuntimeError("HF_TOKEN environment variable not set")

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

def generate_image(prompt: str, output_path: str):
    response = requests.post(
        API_URL,
        headers=headers,
        json={"inputs": prompt},
        timeout=120
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"HF API error {response.status_code}: {response.text}"
        )

    content_type = response.headers.get("Content-Type", "")
    if "image" not in content_type:
        raise RuntimeError(
            f"Unexpected response ({content_type}): {response.text}"
        )

    # 🔹 bytes → PIL Image
    image = Image.open(BytesIO(response.content)).convert("RGB")

    return image