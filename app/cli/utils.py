import re


ANSI_ESCAPE_PATTERN = re.compile(r"\033\[[0-9;]*m")


def color_text(text: str, fg: str = None, bg: str = None) -> str:
    """Wrap text in ANSI color codes when foreground or background is known."""
    fg_colors = {
        "black": 30,
        "red": 31,
        "green": 32,
        "yellow": 33,
        "blue": 34,
        "magenta": 35,
        "cyan": 36,
        "white": 37,
    }

    bg_colors = {
        "black": 40,
        "red": 41,
        "green": 42,
        "yellow": 43,
        "blue": 44,
        "magenta": 45,
        "cyan": 46,
        "white": 47,
    }

    codes = []

    if fg in fg_colors:
        codes.append(str(fg_colors[fg]))

    if bg in bg_colors:
        codes.append(str(bg_colors[bg]))

    if not codes:
        return text

    return f"\033[{';'.join(codes)}m{text}\033[0m"


def print_color(text: str, fg: str = None, bg: str = None, *args, **kwargs):
    """Print text with optional ANSI colors."""
    print(color_text(text, fg, bg), *args, **kwargs)


def visible_length(text: str) -> int:
    """Return text length without ANSI color sequences."""
    return len(ANSI_ESCAPE_PATTERN.sub("", text))


def truncate_visible(text: str, width: int) -> str:
    """Trim text to a visible width without breaking ANSI color sequences."""
    if width <= 0:
        return ""

    if visible_length(text) <= width:
        return text

    suffix = "..." if width >= 3 else "." * width
    target_width = width - len(suffix)
    result = []
    visible_count = 0
    idx = 0
    saw_ansi = False

    while idx < len(text) and visible_count < target_width:
        match = ANSI_ESCAPE_PATTERN.match(text, idx)
        if match:
            result.append(match.group())
            idx = match.end()
            saw_ansi = True
            continue

        result.append(text[idx])
        visible_count += 1
        idx += 1

    if saw_ansi:
        result.append("\033[0m")
    result.append(suffix)
    return "".join(result)


def clear_console() -> None:
    """Clear the terminal screen."""
    print("\033[2J\033[H", end="")


def sakila_banner() -> str:
    banner = "\n".join(
        [
            "  ____        _    _ _        _      ____                           _     ",  # noqa: E501
            " / ___|  __ _| | _(_) | __ _ / |    / ___|  ___  __ _ _ __ ___ ___ | |__  ",  # noqa: E501
            " \\___ \\ / _` | |/ / | |/ _` || |____\\___ \\ / _ \\/ _` | '__/ __/ _ \\| '_ \\ ",  # noqa: E501
            "  ___) | (_| |   <| | | (_| || |_____|__) |  __/ (_| | | | (_| (_) | | | |",  # noqa: E501
            " |____/ \\__,_|_|\\_\\_|_|\\__,_||_|    |____/ \\___|\\__,_|_|  \\___\\___/|_| |_|",  # noqa: E501
        ]
    )
    return color_text(banner, "cyan")
