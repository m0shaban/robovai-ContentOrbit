import base64
import io
import json
import os
import re
import sys
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

import httpx


GROQ_BASE_URL = "https://api.groq.com/openai/v1"


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
            # Don't override real process env
            if k in os.environ:
                continue
            os.environ[k] = v


def _pool_from_env(prefix: str, pool_var: str) -> List[str]:
    keys: List[str] = []
    for k, v in os.environ.items():
        if k.startswith(prefix):
            vv = (v or "").strip()
            if vv:
                keys.append(vv)
    pooled = (os.getenv(pool_var) or "").strip()
    if pooled:
        keys.extend([x.strip() for x in pooled.split(",") if x.strip()])
    # De-dupe
    out: List[str] = []
    seen = set()
    for k in keys:
        if k in seen:
            continue
        seen.add(k)
        out.append(k)
    return out


def _looks_like_key(value: str) -> bool:
    v = (value or "").strip()
    return v.startswith("gsk_") or v.startswith("nvapi-") or v.startswith("ya29.")


def _normalize_display_name(name: str) -> str:
    # crude normalization for matching user-provided names to model ids
    s = name.strip().lower()
    s = re.sub(r"\s+", "-", s)
    s = s.replace("/", "-")
    s = re.sub(r"[^a-z0-9._-]", "", s)
    return s


@dataclass
class TestResult:
    provider: str
    model: str
    test: str
    ok: bool
    status: Optional[int]
    detail: str


async def groq_list_models(
    client: httpx.AsyncClient, api_key: str
) -> Tuple[bool, List[str], str]:
    try:
        r = await client.get(
            f"{GROQ_BASE_URL}/models",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        if r.status_code in (401, 403, 429):
            return False, [], f"HTTP {r.status_code}"
        r.raise_for_status()
        data = r.json()
        models = [
            m.get("id")
            for m in data.get("data", [])
            if isinstance(m, dict) and m.get("id")
        ]
        return True, models, "ok"
    except Exception as e:
        return False, [], str(e)


async def groq_chat_test(
    client: httpx.AsyncClient, api_key: str, model: str
) -> TestResult:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Return only: OK"},
            {"role": "user", "content": "ping"},
        ],
        "temperature": 0,
        "max_tokens": 16,
    }
    try:
        r = await client.post(
            f"{GROQ_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json=payload,
        )
        if r.status_code in (401, 403, 402, 404, 429):
            return TestResult("groq", model, "chat", False, r.status_code, r.text[:200])
        r.raise_for_status()
        data = r.json()
        txt = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        ok = txt.upper().startswith("OK")
        return TestResult(
            "groq", model, "chat", ok, r.status_code, txt[:120] or "(empty)"
        )
    except Exception as e:
        return TestResult("groq", model, "chat", False, None, str(e)[:200])


async def groq_function_call_test(
    client: httpx.AsyncClient, api_key: str, model: str
) -> TestResult:
    # OpenAI-style tool calling
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You must call the tool."},
            {
                "role": "user",
                "content": "What is 2+2? Call the tool calc with args {a:2,b:2}.",
            },
        ],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "calc",
                    "description": "Adds two integers",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "a": {"type": "integer"},
                            "b": {"type": "integer"},
                        },
                        "required": ["a", "b"],
                    },
                },
            }
        ],
        "tool_choice": "auto",
        "temperature": 0,
        "max_tokens": 64,
    }
    try:
        r = await client.post(
            f"{GROQ_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json=payload,
        )
        if r.status_code in (401, 403, 402, 404, 429):
            return TestResult(
                "groq", model, "tool_call", False, r.status_code, r.text[:200]
            )
        r.raise_for_status()
        data = r.json()
        msg = data.get("choices", [{}])[0].get("message", {})
        tool_calls = msg.get("tool_calls") or []
        ok = bool(tool_calls)
        detail = "tool_calls" if ok else (msg.get("content") or "no tool call")
        return TestResult(
            "groq", model, "tool_call", ok, r.status_code, str(detail)[:160]
        )
    except Exception as e:
        return TestResult("groq", model, "tool_call", False, None, str(e)[:200])


