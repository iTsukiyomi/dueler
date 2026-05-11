import discord
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import os


async def generate_team_preview(battle):
    """Generates a message for trainers to preview their team with images."""
    from .buttons import PreviewPromptView

    preview_view = PreviewPromptView(battle)

    # Image configuration
    poke_width = 96
    poke_height = 96
    padding = 12
    header_height = 40

    # Calculate image dimensions
    cols = 6  # 6 Pokemon per row
    img_width = cols * poke_width + (cols + 1) * padding
    img_height = 2 * poke_height + 3 * padding + 2 * header_height

    # Create team preview image with transparent background
    team_image = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))  # Fully transparent background
    draw = ImageDraw.Draw(team_image)

    # Try to load a font, fall back to default if not available
    try:
        font = ImageFont.truetype("arial.ttf", 16)
        small_font = ImageFont.truetype("arial.ttf", 12)
    except:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    # Get the correct data directory path
    data_dir = Path(__file__).parent.parent / "data" / "img"

    # Draw trainer 1 header with white text and semi-transparent background
    trainer1_text = f"{battle.trainer1.name}'s Team"
    text_bbox = draw.textbbox((0, 0), trainer1_text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_x = (img_width - text_width) // 2

    # Draw semi-transparent background for text readability
    draw.rectangle([text_x - 5, 5, text_x + text_width + 5, 30], fill=(0, 0, 0, 128))  # Semi-transparent black
    draw.text((text_x, 10), trainer1_text, fill=(255, 255, 255, 255), font=font)  # White text

    # Draw trainer 1 Pokemon
    y_pos = header_height
    for i, poke in enumerate(battle.trainer1.party[:6]):  # Limit to 6 Pokemon
        x_pos = padding + i * (poke_width + padding)

        # Get Pokemon ID - try different possible attributes
        poke_id = None
        if hasattr(poke, 'pokemon_id'):
            poke_id = poke.pokemon_id
        elif hasattr(poke, 'id'):
            poke_id = poke.id
        elif hasattr(poke, '_id'):
            poke_id = poke._id

        # Try to load Pokemon sprite using various possible paths
        sprite_loaded = False
        if poke_id is not None:
            # Try different possible sprite file formats and paths
            possible_paths = [
                data_dir / f"{poke_id}.png",
                data_dir / f"{poke_id}.jpg",
                data_dir / f"{poke_id}.gif",
                Path("../data/img") / f"{poke_id}.png",  # Relative path fallback
                Path(f"../data/img/{poke_id}.png"),  # Another fallback
            ]

            for sprite_path in possible_paths:
                if sprite_path.exists():
                    try:
                        poke_sprite = Image.open(sprite_path).convert("RGBA")
                        poke_sprite = poke_sprite.resize((poke_width, poke_height), Image.Resampling.LANCZOS)

                        # Paste sprite directly (preserving transparency)
                        team_image.paste(poke_sprite, (x_pos, y_pos), poke_sprite)
                        sprite_loaded = True
                        break
                    except Exception as e:
                        print(f"Failed to load sprite {sprite_path}: {e}")
                        continue

        if not sprite_loaded:
            # Print debug info
            print(f"Could not load sprite for Pokemon: {poke._name}, ID: {poke_id}")
            print(f"Tried paths: {[str(p) for p in possible_paths]}")

            # Draw placeholder rectangle with transparency
            placeholder = Image.new('RGBA', (poke_width, poke_height), (200, 200, 200, 128))
            team_image.paste(placeholder, (x_pos, y_pos), placeholder)
            draw.text((x_pos + 5, y_pos + poke_height // 2), "?", fill=(255, 255, 255, 255), font=font)

        # Draw Pokemon name below sprite with background for readability
        poke_name = poke._name.replace('-', ' ').title()
        name_bbox = draw.textbbox((0, 0), poke_name, font=small_font)
        name_width = name_bbox[2] - name_bbox[0]
        name_x = x_pos + (poke_width - name_width) // 2
        name_y = y_pos + poke_height + 2

        # Semi-transparent background for name
        draw.rectangle([name_x - 2, name_y - 2, name_x + name_width + 2, name_y + 14],
                       fill=(0, 0, 0, 128))
        draw.text((name_x, name_y), poke_name, fill=(255, 255, 255, 255), font=small_font)

    # Draw separator line
    separator_y = y_pos + poke_height + 25
    draw.line([(padding, separator_y), (img_width - padding, separator_y)],
              fill=(255, 255, 255, 180), width=2)  # Semi-transparent white line

    # Draw trainer 2 header
    trainer2_text = f"{battle.trainer2.name}'s Team"
    text_bbox = draw.textbbox((0, 0), trainer2_text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_x = (img_width - text_width) // 2

    # Draw semi-transparent background for text readability
    draw.rectangle([text_x - 5, separator_y + 5, text_x + text_width + 5, separator_y + 30],
                   fill=(0, 0, 0, 128))
    draw.text((text_x, separator_y + 10), trainer2_text, fill=(255, 255, 255, 255), font=font)

    # Draw trainer 2 Pokemon
    y_pos = separator_y + header_height
    for i, poke in enumerate(battle.trainer2.party[:6]):  # Limit to 6 Pokemon
        x_pos = padding + i * (poke_width + padding)

        # Get Pokemon ID - try different possible attributes
        poke_id = None
        if hasattr(poke, 'pokemon_id'):
            poke_id = poke.pokemon_id
        elif hasattr(poke, 'id'):
            poke_id = poke.id
        elif hasattr(poke, '_id'):
            poke_id = poke._id

        # Try to load Pokemon sprite using various possible paths
        sprite_loaded = False
        if poke_id is not None:
            # Try different possible sprite file formats and paths
            possible_paths = [
                data_dir / f"{poke_id}.png",
                data_dir / f"{poke_id}.jpg",
                data_dir / f"{poke_id}.gif",
                Path("../data/img") / f"{poke_id}.png",  # Relative path fallback
                Path(f"../data/img/{poke_id}.png"),  # Another fallback
            ]

            for sprite_path in possible_paths:
                if sprite_path.exists():
                    try:
                        poke_sprite = Image.open(sprite_path).convert("RGBA")
                        poke_sprite = poke_sprite.resize((poke_width, poke_height), Image.Resampling.LANCZOS)

                        # Paste sprite directly (preserving transparency)
                        team_image.paste(poke_sprite, (x_pos, y_pos), poke_sprite)
                        sprite_loaded = True
                        break
                    except Exception as e:
                        print(f"Failed to load sprite {sprite_path}: {e}")
                        continue

        if not sprite_loaded:
            # Print debug info
            print(f"Could not load sprite for Pokemon: {poke._name}, ID: {poke_id}")

            # Draw placeholder rectangle with transparency
            placeholder = Image.new('RGBA', (poke_width, poke_height), (200, 200, 200, 128))
            team_image.paste(placeholder, (x_pos, y_pos), placeholder)
            draw.text((x_pos + 5, y_pos + poke_height // 2), "?", fill=(255, 255, 255, 255), font=font)

        # Draw Pokemon name below sprite with background for readability
        poke_name = poke._name.replace('-', ' ').title()
        name_bbox = draw.textbbox((0, 0), poke_name, font=small_font)
        name_width = name_bbox[2] - name_bbox[0]
        name_x = x_pos + (poke_width - name_width) // 2
        name_y = y_pos + poke_height + 2

        # Semi-transparent background for name
        draw.rectangle([name_x - 2, name_y - 2, name_x + name_width + 2, name_y + 14],
                       fill=(0, 0, 0, 128))
        draw.text((name_x, name_y), poke_name, fill=(255, 255, 255, 255), font=small_font)

    # Save the image as PNG to preserve transparency
    image_path = "team_preview.png"
    team_image.save(image_path, "PNG")

    # Create embed with the team image
    embed = discord.Embed(
        title=f"Battle Team Preview",
        description=f"{battle.trainer1.name} vs {battle.trainer2.name}\nSelect your lead Pokémon!"
    )

    # Attach the image to the embed
    file = discord.File(image_path, filename="team_preview.png")
    embed.set_image(url="attachment://team_preview.png")

    await battle.channel.send(embed=embed, file=file, view=preview_view)

    # Clean up the temporary image file
    try:
        os.remove(image_path)
    except:
        pass

    return preview_view