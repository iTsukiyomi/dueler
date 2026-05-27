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

    def get_background(self, name: str, width: int = 960, height: int = 540, gen: int | None = None, theme: str = "firered") -> Image.Image:
        """Loads a background image by name, falling back to a procedural classic Pokémon background."""
        cache_key = f"bg_{name}_{width}x{height}_{gen}_{theme}"
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
            fallback = self._gen_card_bg(width, height, gen, theme)
        elif name == "trainer_card_bg":
            fallback = self._gen_trainer_card_bg(width, height, gen, theme)
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

    def _gen_card_bg(self, width: int, height: int, gen: int | None = None, theme: str = "firered") -> Image.Image:
        """Generates a generation-specific Pokémon summary screen card background."""
        from .themes import get_palette
        
        # Resolve legacy gen/theme parameters
        theme_lower = theme.lower().strip()
        if theme_lower in ("light", "dark"):
            if gen == 1:
                theme_lower = "firered"
            elif gen == 2:
                theme_lower = "firered"
            elif gen == 3:
                theme_lower = "firered"
            elif gen == 4:
                theme_lower = "platinum"
            elif gen == 5:
                theme_lower = "black"
            elif gen == 6:
                theme_lower = "x"
            elif gen == 7:
                theme_lower = "sun"
            elif gen == 8:
                theme_lower = "sword"
            elif gen == 9:
                theme_lower = "scarlet"
            else:
                theme_lower = "firered"
        
        palette = get_palette(theme_lower)
        
        if gen is None or theme.lower().strip() not in ("light", "dark"):
            if theme_lower == "firered":
                gen = 3
            elif theme_lower in ("heartgold", "platinum"):
                gen = 4
            elif theme_lower == "black":
                gen = 5
            else:
                gen = 6
        
        img = Image.new("RGBA", (width, height))
        draw = ImageDraw.Draw(img)
        
        if gen == 1:
            # Gen 1 GameBoy Monochrome Green
            bg_color = palette.panel_bg
            draw.rectangle([0, 0, width, height], fill=bg_color)
            # Classic GameBoy grid texture (faint dots or vertical lines)
            dot_color = palette.panel_bg_dark
            for y in range(0, height, 4):
                for x in range(0, width, 4):
                    if (x + y) % 8 == 0:
                        draw.point((x, y), fill=dot_color)
            # Outer double-line border
            draw.rectangle([0, 0, width - 1, height - 1], outline=palette.frame_dark, width=3)
            draw.rectangle([4, 4, width - 5, height - 5], outline=palette.frame_dark, width=1)
            
        elif gen == 2:
            # Gen 2 GameBoy Color / Crystal style split-color panel
            draw.rectangle([0, 0, width, height], fill=palette.panel_bg)
            
            # Left panel split (x: 0 to 175)
            left_fill = palette.panel_bg_dark
            draw.rectangle([0, 0, 175, height], fill=left_fill)
            
            # Simple line pattern for Left Panel
            for y in range(0, height, 8):
                draw.line([(0, y), (175, y)], fill=(*palette.frame_mid, 40), width=1)
                
            # Sharp 2px outer border
            draw.rectangle([0, 0, width - 1, height - 1], outline=palette.frame_dark, width=2)
            draw.line([(175, 0), (175, height)], fill=palette.frame_dark, width=2)
            
        elif gen == 3:
            # Gen 3 GBA Summary screen
            draw.rectangle([0, 0, width, height], fill=palette.panel_bg)
            
            # Left side panel gradient
            left_w = 170
            for x in range(left_w):
                f = x / left_w
                r = int(palette.panel_bg_dark[0] * (1 - f) + palette.frame_mid[0] * f * 0.5)
                g = int(palette.panel_bg_dark[1] * (1 - f) + palette.frame_mid[1] * f * 0.5)
                b = int(palette.panel_bg_dark[2] * (1 - f) + palette.frame_mid[2] * f * 0.5)
                draw.line([(x, 0), (x, height)], fill=(r, g, b, 255))
            
            draw.line([(170, 0), (170, height)], fill=palette.frame_dark, width=2)
            draw.rectangle([0, 0, width, 6], fill=palette.frame_dark)
            draw.rectangle([0, 0, width - 1, height - 1], outline=palette.frame_dark, width=2)
            
        elif gen == 4:
            # Gen 4 DS metallic/tech panel with steel/blue frames
            draw.rectangle([0, 0, width, height], fill=palette.panel_bg)
            
            # Tech lines in background
            grid_color = (*palette.frame_mid, 30)
            for x in range(0, width, 30):
                draw.line([(x, 0), (x, height)], fill=grid_color, width=1)
            for y in range(0, height, 30):
                draw.line([(0, y), (width, y)], fill=grid_color, width=1)
                
            draw.rectangle([10, 40, 168, 200], fill=palette.panel_bg_dark, outline=palette.frame_mid, width=2)
            draw.rectangle([0, 0, width - 1, height - 1], outline=palette.frame_dark, width=2)
            
        elif gen == 5:
            # Gen 5 DS carbon-fiber / grid tech style
            draw.rectangle([0, 0, width, height], fill=palette.panel_bg)
            for y in range(0, height, 4):
                draw.line([(0, y), (width, y)], fill=(*palette.frame_mid, 15), width=1)
            for x in range(0, width, 8):
                draw.line([(x, 0), (x, height)], fill=(*palette.frame_mid, 10), width=1)
                
            draw.rectangle([0, 0, width - 1, height - 1], outline=palette.frame_dark, width=2)
            
        else:
            # Gen 6-9 Modern flat card with beautiful smooth pastel gradients
            if theme == "dark":
                for y in range(height):
                    f = y / height
                    r = int(24 * (1 - f) + 48 * f)
                    g = int(24 * (1 - f) + 24 * f)
                    b = int(48 * (1 - f) + 80 * f)
                    draw.line([(0, y), (width, y)], fill=(r, g, b, 255))
            else:
                for y in range(height):
                    f = y / height
                    r = int(230 * (1 - f) + 250 * f)
                    g = int(240 * (1 - f) + 230 * f)
                    b = int(255 * (1 - f) + 240 * f)
                    draw.line([(0, y), (width, y)], fill=(r, g, b, 255))
            
            draw.rectangle([0, 0, width - 1, height - 1], outline=palette.frame_dark, width=2)
            
        return img

    def _gen_trainer_card_bg(self, width: int, height: int, gen: int | None = None, theme: str = "firered") -> Image.Image:
        """Generates a generation-specific trainer card background."""
        from .themes import get_palette
        
        # Resolve legacy gen/theme parameters
        theme_lower = theme.lower().strip()
        if theme_lower in ("light", "dark"):
            if gen == 1:
                theme_lower = "firered"
            elif gen == 2:
                theme_lower = "firered"
            elif gen == 3:
                theme_lower = "firered"
            elif gen == 4:
                theme_lower = "platinum"
            elif gen == 5:
                theme_lower = "black"
            elif gen == 6:
                theme_lower = "x"
            elif gen == 7:
                theme_lower = "sun"
            elif gen == 8:
                theme_lower = "sword"
            elif gen == 9:
                theme_lower = "scarlet"
            else:
                theme_lower = "firered"
        
        palette = get_palette(theme_lower)
        
        if gen is None or theme.lower().strip() not in ("light", "dark"):
            if theme_lower == "firered":
                gen = 3
            elif theme_lower in ("heartgold", "platinum"):
                gen = 4
            elif theme_lower == "black":
                gen = 5
            else:
                gen = 6
        
        img = Image.new("RGBA", (width, height))
        draw = ImageDraw.Draw(img)
        
        if gen == 1:
            draw.rectangle([0, 0, width, height], fill=palette.panel_bg)
            draw.rectangle([0, 0, width - 1, height - 1], outline=palette.frame_dark, width=3)
            draw.rectangle([4, 4, width - 5, height - 5], outline=palette.frame_dark, width=1)
            
            for y in range(48, height - 48, 6):
                draw.point((width - 24, y), fill=palette.frame_dark)
                draw.point((width - 12, y), fill=palette.frame_dark)
                
        elif gen == 2:
            draw.rectangle([0, 0, width, height], fill=palette.panel_bg)
            grid_color = (*palette.frame_mid, 30)
            for offset in range(-height, width + height, 15):
                draw.line([(offset, 0), (offset + height, height)], fill=grid_color, width=1)
                
            draw.rectangle([0, 0, width - 1, height - 1], outline=palette.frame_dark, width=3)
            draw.rectangle([3, 3, width - 4, height - 4], outline=(255, 255, 255, 255) if theme == "light" else palette.panel_bg_dark, width=1)
            
        elif gen == 3:
            if theme == "dark":
                base_color = (64, 40, 24, 255)
                stripe_color = (48, 28, 16, 255)
            else:
                base_color = (248, 176, 112, 255)
                stripe_color = (240, 144, 80, 255)
                
            draw.rectangle([0, 0, width, height], fill=base_color)
            for offset in range(-height, width + height, 20):
                draw.line([(offset, 0), (offset + height, height)], fill=stripe_color, width=8)
                
            draw.rectangle([0, 0, width - 1, height - 1], outline=palette.frame_dark, width=4)
            draw.rectangle([4, 4, width - 5, height - 5], outline=(255, 255, 255, 255) if theme == "light" else palette.panel_bg_dark, width=2)
            draw.rectangle([6, 6, width - 7, 36], fill=palette.frame_dark)
            
        elif gen == 4:
            if theme == "dark":
                for y in range(height):
                    f = y / height
                    c = int(48 * (1 - f) + 24 * f)
                    draw.line([(0, y), (width, y)], fill=(c, c, c + 8, 255))
            else:
                for y in range(height):
                    f = y / height
                    c = int(220 * (1 - f) + 190 * f)
                    draw.line([(0, y), (width, y)], fill=(c, c - 5, c - 15, 255))
                    
            draw.rectangle([0, 0, width - 1, height - 1], outline=palette.frame_dark, width=3)
            draw.rectangle([4, 4, width - 5, height - 5], outline=palette.frame_mid, width=1)
            draw.rectangle([5, 5, width - 6, 36], fill=palette.frame_dark)
            
        elif gen == 5:
            draw.rectangle([0, 0, width, height], fill=palette.panel_bg)
            stripe_color = (*palette.frame_mid, 20)
            for offset in range(-height, width + height, 12):
                draw.line([(offset, 0), (offset + height, height)], fill=stripe_color, width=4)
                
            draw.rectangle([0, 0, width - 1, height - 1], outline=palette.frame_dark, width=3)
            draw.rectangle([4, 4, width - 5, height - 5], outline=palette.frame_mid, width=1)
            draw.rectangle([5, 5, width - 6, 36], fill=palette.frame_dark)
            
        else:
            if theme == "dark":
                for y in range(height):
                    f = y / height
                    r = int(16 * (1 - f) + 48 * f)
                    g = int(40 * (1 - f) + 16 * f)
                    b = int(64 * (1 - f) + 80 * f)
                    draw.line([(0, y), (width, y)], fill=(r, g, b, 255))
            else:
                for y in range(height):
                    f = y / height
                    r = int(255 * (1 - f) + 253 * f)
                    g = int(180 * (1 - f) + 220 * f)
                    b = int(140 * (1 - f) + 160 * f)
                    draw.line([(0, y), (width, y)], fill=(r, g, b, 255))
                    
            draw.rectangle([0, 0, width - 1, height - 1], outline=palette.frame_dark, width=2)
            draw.rectangle([3, 3, width - 4, 36], fill=palette.header_bg)
            
        return img

    def clear(self) -> None:
        self.cache.clear()
