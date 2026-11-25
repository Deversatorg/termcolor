# Copyright (c) 2008-2011 Volvox Development Team
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# Author: Konstantin Lepa <konstantin.lepa@gmail.com>

"""ANSI color formatting for output in terminal."""

from __future__ import annotations

import os
import sys
from functools import cache

TYPE_CHECKING = False
if TYPE_CHECKING:
    from collections.abc import Iterable
    from typing import Any


ATTRIBUTES: dict[str, int] = {
    "bold": 1,
    "dark": 2,
    "italic": 3,
    "underline": 4,
    "blink": 5,
    "reverse": 7,
    "concealed": 8,
    "strike": 9,
}

HIGHLIGHTS: dict[str, int] = {
    "on_black": 40,
    "on_grey": 40,  # Actually black but kept for backwards compatibility
    "on_red": 41,
    "on_green": 42,
    "on_yellow": 43,
    "on_blue": 44,
    "on_magenta": 45,
    "on_cyan": 46,
    "on_light_grey": 47,
    "on_dark_grey": 100,
    "on_light_red": 101,
    "on_light_green": 102,
    "on_light_yellow": 103,
    "on_light_blue": 104,
    "on_light_magenta": 105,
    "on_light_cyan": 106,
    "on_white": 107,
}

COLORS: dict[str, int] = {
    "black": 30,
    "grey": 30,  # Actually black but kept for backwards compatibility
    "red": 31,
    "green": 32,
    "yellow": 33,
    "blue": 34,
    "magenta": 35,
    "cyan": 36,
    "light_grey": 37,
    "dark_grey": 90,
    "light_red": 91,
    "light_green": 92,
    "light_yellow": 93,
    "light_blue": 94,
    "light_magenta": 95,
    "light_cyan": 96,
    "white": 97,
}


NAMED_RGB: dict[str, tuple[int, int, int]] = {
    # Custom true-colour palette (PizzaWSB theme). Usable as `color`, or with an
    # "on_" prefix as `on_color`, e.g. colored("x", "pizza_red", "on_mozzarella").
    "pizza_red": (200, 30, 45),
    "basil_green": (60, 140, 60),
    "mozzarella": (250, 245, 230),
    "crust_brown": (170, 110, 50),
    "wsb_blue": (0, 70, 140),
}


RESET = "\033[0m"

_RGB_FORE_FMT = "38;2;%d;%d;%d"
_RGB_BACK_FMT = "48;2;%d;%d;%d"


def _named_code(name: str, table: dict[str, int], fmt: str, prefix: str = "") -> str:
    """Return the SGR code for a basic colour name or a NAMED_RGB entry."""
    if name in table:
        return str(table[name])
    rgb_name = name[len(prefix) :] if prefix and name.startswith(prefix) else None
    if rgb_name is not None and rgb_name in NAMED_RGB:
        return fmt % NAMED_RGB[rgb_name]
    if not prefix and name in NAMED_RGB:
        return fmt % NAMED_RGB[name]
    raise KeyError(name)


@cache
def can_colorize(
    *, no_color: bool | None = None, force_color: bool | None = None
) -> bool:
    """Check env vars and for tty/dumb terminal"""
    # First check overrides:
    # "User-level configuration files and per-instance command-line arguments should
    # override $NO_COLOR. A user should be able to export $NO_COLOR in their shell
    # configuration file as a default, but configure a specific program in its
    # configuration file to specifically enable color."
    # https://no-color.org
    if no_color is not None and no_color:
        return False
    if force_color is not None and force_color:
        return True

    # Then check env vars:
    if os.environ.get("ANSI_COLORS_DISABLED"):
        return False
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True

    # Then check system:
    if os.environ.get("TERM") == "dumb":
        return False
    if not hasattr(sys.stdout, "fileno"):
        return False

    try:
        return os.isatty(sys.stdout.fileno())
    except OSError:
        return sys.stdout.isatty()


def _check_rgb(rgb: tuple[int, int, int]) -> None:
    if len(rgb) != 3 or not all(0 <= c <= 255 for c in rgb):
        msg = f"Expected a tuple of 3 ints in range 0-255, got {rgb!r}"
        raise ValueError(msg)


