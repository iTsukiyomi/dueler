import os
from pathlib import Path
from PIL import Image

class AssetLoader:
    """Manages loading and caching of image assets for the rendering pipeline.

    Provides safe fallback operations (like generating procedural grids or gradients)
    if disk assets are missing, ensuring high availability.
    """

    def __init__(self, asset_dir: Path) -> None:
        self.asset_dir = asset_dir
        self.cache: dict[str, Image.Image] = {}

    def get_background(self, name: str, width: int = 960, height: int = 540) -> Image.Image:
        """Loads a background image by name, falling back to a procedural gradient if not found."""
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
            # Procedural fallback: Dark violet/magenta grid space for Trick Room
            fallback = Image.new("RGBA", (width, height))
            from PIL import ImageDraw
            draw = ImageDraw.Draw(fallback)
            
            for y in range(height):
                f = y / height
                r = int(30 * (1 - f) + 10 * f)
                g = int(10 * (1 - f) + 5 * f)
                b = int(60 * (1 - f) + 30 * f)
                draw.line([(0, y), (width, y)], fill=(r, g, b, 255))
                
            horizon_y = height // 2
            for y in range(0, height, 20):
                opacity = int(70 * (abs(y - horizon_y) / horizon_y))
                draw.line([(0, y), (width, y)], fill=(255, 0, 255, opacity))
                
            center_x = width // 2
            for x in range(-width, 2 * width, 100):
                opacity = 50
                draw.line([(center_x, horizon_y), (x, 0)], fill=(255, 0, 255, opacity))
                draw.line([(center_x, horizon_y), (x, height)], fill=(255, 0, 255, opacity))
                
            self.cache[cache_key] = fallback
            return fallback

        # Procedural fallback: Classic grass background (old pokemon games style)
        fallback = Image.new("RGBA", (width, height))
        from PIL import ImageDraw
        draw = ImageDraw.Draw(fallback)
        
        # Draw sky gradient (light blue to cyan-white at horizon)
        horizon_y = int(height * 0.5)
        for y in range(horizon_y):
            f = y / horizon_y
            r = int(135 * (1 - f) + 224 * f)
            g = int(206 * (1 - f) + 242 * f)
            b = int(250 * (1 - f) + 253 * f)
            draw.line([(0, y), (width, y)], fill=(r, g, b, 255))
            
        # Draw soft green battlefield plane (from light yellowish green to darker forest green)
        for y in range(horizon_y, height):
            f = (y - horizon_y) / (height - horizon_y)
            r = int(152 * (1 - f) + 46 * f)
            g = int(223 * (1 - f) + 125 * f)
            b = int(138 * (1 - f) + 50 * f)
            draw.line([(0, y), (width, y)], fill=(r, g, b, 255))
            
        # Draw a horizontal line at the horizon (darker green grass boundary)
        draw.line([(0, horizon_y), (width, horizon_y)], fill=(34, 110, 34, 255), width=2)
        
        # Add some simple retro grass tufts / patterns on the green battlefield plane
        import random
        # Seed it so it's deterministic for the background
        rnd = random.Random(42)
        for _ in range(30):
            gx = rnd.randint(20, width - 40)
            gy = rnd.randint(horizon_y + 10, height - 20)
            # Draw a tiny 3-stroke retro grass tuft
            draw.line([(gx, gy), (gx - 3, gy - 6)], fill=(34, 110, 34, 160), width=1)
            draw.line([(gx, gy), (gx, gy - 8)], fill=(34, 110, 34, 180), width=1)
            draw.line([(gx, gy), (gx + 3, gy - 6)], fill=(34, 110, 34, 160), width=1)

        self.cache[cache_key] = fallback
        return fallback

    def clear(self) -> None:
        self.cache.clear()
