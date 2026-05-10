import discord
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import os
from ..ui import PreviewPromptView


async def generate_team_preview(battle):
    """Generates a message for trainers to preview their team with images."""
    preview_view = PreviewPromptView(battle)

    poke_width = 96
    poke_height = 96
    padding = 12
    header_height = 40

    cols = 6
    img_width = cols * poke_width + (cols + 1) * padding
    img_height = 2 * poke_height + 3 * padding + 2 * header_height

    team_image = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(team_image)

    try:
        font = ImageFont.truetype("arial.ttf", 16)
        small_font = ImageFont.truetype("arial.ttf", 12)
    except:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    data_dir = Path(__file__).parent.parent / "data" / "img"

    trainer1_text = f"{battle.trainer1.name}'s Team"
    text_bbox = draw.textbbox((0, 0), trainer1_text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_x = (img_width - text_width) // 2

    draw.rectangle([text_x - 5, 5, text_x + text_width + 5, 30], fill=(0, 0, 0, 128))
    draw.text((text_x, 10), trainer1_text, fill=(255, 255, 255, 255), font=font)

    y_pos = header_height
    for i, poke in enumerate(battle.trainer1.party[:6]):
        x_pos = padding + i * (poke_width + padding)

        poke_id = None
        if hasattr(poke, 'pokemon_id'):
            poke_id = poke.pokemon_id
        elif hasattr(poke, 'id'):
            poke_id = poke.id
        elif hasattr(poke, '_id'):
            poke_id = poke._id

        sprite_loaded = False
        if poke_id is not None:
            possible_paths = [
                data_dir / f"{poke_id}.png",
                data_dir / f"{poke_id}.jpg",
                data_dir / f"{poke_id}.gif",
                Path("data/img") / f"{poke_id}.png",
                Path(f"data/img/{poke_id}.png"),
            ]

            for sprite_path in possible_paths:
                if sprite_path.exists():
                    try:
                        poke_sprite = Image.open(sprite_path).convert("RGBA")
                        poke_sprite = poke_sprite.resize((poke_width, poke_height), Image.Resampling.LANCZOS)
                        team_image.paste(poke_sprite, (x_pos, y_pos), poke_sprite)
                        sprite_loaded = True
                        break
                    except Exception as e:
                        print(f"Failed to load sprite {sprite_path}: {e}")
                        continue

        if not sprite_loaded:
            print(f"Could not load sprite for Pokemon: {poke._name}, ID: {poke_id}")
            print(f"Tried paths: {[str(p) for p in possible_paths]}")
            placeholder = Image.new('RGBA', (poke_width, poke_height), (200, 200, 200, 128))
            team_image.paste(placeholder, (x_pos, y_pos), placeholder)
            draw.text((x_pos + 5, y_pos + poke_height // 2), "?", fill=(255, 255, 255, 255), font=font)

        poke_name = poke._name.replace('-', ' ').title()
        name_bbox = draw.textbbox((0, 0), poke_name, font=small_font)
        name_width = name_bbox[2] - name_bbox[0]
        name_x = x_pos + (poke_width - name_width) // 2
        name_y = y_pos + poke_height + 2

        draw.rectangle([name_x - 2, name_y - 2, name_x + name_width + 2, name_y + 14],
                       fill=(0, 0, 0, 128))
        draw.text((name_x, name_y), poke_name, fill=(255, 255, 255, 255), font=small_font)

    separator_y = y_pos + poke_height + 25
    draw.line([(padding, separator_y), (img_width - padding, separator_y)],
              fill=(255, 255, 255, 180), width=2)

    trainer2_text = f"{battle.trainer2.name}'s Team"
    text_bbox = draw.textbbox((0, 0), trainer2_text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_x = (img_width - text_width) // 2

    draw.rectangle([text_x - 5, separator_y + 5, text_x + text_width + 5, separator_y + 30],
                   fill=(0, 0, 0, 128))
    draw.text((text_x, separator_y + 10), trainer2_text, fill=(255, 255, 255, 255), font=font)

    y_pos = separator_y + header_height
    for i, poke in enumerate(battle.trainer2.party[:6]):
        x_pos = padding + i * (poke_width + padding)

        poke_id = None
        if hasattr(poke, 'pokemon_id'):
            poke_id = poke.pokemon_id
        elif hasattr(poke, 'id'):
            poke_id = poke.id
        elif hasattr(poke, '_id'):
            poke_id = poke._id

        sprite_loaded = False
        if poke_id is not None:
            possible_paths = [
                data_dir / f"{poke_id}.png",
                data_dir / f"{poke_id}.jpg",
                data_dir / f"{poke_id}.gif",
                Path("data/img") / f"{poke_id}.png",
                Path(f"data/img/{poke_id}.png"),
            ]

            for sprite_path in possible_paths:
                if sprite_path.exists():
                    try:
                        poke_sprite = Image.open(sprite_path).convert("RGBA")
                        poke_sprite = poke_sprite.resize((poke_width, poke_height), Image.Resampling.LANCZOS)
                        team_image.paste(poke_sprite, (x_pos, y_pos), poke_sprite)
                        sprite_loaded = True
                        break
                    except Exception as e:
                        print(f"Failed to load sprite {sprite_path}: {e}")
                        continue

        if not sprite_loaded:
            print(f"Could not load sprite for Pokemon: {poke._name}, ID: {poke_id}")
            placeholder = Image.new('RGBA', (poke_width, poke_height), (200, 200, 200, 128))
            team_image.paste(placeholder, (x_pos, y_pos), placeholder)
            draw.text((x_pos + 5, y_pos + poke_height // 2), "?", fill=(255, 255, 255, 255), font=font)

        poke_name = poke._name.replace('-', ' ').title()
        name_bbox = draw.textbbox((0, 0), poke_name, font=small_font)
        name_width = name_bbox[2] - name_bbox[0]
        name_x = x_pos + (poke_width - name_width) // 2
        name_y = y_pos + poke_height + 2

        draw.rectangle([name_x - 2, name_y - 2, name_x + name_width + 2, name_y + 14],
                       fill=(0, 0, 0, 128))
        draw.text((name_x, name_y), poke_name, fill=(255, 255, 255, 255), font=small_font)

    image_path = "team_preview.png"
    team_image.save(image_path, "PNG")

    embed = discord.Embed(
        title=f"Battle Team Preview",
        description=f"{battle.trainer1.name} vs {battle.trainer2.name}\nSelect your lead Pokémon!"
    )

    file = discord.File(image_path, filename="team_preview.png")
    embed.set_image(url="attachment://team_preview.png")

    await battle.channel.send(embed=embed, file=file, view=preview_view)

    try:
        os.remove(image_path)
    except:
        pass

    return preview_view