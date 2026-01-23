"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🎨 ContentOrbit Image Generator                            ║
║                    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                            ║
║                                                                              ║
║   A sophisticated programmatic graphic design engine that generates          ║
║   professional social media images from scratch - no templates needed!       ║
║                                                                              ║
║   Features:                                                                  ║
║   • Dynamic gradient backgrounds (linear, radial, diagonal)                  ║
║   • Geometric art elements (circles, lines, dots, waves)                     ║
║   • Smart text wrapping with emoji support via pilmoji                       ║
║   • Professional overlays and borders                                        ║
║   • Auto-upload to ImgBB                                                     ║
║                                                                              ║
║   Author: ContentOrbit Team                                                  ║
║   Version: 1.0.0                                                             ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import io
import os
import base64
import random
import math
import logging
import re
import json
import urllib.parse
from typing import Optional, Tuple, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Try to import pilmoji for emoji support
try:
    from pilmoji import Pilmoji

    PILMOJI_AVAILABLE = True
except ImportError:
    PILMOJI_AVAILABLE = False
    logging.warning(
        "⚠️ pilmoji not installed. Falling back to system emoji font (if available)."
    )

# Arabic text support - CRITICAL for RTL languages
try:
    import arabic_reshaper
    from bidi.algorithm import get_display

    ARABIC_SUPPORT = True
except ImportError:
    ARABIC_SUPPORT = False
    logging.warning(
        "⚠️ arabic-reshaper/python-bidi not installed. Arabic text may not render correctly."
    )

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# 🎨 ARTISTIC COLOR PALETTES - Carefully curated for visual impact
# ═══════════════════════════════════════════════════════════════════════════════


class ColorPalette(Enum):
    """
    Professional color palettes inspired by modern design trends.
    Each palette contains: (primary, secondary, accent, text_color)
    """

    # Deep space vibes - mysterious and professional
    COSMIC_NIGHT = [
        (15, 23, 42),  # Deep navy
        (30, 58, 138),  # Royal blue
        (139, 92, 246),  # Purple accent
    ]

    # Sunset gradient - warm and inviting
    SUNSET_GLOW = [
        (127, 29, 29),  # Deep red
        (194, 65, 12),  # Burnt orange
        (251, 191, 36),  # Golden yellow
    ]

    # Ocean depths - calm and trustworthy
    OCEAN_DEEP = [
        (6, 78, 59),  # Deep teal
        (13, 148, 136),  # Teal
        (45, 212, 191),  # Aqua accent
    ]

    # Cyber punk - edgy and modern
    CYBER_PUNK = [
        (30, 10, 60),  # Deep purple
        (236, 72, 153),  # Hot pink
        (34, 211, 238),  # Cyan accent
    ]

    # Forest mystery - natural and grounded
    FOREST_MIST = [
        (20, 30, 25),  # Dark forest
        (34, 87, 64),  # Forest green
        (74, 222, 128),  # Lime accent
    ]

    # Royal elegance - luxurious feel
    ROYAL_GOLD = [
        (23, 23, 33),  # Near black
        (88, 28, 135),  # Royal purple
        (250, 204, 21),  # Gold accent
    ]

    # Tech blue - modern and clean
    TECH_BLUE = [
        (15, 23, 42),  # Dark slate
        (37, 99, 235),  # Bright blue
        (96, 165, 250),  # Light blue accent
    ]

    # Warm gradient - friendly and approachable
    WARM_EMBER = [
        (69, 10, 10),  # Deep maroon
        (185, 28, 28),  # Red
        (252, 165, 165),  # Soft pink accent
    ]


@dataclass
class DesignConfig:
    """
    Configuration for image generation.
    Allows fine-tuning of all artistic parameters.
    """

    # Canvas dimensions (OG Image standard)
    width: int = 1200
    height: int = 630

    # Typography settings
    # Bigger by default for social readability.
    title_font_size: int = 40
    hook_font_size: int = 20
    title_max_width: int = 980  # Max width before wrapping
    # Default layout target: 1-2 title lines + 0-1 hook line (social friendly)
    max_title_lines: int = 3
    max_hook_lines: int = 1
    min_title_font_size: int = 38
    min_hook_font_size: int = 23

    # Text effects (readability on any background)
    text_shadow: bool = True
    text_shadow_offset: int = 3
    text_shadow_alpha: int = 220
    text_outline_width: int = 3
    text_outline_alpha: int = 220
    text_align: str = "center"  # center|right

    # Overlay settings
    overlay_opacity: float = 0.25  # Lower opacity to show background better

    # Glass card settings (for templates)
    card_opacity: int = 60  # More transparent
    card_blur_radius: int = 0  # No blur
    card_radius: int = 28
    card_padding_x: int = 30
    card_padding_y: int = 25

    # Geometric elements
    num_circles: int = 8
    num_dots: int = 50
    num_lines: int = 6

    # Border settings
    border_width: int = 4
    border_glow: bool = True

    # Gradient direction: 'diagonal', 'horizontal', 'vertical', 'radial'
    gradient_type: str = "diagonal"


class ImageTemplate(Enum):
    """High-level layout templates for OG images."""

    HERO_CARD = "hero_card"  # big centered glass card
    SPLIT_HERO = "split_hero"  # text panel + art area
    MINIMAL_BOLD = "minimal_bold"  # minimal, huge headline


@dataclass
class TopicProfile:
    palette: ColorPalette
    gradient_type: str
    template: ImageTemplate
    badge_text: Optional[str] = None
    badge_emoji: Optional[str] = None


