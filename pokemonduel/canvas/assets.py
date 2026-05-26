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

        # Procedural fallback: Deep space cyber battle arena gradient
        fallback = Image.new("RGBA", (width, height))
        # Draw a beautiful horizontal gradient with a subtle grid
        from PIL import ImageDraw
        draw = ImageDraw.Draw(fallback)
        
        # Draw sky gradient (dark blue to purple-gray)
        for y in range(height):
            # Calculate gradient factor
            f = y / height
            r = int(10 * (1 - f) + 24 * f)
            g = int(14 * (1 - f) + 28 * f)
            b = int(28 * (1 - f) + 48 * f)
            draw.line([(0, y), (width, y)], fill=(r, g, b, 255))
            
        # Draw subtle grid lines on the bottom half (the battlefield plane)
        battle_start_y = int(height * 0.45)
        for y in range(battle_start_y, height, 15):
            opacity = int(40 * ((y - battle_start_y) / (height - battle_start_y)))
            draw.line([(0, y), (width, y)], fill=(0, 240, 255, opacity))
            
        # Perspective grid lines meeting at the horizon (center, battle_start_y)
        horizon_x = width // 2
        for x in range(-width, 2 * width, 80):
            opacity = 35
            draw.line([(horizon_x, battle_start_y), (x, height)], fill=(0, 240, 255, opacity))

        self.cache[cache_key] = fallback
        return fallback

    def clear(self) -> None:
        self.cache.clear()
