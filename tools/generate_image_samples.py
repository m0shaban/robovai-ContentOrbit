import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.image_generator import ImageGenerator
from core.config_manager import ConfigManager


def main() -> int:
    os.environ.setdefault("LOCAL_BACKGROUNDS_ENABLED", "1")
    os.environ.setdefault("LOCAL_BACKGROUNDS_DIR", "assets/backgrounds")
    os.environ.setdefault("LOCAL_BACKGROUNDS_STRATEGY", "topic")

    # Make variety obvious in samples
    os.environ.setdefault("DESIGN_PALETTE_MODE", "random")

    title = os.getenv("SAMPLES_TITLE") or "أهم أخبار الذكاء الاصطناعي اليوم"
    hook = os.getenv("SAMPLES_HOOK") or "ملخص سريع لأبرز التطورات التقنية"

    try:
        count = int(os.getenv("SAMPLES_COUNT") or "6")
    except Exception:
        count = 6
    count = max(1, min(12, count))

    out_dir = Path(os.getenv("SAMPLES_OUT_DIR") or "output")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load config.json so samples reflect dashboard poster settings
    config = ConfigManager()
    gen = ImageGenerator(config=config)

    for i in range(1, count + 1):
        img = gen.generate(title=title, hook=hook)
        out_path = out_dir / f"sample_{i:02d}.png"
        img.save(out_path, format="PNG")
        print(f"saved: {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
