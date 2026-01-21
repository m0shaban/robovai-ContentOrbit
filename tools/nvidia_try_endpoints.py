import base64
import io
import os
import sys
from typing import Any, Dict, Optional, Tuple

import requests


def load_dotenv(path: str) -> None:
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip()
            if not k:
                continue
            if k in os.environ:
                continue
            os.environ[k] = v


def pick_nvidia_key() -> Optional[str]:
    # Prefer explicit NVIDIA_API_KEY, otherwise any NVIDIA_API_KEY*
    base = (os.getenv("NVIDIA_API_KEY") or "").strip()
    if base:
        return base

    for k, v in os.environ.items():
        if k.startswith("NVIDIA_API_KEY") and (v or "").strip():
            return (v or "").strip()
    return None


def make_png_data_url(size: int = 1024) -> str:
    from PIL import Image

    size = max(256, min(int(size), 1536))
    img = Image.new("RGB", (size, size), (240, 240, 240))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64}"


def make_example_id_data_url(example_id: int) -> str:
    # Per NVIDIA NIM Preview API docs: only predefined example images are accepted.
    # Format: data:image/png;example_id,{example_id}
    return f"data:image/png;example_id,{int(example_id)}"


def extract_image_from_response(data: Any) -> Optional[Tuple[str, str]]:
    """Return (kind, value) where kind is one of: data_url, base64, url."""
    if isinstance(data, dict):
        # NIM responses commonly return artifacts: [{base64: ..., seed: ..., ...}]
        artifacts = data.get("artifacts")
        if isinstance(artifacts, list) and artifacts:
            a0 = artifacts[0]
            if isinstance(a0, dict):
                for key in ("base64", "b64_json", "image", "data", "url"):
                    v = a0.get(key)
                    if isinstance(v, str) and v:
                        return _classify_image(v)

        for key in ("image", "output", "result"):
            v = data.get(key)
            if isinstance(v, str) and v:
                return _classify_image(v)

        imgs = data.get("images")
        if isinstance(imgs, list) and imgs:
            v0 = imgs[0]
            if isinstance(v0, str) and v0:
                return _classify_image(v0)
            if isinstance(v0, dict):
                for key in ("image", "b64_json", "base64", "data", "url"):
                    v = v0.get(key)
                    if isinstance(v, str) and v:
                        return _classify_image(v)

    return None


def _classify_image(v: str) -> Tuple[str, str]:
    vv = v.strip()
    if vv.startswith("data:image"):
        return "data_url", vv
    if vv.startswith("http://") or vv.startswith("https://"):
        return "url", vv
    # fallback assume base64
    return "base64", vv


def save_image(kind: str, value: str, out_path: str) -> None:
    if kind == "url":
        r = requests.get(value, timeout=60)
        r.raise_for_status()
        with open(out_path, "wb") as f:
            f.write(r.content)
        return

    if kind == "data_url":
        b64 = value.split(",", 1)[1]
        img_bytes = base64.b64decode(b64)
    else:
        img_bytes = base64.b64decode(value)

    with open(out_path, "wb") as f:
        f.write(img_bytes)


def post_json(
    url: str,
    payload: Dict[str, Any],
    api_key: str,
    *,
    timeout_s: int = 300,
) -> Tuple[int, str, Any, Dict[str, str]]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    r = requests.post(url, headers=headers, json=payload, timeout=(15, timeout_s))
    text = r.text
    try:
        j = r.json()
    except Exception:
        j = None
    resp_headers = {k.lower(): v for k, v in r.headers.items()}
    return r.status_code, text, j, resp_headers


