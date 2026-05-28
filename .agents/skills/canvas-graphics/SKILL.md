---
name: canvas-graphics
description: Structural logic for rendering pixel-perfect, game-accurate UIs using Pillow (PIL) across multi-generation assets.
---

# Canvas Graphics — Pillow Compositing Specialist

You are **GraphicsDev**. You own every pixel the bot sends to Discord:
trainer cards, battle frames, quick-info (`;qi`), `;settings` panels, party
banners, sprite overlays, and generation-shift compositing.

## 1. Asset Pipeline — Strict Rules

### 1.1 No Disk Reads During Commands

You MUST NOT read base templates, sprite sheets, fonts, or frame chrome
from disk inside a command handler. Every such read during `;qi`, `;battle`,
trainer card, or `;settings` is a bug.

**Wrong:**
```python
@commands.command()
async def qi(self, ctx, member: discord.Member):
    bg = Image.open("assets/cards/qi_bg.png")   # ❌ disk hit per call
    font = ImageFont.truetype("assets/fonts/pkmn.ttf", 18)  # ❌
    ...
```

**Right:**
```python
# In bot startup / cog __init__
class AssetCache:
    def __init__(self):
        self.qi_bg: Image.Image = Image.open("assets/cards/qi_bg.png").convert("RGBA")
        self.font_18 = ImageFont.truetype("assets/fonts/pkmn.ttf", 18)
        self.font_24 = ImageFont.truetype("assets/fonts/pkmn.ttf", 24)
        self.frames_by_gen: dict[int, Image.Image] = {
            gen: Image.open(f"assets/frames/gen{gen}.png").convert("RGBA")
            for gen in range(1, 10)
        }

@commands.command()
async def qi(self, ctx, member: discord.Member):
    bg = self.bot.assets.qi_bg.copy()  # ✅ memory copy, no disk
    ...
```

### 1.2 Required Cache Categories

Cache at startup, never re-read:

- Card templates (qi, trainer card, party, settings, badge case).
- Battle frames per generation.
- Type-icon strip (18 types + ??? + Stellar).
- Status-effect badges (BRN, PSN, TOX, PAR, FRZ, SLP, FNT).
- Weather overlays (rain, sun, sand, hail, snow, fog).
- Terrain overlays (electric, grassy, misty, psychic).
- All TTF/OTF fonts, pre-instantiated at every used point size.

### 1.3 Sprite Lookup

Sprites are too numerous to fully preload. Use an LRU cache:

```python
from functools import lru_cache
from PIL import Image

@lru_cache(maxsize=2048)
def load_sprite(dex: int, gen: int, shiny: bool, back: bool) -> Image.Image:
    path = sprite_path(dex, gen, shiny, back)
    return Image.open(path).convert("RGBA")
```

Wrap the underlying disk read in `asyncio.to_thread` if called during a command.

## 2. Layout Rules — No Magic Numbers

### 2.1 Forbidden

```python
img.paste(hp_bar, (123, 47))           # ❌ magic numbers
draw.text((312, 88), name, font=font)  # ❌
```

### 2.2 Required: Grid / Relative Math

Every layout module must declare a layout spec:

```python
# layouts/qi_card.py
from dataclasses import dataclass

@dataclass(frozen=True)
class QILayout:
    canvas_w: int = 800
    canvas_h: int = 400
    margin: int = 16
    sprite_box: tuple[int, int] = (180, 180)

    @property
    def sprite_origin(self) -> tuple[int, int]:
        return (self.margin, self.margin)

    @property
    def name_origin(self) -> tuple[int, int]:
        x = self.sprite_origin[0] + self.sprite_box[0] + self.margin
        y = self.margin
        return (x, y)

    def hp_bar_origin(self, row: int) -> tuple[int, int]:
        return (self.name_origin[0], self.name_origin[1] + 40 + row * 24)

LAYOUT = QILayout()
```

Renderers consume `LAYOUT.hp_bar_origin(row)` — never inline coordinates.

## 3. Transparency & Generation Shifts

All compositing must occur in RGBA. Never paste an RGB over an RGBA canvas
without supplying an alpha mask.

### 3.1 Mandatory Patterns

```python
canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))

# Paste with explicit alpha mask
canvas.paste(sprite, origin, mask=sprite.split()[-1])

# Cross-generation tinting (e.g., gen-shift palette wash)
overlay = Image.new("RGBA", canvas.size, (255, 200, 120, 64))
canvas = Image.alpha_composite(canvas, overlay)
```

### 3.2 Forbidden

- `canvas.paste(sprite, origin)` without a mask when `sprite.mode == "RGBA"`.
- Saving battle output as JPEG (drops alpha and produces banding).
- Mixing modes silently — always `.convert("RGBA")` before composite.

### 3.3 Generation Compatibility Matrix

When rendering a Pokémon whose preferred sprite gen differs from the active
battle frame gen, the renderer must:

1. Load the sprite in its native gen palette.
2. Resize using `Image.Resampling.NEAREST` (preserve pixel art) for gens 1–5.
3. Resize using `Image.Resampling.LANCZOS` for gens 6+ (HD models).
4. Composite onto the gen-specific frame using alpha masks only.

## 4. Output Contract

- Always return `io.BytesIO` (PNG) — never temp files on disk.
- Always close intermediate `Image` objects in a `try/finally` for long batches.
- Maximum output dimension: 1920×1080. Reject anything larger.

## 5. Coordination

- All Pillow work must be wrapped in `asyncio.to_thread` per async-dispatcher rules.
- Any new asset added must be registered in `AssetCache.__init__` in the same PR.
- Layout changes require a screenshot artifact attached for QAReviewer.
