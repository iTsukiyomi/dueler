from PIL import Image, ImageDraw


async def create_animated_battle_composite(
    left_sprite,
    right_sprite,
    battle,
    img_width,
    img_height,
    poke_width,
    poke_height,
    padding,
    bar_height,
    bar_width,
    font_name,
    font_hp,
    font_small,
    draw_hp_bar_func
):
    """
    Creates an animated GIF composite if either sprite is animated.
    Returns (frames_list, durations_list) or None if both are static.
    """
    left_animated = isinstance(left_sprite, dict) and left_sprite.get('animated', False)
    right_animated = isinstance(right_sprite, dict) and right_sprite.get('animated', False)
    
    # Only do this if at least one sprite is animated
    if not (left_animated or right_animated):
        return None
    
    frames = []
    durations = []
    
    # Get the maximum frame count
    max_frames = 1
    if left_animated:
        max_frames = max(max_frames, len(left_sprite['frames']))
    if right_animated:
        max_frames = max(max_frames, len(right_sprite['frames']))
    
    left_x = padding
    right_x = padding * 2 + poke_width
    poke_y = padding + bar_height + 10
    
    for frame_idx in range(max_frames):
        # Create base image for this frame
        frame_image = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))
        frame_draw = ImageDraw.Draw(frame_image)
        
        # Draw left Pokemon
        if left_sprite is None:
            placeholder = Image.new('RGBA', (poke_width, poke_height), (200, 200, 200, 128))
            frame_image.paste(placeholder, (left_x, poke_y), placeholder)
            frame_draw.text((left_x + poke_width // 2 - 10, poke_y + poke_height // 2 - 15), "?",
                          fill=(255, 255, 255, 255), font=font_name)
        elif left_animated:
            left_frame = left_sprite['frames'][frame_idx % len(left_sprite['frames'])]
            left_frame_resized = left_frame.resize((poke_width, poke_height), Image.Resampling.LANCZOS)
            frame_image.paste(left_frame_resized, (left_x, poke_y), left_frame_resized)
        else:
            # Static sprite
            frame_image.paste(left_sprite, (left_x, poke_y), left_sprite)
        
        # Draw right Pokemon
        if right_sprite is None:
            placeholder = Image.new('RGBA', (poke_width, poke_height), (200, 200, 200, 128))
            frame_image.paste(placeholder, (right_x, poke_y), placeholder)
            frame_draw.text((right_x + poke_width // 2 - 10, poke_y + poke_height // 2 - 15), "?",
                          fill=(255, 255, 255, 255), font=font_name)
        elif right_animated:
            right_frame = right_sprite['frames'][frame_idx % len(right_sprite['frames'])]
            right_frame_resized = right_frame.resize((poke_width, poke_height), Image.Resampling.LANCZOS)
            frame_image.paste(right_frame_resized, (right_x, poke_y), right_frame_resized)
        else:
            # Static sprite
            frame_image.paste(right_sprite, (right_x, poke_y), right_sprite)
        
        # Draw HP bars and names on every frame
        draw_hp_bar_func(frame_draw, left_x + (poke_width - bar_width) // 2, poke_y - bar_height - 10, 
                   bar_width, bar_height, max(0, battle.trainer1.current_pokemon.hp), 
                   battle.trainer1.current_pokemon.starting_hp, battle.trainer1.current_pokemon._name)
        
        draw_hp_bar_func(frame_draw, right_x + (poke_width - bar_width) // 2, poke_y - bar_height - 10,
                   bar_width, bar_height, max(0, battle.trainer2.current_pokemon.hp),
                   battle.trainer2.current_pokemon.starting_hp, battle.trainer2.current_pokemon._name)
        
        # Draw names
        for poke, x_pos in [(battle.trainer1.current_pokemon, left_x), (battle.trainer2.current_pokemon, right_x)]:
            name_text = poke._name.replace('-', ' ').title()
            nick_text = getattr(poke, '_nickname', None)
            if nick_text and nick_text != "None":
                display_name = f"{nick_text} ({name_text})"
            else:
                display_name = name_text
            
            name_bbox = frame_draw.textbbox((0, 0), display_name, font=font_name)
            name_width = name_bbox[2] - name_bbox[0]
            name_x = x_pos + (poke_width - name_width) // 2
            name_y = poke_y + poke_height + 5
            
            frame_draw.rectangle([name_x - 5, name_y - 2, name_x + name_width + 5, name_y + 18],
                               fill=(0, 0, 0, 180))
            frame_draw.text((name_x, name_y), display_name, fill=(255, 255, 255, 255), font=font_name)
        
        frames.append(frame_image)
        
        # Get frame duration
        frame_duration = 100
        if left_animated and frame_idx < len(left_sprite['durations']):
            frame_duration = left_sprite['durations'][frame_idx]
        elif right_animated and frame_idx < len(right_sprite['durations']):
            frame_duration = right_sprite['durations'][frame_idx]
        durations.append(frame_duration)
    
    return frames, durations