async def nvidia_flux_test(api_keys: List[str], url: str) -> TestResult:
    if not api_keys:
        return TestResult(
            "nvidia", "flux", "img2img", False, None, "no NVIDIA_API_KEY*"
        )

    # create tiny image
    try:
        from PIL import Image
    except Exception:
        return TestResult(
            "nvidia", "flux", "img2img", False, None, "Pillow not installed"
        )

    # Many image models expect a minimum resolution; too-small inputs can cause
    # generic "Inference error" responses. Use a reasonable default size.
    size_raw = (os.getenv("NVIDIA_TEST_IMAGE_SIZE") or "1024").strip()
    try:
        size = int(size_raw)
    except Exception:
        size = 1024
    size = max(256, min(size, 1536))

    img = Image.new("RGB", (size, size), (240, 240, 240))
    mask = Image.new("L", (size, size), 255)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64_png = base64.b64encode(buf.getvalue()).decode("utf-8")
    data_url = "data:image/png;base64," + b64_png

    mbuf = io.BytesIO()
    mask.save(mbuf, format="PNG")
    b64_mask = base64.b64encode(mbuf.getvalue()).decode("utf-8")
    mask_data_url = "data:image/png;base64," + b64_mask

    prompt = "High quality cinematic abstract tech background, no text, no logos, no watermark"
    neg = "text, words, letters, logo, watermark"

    tuned_payload = {
        "prompt": prompt,
        "negative_prompt": neg,
        "aspect_ratio": "match_input_image",
        "steps": int(os.getenv("NVIDIA_IMAGE_STEPS", "10")),
        "cfg_scale": float(os.getenv("NVIDIA_CFG_SCALE", "3.5")),
        "seed": int(os.getenv("NVIDIA_IMAGE_SEED", "0")),
    }

    minimal_payload = {
        "prompt": prompt,
        "negative_prompt": neg,
    }

    # Try a small set of common request shapes; endpoints sometimes accept
    # either a data URL or raw base64, and may name the field differently.
    payload_variants = [
        # Minimal
        {**minimal_payload, "image": data_url},
        {**minimal_payload, "image": b64_png},
        {**minimal_payload, "input_image": data_url},
        {**minimal_payload, "input_image": b64_png},
        {**minimal_payload, "init_image": data_url},
        {**minimal_payload, "init_image": b64_png},
        # Minimal + mask (some edit endpoints require it)
        {**minimal_payload, "image": data_url, "mask": mask_data_url},
        {**minimal_payload, "image": data_url, "mask_image": mask_data_url},
        {**minimal_payload, "input_image": data_url, "mask": mask_data_url},
        {**minimal_payload, "input_image": data_url, "mask_image": mask_data_url},
        # Tuned
        {**tuned_payload, "image": data_url},
        {**tuned_payload, "image": b64_png},
        {**tuned_payload, "input_image": data_url},
        {**tuned_payload, "input_image": b64_png},
        {**tuned_payload, "init_image": data_url},
        {**tuned_payload, "init_image": b64_png},
        # Tuned + mask
        {**tuned_payload, "image": data_url, "mask": mask_data_url},
        {**tuned_payload, "image": data_url, "mask_image": mask_data_url},
        {**tuned_payload, "input_image": data_url, "mask": mask_data_url},
        {**tuned_payload, "input_image": data_url, "mask_image": mask_data_url},
        # txt2img attempt (some endpoints ignore the image field)
        {**minimal_payload},
    ]

    async with httpx.AsyncClient(timeout=90.0) as client:
        last = ""
        for k in api_keys:
            try:
                for idx, payload in enumerate(payload_variants, start=1):
                    r = await client.post(
                        url,
                        headers={
                            "Authorization": f"Bearer {k}",
                            "Accept": "application/json",
                            "Content-Type": "application/json",
                        },
                        json=payload,
                    )

                    if r.status_code in (401, 403, 429):
                        last = f"HTTP {r.status_code}" + (
                            f" {r.text[:200]}" if r.text else ""
                        )
                        break
                    if 400 <= r.status_code < 600:
                        last = (
                            f"HTTP {r.status_code}"
                            + (f" {r.text[:400]}" if r.text else "")
                            + f" (variant {idx})"
                        )
                        continue

                    r.raise_for_status()
                    data = r.json()
                    # Attempt to locate image field
                    candidate = None
                    if isinstance(data, dict):
                        for key in ("image", "output", "result"):
                            v = data.get(key)
                            if isinstance(v, str) and v:
                                candidate = v
                                break
                        if candidate is None:
                            imgs = data.get("images")
                            if isinstance(imgs, list) and imgs:
                                v0 = imgs[0]
                                if isinstance(v0, str):
                                    candidate = v0
                                elif isinstance(v0, dict):
                                    candidate = (
                                        v0.get("image")
                                        or v0.get("base64")
                                        or v0.get("b64_json")
                                        or v0.get("data")
                                    )
                    if not candidate:
                        last = f"no image in response (variant {idx})"
                        continue
                    return TestResult(
                        "nvidia",
                        "flux.1-kontext-dev",
                        "img2img",
                        True,
                        r.status_code,
                        f"ok (variant {idx})",
                    )
            except Exception as e:
                last = str(e)[:200]
                continue
        return TestResult(
            "nvidia", "flux.1-kontext-dev", "img2img", False, None, last or "failed"
        )


