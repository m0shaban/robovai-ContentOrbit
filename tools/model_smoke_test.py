import os
import re
import sys
import urllib.parse
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
            mid
            for m in data.get("data", [])
            if isinstance(m, dict)
            for mid in [m.get("id")]
            if isinstance(mid, str) and mid
        ]
        return True, models, "ok"
    except Exception as e:
        return False, [], str(e)


def collect_env_models() -> List[str]:
    """Collect Groq model IDs configured via env vars."""
    models: List[str] = []
    for k, v in os.environ.items():
        if not k.startswith("GROQ_MODEL_"):
            continue
        vv = (v or "").strip()
        if vv:
            models.append(vv)
    for k in ("GROQ_IMAGE_PROMPT_MODEL",):
        vv = (os.getenv(k) or "").strip()
        if vv:
            models.append(vv)
    return models


def collect_user_requested_models() -> List[str]:
    """Collect model IDs passed on the CLI: `python tools/model_smoke_test.py model1,model2`."""
    out: List[str] = []
    for arg in sys.argv[1:]:
        if not arg:
            continue
        out.extend([x.strip() for x in arg.split(",") if x.strip()])
    return out


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


def _pollinations_build_url(
    prompt: str,
    width: int,
    height: int,
    model: str,
    seed: str,
) -> str:
    q = urllib.parse.quote((prompt or "").strip() or "abstract tech background")
    params: Dict[str, str] = {
        "width": str(width),
        "height": str(height),
        "nologo": "true",
    }
    if model:
        params["model"] = model
    if seed:
        params["seed"] = seed
    return f"https://image.pollinations.ai/prompt/{q}?{urllib.parse.urlencode(params)}"


async def pollinations_image_test(client: httpx.AsyncClient) -> TestResult:
    model = (os.getenv("POLLINATIONS_MODEL") or "flux").strip() or "flux"
    seed = (os.getenv("POLLINATIONS_SEED") or "").strip()
    try:
        width = int((os.getenv("POLLINATIONS_WIDTH") or "1200").strip() or 1200)
        height = int((os.getenv("POLLINATIONS_HEIGHT") or "630").strip() or 630)
    except Exception:
        width, height = 1200, 630

    prompt = "High quality abstract tech background, no text, no logos"
    url = _pollinations_build_url(
        prompt, width=width, height=height, model=model, seed=seed
    )

    try:
        r = await client.get(url, follow_redirects=True)
        if r.status_code >= 400:
            return TestResult(
                "pollinations", model, "image", False, r.status_code, r.text[:160]
            )
        ctype = (r.headers.get("content-type") or "").lower()
        ok = ctype.startswith("image/") and len(r.content) > 1000
        return TestResult(
            "pollinations",
            model,
            "image",
            ok,
            r.status_code,
            ctype or "(no content-type)",
        )
    except Exception as e:
        return TestResult("pollinations", model, "image", False, None, str(e)[:200])


async def main() -> int:
    # Load .env into process env for this script
    load_dotenv(os.path.join(os.getcwd(), ".env"))

    groq_keys = _pool_from_env("GROQ_API_KEY", "GROQ_API_KEYS")
    provider = (
        (os.getenv("IMAGE_AI_PROVIDER", "pollinations") or "pollinations")
        .strip()
        .lower()
    )
    pollinations_enabled = (os.getenv("ENABLE_IMAGE_AI") or "0").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )

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

    # --- Pollinations ---
    if pollinations_enabled and provider in ("pollinations", "auto"):
        async with httpx.AsyncClient(timeout=30.0) as client:
            results.append(await pollinations_image_test(client))

    print_table(results)

    failed = [r for r in results if not r.ok]
    return 1 if failed else 0


if __name__ == "__main__":
    try:
        import asyncio

        raise SystemExit(asyncio.run(main()))
    except KeyboardInterrupt:
        raise SystemExit(130)
