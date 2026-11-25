"""ANSI color formatting for output in terminal."""

from __future__ import annotations

__lazy_modules__ = {"termcolor.termcolor"}

from termcolor.termcolor import (
    ATTRIBUTES,
    COLORS,
    HIGHLIGHTS,
    NAMED_RGB,
    RESET,
    can_colorize,
    colored,
    cprint,
    gradient,
)

__all__ = [
    "ATTRIBUTES",
    "COLORS",
    "HIGHLIGHTS",
    "NAMED_RGB",
    "RESET",
    "can_colorize",
    "colored",
    "cprint",
    "gradient",
]
