import os

from core.image_generator import ImageGenerator


def main() -> int:
    # Use local backgrounds (the images you placed in ./output).
    os.environ.setdefault("LOCAL_BACKGROUNDS_ENABLED", "1")
    os.environ.setdefault("LOCAL_BACKGROUNDS_DIR", "assets/backgrounds")
    os.environ.setdefault("LOCAL_BACKGROUNDS_STRATEGY", "topic")

    generator = ImageGenerator()

    title = "أهم أخبار الذكاء الاصطناعي اليوم"
    hook = "ملخص سريع لأبرز التطورات التقنية"
    img = generator.generate(title=title, hook=hook)

    os.makedirs("output", exist_ok=True)
    out_path = os.path.join("output", "demo_local_background.png")
    img.save(out_path, format="PNG")
    print(f"saved: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
