import os
from pathlib import Path
from PIL import Image, ImageDraw

class AssetLoader:
    """Manages loading and caching of image assets for the rendering pipeline.

    Provides safe fallback operations (like generating procedural backgrounds)
    if disk assets are missing, ensuring high availability.

    Theme: Classic Pokémon (Fire Red / Black & White era).
    """

    def __init__(self, asset_dir: Path) -> None:
        self.asset_dir = asset_dir
        self.cache: dict[str, Image.Image] = {}

    def get_background(self, name: str, width: int = 960, height: int = 540) -> Image.Image:
        """Loads a background image by name, falling back to a procedural classic Pokémon background."""
        cache_key = f"bg_{name}_{width}x{height}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        filepath = self.asset_dir / f"{name}.png"
        if filepath.exists():
            try:
                img = Image.open(filepath).convert("RGBA")
                img = img.resize((width, height), Image.Resampling.LANCZOS)
                self.cache[cache_key] = img
                return img
            except Exception:
                pass

        if name == "trick_room":
            fallback = self._gen_trick_room_bg(width, height)
        elif name == "team_preview_bg":
            fallback = self._gen_team_preview_bg(width, height)
        elif name == "card_bg":
            fallback = self._gen_card_bg(width, height)
        else:
            fallback = self._gen_battle_bg(width, height)

        self.cache[cache_key] = fallback
        return fallback

    # -- Classic Pokémon Battle Background (Gen 3/5 inspired) --

    def _gen_battle_bg(self, width: int, height: int) -> Image.Image:
        """Classic outdoor Pokémon battle field — flat grass, clean sky, horizon line."""
        img = Image.new("RGBA", (width, height))
        draw = ImageDraw.Draw(img)

        horizon_y = int(height * 0.45)

        # Sky: gentle blue gradient (light cerulean → pale sky)
        for y in range(horizon_y):
            f = y / max(1, horizon_y)
            r = int(104 + (176 - 104) * f)
            g = int(168 + (216 - 168) * f)
            b = int(240 + (248 - 240) * f)
            draw.line([(0, y), (width, y)], fill=(r, g, b, 255))

        # Simple cloud accents
        import random
        rnd = random.Random(42)
        for _ in range(4):
            cx = rnd.randint(60, width - 120)
            cy = rnd.randint(20, horizon_y - 50)
            cw = rnd.randint(80, 160)
            ch = rnd.randint(20, 35)
            draw.ellipse([cx, cy, cx + cw, cy + ch], fill=(255, 255, 255, 60))
            draw.ellipse([cx + 20, cy - 8, cx + cw - 20, cy + ch - 5], fill=(255, 255, 255, 45))

        # Ground: flat grass green zones (Gen 3 style — 2 tone stripes)
        grass_light = (120, 200, 80, 255)
        grass_dark = (88, 168, 56, 255)
        grass_dirt = (192, 168, 120, 255)

        for y in range(horizon_y, height):
            f = (y - horizon_y) / max(1, (height - horizon_y))
            # Alternate bands every ~30px for a flat retro field look
            band = ((y - horizon_y) // 28) % 2
            if band == 0:
                r = int(grass_light[0] * (1 - f * 0.3) + grass_dirt[0] * f * 0.3)
                g = int(grass_light[1] * (1 - f * 0.3) + grass_dirt[1] * f * 0.3)
                b = int(grass_light[2] * (1 - f * 0.3) + grass_dirt[2] * f * 0.3)
            else:
                r = int(grass_dark[0] * (1 - f * 0.3) + grass_dirt[0] * f * 0.3)
                g = int(grass_dark[1] * (1 - f * 0.3) + grass_dirt[1] * f * 0.3)
                b = int(grass_dark[2] * (1 - f * 0.3) + grass_dirt[2] * f * 0.3)
            draw.line([(0, y), (width, y)], fill=(r, g, b, 255))

        # Horizon line (dark green border)
        draw.line([(0, horizon_y), (width, horizon_y)], fill=(56, 120, 40, 255), width=2)
        draw.line([(0, horizon_y + 2), (width, horizon_y + 2)], fill=(72, 140, 52, 200), width=1)

        return img

    # -- Trick Room Background --

    def _gen_trick_room_bg(self, width: int, height: int) -> Image.Image:
        """Dark purple dimensional space for Trick Room — classic Gen 5 style."""
        img = Image.new("RGBA", (width, height))
        draw = ImageDraw.Draw(img)

        # Dark purple gradient
        for y in range(height):
            f = y / height
            r = int(40 * (1 - f) + 16 * f)
            g = int(16 * (1 - f) + 8 * f)
            b = int(72 * (1 - f) + 40 * f)
            draw.line([(0, y), (width, y)], fill=(r, g, b, 255))

        # Perspective grid lines (classic trick room look)
        horizon_y = height // 2
        grid_color = (140, 80, 180, 50)
        for y in range(0, height, 24):
            draw.line([(0, y), (width, y)], fill=grid_color, width=1)

        center_x = width // 2
        for x in range(-width, 2 * width, 80):
            draw.line([(center_x, horizon_y), (x, 0)], fill=(140, 80, 180, 35), width=1)
            draw.line([(center_x, horizon_y), (x, height)], fill=(140, 80, 180, 35), width=1)

        return img

    # -- Team Preview Background --

    def _gen_team_preview_bg(self, width: int, height: int) -> Image.Image:
        """Dark blue Pokémon menu background (like PC Box / Party screen)."""
        img = Image.new("RGBA", (width, height))
        draw = ImageDraw.Draw(img)

        # Dark blue base (like the Gen 3/5 PC box or team menu)
        for y in range(height):
            f = y / height
            r = int(24 + 16 * f)
            g = int(40 + 24 * f)
            b = int(88 + 40 * f)
            draw.line([(0, y), (width, y)], fill=(r, g, b, 255))

        # Subtle diagonal pattern (like classic Pokémon menu backgrounds)
        pattern_color = (255, 255, 255, 8)
        for offset in range(-height, width + height, 16):
            draw.line([(offset, 0), (offset + height, height)], fill=pattern_color, width=1)

        return img

    # -- Pokémon Card Background --

    def _gen_card_bg(self, width: int, height: int) -> Image.Image:
        """Cream/off-white Pokémon summary screen background."""
        img = Image.new("RGBA", (width, height))
        draw = ImageDraw.Draw(img)

        # Cream/off-white fill (classic summary screen)
        cream = (248, 244, 232, 255)
        draw.rectangle([0, 0, width, height], fill=cream)

        # Subtle paper texture — very faint horizontal lines
        for y in range(0, height, 4):
            draw.line([(0, y), (width, y)], fill=(232, 228, 216, 120), width=1)

        # Dark blue header bar at top (like Gen 3/5 summary header)
        header_h = 6
        draw.rectangle([0, 0, width, header_h], fill=(48, 56, 112, 255))

        # Dark border frame
        draw.rectangle([0, 0, width - 1, height - 1], outline=(48, 56, 112, 255), width=2)

        return img

    def clear(self) -> None:
        self.cache.clear()
