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
from typing import Optional, Tuple, List
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
    logging.warning("⚠️ pilmoji not installed. Emojis may not render correctly.")

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
    title_font_size: int = 64
    hook_font_size: int = 32
    title_max_width: int = 1000  # Max width before wrapping

    # Overlay settings
    overlay_opacity: float = 0.4  # 0.0 to 1.0

    # Geometric elements
    num_circles: int = 8
    num_dots: int = 50
    num_lines: int = 6

    # Border settings
    border_width: int = 4
    border_glow: bool = True

    # Gradient direction: 'diagonal', 'horizontal', 'vertical', 'radial'
    gradient_type: str = "diagonal"


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

    def __init__(self, imgbb_api_key: Optional[str] = None):
        """
        Initialize the image generator.

        Args:
            imgbb_api_key: API key for ImgBB upload service
        """
        self.imgbb_api_key = imgbb_api_key or os.getenv(
            "IMGBB_API_KEY", "c1633f2c05d08d77b999ead25c49295a"
        )
        self.config = DesignConfig()

        # Font paths - we'll try multiple locations
        self.font_paths = self._discover_fonts()

        logger.info("🎨 Image Generator initialized")

    def _discover_fonts(self) -> dict:
        """
        Discover available fonts on the system.
        Returns a dictionary of font types to paths.
        """
        # Common font locations
        font_dirs = [
            "C:/Windows/Fonts",
            "/usr/share/fonts",
            "/System/Library/Fonts",
            os.path.join(os.path.dirname(__file__), "..", "assets", "fonts"),
        ]

        # Preferred fonts for different purposes
        preferred_fonts = {
            "title": [
                "arialbd.ttf",
                "Arial Bold.ttf",
                "Roboto-Bold.ttf",
                "DejaVuSans-Bold.ttf",
            ],
            "hook": ["arial.ttf", "Arial.ttf", "Roboto-Regular.ttf", "DejaVuSans.ttf"],
            "arabic": [
                "arial.ttf",
                "Tahoma.ttf",
                "segoeui.ttf",
                "NotoSansArabic-Regular.ttf",
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

    def _get_font(self, font_type: str, size: int) -> ImageFont.FreeTypeFont:
        """
        Get a font object, with fallback to default if not found.
        """
        try:
            if font_type in self.font_paths:
                return ImageFont.truetype(self.font_paths[font_type], size)
            # Fallback to arial
            return ImageFont.truetype("arial.ttf", size)
        except Exception:
            # Ultimate fallback to default
            return ImageFont.load_default()

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
            return bidi_text
        except Exception as e:
            logger.warning(f"Arabic processing failed: {e}")
            return text

    def _wrap_text(
        self, text: str, font: ImageFont.FreeTypeFont, max_width: int
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

            # Get text width
            try:
                bbox = font.getbbox(test_line)
                text_width = bbox[2] - bbox[0]
            except:
                text_width = len(test_line) * (font.size * 0.6)

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
        font: ImageFont.FreeTypeFont,
        color: Tuple[int, int, int] = (255, 255, 255),
        shadow: bool = True,
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

        if shadow:
            # Add drop shadow for depth
            shadow_offset = 3
            shadow_color = (0, 0, 0)

            if PILMOJI_AVAILABLE:
                with Pilmoji(image) as pilmoji:
                    pilmoji.text(
                        (x + shadow_offset, y + shadow_offset),
                        processed_text,
                        font=font,
                        fill=shadow_color,
                    )
                    pilmoji.text((x, y), processed_text, font=font, fill=color)
            else:
                draw = ImageDraw.Draw(image)
                draw.text(
                    (x + shadow_offset, y + shadow_offset),
                    processed_text,
                    font=font,
                    fill=shadow_color,
                )
                draw.text((x, y), processed_text, font=font, fill=color)
        else:
            if PILMOJI_AVAILABLE:
                with Pilmoji(image) as pilmoji:
                    pilmoji.text((x, y), processed_text, font=font, fill=color)
            else:
                draw = ImageDraw.Draw(image)
                draw.text((x, y), processed_text, font=font, fill=color)

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

        # Choose a random palette if not specified
        if palette is None:
            palette = random.choice(list(ColorPalette))

        colors = palette.value
        accent_color = colors[-1]  # Last color is always the accent

        # Override gradient type if specified
        if gradient_type:
            self.config.gradient_type = gradient_type

        size = (self.config.width, self.config.height)

        # ═══════════════════════════════════════════════════════════════════
        # LAYER 1: Base Gradient Background
        # ═══════════════════════════════════════════════════════════════════
        image = self._create_gradient(size, colors, self.config.gradient_type)
        image = image.convert("RGBA")

        # ═══════════════════════════════════════════════════════════════════
        # LAYER 2: Geometric Art Elements
        # ═══════════════════════════════════════════════════════════════════
        image = self._add_geometric_elements(image, accent_color)

        # ═══════════════════════════════════════════════════════════════════
        # LAYER 3: Dark Overlay for Text Contrast
        # ═══════════════════════════════════════════════════════════════════
        image = self._add_overlay(image)

        # ═══════════════════════════════════════════════════════════════════
        # LAYER 4: Professional Border
        # ═══════════════════════════════════════════════════════════════════
        image = self._add_border(image, accent_color)

        # ═══════════════════════════════════════════════════════════════════
        # LAYER 5: Typography - Title
        # ═══════════════════════════════════════════════════════════════════
        title_font = self._get_font("title", self.config.title_font_size)

        # Wrap the title text
        title_lines = self._wrap_text(title, title_font, self.config.title_max_width)

        # Calculate total text height
        line_height = self.config.title_font_size + 10
        total_title_height = len(title_lines) * line_height

        # Position title (centered, upper third of image)
        if hook:
            title_y = (self.config.height // 2) - total_title_height - 20
        else:
            title_y = (self.config.height - total_title_height) // 2

        # Render each line of the title
        for i, line in enumerate(title_lines):
            # Calculate line width for centering
            try:
                bbox = title_font.getbbox(line)
                line_width = bbox[2] - bbox[0]
            except:
                line_width = len(line) * (self.config.title_font_size * 0.6)

            line_x = (self.config.width - line_width) // 2
            line_y = title_y + (i * line_height)

            image = self._render_text_with_emoji(
                image,
                line,
                (line_x, line_y),
                title_font,
                color=(255, 255, 255),
                shadow=True,
            )

        # ═══════════════════════════════════════════════════════════════════
        # LAYER 6: Typography - Hook/Subtitle
        # ═══════════════════════════════════════════════════════════════════
        if hook:
            hook_font = self._get_font("hook", self.config.hook_font_size)

            # Wrap hook text
            hook_lines = self._wrap_text(hook, hook_font, self.config.title_max_width)

            hook_line_height = self.config.hook_font_size + 8
            hook_y = title_y + total_title_height + 30

            for i, line in enumerate(hook_lines):
                try:
                    bbox = hook_font.getbbox(line)
                    line_width = bbox[2] - bbox[0]
                except:
                    line_width = len(line) * (self.config.hook_font_size * 0.6)

                line_x = (self.config.width - line_width) // 2
                line_y = hook_y + (i * hook_line_height)

                # Use accent color for hook
                image = self._render_text_with_emoji(
                    image,
                    line,
                    (line_x, line_y),
                    hook_font,
                    color=accent_color,
                    shadow=True,
                )

        # ═══════════════════════════════════════════════════════════════════
        # LAYER 7: Branding (Optional watermark)
        # ═══════════════════════════════════════════════════════════════════
        small_font = self._get_font("hook", 18)
        brand_text = "ContentOrbit"

        try:
            bbox = small_font.getbbox(brand_text)
            brand_width = bbox[2] - bbox[0]
        except:
            brand_width = len(brand_text) * 10

        brand_x = self.config.width - brand_width - 30
        brand_y = self.config.height - 40

        draw = ImageDraw.Draw(image, "RGBA")
        draw.text(
            (brand_x, brand_y), brand_text, font=small_font, fill=(255, 255, 255, 80)
        )

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

    def save_local(
        self, image: Image.Image, filename: str = "generated_image.png"
    ) -> str:
        """
        Save the image locally for testing/preview.

        Args:
            image: PIL Image to save
            filename: Output filename

        Returns:
            Full path to saved file
        """
        output_dir = os.path.join(os.path.dirname(__file__), "..", "output")
        os.makedirs(output_dir, exist_ok=True)

        filepath = os.path.join(output_dir, filename)
        image.save(filepath, "PNG", quality=95)

        logger.info(f"💾 Image saved: {filepath}")
        return filepath


# ═══════════════════════════════════════════════════════════════════════════════
# 🧪 TESTING & DEMONSTRATION
# ═══════════════════════════════════════════════════════════════════════════════


def demo():
    """
    Demonstrate the image generator capabilities.
    """
    generator = ImageGenerator()

    # Test with various content
    test_cases = [
        {
            "title": "🚀 كيف تجعل الذكاء الاصطناعي يكتب بأسلوب أنيق؟",
            "hook": "اكتشف أسرار الكتابة الإبداعية مع AI",
            "palette": ColorPalette.COSMIC_NIGHT,
        },
        {
            "title": "🔥 Top 10 Python Libraries You Need in 2026",
            "hook": "Level up your coding game today!",
            "palette": ColorPalette.CYBER_PUNK,
        },
        {
            "title": "✨ The Future of Technology is Here",
            "hook": None,
            "palette": ColorPalette.TECH_BLUE,
        },
    ]

    for i, test in enumerate(test_cases):
        print(f"\n{'='*60}")
        print(f"Test {i+1}: {test['title'][:40]}...")
        print(f"{'='*60}")

        image = generator.generate(
            title=test["title"], hook=test["hook"], palette=test["palette"]
        )

        # Save locally
        filename = f"test_image_{i+1}.png"
        filepath = generator.save_local(image, filename)
        print(f"✅ Saved: {filepath}")

        # Upload to ImgBB
        url = generator.upload_to_imgbb(image)
        if url:
            print(f"🌐 URL: {url}")
        else:
            print("⚠️ Upload skipped or failed")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    demo()