def collect_env_models() -> List[str]:
    vals: List[str] = []
    for k, v in os.environ.items():
        if not k.startswith("GROQ_MODEL_"):
            continue
        vv = (v or "").strip()
        if not vv:
            continue
        if _looks_like_key(vv):
            continue
        vals.append(vv)
    # Add the defaults too
    for k in (
        "GROQ_MODEL_LONG",
        "GROQ_MODEL_LONG_EN",
        "GROQ_MODEL_SHORT",
        "GROQ_MODEL_SHORT_EN",
    ):
        vv = (os.getenv(k) or "").strip()
        if vv and not _looks_like_key(vv):
            vals.append(vv)
    # de-dupe
    out: List[str] = []
    seen = set()
    for m in vals:
        if m in seen:
            continue
        seen.add(m)
        out.append(m)
    return out


def collect_user_requested_models() -> List[str]:
    # Rough guesses for common Groq IDs (will be filtered against /models)
    candidates = [
        "gpt-oss-120b",
        "gpt-oss-20b",
        "qwen3-32b",
        "qwen-3-32b",
        "llama-4-scout",
        "llama-4-maverick",
        "kimi-k2",
        "llama-3.3-70b",
    ]
    # De-dupe
    out: List[str] = []
    seen = set()
    for c in candidates:
        if c in seen:
            continue
        seen.add(c)
        out.append(c)
    return out


def print_table(results: List[TestResult]) -> None:
    # Simple fixed-width output
    cols = ["provider", "model", "test", "ok", "status", "detail"]
    rows = [
        [
            r.provider,
            r.model,
            r.test,
            "YES" if r.ok else "NO",
            str(r.status or ""),
            r.detail,
        ]
        for r in results
    ]
    widths = [len(c) for c in cols]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    def fmt(row: List[str]) -> str:
        return " | ".join(cell.ljust(widths[i]) for i, cell in enumerate(row))

    print(fmt(cols))
    print("-+-".join("-" * w for w in widths))
    for row in rows:
        print(fmt(row))


async def main() -> int:
    # Load .env into process env for this script
    load_dotenv(os.path.join(os.getcwd(), ".env"))

    groq_keys = _pool_from_env("GROQ_API_KEY", "GROQ_API_KEYS")
    nvidia_keys = _pool_from_env("NVIDIA_API_KEY", "NVIDIA_API_KEYS")

    results: List[TestResult] = []

    # --- Groq ---
    if not groq_keys:
        results.append(
            TestResult("groq", "(none)", "models", False, None, "no GROQ_API_KEY*")
        )
    else:
        async with httpx.AsyncClient(timeout=30.0) as client:
            ok, model_list, detail = await groq_list_models(client, groq_keys[0])
            results.append(
                TestResult("groq", "(list)", "models", ok, 200 if ok else None, detail)
            )

            # Build test set
            raw_targets: List[str] = []
            raw_targets.extend(collect_env_models())
            raw_targets.extend(collect_user_requested_models())

            # de-dupe
            seen = set()
            targets: List[str] = []
            for m in raw_targets:
                if m in seen:
                    continue
                seen.add(m)
                targets.append(m)

            # If we can list models, only test those that exist
            if model_list:
                available = set(model_list)
                norm_map = {_normalize_display_name(mid): mid for mid in model_list}

                resolved: List[str] = []
                missing: List[str] = []
                for m in targets:
                    if m in available:
                        resolved.append(m)
                        continue
                    nm = _normalize_display_name(m)
                    if nm in norm_map:
                        resolved.append(norm_map[nm])
                        continue
                    missing.append(m)

                for m in missing:
                    results.append(
                        TestResult(
                            "groq", m, "available", False, None, "not in /models"
                        )
                    )

                # de-dupe resolved (normalization can map multiple candidates to the same id)
                seen = set()
                deduped: List[str] = []
                for m in resolved:
                    if m in seen:
                        continue
                    seen.add(m)
                    deduped.append(m)
                targets = deduped

            # If still empty, fall back to GroqConfig default-ish candidates
            if not targets:
                targets = ["llama-3.1-8b-instant", "llama-3.1-70b-versatile"]

            # de-dupe
            seen = set()
            uniq_targets = []
            for m in targets:
                if m in seen:
                    continue
                seen.add(m)
                uniq_targets.append(m)

            # Run tests
            for model in uniq_targets:
                # rotate keys quickly: first key for test
                api_key = groq_keys[0]
                results.append(await groq_chat_test(client, api_key, model))
                results.append(await groq_function_call_test(client, api_key, model))

    # --- NVIDIA flux ---
    flux_url = (
        os.getenv("NVIDIA_FLUX_KONTEXT_URL") or ""
    ).strip() or "https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux.1-kontext-dev"
    results.append(await nvidia_flux_test(nvidia_keys, flux_url))

    print_table(results)

    failed = [r for r in results if not r.ok]
    return 1 if failed else 0


if __name__ == "__main__":
    try:
        import asyncio

        raise SystemExit(asyncio.run(main()))
    except KeyboardInterrupt:
        raise SystemExit(130)