class ImageGenerator:
    """
    🎨 The Artistic Engine

    This class is the heart of our programmatic design system.
    It generates professional images through pure code - no templates!

    The design philosophy follows these principles:
    1. Dynamic backgrounds that never repeat
    2. Layered composition for depth
    3. Smart typography that adapts to content
    4. Subtle geometric art for visual interest
    """

    def __init__(
        self, imgbb_api_key: Optional[str] = None, config: Optional[object] = None
    ):
        """
        Initialize the image generator.

        Args:
            imgbb_api_key: API key for ImgBB upload service
        """
        # Never hardcode secrets; rely on env/.env.
        self.imgbb_api_key = imgbb_api_key or (os.getenv("IMGBB_API_KEY") or "").strip()
        self.config = DesignConfig()

        # Optional config-driven overrides (dashboard/config.json)
        self._app_config = (
            getattr(config, "app_config", None) if config is not None else None
        )
        self._poster_cfg = (
            getattr(self._app_config, "poster", None)
            if self._app_config is not None
            else None
        )

        # Round-robin indexes for multi-key pools
        self._groq_key_index = 0

        # Font paths - we'll try multiple locations
        self.font_paths = self._discover_fonts()

        # Apply poster overrides after fonts are discovered
        self._apply_poster_overrides()

        if not self.imgbb_api_key:
            logger.warning("⚠️ IMGBB_API_KEY is not set; uploads will fail.")

        logger.info("🎨 Image Generator initialized")

    def _apply_poster_overrides(self) -> None:
        """Apply dashboard-driven poster overrides onto the internal DesignConfig."""
        if self._poster_cfg is None:
            return

        try:
            if hasattr(self._poster_cfg, "enabled") and not bool(
                getattr(self._poster_cfg, "enabled")
            ):
                return
        except Exception:
            return

        for attr in (
            "title_font_size",
            "hook_font_size",
            "min_title_font_size",
            "min_hook_font_size",
            "max_title_lines",
            "max_hook_lines",
            "overlay_opacity",
            "card_opacity",
            "border_width",
            "border_glow",
            "text_shadow",
            "text_shadow_offset",
            "text_shadow_alpha",
            "text_outline_width",
            "text_outline_alpha",
            "text_align",
        ):
            if not hasattr(self._poster_cfg, attr):
                continue
            v = getattr(self._poster_cfg, attr)
            if v is None:
                continue
            try:
                setattr(self.config, attr, v)
            except Exception:
                continue

    def _env_flag(self, name: str, default: str = "0") -> bool:
        return (os.getenv(name, default) or default).strip().lower() in (
            "1",
            "true",
            "yes",
            "on",
        )

    def _cover_resize(self, img: Image.Image, size: Tuple[int, int]) -> Image.Image:
        """Resize an image to cover the target size (center-crop)."""
        target_w, target_h = size
        src = img.convert("RGBA")
        src_w, src_h = src.size
        if src_w <= 0 or src_h <= 0:
            return src.resize(size, Image.Resampling.LANCZOS)

        scale = max(target_w / src_w, target_h / src_h)
        new_w = max(1, int(round(src_w * scale)))
        new_h = max(1, int(round(src_h * scale)))
        resized = src.resize((new_w, new_h), Image.Resampling.LANCZOS)

        left = max(0, (new_w - target_w) // 2)
        top = max(0, (new_h - target_h) // 2)
        return resized.crop((left, top, left + target_w, top + target_h))

    def _list_local_background_paths(self) -> List[str]:
        base_dir = (
            os.getenv("LOCAL_BACKGROUNDS_DIR") or "assets/backgrounds"
        ).strip() or "assets/backgrounds"
        if not os.path.isabs(base_dir):
            base_dir = os.path.join(os.getcwd(), base_dir)
        if not os.path.isdir(base_dir):
            return []

        exts = (".png", ".jpg", ".jpeg", ".webp")
        out: List[str] = []
        try:
            for name in os.listdir(base_dir):
                if name.lower().endswith(exts):
                    out.append(os.path.join(base_dir, name))
        except Exception:
            return []

        out.sort()
        return out

    def _pick_local_background_path(
        self, profile: "TopicProfile", title: str, hook: Optional[str]
    ) -> Optional[str]:
        paths = self._list_local_background_paths()
        if not paths:
            return None

        strategy = (os.getenv("LOCAL_BACKGROUNDS_STRATEGY") or "topic").strip().lower()
        if strategy not in ("topic", "random"):
            strategy = "topic"

        if strategy == "random":
            return random.choice(paths)

        # Topic-aware selection: match by filename keywords.
        text = f"{title or ''} {hook or ''}".lower()

        def want(*tokens: str) -> bool:
            return any(t and (t.lower() in text) for t in tokens)

        preferred: List[str] = []

        # Keyword-driven picks (Arabic + English)
        if want("ai", "artificial", "machine", "ذكاء", "اصطناعي", "تعلم", "نموذج"):
            preferred += ["ai_wave", "space_dust"]
        if want("security", "cyber", "hack", "هكر", "اختراق", "أمن", "سيبر"):
            preferred += ["tech_grid", "neon_cyber"]
        if want("finance", "business", "startup", "استثمار", "مال", "تمويل", "شركات"):
            preferred += ["finance_gold"]
        if want("data", "analytics", "statistics", "بيانات", "تحليل"):
            preferred += ["heatmap"]
        if want("design", "ui", "ux", "تصميم"):
            preferred += ["clean_minimal", "soft_pastel"]
        if want("news", "breaking", "خبر", "عاجل", "تحديث"):
            preferred += ["newsprint"]
        if want("ocean", "sea", "بحر", "محيط"):
            preferred += ["ocean_deep"]
        if want("circuit", "chip", "gpu", "hardware", "شريحة", "معالج"):
            preferred += ["circuit_board", "tech_grid"]
        if want("engineer", "build", "code", "برمجة", "مطور", "هندسة"):
            preferred += ["blueprint", "tech_grid"]

        # Palette-driven fallback
        try:
            if profile.palette == ColorPalette.CYBER_PUNK:
                preferred += ["neon_cyber"]
            elif profile.palette == ColorPalette.TECH_BLUE:
                preferred += ["tech_grid"]
            elif profile.palette == ColorPalette.OCEAN_DEEP:
                preferred += ["ocean_deep"]
            elif profile.palette == ColorPalette.ROYAL_GOLD:
                preferred += ["finance_gold"]
            elif profile.palette == ColorPalette.SUNSET_GLOW:
                preferred += ["gradient_sunset"]
        except Exception:
            pass

        # Generic fallback (looks good for most posts)
        preferred += ["tech_grid", "gradient_sunset", "dark_glass", "clean_minimal"]

        candidates: List[str] = []
        for token in preferred:
            for p in paths:
                if token in os.path.basename(p).lower():
                    candidates.append(p)

        # If we found any matches, pick randomly among them to avoid repeating the
        # same background for similar topics.
        if candidates:
            # De-dup while preserving order
            deduped = list(dict.fromkeys(candidates))
            return random.choice(deduped)

        return random.choice(paths)

    def _choose_palette(
        self, profile: "TopicProfile", *, use_local_bg: bool
    ) -> ColorPalette:
        """Choose a palette based on env + context.

        Env: DESIGN_PALETTE_MODE
        - topic: always use the topic-inferred palette (old behavior)
        - random: pick a random palette
        - mixed: prefer topic palette but rotate through others

        Default:
        - When local backgrounds are enabled: random (more variety)
        - Otherwise: topic (more consistent gradients)
        """

        mode = (os.getenv("DESIGN_PALETTE_MODE") or "").strip().lower()
        if not mode:
            mode = "random" if use_local_bg else "topic"

        if mode not in ("topic", "random", "mixed"):
            mode = "topic"

        if mode == "topic":
            return profile.palette

        pool = list(ColorPalette)
        if not pool:
            return profile.palette

        if mode == "mixed":
            pool = [profile.palette] + [p for p in pool if p != profile.palette]

        try:
            return random.choice(pool)
        except Exception:
            return profile.palette

    def _pollinations_build_url(self, prompt: str, *, width: int, height: int) -> str:
        prompt = (prompt or "").strip()
        encoded = urllib.parse.quote(prompt, safe="")
        base = f"https://image.pollinations.ai/prompt/{encoded}"

        model = (os.getenv("POLLINATIONS_MODEL") or "flux").strip() or "flux"
        seed = (os.getenv("POLLINATIONS_SEED") or "").strip()

        params = {
            "width": str(width),
            "height": str(height),
            "model": model,
            "nologo": "true",
        }
        if seed:
            params["seed"] = seed

        return base + "?" + urllib.parse.urlencode(params)

    def _pollinations_generate_background(
        self, prompt: str, size: Tuple[int, int]
    ) -> Optional[Image.Image]:
        try:
            url = self._pollinations_build_url(prompt, width=size[0], height=size[1])
            r = requests.get(url, timeout=60)
            r.raise_for_status()
            img = Image.open(io.BytesIO(r.content))
            img = img.convert("RGBA")
            return self._cover_resize(img, size)
        except Exception as e:
            logger.warning(f"Pollinations background failed: {e}")
            return None

    def _load_local_background(
        self,
        profile: "TopicProfile",
        title: str,
        hook: Optional[str],
        size: Tuple[int, int],
    ) -> Optional[Image.Image]:
        path = self._pick_local_background_path(profile=profile, title=title, hook=hook)
        if not path:
            return None

        try:
            bg = Image.open(path)
            bg = self._cover_resize(bg, size)

            blur = float((os.getenv("LOCAL_BACKGROUNDS_BLUR") or "0").strip() or 0)
            if blur > 0:
                bg = bg.filter(
                    ImageFilter.GaussianBlur(radius=min(20.0, max(0.0, blur)))
                )

            dim = float((os.getenv("LOCAL_BACKGROUNDS_DIM") or "0").strip() or 0)
            if dim > 0:
                dim = min(0.8, max(0.0, dim))
                overlay = Image.new("RGBA", size, (0, 0, 0, int(255 * dim)))
                bg = Image.alpha_composite(bg.convert("RGBA"), overlay)

            return bg.convert("RGBA")
        except Exception as e:
            logger.warning(f"Failed to load local background '{path}': {e}")
            return None

    def _has_emoji(self, text: str) -> bool:
        """Best-effort emoji detection without extra deps."""
        if not text:
            return False
        try:
            # Main emoji blocks + some symbol blocks
            return (
                re.search(
                    r"[\U0001F300-\U0001FAFF\u2600-\u26FF\u2700-\u27BF]",
                    text,
                )
                is not None
            )
        except Exception:
            return False

    def _maybe_prefix_emoji(
        self, title: str, hook: Optional[str], profile: "TopicProfile"
    ) -> tuple[str, Optional[str]]:
        cfg_enabled = (
            getattr(self._poster_cfg, "auto_emoji_title", None)
            if self._poster_cfg is not None
            else None
        )
        enabled = (
            bool(cfg_enabled)
            if cfg_enabled is not None
            else self._env_flag("AUTO_EMOJI_TITLE", "1")
        )
        if not enabled:
            return title, hook

        clean_title = (title or "").strip()
        if not clean_title:
            return title, hook

        # If the title already contains an emoji, do nothing.
        if self._has_emoji(clean_title):
            return clean_title, hook

        # Prefer the inferred topic badge emoji.
        emoji = (getattr(profile, "badge_emoji", None) or "").strip() or "✨"
        return f"{emoji} {clean_title}", hook

    def _add_watermark(self, image: Image.Image, text: str) -> Image.Image:
        if image.mode != "RGBA":
            image = image.convert("RGBA")

        text = (text or "").strip()
        if not text:
            return image

        cfg_opacity = (
            getattr(self._poster_cfg, "watermark_opacity", None)
            if self._poster_cfg is not None
            else None
        )
        try:
            opacity = (
                float(cfg_opacity)
                if cfg_opacity is not None
                else float(
                    (os.getenv("IMAGE_WATERMARK_OPACITY") or "0.33").strip() or 0.33
                )
            )
        except Exception:
            opacity = 0.33
        opacity = min(0.9, max(0.05, opacity))

        cfg_size = (
            getattr(self._poster_cfg, "watermark_font_size", None)
            if self._poster_cfg is not None
            else None
        )
        try:
            font_size = (
                int(cfg_size)
                if cfg_size is not None
                else int((os.getenv("IMAGE_WATERMARK_FONT_SIZE") or "18").strip() or 18)
            )
        except Exception:
            font_size = 18
        font_size = max(10, min(36, font_size))

        processed = self._process_arabic_text(text)
        font = self._get_font(
            "arabic" if self._contains_arabic(text) else "hook", font_size
        )
        overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay, "RGBA")

        try:
            bbox = font.getbbox(processed)
            text_w = int(bbox[2] - bbox[0])
            text_h = int(bbox[3] - bbox[1])
        except Exception:
            text_w = max(10, int(len(text) * (font_size * 0.6)))
            text_h = int(font_size * 1.2)

        pad_x = 14
        pad_y = 8
        margin = 24

        box_w = text_w + pad_x * 2
        box_h = text_h + pad_y * 2

        x1 = image.size[0] - box_w - margin
        y1 = image.size[1] - box_h - margin
        x2 = x1 + box_w
        y2 = y1 + box_h

        # Subtle pill background for readability
        bg_alpha = int(255 * (opacity * 0.55))
        txt_alpha = int(255 * opacity)

        try:
            draw.rounded_rectangle(
                (x1, y1, x2, y2), radius=16, fill=(0, 0, 0, bg_alpha)
            )
        except Exception:
            draw.rectangle((x1, y1, x2, y2), fill=(0, 0, 0, bg_alpha))

        # Slight shadow
        draw.text(
            (x1 + pad_x + 1, y1 + pad_y + 1),
            processed,
            font=font,
            fill=(0, 0, 0, txt_alpha),
        )
        draw.text(
            (x1 + pad_x, y1 + pad_y),
            processed,
            font=font,
            fill=(255, 255, 255, txt_alpha),
        )

        return Image.alpha_composite(image, overlay)

    def _get_key_pool(self, pool_var: str, key_prefix: str) -> List[str]:
        """Return a stable, de-duplicated list of API keys.

        Priority:
        1) Comma-separated list in `pool_var`.
        2) Single base key `{key_prefix}`.
        3) Any env vars starting with `{key_prefix}` (e.g. *_2, *_DEEPSEEK).
        """
        keys: List[str] = []

        raw_pool = (os.getenv(pool_var) or "").strip()
        if raw_pool:
            for part in raw_pool.split(","):
                k = part.strip()
                if k:
                    keys.append(k)

        base = (os.getenv(key_prefix) or "").strip()
        if base:
            keys.append(base)

        # Collect any other keys that share the same prefix
        try:
            for env_k, env_v in os.environ.items():
                if env_k == key_prefix:
                    continue
                if env_k.startswith(key_prefix) and (env_v or "").strip():
                    keys.append(str(env_v).strip())
        except Exception:
            pass

        # De-dup preserve order
        out: List[str] = []
        seen = set()
        for k in keys:
            if not k:
                continue
            if k in seen:
                continue
            seen.add(k)
            out.append(k)
        return out

    def _pick_from_pool(self, keys: List[str], index_attr: str) -> Optional[str]:
        if not keys:
            return None
        try:
            idx = int(getattr(self, index_attr, 0))
        except Exception:
            idx = 0
        key = keys[idx % len(keys)]
        setattr(self, index_attr, (idx + 1) % max(1, len(keys)))
        return key

    def _discover_fonts(self) -> dict:
        """
        Discover available fonts on the system.
        Returns a dictionary of font types to paths.
        """
        # Common font locations
        pil_fonts_dir = os.path.join(os.path.dirname(ImageFont.__file__), "fonts")
        font_dirs = [
            "C:/Windows/Fonts",
            "/usr/share/fonts",
            "/usr/local/share/fonts",
            "/System/Library/Fonts",
            pil_fonts_dir,
            os.path.join(os.path.dirname(__file__), "..", "assets", "fonts"),
        ]

        # Preferred fonts for different purposes
        preferred_fonts = {
            "title": [
                "arialbd.ttf",
                "Arial Bold.ttf",
                "segoeuib.ttf",
                "Roboto-Bold.ttf",
                "DejaVuSans-Bold.ttf",
                "LiberationSans-Bold.ttf",
                "NotoSans-Bold.ttf",
            ],
            "hook": [
                "arial.ttf",
                "Arial.ttf",
                "segoeui.ttf",
                "Roboto-Regular.ttf",
                "DejaVuSans.ttf",
                "LiberationSans-Regular.ttf",
                "NotoSans-Regular.ttf",
            ],
            "arabic": [
                "NotoSansArabic-Bold.ttf",
                "NotoSansArabic-Regular.ttf",
                "NotoNaskhArabic-Regular.ttf",
                "NotoKufiArabic-Regular.ttf",
                "NotoSansArabicUI-Regular.ttf",
                "DejaVuSans.ttf",
                "Tahoma.ttf",
                "segoeui.ttf",
                "arial.ttf",
            ],
            "emoji": [
                # Windows
                "seguiemj.ttf",
                "seguiemoji.ttf",
                "Segoe UI Emoji.ttf",
                # Linux
                "NotoColorEmoji.ttf",
            ],
        }

        found_fonts = {}

        for font_type, font_names in preferred_fonts.items():
            for font_dir in font_dirs:
                if not os.path.exists(font_dir):
                    continue
                for font_name in font_names:
                    font_path = os.path.join(font_dir, font_name)
                    if os.path.exists(font_path):
                        found_fonts[font_type] = font_path
                        break
                if font_type in found_fonts:
                    break

        return found_fonts

    def _get_font(
        self, font_type: str, size: int
    ) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        """
        Get a font object, with fallback to default if not found.
        """

        def try_load(path: str) -> Optional[ImageFont.FreeTypeFont]:
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                return None

        # 1) Discovered fonts by absolute path
        if font_type in self.font_paths:
            f = try_load(self.font_paths[font_type])
            if f is not None:
                return f

        # 2) Pillow bundled DejaVu fonts (reliable cross-platform fallback)
        pil_fonts_dir = os.path.join(os.path.dirname(ImageFont.__file__), "fonts")
        candidate_paths: List[str] = []

        if font_type == "title":
            candidate_paths.append(os.path.join(pil_fonts_dir, "DejaVuSans-Bold.ttf"))
        else:
            candidate_paths.append(os.path.join(pil_fonts_dir, "DejaVuSans.ttf"))

        # 3) Try common system font filenames by name (relies on fontconfig paths)
        if font_type == "arabic":
            candidate_paths += [
                "NotoSansArabic-Regular.ttf",
                "NotoNaskhArabic-Regular.ttf",
                "DejaVuSans.ttf",
            ]
        else:
            candidate_paths += [
                "DejaVuSans.ttf",
                "DejaVuSans-Bold.ttf",
                "LiberationSans-Regular.ttf",
                "LiberationSans-Bold.ttf",
                "arial.ttf",
            ]

        for p in candidate_paths:
            f = try_load(p)
            if f is not None:
                return f

        # Ultimate fallback (small bitmap font)
        return ImageFont.load_default()

    def _get_emoji_font(self, size: int) -> Optional[ImageFont.FreeTypeFont]:
        """Best-effort emoji font (for when pilmoji isn't available)."""
        try:
            if "emoji" in self.font_paths:
                return ImageFont.truetype(self.font_paths["emoji"], size)
        except Exception:
            return None

        # Fallback: try common Windows font filename directly
        try:
            return ImageFont.truetype("seguiemj.ttf", size)
        except Exception:
            return None

    def _iter_text_runs(self, text: str) -> List[Tuple[bool, str]]:
        """Split text into runs: (is_emoji, run_text)."""
        if not text:
            return []

        runs: List[Tuple[bool, str]] = []
        current = [text[0]]
        current_is_emoji = self._has_emoji(text[0])

        for ch in text[1:]:
            ch_is_emoji = self._has_emoji(ch)
            if ch_is_emoji == current_is_emoji:
                current.append(ch)
                continue
            runs.append((current_is_emoji, "".join(current)))
            current = [ch]
            current_is_emoji = ch_is_emoji

        runs.append((current_is_emoji, "".join(current)))
        return runs

    def _analyze_topic(self, title: str, hook: Optional[str] = None) -> TopicProfile:
        """Infer a topic profile (palette/template/badge) from title/hook."""
        text = f"{title} {(hook or '')}".strip().lower()

        buckets: Dict[str, Dict[str, Any]] = {
            "ai": {
                "keys": [
                    "ai",
                    "artificial intelligence",
                    "llm",
                    "gpt",
                    "groq",
                    "machine learning",
                    "deep learning",
                    "ذكاء",
                    "اصطناعي",
                    "تعلم آلي",
                    "نماذج",
                ],
                "palette": ColorPalette.COSMIC_NIGHT,
                "badge": ("AI", "🤖"),
                "gradient": "radial",
                "template": ImageTemplate.HERO_CARD,
            },
            "security": {
                "keys": [
                    "security",
                    "vulnerability",
                    "breach",
                    "malware",
                    "ransomware",
                    "zero day",
                    "cyber",
                    "أمان",
                    "اختراق",
                    "ثغرة",
                    "هجمات",
                ],
                "palette": ColorPalette.ROYAL_GOLD,
                "badge": ("SEC", "🛡️"),
                "gradient": "vertical",
                "template": ImageTemplate.MINIMAL_BOLD,
            },
            "cloud": {
                "keys": [
                    "cloud",
                    "aws",
                    "azure",
                    "gcp",
                    "kubernetes",
                    "docker",
                    "سحابة",
                    "كلاود",
                    "حاويات",
                ],
                "palette": ColorPalette.TECH_BLUE,
                "badge": ("CLOUD", "☁️"),
                "gradient": "diagonal",
                "template": ImageTemplate.SPLIT_HERO,
            },
            "dev": {
                "keys": [
                    "python",
                    "javascript",
                    "typescript",
                    "react",
                    "node",
                    "api",
                    "database",
                    "sql",
                    "برمجة",
                    "كود",
                    "بايثون",
                    "جافاسكريبت",
                    "تطوير",
                ],
                "palette": ColorPalette.CYBER_PUNK,
                "badge": ("DEV", "💻"),
                "gradient": "diagonal",
                "template": ImageTemplate.SPLIT_HERO,
            },
            "business": {
                "keys": [
                    "business",
                    "startup",
                    "growth",
                    "marketing",
                    "strategy",
                    "أعمال",
                    "بيزنس",
                    "ريادة",
                    "تسويق",
                    "استراتيجية",
                ],
                "palette": ColorPalette.SUNSET_GLOW,
                "badge": ("BIZ", "📈"),
                "gradient": "horizontal",
                "template": ImageTemplate.HERO_CARD,
            },
        }

        matched = None
        for name, spec in buckets.items():
            keys: List[str] = list(spec.get("keys") or [])
            if any(k in text for k in keys):
                matched = name
                break

        if matched is None:
            return TopicProfile(
                palette=ColorPalette.TECH_BLUE,
                gradient_type="diagonal",
                template=ImageTemplate.HERO_CARD,
                badge_text="TECH",
                badge_emoji="✨",
            )

        spec = buckets[matched]
        badge = spec.get("badge") or (None, None)
        badge_text, badge_emoji = badge
        return TopicProfile(
            palette=spec["palette"],  # type: ignore[index]
            gradient_type=str(spec.get("gradient") or "diagonal"),
            template=spec["template"],  # type: ignore[index]
            badge_text=str(badge_text) if badge_text else None,
            badge_emoji=str(badge_emoji) if badge_emoji else None,
        )

    def _measure_text_width(
        self, text: str, font: ImageFont.FreeTypeFont | ImageFont.ImageFont
    ) -> int:
        try:
            bbox = font.getbbox(text)
            return int(bbox[2] - bbox[0])
        except Exception:
            return int(len(text) * (getattr(font, "size", 16) * 0.6))

    def _fit_font_and_wrap(
        self,
        text: str,
        font_type: str,
        start_size: int,
        min_size: int,
        max_width: int,
        max_lines: int,
    ) -> tuple[ImageFont.FreeTypeFont | ImageFont.ImageFont, List[str]]:
        text = re.sub(r"\s+", " ", (text or "").strip())
        if not text:
            return self._get_font(font_type, start_size), []

        # Choose an Arabic-capable font when needed.
        effective_font_type = "arabic" if self._contains_arabic(text) else font_type

        size = start_size
        while size >= min_size:
            font = self._get_font(effective_font_type, size)
            lines = self._wrap_text(text, font, max_width)
            if len(lines) <= max_lines:
                return font, lines
            size -= 4

        font = self._get_font(effective_font_type, min_size)
        lines = self._wrap_text(text, font, max_width)
        return font, lines[:max_lines]

    def _rounded_rect(
        self,
        draw: ImageDraw.ImageDraw,
        xy: Tuple[int, int, int, int],
        radius: int,
        fill: Tuple[int, int, int, int],
        outline: Optional[Tuple[int, int, int, int]] = None,
        width: int = 2,
    ):
        try:
            draw.rounded_rectangle(
                xy, radius=radius, fill=fill, outline=outline, width=width
            )
        except Exception:
            draw.rectangle(xy, fill=fill, outline=outline, width=width)

    def _add_glass_card(
        self,
        image: Image.Image,
        box: Tuple[int, int, int, int],
        accent_color: Tuple[int, int, int],
    ) -> Image.Image:
        if image.mode != "RGBA":
            image = image.convert("RGBA")

        x1, y1, x2, y2 = box
        region = image.crop((x1, y1, x2, y2))
        # Disabled blur to keep background clear
        # region = region.filter(
        #    ImageFilter.GaussianBlur(radius=self.config.card_blur_radius)
        # )
        image.paste(region, (x1, y1))

        overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay, "RGBA")
        panel_fill = (0, 0, 0, int(self.config.card_opacity))
        panel_outline = (*accent_color, 120)
        self._rounded_rect(
            od,
            (x1, y1, x2, y2),
            radius=self.config.card_radius,
            fill=panel_fill,
            outline=panel_outline,
            width=2,
        )
        return Image.alpha_composite(image, overlay)

    def _draw_badge(
        self,
        image: Image.Image,
        text: str,
        emoji: Optional[str],
        x: int,
        y: int,
        accent_color: Tuple[int, int, int],
    ) -> Image.Image:
        if image.mode != "RGBA":
            image = image.convert("RGBA")
        draw = ImageDraw.Draw(image, "RGBA")

        badge_font = self._get_font("hook", 26)
        badge_text = f"{(emoji + ' ') if emoji else ''}{text}".strip()
        w = self._measure_text_width(self._process_arabic_text(badge_text), badge_font)
        h = 34
        pad_x = 16
        pad_y = 8
        box = (x, y, x + w + pad_x * 2, y + h + pad_y * 2)
        self._rounded_rect(
            draw,
            box,
            radius=18,
            fill=(*accent_color, 90),
            outline=(255, 255, 255, 120),
            width=1,
        )
        return self._render_text_with_emoji(
            image,
            badge_text,
            (x + pad_x, y + pad_y),
            badge_font,
            color=(255, 255, 255),
            shadow=False,
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # 🌈 GRADIENT GENERATION - The foundation of our backgrounds
    # ═══════════════════════════════════════════════════════════════════════════

    def _create_gradient(
        self,
        size: Tuple[int, int],
        colors: List[Tuple[int, int, int]],
        gradient_type: str = "diagonal",
    ) -> Image.Image:
        """
        Generate a beautiful gradient background.

        This is where the magic begins! We create smooth color transitions
        that form the foundation of our design.

        Args:
            size: (width, height) of the image
            colors: List of RGB color tuples
            gradient_type: 'diagonal', 'horizontal', 'vertical', 'radial'

        Returns:
            PIL Image with gradient
        """
        width, height = size
        image = Image.new("RGB", size)
        pixels = image.load()
        if pixels is None:
            return image

        # Ensure we have at least 2 colors
        if len(colors) < 2:
            colors = colors + [(0, 0, 0)]

        c1, c2 = colors[0], colors[1]
        c3 = colors[2] if len(colors) > 2 else c2

        for y in range(height):
            for x in range(width):
                if gradient_type == "diagonal":
                    # Diagonal gradient from top-left to bottom-right
                    # with a twist of the third color
                    ratio = (x + y) / (width + height)

                elif gradient_type == "horizontal":
                    ratio = x / width

                elif gradient_type == "vertical":
                    ratio = y / height

                elif gradient_type == "radial":
                    # Radial gradient from center
                    cx, cy = width / 2, height / 2
                    max_dist = math.sqrt(cx**2 + cy**2)
                    dist = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
                    ratio = dist / max_dist

                else:
                    ratio = (x + y) / (width + height)

                # Smooth interpolation with easing
                ratio = self._ease_in_out(ratio)

                # Three-color gradient magic
                if ratio < 0.5:
                    sub_ratio = ratio * 2
                    r = int(c1[0] + (c2[0] - c1[0]) * sub_ratio)
                    g = int(c1[1] + (c2[1] - c1[1]) * sub_ratio)
                    b = int(c1[2] + (c2[2] - c1[2]) * sub_ratio)
                else:
                    sub_ratio = (ratio - 0.5) * 2
                    r = int(c2[0] + (c3[0] - c2[0]) * sub_ratio)
                    g = int(c2[1] + (c3[1] - c2[1]) * sub_ratio)
                    b = int(c2[2] + (c3[2] - c2[2]) * sub_ratio)

                pixels[x, y] = (r, g, b)

        return image

    def _ease_in_out(self, t: float) -> float:
        """
        Smooth easing function for gradient transitions.
        Creates a more pleasing visual flow.
        """
        return t * t * (3 - 2 * t)

    # ═══════════════════════════════════════════════════════════════════════════
    # 🔷 GEOMETRIC ART ELEMENTS - Adding depth and visual interest
    # ═══════════════════════════════════════════════════════════════════════════

    def _add_geometric_elements(
        self, image: Image.Image, accent_color: Tuple[int, int, int]
    ) -> Image.Image:
        """
        Add subtle geometric decorations to the image.

        These elements add depth and visual interest without
        overwhelming the main content. Think of them as the
        "seasoning" of our design dish.

        Elements include:
        - Floating circles with varying opacity
        - Scattered dots creating a starfield effect
        - Diagonal lines adding dynamism
        - Corner decorations for framing
        """
        draw = ImageDraw.Draw(image, "RGBA")
        width, height = image.size

        # ═══════════════════════════════════════════════════════════════════
        # 🔵 FLOATING CIRCLES - Like bubbles rising through the design
        # ═══════════════════════════════════════════════════════════════════
        for _ in range(self.config.num_circles):
            # Random position, biased towards corners
            if random.random() > 0.5:
                x = (
                    random.randint(0, width // 4)
                    if random.random() > 0.5
                    else random.randint(3 * width // 4, width)
                )
                y = (
                    random.randint(0, height // 3)
                    if random.random() > 0.5
                    else random.randint(2 * height // 3, height)
                )
            else:
                x = random.randint(0, width)
                y = random.randint(0, height)

            radius = random.randint(20, 120)
            opacity = random.randint(10, 40)

            # Create a glowing circle effect
            color_with_alpha = (*accent_color, opacity)
            draw.ellipse(
                [x - radius, y - radius, x + radius, y + radius],
                fill=color_with_alpha,
                outline=None,
            )

        # ═══════════════════════════════════════════════════════════════════
        # ✨ SCATTERED DOTS - Creating a cosmic/particle effect
        # ═══════════════════════════════════════════════════════════════════
        for _ in range(self.config.num_dots):
            x = random.randint(0, width)
            y = random.randint(0, height)
            size = random.randint(1, 4)
            opacity = random.randint(30, 100)

            color_with_alpha = (255, 255, 255, opacity)
            draw.ellipse(
                [x - size, y - size, x + size, y + size], fill=color_with_alpha
            )

        # ═══════════════════════════════════════════════════════════════════
        # 📐 DIAGONAL LINES - Adding movement and energy
        # ═══════════════════════════════════════════════════════════════════
        for i in range(self.config.num_lines):
            # Lines emanating from corners
            if i % 2 == 0:
                start_x = random.randint(-50, width // 4)
                start_y = random.randint(-50, height // 4)
            else:
                start_x = random.randint(3 * width // 4, width + 50)
                start_y = random.randint(3 * height // 4, height + 50)

            length = random.randint(100, 300)
            angle = random.uniform(0, math.pi * 2)
            end_x = start_x + int(length * math.cos(angle))
            end_y = start_y + int(length * math.sin(angle))

            opacity = random.randint(15, 35)
            line_width = random.randint(1, 3)

            color_with_alpha = (*accent_color, opacity)
            draw.line(
                [(start_x, start_y), (end_x, end_y)],
                fill=color_with_alpha,
                width=line_width,
            )

        # ═══════════════════════════════════════════════════════════════════
        # 🔲 CORNER DECORATIONS - Professional framing
        # ═══════════════════════════════════════════════════════════════════
        corner_size = 80
        corner_opacity = 30
        corner_color = (*accent_color, corner_opacity)

        # Top-left corner bracket
        draw.line([(20, 20), (20, 20 + corner_size)], fill=corner_color, width=3)
        draw.line([(20, 20), (20 + corner_size, 20)], fill=corner_color, width=3)

        # Top-right corner bracket
        draw.line(
            [(width - 20, 20), (width - 20, 20 + corner_size)],
            fill=corner_color,
            width=3,
        )
        draw.line(
            [(width - 20, 20), (width - 20 - corner_size, 20)],
            fill=corner_color,
            width=3,
        )

        # Bottom-left corner bracket
        draw.line(
            [(20, height - 20), (20, height - 20 - corner_size)],
            fill=corner_color,
            width=3,
        )
        draw.line(
            [(20, height - 20), (20 + corner_size, height - 20)],
            fill=corner_color,
            width=3,
        )

        # Bottom-right corner bracket
        draw.line(
            [(width - 20, height - 20), (width - 20, height - 20 - corner_size)],
            fill=corner_color,
            width=3,
        )
        draw.line(
            [(width - 20, height - 20), (width - 20 - corner_size, height - 20)],
            fill=corner_color,
            width=3,
        )

        return image

    def _add_overlay(self, image: Image.Image) -> Image.Image:
        """
        Add a semi-transparent dark overlay.

        This creates contrast for text readability while
        maintaining the beautiful gradient background.
        It's like adding a gentle shadow layer.
        """
        overlay = Image.new(
            "RGBA", image.size, (0, 0, 0, int(255 * self.config.overlay_opacity))
        )

        # Convert image to RGBA if needed
        if image.mode != "RGBA":
            image = image.convert("RGBA")

        # Composite the overlay
        image = Image.alpha_composite(image, overlay)

        return image

    def _add_border(
        self, image: Image.Image, accent_color: Tuple[int, int, int]
    ) -> Image.Image:
        """
        Add a professional border with optional glow effect.

        The border frames our content and adds a polished,
        finished look to the design.
        """
        draw = ImageDraw.Draw(image, "RGBA")
        width, height = image.size

        border_width = self.config.border_width

        if self.config.border_glow:
            # Glow effect - multiple layers with decreasing opacity
            for i in range(4):
                glow_width = border_width + (4 - i) * 2
                opacity = 20 + i * 20
                color = (*accent_color, opacity)

                draw.rectangle(
                    [
                        glow_width,
                        glow_width,
                        width - glow_width - 1,
                        height - glow_width - 1,
                    ],
                    outline=color,
                    width=2,
                )

        # Main border
        border_color = (*accent_color, 180)
        draw.rectangle(
            [
                border_width,
                border_width,
                width - border_width - 1,
                height - border_width - 1,
            ],
            outline=border_color,
            width=border_width,
        )

        return image

    # ═══════════════════════════════════════════════════════════════════════════
    # 📝 TEXT RENDERING - The star of the show
    # ═══════════════════════════════════════════════════════════════════════════

    def _contains_arabic(self, text: str) -> bool:
        """
        Check if text contains Arabic characters.
        Arabic Unicode range: 0x0600-0x06FF
        """
        for char in text:
            if "\u0600" <= char <= "\u06ff" or "\u0750" <= char <= "\u077f":
                return True
        return False

    def _process_arabic_text(self, text: str) -> str:
        """
        Process Arabic text for correct rendering.

        This fixes two issues:
        1. Letter shaping (disconnected -> connected letters)
        2. RTL direction (right-to-left display)
        """
        if not ARABIC_SUPPORT:
            return text

        if not self._contains_arabic(text):
            return text

        try:
            # Step 1: Reshape Arabic letters to connect properly
            reshaped_text = arabic_reshaper.reshape(text)
            # Step 2: Apply bidirectional algorithm for RTL
            bidi_text = get_display(reshaped_text)
            return str(bidi_text)
        except Exception as e:
            logger.warning(f"Arabic processing failed: {e}")
            return text

    def _wrap_text(
        self,
        text: str,
        font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
        max_width: int,
    ) -> List[str]:
        """
        Intelligently wrap text to fit within a maximum width.

        This ensures long titles don't get cut off and
        look professional across all content lengths.
        """
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            current_line.append(word)
            test_line = " ".join(current_line)

            display_line = self._process_arabic_text(test_line)

            # Get text width
            try:
                bbox = font.getbbox(display_line)
                text_width = bbox[2] - bbox[0]
            except Exception:
                text_width = int(len(test_line) * (getattr(font, "size", 16) * 0.6))

            if text_width > max_width:
                # Line is too long, move last word to new line
                if len(current_line) > 1:
                    current_line.pop()
                    lines.append(" ".join(current_line))
                    current_line = [word]
                else:
                    # Single word is too long, keep it anyway
                    lines.append(test_line)
                    current_line = []

        # Don't forget the last line
        if current_line:
            lines.append(" ".join(current_line))

        return lines

    def _render_text_with_emoji(
        self,
        image: Image.Image,
        text: str,
        position: Tuple[int, int],
        font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
        color: Tuple[int, int, int] = (255, 255, 255),
        shadow: bool = True,
        outline_width: Optional[int] = None,
        shadow_offset: Optional[int] = None,
    ) -> Image.Image:
        """
        Render text with full emoji and Arabic support.

        For Arabic text:
        1. Reshapes disconnected letters to connected form
        2. Applies RTL bidirectional algorithm

        This uses pilmoji when available to properly render
        colorful emojis alongside regular text.
        """
        x, y = position

        # 🔤 Process Arabic text for correct rendering
        processed_text = self._process_arabic_text(text)

        draw = ImageDraw.Draw(image, "RGBA")
        emoji_font = (
            None
            if PILMOJI_AVAILABLE
            else self._get_emoji_font(getattr(font, "size", 24))
        )

        def _normalize_fill(fill: Tuple[int, int, int] | Tuple[int, int, int, int]):
            if len(fill) == 4:
                return fill
            return (fill[0], fill[1], fill[2], 255)

        def draw_runs(
            at_x: int, at_y: int, fill: Tuple[int, int, int] | Tuple[int, int, int, int]
        ):
            fill_rgba = _normalize_fill(fill)
            if PILMOJI_AVAILABLE:
                with Pilmoji(image) as pilmoji:
                    pilmoji.text(
                        (at_x, at_y), processed_text, font=font, fill=fill_rgba
                    )
                return

            # If no emoji font (or no emoji), draw normally.
            if emoji_font is None or not self._has_emoji(processed_text):
                draw.text((at_x, at_y), processed_text, font=font, fill=fill_rgba)
                return

            # Mixed rendering: base font for text, emoji font for emoji chars.
            cx = at_x
            for is_emoji, run_text in self._iter_text_runs(processed_text):
                run_font = emoji_font if is_emoji else font
                draw.text((cx, at_y), run_text, font=run_font, fill=fill_rgba)

                try:
                    bbox = run_font.getbbox(run_text)
                    run_w = int(bbox[2] - bbox[0])
                except Exception:
                    run_w = int(len(run_text) * (getattr(run_font, "size", 16) * 0.6))
                cx += run_w

        ow = outline_width
        if ow is None:
            ow = int(getattr(self.config, "text_outline_width", 0) or 0)
        ow = max(0, ow)

        so = shadow_offset
        if so is None:
            so = int(getattr(self.config, "text_shadow_offset", 0) or 0)
        so = max(0, so)

        outline_alpha = int(getattr(self.config, "text_outline_alpha", 220) or 220)
        shadow_alpha = int(getattr(self.config, "text_shadow_alpha", 220) or 220)

        if ow > 0:
            outline_fill = (0, 0, 0, outline_alpha)
            for dx in range(-ow, ow + 1):
                for dy in range(-ow, ow + 1):
                    if dx == 0 and dy == 0:
                        continue
                    if max(abs(dx), abs(dy)) != ow:
                        continue
                    draw_runs(x + dx, y + dy, outline_fill)

        shadow_enabled = shadow and bool(getattr(self.config, "text_shadow", True))
        if shadow_enabled and so > 0:
            draw_runs(x + so, y + so, (0, 0, 0, shadow_alpha))

        draw_runs(x, y, color)

        return image

    # ═══════════════════════════════════════════════════════════════════════════
    # 🖼️ MAIN GENERATION METHOD - Bringing it all together
    # ═══════════════════════════════════════════════════════════════════════════

    def generate(
        self,
        title: str,
        hook: Optional[str] = None,
        palette: Optional[ColorPalette] = None,
        gradient_type: Optional[str] = None,
        template: Optional[ImageTemplate] = None,
        background_override: Optional[Image.Image] = None,
    ) -> Image.Image:
        """
        Generate a professional social media image.

        This is the main composition method that orchestrates
        all the artistic elements into a cohesive design.

        Args:
            title: Main headline text (can include emojis)
            hook: Optional subtitle/hook text
            palette: Color palette to use (random if not specified)
            gradient_type: Type of gradient ('diagonal', 'horizontal', 'vertical', 'radial')

        Returns:
            PIL Image object (1200x630 OG format)
        """
        logger.info(f"🎨 Generating image for: {title[:50]}...")

        profile = self._analyze_topic(title, hook)
        title, hook = self._maybe_prefix_emoji(title=title, hook=hook, profile=profile)

        # Used both for background selection and for picking default palette behavior.
        use_local_bg = background_override is None and self._env_flag(
            "LOCAL_BACKGROUNDS_ENABLED", "1"
        )

        if palette is None:
            palette = self._choose_palette(profile, use_local_bg=use_local_bg)
        if gradient_type is None:
            gradient_type = profile.gradient_type

        colors = palette.value
        accent_color = colors[-1]

        if gradient_type:
            self.config.gradient_type = gradient_type

        if template is None:
            template = profile.template
        size = (self.config.width, self.config.height)

        if background_override is not None:
            image = background_override.convert("RGBA")
            if image.size != size:
                image = image.resize(size, Image.Resampling.LANCZOS)
        else:
            ai_bg: Optional[Image.Image] = None
            if self._env_flag("ENABLE_IMAGE_AI", "0"):
                provider = (
                    (os.getenv("IMAGE_AI_PROVIDER", "pollinations") or "pollinations")
                    .strip()
                    .lower()
                )
                if provider not in ("pollinations", "auto", "none"):
                    provider = "pollinations"
                if provider in ("pollinations", "auto"):
                    prompt = self._build_ai_image_prompt(title=title, hook=hook)
                    ai_bg = self._pollinations_generate_background(prompt, size=size)

            if ai_bg is not None:
                image = ai_bg.convert("RGBA")
                if image.size != size:
                    image = image.resize(size, Image.Resampling.LANCZOS)
            else:
                local_bg = None
                if use_local_bg:
                    local_bg = self._load_local_background(
                        profile=profile, title=title, hook=hook, size=size
                    )
                if local_bg is not None:
                    image = local_bg
                else:
                    image = self._create_gradient(
                        size, colors, self.config.gradient_type
                    ).convert("RGBA")
                    image = self._add_geometric_elements(image, accent_color)

        # Contrast helpers (keep on even for AI backgrounds)
        image = self._add_overlay(image)
        image = self._add_border(image, accent_color)

        draw = ImageDraw.Draw(image, "RGBA")

        margin = 70

        def center_line_x(
            line: str,
            font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
            x1: int,
            x2: int,
        ):
            processed = self._process_arabic_text(line)
            w = self._measure_text_width(processed, font)
            align = (
                (getattr(self.config, "text_align", "center") or "center")
                .strip()
                .lower()
            )
            if align == "right":
                return x2 - w
            return x1 + ((x2 - x1) - w) // 2

        if template == ImageTemplate.SPLIT_HERO:
            split_x = int(self.config.width * 0.62)
            card_box = (margin, 90, split_x, self.config.height - 90)
            image = self._add_glass_card(image, card_box, accent_color)

            # Big accent circle on the right for visual balance
            circle_overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
            cd = ImageDraw.Draw(circle_overlay, "RGBA")
            r = int(self.config.height * 0.62)
            cx = int(self.config.width * 0.80)
            cy = int(self.config.height * 0.52)
            cd.ellipse(
                (cx - r, cy - r, cx + r, cy + r),
                fill=(*accent_color, 55),
                outline=(255, 255, 255, 40),
                width=3,
            )
            image = Image.alpha_composite(image, circle_overlay)

            card_x1, card_y1, card_x2, card_y2 = card_box
            if profile.badge_text:
                image = self._draw_badge(
                    image,
                    profile.badge_text,
                    profile.badge_emoji,
                    x=card_x1 + 28,
                    y=card_y1 + 24,
                    accent_color=accent_color,
                )

            content_x1 = card_x1 + 40
            content_x2 = card_x2 - 40
            content_width = content_x2 - content_x1
            title_font, title_lines = self._fit_font_and_wrap(
                title,
                font_type="title",
                start_size=self.config.title_font_size,
                min_size=self.config.min_title_font_size,
                max_width=content_width,
                max_lines=self.config.max_title_lines,
            )
            hook_font, hook_lines = self._fit_font_and_wrap(
                hook or "",
                font_type="hook",
                start_size=self.config.hook_font_size,
                min_size=self.config.min_hook_font_size,
                max_width=content_width,
                max_lines=self.config.max_hook_lines,
            )

            title_line_h = (
                int(getattr(title_font, "size", self.config.title_font_size)) + 14
            )
            hook_line_h = (
                int(getattr(hook_font, "size", self.config.hook_font_size)) + 10
            )

            block_h = (len(title_lines) * title_line_h) + (
                (22 + len(hook_lines) * hook_line_h) if hook_lines else 0
            )
            start_y = card_y1 + (card_y2 - card_y1 - block_h) // 2
            y = start_y

            for line in title_lines:
                x = center_line_x(line, title_font, content_x1, content_x2)
                image = self._render_text_with_emoji(
                    image,
                    line,
                    (x, y),
                    title_font,
                    color=(255, 255, 255),
                    shadow=True,
                )
                y += title_line_h

            if hook_lines:
                # Divider
                y += 6
                draw = ImageDraw.Draw(image, "RGBA")
                draw.line(
                    [(content_x1, y), (content_x2, y)],
                    fill=(*accent_color, 140),
                    width=4,
                )
                y += 18
                for line in hook_lines:
                    x = center_line_x(line, hook_font, content_x1, content_x2)
                    image = self._render_text_with_emoji(
                        image,
                        line,
                        (x, y),
                        hook_font,
                        color=accent_color,
                        shadow=True,
                    )
                    y += hook_line_h

        elif template == ImageTemplate.MINIMAL_BOLD:
            if profile.badge_text:
                image = self._draw_badge(
                    image,
                    profile.badge_text,
                    profile.badge_emoji,
                    x=margin,
                    y=60,
                    accent_color=accent_color,
                )

            content_x1 = margin
            content_x2 = self.config.width - margin
            content_width = content_x2 - content_x1

            title_font, title_lines = self._fit_font_and_wrap(
                title,
                font_type="title",
                start_size=self.config.title_font_size,
                min_size=self.config.min_title_font_size,
                max_width=content_width,
                max_lines=self.config.max_title_lines,
            )
            hook_font, hook_lines = self._fit_font_and_wrap(
                hook or "",
                font_type="hook",
                start_size=self.config.hook_font_size,
                min_size=self.config.min_hook_font_size,
                max_width=content_width,
                max_lines=self.config.max_hook_lines,
            )

            title_line_h = (
                int(getattr(title_font, "size", self.config.title_font_size)) + 16
            )
            hook_line_h = (
                int(getattr(hook_font, "size", self.config.hook_font_size)) + 10
            )
            block_h = (len(title_lines) * title_line_h) + (
                (26 + len(hook_lines) * hook_line_h) if hook_lines else 0
            )

            y = (self.config.height - block_h) // 2
            for line in title_lines:
                x = center_line_x(line, title_font, content_x1, content_x2)
                image = self._render_text_with_emoji(
                    image,
                    line,
                    (x, y),
                    title_font,
                    color=(255, 255, 255),
                    shadow=True,
                )
                y += title_line_h

            # Accent underline
            y += 4
            underline_w = int(content_width * 0.45)
            ux1 = (self.config.width - underline_w) // 2
            draw = ImageDraw.Draw(image, "RGBA")
            draw.line(
                [(ux1, y), (ux1 + underline_w, y)],
                fill=(*accent_color, 190),
                width=6,
            )
            y += 22

            for line in hook_lines:
                x = center_line_x(line, hook_font, content_x1, content_x2)
                image = self._render_text_with_emoji(
                    image,
                    line,
                    (x, y),
                    hook_font,
                    color=accent_color,
                    shadow=True,
                )
                y += hook_line_h

        else:
            # Default HERO_CARD
            # Smaller box to show more background
            card_box = (
                margin + 60,
                140,  # Moved higher up to give more vertical space
                self.config.width - (margin + 60),
                self.config.height - 140,  # Taller box overall (less bottom margin)
            )
            image = self._add_glass_card(image, card_box, accent_color)

            card_x1, card_y1, card_x2, card_y2 = card_box
            if profile.badge_text:
                image = self._draw_badge(
                    image,
                    profile.badge_text,
                    profile.badge_emoji,
                    x=card_x1 + 30,
                    y=card_y1 + 26, # Keep badge relative to top
                    accent_color=accent_color,
                )

            # Reduce internal padding to use more space within the smaller box
            content_x1 = card_x1 + 20
            content_x2 = card_x2 - 20
            content_width = content_x2 - content_x1

            title_font, title_lines = self._fit_font_and_wrap(
                title,
                font_type="title",
                start_size=self.config.title_font_size,
                min_size=self.config.min_title_font_size,
                max_width=content_width,
                max_lines=self.config.max_title_lines,
            )
            hook_font, hook_lines = self._fit_font_and_wrap(
                hook or "",
                font_type="hook",
                start_size=self.config.hook_font_size,
                min_size=self.config.min_hook_font_size,
                max_width=content_width,
                max_lines=self.config.max_hook_lines,
            )

            title_line_h = (
                int(getattr(title_font, "size", self.config.title_font_size)) + 14
            )
            hook_line_h = (
                int(getattr(hook_font, "size", self.config.hook_font_size)) + 10
            )

            block_h = (len(title_lines) * title_line_h) + (
                (22 + len(hook_lines) * hook_line_h) if hook_lines else 0
            )
            y = card_y1 + (card_y2 - card_y1 - block_h) // 2

            for line in title_lines:
                x = center_line_x(line, title_font, content_x1, content_x2)
                image = self._render_text_with_emoji(
                    image,
                    line,
                    (x, y),
                    title_font,
                    color=(255, 255, 255),
                    shadow=True,
                )
                y += title_line_h

            if hook_lines:
                y += 6
                draw = ImageDraw.Draw(image, "RGBA")
                draw.line(
                    [(content_x1, y), (content_x2, y)],
                    fill=(*accent_color, 140),
                    width=4,
                )
                y += 18

                for line in hook_lines:
                    x = center_line_x(line, hook_font, content_x1, content_x2)
                    image = self._render_text_with_emoji(
                        image,
                        line,
                        (x, y),
                        hook_font,
                        color=accent_color,
                        shadow=True,
                    )
                    y += hook_line_h

        # ═══════════════════════════════════════════════════════════════════
        # LAYER 7: Branding (Optional watermark)
        # ═══════════════════════════════════════════════════════════════════
        cfg_watermark_text = (
            (
                getattr(self._poster_cfg, "watermark_text", "")
                if self._poster_cfg is not None
                else ""
            )
            or ""
        ).strip()

        env_watermark_text = (os.getenv("IMAGE_WATERMARK_TEXT") or "").strip()
        env_watermark_enabled = self._env_flag("IMAGE_WATERMARK_ENABLED", "0")

        watermark_enabled = bool(cfg_watermark_text) or (
            env_watermark_enabled and bool(env_watermark_text)
        )
        if watermark_enabled:
            watermark_text = (
                cfg_watermark_text if cfg_watermark_text else env_watermark_text
            )
            if watermark_text:
                image = self._add_watermark(image, watermark_text)

        # Convert back to RGB for saving
        final_image = Image.new("RGB", image.size, (0, 0, 0))
        final_image.paste(
            image, mask=image.split()[-1] if image.mode == "RGBA" else None
        )

        logger.info("✅ Image generated successfully!")
        return final_image

    # ═══════════════════════════════════════════════════════════════════════════
    # ☁️ UPLOAD TO IMGBB - Getting our art online
    # ═══════════════════════════════════════════════════════════════════════════

    def upload_to_imgbb(self, image: Image.Image) -> Optional[str]:
        """
        Upload the generated image to ImgBB.

        Args:
            image: PIL Image to upload

        Returns:
            Direct URL of the uploaded image, or None if failed
        """
        logger.info("☁️ Uploading image to ImgBB...")

        try:
            # Convert image to base64
            buffer = io.BytesIO()
            image.save(buffer, format="PNG", quality=95)
            buffer.seek(0)

            base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

            # Upload to ImgBB
            response = requests.post(
                "https://api.imgbb.com/1/upload",
                data={
                    "key": self.imgbb_api_key,
                    "image": base64_image,
                    "name": f"contentorbit_{random.randint(1000, 9999)}",
                },
                timeout=30,
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    url = result["data"]["url"]
                    logger.info(f"✅ Image uploaded: {url}")
                    return url
                else:
                    logger.error(f"❌ ImgBB error: {result}")
                    return None
            else:
                logger.error(f"❌ ImgBB HTTP error: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"❌ Upload failed: {e}")
            return None

    def generate_and_upload(
        self,
        title: str,
        hook: Optional[str] = None,
        palette: Optional[ColorPalette] = None,
    ) -> Optional[str]:
        """
        Generate an image and upload it to ImgBB.

        This is the main entry point for the complete workflow.

        Args:
            title: Main headline text
            hook: Optional subtitle text
            palette: Color palette to use

        Returns:
            URL of the uploaded image, or None if failed
        """
        image = self.generate(title, hook, palette)
        return self.upload_to_imgbb(image)

    def generate_variants(
        self,
        title: str,
        hook: Optional[str] = None,
        count: int = 3,
        palettes: Optional[List[ColorPalette]] = None,
    ) -> List[Image.Image]:
        """Generate multiple design variants for the same post."""
        count = max(1, min(int(count), 6))
        profile = self._analyze_topic(title, hook)

        templates = [
            profile.template,
            ImageTemplate.HERO_CARD,
            ImageTemplate.MINIMAL_BOLD,
        ]
        gradients = [profile.gradient_type, "diagonal", "radial", "vertical"]

        if palettes is None:
            palettes = [
                profile.palette,
                ColorPalette.COSMIC_NIGHT,
                ColorPalette.SUNSET_GLOW,
            ]

        images: List[Image.Image] = []
        for i in range(count):
            template = templates[i % len(templates)]
            gradient = gradients[i % len(gradients)]
            palette = palettes[i % len(palettes)]

            images.append(
                self.generate(
                    title=title,
                    hook=hook,
                    palette=palette,
                    gradient_type=gradient,
                    template=template,
                )
            )

        # Keep list bounded (caller may request up to 6)
        return images[: max(1, min(count, 6))]

    def _build_ai_image_prompt(self, title: str, hook: Optional[str]) -> str:
        """Create a prompt for image generation.

        Order:
        1) Groq (if enabled + keys available)
        2) Gemini (Google AI Studio) as a free-ish fallback (text only)
        3) Heuristic fallback prompt
        """
        base = {
            "title": (title or "").strip(),
            "hook": (hook or "").strip(),
        }

        # Heuristic fallback prompt (English tends to work best for image models)
        fallback = (
            "Create a high-quality cinematic illustration background for a tech social post. "
            "No text, no letters, no watermark, no logo. "
            "Modern, clean, high contrast, professional. "
            f"Theme: {base['title']}. "
        )
        if base["hook"]:
            fallback += f"Context: {base['hook']}. "

        disable_groq = os.getenv(
            "DISABLE_GROQ_FOR_IMAGE_PROMPT", "0"
        ).strip().lower() in (
            "1",
            "true",
            "yes",
        )

        sys = (
            "You write short, high-quality prompts for image generation. "
            "Output ONLY the prompt. No quotes. No markdown. "
            "Rules: no text/letters/logos/watermarks in the image. "
            "Prefer cinematic lighting and modern tech aesthetics."
        )
        user = (
            f"Title: {base['title']}\n"
            f"Hook: {base['hook']}\n\n"
            "Write ONE concise prompt (max 60 words) for a background illustration."
        )

        # 1) Groq prompt-writing (pool-aware)
        if not disable_groq:
            groq_keys = self._get_key_pool("GROQ_API_KEYS", "GROQ_API_KEY")
            model = (
                (os.getenv("GROQ_MODEL_IMAGE_PROMPT") or "").strip()
                or (os.getenv("GROQ_IMAGE_PROMPT_MODEL") or "").strip()
                or "llama-3.1-8b-instant"
            )

            url = "https://api.groq.com/openai/v1/chat/completions"
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": sys},
                    {"role": "user", "content": user},
                ],
                "temperature": 0.7,
                "max_tokens": 160,
            }

            # Try each key once (smart fallback when credits/rate-limit hit)
            for _ in range(max(1, len(groq_keys))):
                groq_key = self._pick_from_pool(groq_keys, "_groq_key_index")
                if not groq_key:
                    break
                try:
                    headers = {
                        "Authorization": f"Bearer {groq_key}",
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    }
                    r = requests.post(url, headers=headers, json=payload, timeout=20)
                    if r.status_code in (401, 403, 429):
                        continue
                    r.raise_for_status()
                    data = r.json()
                    content = (
                        data.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", "")
                        .strip()
                    )
                    if content:
                        return content.strip().strip('"').strip("'")
                except Exception:
                    continue

        # 2) Gemini fallback (Google AI Studio) - prompt-writing only
        gemini_prompt = self._gemini_prompt(sys_prompt=sys, user_prompt=user)
        if gemini_prompt:
            return gemini_prompt

        return fallback

    def _gemini_prompt(self, sys_prompt: str, user_prompt: str) -> Optional[str]:
        """Generate a short image prompt via Google AI Studio (Gemini).

        This is used as a fallback when Groq is unavailable/disabled.
        """
        api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
        if not api_key:
            return None

        model = (os.getenv("GEMINI_PROMPT_MODEL") or "gemini-1.5-flash").strip()

        # v1beta Generative Language API
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        params = {"key": api_key}
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": f"System: {sys_prompt}\n\nUser: {user_prompt}\n\nOutput ONLY the prompt."
                        }
                    ],
                }
            ],
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 160},
        }

        try:
            r = requests.post(url, params=params, json=payload, timeout=20)
            if r.status_code in (401, 403, 429):
                return None
            r.raise_for_status()
            data = r.json()
            cands = data.get("candidates") or []
            if not cands:
                return None
            parts = (
                cands[0].get("content", {}).get("parts")
                if isinstance(cands[0], dict)
                else None
            )
            if not parts:
                return None
            text = (parts[0].get("text") or "").strip()
            if not text:
                return None
            return text.strip().strip('"').strip("'")
        except Exception:
            return None