def colored(
    text: object,
    color: str | tuple[int, int, int] | None = None,
    on_color: str | tuple[int, int, int] | None = None,
    attrs: Iterable[str] | None = None,
    *,
    no_color: bool | None = None,
    force_color: bool | None = None,
) -> str:
    """Colorize text.

    Available text colors:
        black, red, green, yellow, blue, magenta, cyan, white,
        light_grey, dark_grey, light_red, light_green, light_yellow, light_blue,
        light_magenta, light_cyan.

    Available text highlights:
        on_black, on_red, on_green, on_yellow, on_blue, on_magenta, on_cyan, on_white,
        on_light_grey, on_dark_grey, on_light_red, on_light_green, on_light_yellow,
        on_light_blue, on_light_magenta, on_light_cyan.

    Alternatively, both text colors (color) and highlights (on_color) may
    be specified via a tuple of 0-255 ints (R, G, B).

    Available attributes:
        bold, dark, italic, underline, blink, reverse, concealed, strike.

    Example:
        colored('Hello, World!', 'red', 'on_black', ['bold', 'blink'])
        colored('Hello, World!', 'green')
        colored('Hello, World!', (255, 0, 255))  # Purple
    """
    result = str(text)
    if no_color is None and force_color is None:
        # Fast path: functools.cache has a much cheaper key for no arguments
        if not can_colorize():
            return result
    elif not can_colorize(no_color=no_color, force_color=force_color):
        return result

    codes = []

    if attrs is not None:
        for attr in attrs:
            codes.append(str(ATTRIBUTES[attr]))  # noqa: PERF401  # faster than extend

    if color is not None:
        if isinstance(color, str):
            codes.append(_named_code(color, COLORS, _RGB_FORE_FMT))
        elif isinstance(color, tuple):
            _check_rgb(color)
            codes.append(_RGB_FORE_FMT % color)

    if on_color is not None:
        if isinstance(on_color, str):
            codes.append(_named_code(on_color, HIGHLIGHTS, _RGB_BACK_FMT, "on_"))
        elif isinstance(on_color, tuple):
            _check_rgb(on_color)
            codes.append(_RGB_BACK_FMT % on_color)

    if codes:
        result = f"\033[{';'.join(codes)}m{result}"

    result += RESET

    return result


def cprint(
    text: object,
    color: str | tuple[int, int, int] | None = None,
    on_color: str | tuple[int, int, int] | None = None,
    attrs: Iterable[str] | None = None,
    *,
    no_color: bool | None = None,
    force_color: bool | None = None,
    **kwargs: Any,
) -> None:
    """Print colorized text.

    It accepts arguments of print function.
    """
    print(
        (
            colored(
                text,
                color,
                on_color,
                attrs,
                no_color=no_color,
                force_color=force_color,
            )
        ),
        **kwargs,
    )


def _to_rgb(color: str | tuple[int, int, int]) -> tuple[int, int, int]:
    if isinstance(color, str):
        if color not in NAMED_RGB:
            msg = f"Unknown NAMED_RGB colour {color!r}, expected one of {sorted(NAMED_RGB)}"
            raise ValueError(msg)
        return NAMED_RGB[color]
    _check_rgb(color)
    return color


def gradient(
    text: object,
    start: str | tuple[int, int, int],
    end: str | tuple[int, int, int],
    attrs: Iterable[str] | None = None,
    *,
    no_color: bool | None = None,
    force_color: bool | None = None,
) -> str:
    """Colorize text with a linear true-colour gradient from `start` to `end`.

    `start` and `end` are (R, G, B) tuples or names from NAMED_RGB.
    Whitespace keeps its position but gets no colour code.

    Example:
        gradient('PizzaWSB', 'pizza_red', 'mozzarella')
        gradient('Hello', (255, 0, 0), (0, 0, 255), attrs=['bold'])
    """
    a, b = _to_rgb(start), _to_rgb(end)
    result = str(text)
    if not result or not can_colorize(no_color=no_color, force_color=force_color):
        return result
    n = max(len(result) - 1, 1)
    parts = []
    for i, ch in enumerate(result):
        if ch.isspace():
            parts.append(ch)
            continue
        rgb = tuple(round(a[k] + (b[k] - a[k]) * i / n) for k in range(3))
        parts.append(colored(ch, rgb, attrs=attrs, force_color=True)[: -len(RESET)])
    return "".join(parts) + RESET