def main() -> int:
    load_dotenv(os.path.join(os.getcwd(), ".env"))

    api_key = pick_nvidia_key()
    if not api_key:
        print("Missing NVIDIA_API_KEY (or NVIDIA_API_KEY_2...) in env")
        return 2

    # 1) Kontext (img2img edit)
    kontext_url = (
        "https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux.1-kontext-dev"
    )

    # NVIDIA NIM Preview APIs only accept predefined images via example_id.
    # Use base64 image only if explicitly requested.
    use_real_image = (os.getenv("NVIDIA_USE_REAL_IMAGE") or "").strip().lower() in (
        "1",
        "true",
        "yes",
    )
    if use_real_image:
        test_size = int((os.getenv("NVIDIA_TEST_IMAGE_SIZE") or "1024").strip() or 1024)
        img_data_url = make_png_data_url(test_size)
    else:
        kontext_example_id = int(
            (
                os.getenv("NVIDIA_KONTEXT_EXAMPLE_ID")
                or os.getenv("NVIDIA_EXAMPLE_IMAGE_ID")
                or "0"
            ).strip()
            or 0
        )
        img_data_url = make_example_id_data_url(kontext_example_id)

    kontext_payload: Dict[str, Any] = {
        "prompt": "Now the mouse is holding pizza instead",
        "image": img_data_url,
        "aspect_ratio": "match_input_image",
        "steps": 30,
        "cfg_scale": 3.5,
        "seed": 0,
    }

    print("--- NVIDIA Kontext ---")
    status, text, data, headers = post_json(kontext_url, kontext_payload, api_key)
    print("status:", status)
    print("content-type:", headers.get("content-type"))
    if status != 200:
        print(text[:800])
    else:
        img = extract_image_from_response(data)
        print(
            "response keys:",
            list(data.keys()) if isinstance(data, dict) else type(data),
        )
        if (
            isinstance(data, dict)
            and isinstance(data.get("artifacts"), list)
            and data["artifacts"]
        ):
            a0 = data["artifacts"][0]
            if isinstance(a0, dict):
                print("artifact keys:", list(a0.keys()))
        if img:
            kind, value = img
            os.makedirs("output", exist_ok=True)
            out_path = os.path.join("output", "nvidia_kontext.png")
            save_image(kind, value, out_path)
            print("saved:", out_path)
        else:
            print("No image found in response")

    # 2) FLUX.1-dev (txt2img)
    dev_url = "https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux.1-dev"

    print("\n--- NVIDIA FLUX.1-dev ---")
    dev_payload_variants = [
        # Minimal required fields per API docs
        {"prompt": "a simple coffee shop interior"},
        # Explicit base mode
        {"prompt": "a simple coffee shop interior", "mode": "base"},
        # Full payload (only 1024x1024 is supported per docs)
        {
            "prompt": "a simple coffee shop interior",
            "mode": "base",
            "cfg_scale": 5,
            "width": 1024,
            "height": 1024,
            "seed": 0,
            "steps": 50,
        },
    ]

    last_text = ""
    last_status = None
    last_headers: Dict[str, str] = {}
    last_data: Any = None

    for i, dev_payload in enumerate(dev_payload_variants, start=1):
        print(
            f"attempt {i}/{len(dev_payload_variants)} payload keys:",
            sorted(dev_payload.keys()),
        )
        status, text, data, headers = post_json(
            dev_url, dev_payload, api_key, timeout_s=420
        )
        print("status:", status)
        print("content-type:", headers.get("content-type"))
        if status == 200:
            last_status, last_text, last_headers, last_data = (
                status,
                text,
                headers,
                data,
            )
            break

        # capture and continue to next variant
        last_status, last_text, last_headers, last_data = status, text, headers, data
        print(text[:400])

    if last_status != 200:
        print("final status:", last_status)
        print(last_text[:800])
        return 1

    img = extract_image_from_response(last_data)
    print(
        "response keys:",
        list(last_data.keys()) if isinstance(last_data, dict) else type(last_data),
    )
    if img:
        kind, value = img
        os.makedirs("output", exist_ok=True)
        out_path = os.path.join("output", "nvidia_flux1_dev.png")
        save_image(kind, value, out_path)
        print("saved:", out_path)
        return 0

    print("No image found in response")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
