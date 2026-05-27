import sys

function_code = """
    def render_settings_menu(self, current_theme: str, current_gen: int) -> io.BytesIO:
        \"\"\"Render a classic Pokémon-style settings menu image.\"\"\"
        width, height = 480, 240
        
        canvas = Image.new("RGBA", (width, height), self.palette.frame_mid)
        draw = ImageDraw.Draw(canvas)
        
        # Draw main background
        self._draw_classic_panel(draw, 4, 4, width - 4, height - 4, fill=self.palette.panel_bg_dark, border=self.palette.frame_dark, border_width=4, radius=6)
        
        # Draw header
        self._draw_header_bar(draw, 12, 12, width - 12, 30, text="OPTIONS", bg=self.palette.header_bg)
        
        # Draw options container
        self._draw_classic_panel(draw, 12, 50, width - 12, height - 12, fill=self.palette.panel_bg, border=self.palette.frame_dark, border_width=2, radius=4)
        
        # Draw settings entries
        font = self.fonts["body_bold"]
        font_sm = self.fonts["small"]
        
        # Theme Option
        draw.text((24, 64), "THEME", fill=self.palette.frame_mid, font=font)
        # Highlight box for value
        self._draw_classic_panel(draw, 220, 60, 440, 90, fill=self.palette.panel_bg_dark, border=self.palette.frame_mid, border_width=1, radius=2)
        draw.text((230, 64), current_theme.upper(), fill=self.palette.text_dark, font=font)
        
        # Gen Option
        draw.text((24, 114), "GENERATION", fill=self.palette.frame_mid, font=font)
        # Highlight box for value
        self._draw_classic_panel(draw, 220, 110, 440, 140, fill=self.palette.panel_bg_dark, border=self.palette.frame_mid, border_width=1, radius=2)
        draw.text((230, 114), f"GEN {current_gen}", fill=self.palette.text_dark, font=font)

        # Help Text
        help_txt = "Use the dropdowns below to change settings."
        draw.text((24, 180), help_txt, fill=self.palette.text_light, font=font_sm)
        
        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        buf.seek(0)
        return buf
"""

def main():
    with open("pokemonduel/canvas/renderer.py", "a") as f:
        f.write(function_code)

if __name__ == "__main__":
    main()
