from .palette import get_palette, ThemePalette

def get_theme_renderer(theme: str, renderer):
    theme = theme.lower().strip()
    if theme == "firered":
        from .firered import FireRedRenderer
        return FireRedRenderer(renderer)
    elif theme == "heartgold":
        from .heartgold import HeartGoldRenderer
        return HeartGoldRenderer(renderer)
    elif theme == "platinum":
        from .platinum import PlatinumRenderer
        return PlatinumRenderer(renderer)
    elif theme == "black":
        from .black import BlackRenderer
        return BlackRenderer(renderer)
    elif theme == "x":
        from .x import XRenderer
        return XRenderer(renderer)
    elif theme == "sun":
        from .sun import SunRenderer
        return SunRenderer(renderer)
    elif theme == "sword":
        from .sword import SwordRenderer
        return SwordRenderer(renderer)
    elif theme == "scarlet":
        from .scarlet import ScarletRenderer
        return ScarletRenderer(renderer)
    else:
        from .firered import FireRedRenderer
        return FireRedRenderer(renderer)
