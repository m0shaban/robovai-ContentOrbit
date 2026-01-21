import re
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    pat_getenv = re.compile(r"os\.getenv\(\s*['\"]([A-Z0-9_]+)['\"]")
    pat_environ_get = re.compile(r"os\.environ\.get\(\s*['\"]([A-Z0-9_]+)['\"]")
    pat_environ_setdefault = re.compile(
        r"os\.environ\.setdefault\(\s*['\"]([A-Z0-9_]+)['\"]"
    )
    pat_env_call = re.compile(r"\benv\((.*?)\)", re.DOTALL)
    pat_env_first_call = re.compile(r"\b_env_first\((.*?)\)", re.DOTALL)
    pat_str_literal = re.compile(r"['\"]([A-Z0-9_]+)['\"]")

    names: set[str] = set()
    for path in root.rglob("*.py"):
        if ".venv" in path.parts:
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        names.update(pat_getenv.findall(content))
        names.update(pat_environ_get.findall(content))
        names.update(pat_environ_setdefault.findall(content))

        # ConfigManager.env("A", "B") style wrappers
        for m in pat_env_call.findall(content):
            names.update(pat_str_literal.findall(m))

        # LLMClient._env_first("A", "B") style wrappers
        for m in pat_env_first_call.findall(content):
            names.update(pat_str_literal.findall(m))

    for n in sorted(names):
        if len(n) < 3:
            continue
        if "_" not in n and n not in {"PORT"}:
            continue
        print(n)


if __name__ == "__main__":
    main()
