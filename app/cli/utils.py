def color_text(text: str, fg:str=None, bg:str=None) -> str:
    fg_colors = {"black": 30,"red": 31,"green": 32,"yellow": 33,"blue": 34,
        "magenta": 35,"cyan": 36,"white": 37,
    }

    bg_colors = {
        "black": 40, "red": 41, "green": 42, "yellow": 43, "blue": 44,"magenta": 45,
        "cyan": 46,"white": 47,
    }

    codes = []

    if fg in fg_colors:
        codes.append(str(fg_colors[fg]))

    if bg in bg_colors:
        codes.append(str(bg_colors[bg]))

    if not codes:
        return text

    return f"\033[{';'.join(codes)}m{text}\033[0m"

def print_color(text: str, fg:str=None, bg:str=None, *args, **kwargs):
    print(color_text(text, fg, bg), *args, **kwargs)