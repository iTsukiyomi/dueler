import discord
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import os
from ..ui import BattlePromptView


async def generate_main_battle_message(battle):
    """Generates a message representing the current state of the battle with sprite images and dynamic HP bars."""
    # Image configuration
    poke_width = 150
    poke_height = 150
    padding = 20
    bar_height = 25
    bar_width = 140
    name_height = 30

    img_width = poke_width * 2 + padding * 3
    img_height = poke_height + padding * 2 + bar_height + name_height + 20

    # Create image with transparent background
    battle_image = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(battle_image)

    # Font setup
    try:
        font_name = ImageFont.truetype("arial.ttf", 14)
        font_hp = ImageFont.truetype("arial.ttf", 12)
        font_small = ImageFont.truetype("arial.ttf", 10)
    except:
        font_name = ImageFont.load_default()
        font_hp = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Helper to get sprite path
    data_dir = Path(__file__).parent.parent / "data" / "img"

    def load_sprite(poke):
        # Get Pokemon ID - try different possible attributes
        poke_id = None
        if hasattr(poke, 'pokemon_id'):
            poke_id = poke.pokemon_id
        elif hasattr(poke, 'id'):
            poke_id = poke.id
        elif hasattr(poke, '_id'):
            poke_id = poke._id

        if poke_id is None:
            return None

        # Try different possible sprite file formats and paths
        possible_paths = [
            data_dir / f"{poke_id}.png",
            data_dir / f"{poke_id}.jpg",
            data_dir / f"{poke_id}.gif",
            Path("../data/img") / f"{poke_id}.png",
            Path(f"../data/img/{poke_id}.png"),
        ]

        for sprite_path in possible_paths:
            if sprite_path.exists():
                try:
                    sprite = Image.open(sprite_path).convert("RGBA")
                    sprite = sprite.resize((poke_width, poke_height), Image.Resampling.LANCZOS)
                    return sprite
                except:
                    continue
        return None

    # Draw HP Bar function
    def draw_hp_bar(draw_obj, x, y, width, height, current_hp, max_hp, poke_name):
        # Background bar (dark gray)
        draw_obj.rectangle([x, y, x + width, y + height], fill=(60, 60, 60, 255))

        # Calculate fill length
        fill_width = int(width * (current_hp / max_hp)) if max_hp > 0 else 0

        # Color thresholds based on HP percentage
        ratio = current_hp / max_hp if max_hp > 0 else 0
        if ratio > 0.5:
            color = (34, 139, 34, 255)  # Forest green
        elif ratio > 0.25:
            color = (255, 165, 0, 255)  # Orange
        else:
            color = (220, 20, 60, 255)  # Crimson red

        # Filled portion of HP bar
        if fill_width > 0:
            draw_obj.rectangle([x, y, x + fill_width, y + height], fill=color)

        # Draw border around HP bar
        draw_obj.rectangle([x, y, x + width, y + height], outline=(255, 255, 255, 255), width=2)

        # HP text on the bar
        hp_text = f"{current_hp}/{max_hp}"
        hp_bbox = draw_obj.textbbox((0, 0), hp_text, font=font_hp)
        hp_text_width = hp_bbox[2] - hp_bbox[0]
        hp_text_x = x + (width - hp_text_width) // 2
        hp_text_y = y + (height - 12) // 2

        # Text shadow for better readability
        draw_obj.text((hp_text_x + 1, hp_text_y + 1), hp_text, fill=(0, 0, 0, 255), font=font_hp)
        draw_obj.text((hp_text_x, hp_text_y), hp_text, fill=(255, 255, 255, 255), font=font_hp)

    # Helper to draw Pokemon with HP bar and text
    def draw_pokemon(draw_obj, poke, x, y, is_left=True):
        # Load sprite
        sprite = load_sprite(poke)
        if sprite is None:
            # Use placeholder rectangle
            placeholder = Image.new('RGBA', (poke_width, poke_height), (200, 200, 200, 128))
            battle_image.paste(placeholder, (x, y), placeholder)
            # Draw question mark
            draw_obj.text((x + poke_width // 2 - 10, y + poke_height // 2 - 15), "?",
                          fill=(255, 255, 255, 255), font=font_name)
        else:
            battle_image.paste(sprite, (x, y), sprite)

        # Draw HP bar above sprite
        bar_x = x + (poke_width - bar_width) // 2
        bar_y = y - bar_height - 10
        max_hp = poke.starting_hp
        current_hp = max(0, poke.hp)
        draw_hp_bar(draw_obj, bar_x, bar_y, bar_width, bar_height, current_hp, max_hp, poke._name)

        # Draw Pokemon name and nickname
        name_text = poke._name.replace('-', ' ').title()
        nick_text = getattr(poke, '_nickname', None)
        if nick_text and nick_text != "None":
            display_name = f"{nick_text} ({name_text})"
        else:
            display_name = name_text

        # Calculate text position
        name_bbox = draw_obj.textbbox((0, 0), display_name, font=font_name)
        name_width = name_bbox[2] - name_bbox[0]
        name_x = x + (poke_width - name_width) // 2
        name_y = y + poke_height + 5

        # Draw semi-transparent background for name
        draw_obj.rectangle([name_x - 5, name_y - 2, name_x + name_width + 5, name_y + 18],
                           fill=(0, 0, 0, 180))
        draw_obj.text((name_x, name_y), display_name, fill=(255, 255, 255, 255), font=font_name)

        # Draw status condition if any
        if poke.nv.current:
            status_text = poke.nv.current.upper()
            status_bbox = draw_obj.textbbox((0, 0), status_text, font=font_small)
            status_width = status_bbox[2] - status_bbox[0]
            status_x = x + (poke_width - status_width) // 2
            status_y = name_y + 20

            # Status color coding
            status_colors = {
                'BURN': (255, 69, 0, 180),
                'POISON': (128, 0, 128, 180),
                'B-POISON': (148, 0, 211, 180),
                'PARALYSIS': (255, 255, 0, 180),
                'SLEEP': (70, 130, 180, 180),
                'FREEZE': (173, 216, 230, 180)
            }
            status_color = status_colors.get(status_text, (128, 128, 128, 180))

            draw_obj.rectangle([status_x - 3, status_y - 1, status_x + status_width + 3, status_y + 12],
                               fill=status_color)
            draw_obj.text((status_x, status_y), status_text, fill=(255, 255, 255, 255), font=font_small)

    # Draw left (trainer1) and right (trainer2) Pokemon
    left_x = padding
    right_x = padding * 2 + poke_width
    poke_y = padding + bar_height + 10

    draw_pokemon(draw, battle.trainer1.current_pokemon, left_x, poke_y, is_left=True)
    draw_pokemon(draw, battle.trainer2.current_pokemon, right_x, poke_y, is_left=False)

    # Save image
    image_path = "battle_msg.png"
    battle_image.save(image_path, "PNG")

    # Build description text
    desc = ""
    if battle.weather._weather_type:
        desc += f"Weather: {battle.weather._weather_type.title()}\n"
    if battle.terrain.item:
        desc += f"Terrain: {battle.terrain.item.title()}\n"
    if battle.trick_room.active():
        desc += "Trick Room: Active\n"
    desc += "\n"

    # Add detailed status for each Pokemon
    desc += f"{battle.trainer1.name}'s {battle.trainer1.current_pokemon.name}\n"
    desc += f" HP: {battle.trainer1.current_pokemon.hp}/{battle.trainer1.current_pokemon.starting_hp}\n"
    if battle.trainer1.current_pokemon.nv.current:
        desc += f" Status: {battle.trainer1.current_pokemon.nv.current}\n"
    if battle.trainer1.current_pokemon.substitute:
        desc += " Behind a substitute!\n"
    desc += "\n"
    desc += f"{battle.trainer2.name}'s {battle.trainer2.current_pokemon.name}\n"
    desc += f" HP: {battle.trainer2.current_pokemon.hp}/{battle.trainer2.current_pokemon.starting_hp}\n"
    if battle.trainer2.current_pokemon.nv.current:
        desc += f" Status: {battle.trainer2.current_pokemon.nv.current}\n"
    if battle.trainer2.current_pokemon.substitute:
        desc += " Behind a substitute!\n"

    # Create embed with the battle image
    e = discord.Embed(
        title=f"Battle between {battle.trainer1.name} and {battle.trainer2.name}",
        description=desc)
    e.set_footer(text="Who Wins!?")
    e.set_image(url="attachment://battle_msg.png")

    try:
        battle_view = BattlePromptView(battle)
        file = discord.File(image_path, filename="battle_msg.png")
        await battle.channel.send(embed=e, file=file, view=battle_view)
    except RuntimeError:
        pass

    # Clean up the temporary image file
    try:
        os.remove(image_path)
    except:
        pass

    return battle_view


async def generate_text_battle_message(battle):
    """
    Send battle.msg in a boilerplate embed.
    Handles the message being too long.
    """
    page = ""
    pages = []
    base_embed = discord.Embed()  # Fixed color
    raw = battle.msg.strip().split("\n")

    for part in raw:
        if len(page + part) > 2000:
            embed = base_embed.copy()
            embed.description = page.strip()
            pages.append(embed)
            page = ""
        page += part + "\n"

    page = page.strip()
    if page:
        embed = base_embed.copy()
        embed.description = page
        pages.append(embed)

    for page in pages:
        await battle.channel.send(embed=page)

    battle.msg = ""