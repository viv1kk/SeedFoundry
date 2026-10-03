"""Resolved design-token values, read from the frontend's tokens.css (D-37), for the visual QA
rules that need a colour (contrast, palette). tokens.css is the one place the values live, so
the validators read it rather than keep a copy (D-57)."""

from __future__ import annotations

import re
from functools import cache
from pathlib import Path

TOKENS_CSS = Path(__file__).resolve().parents[3] / "frontend" / "src" / "styles" / "tokens.css"

_DECLARATION = re.compile(r"(--[\w-]+)\s*:\s*([^;]+);")
_VAR = re.compile(r"^var\((--[\w-]+)\)$")
_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")


def _block(css: str, selector: str) -> dict[str, str]:
    start = css.index(f"{selector} {{")
    body = css[start : css.index("}", start)]
    return {name: value.strip() for name, value in _DECLARATION.findall(body)}


@cache
def themes(path: Path = TOKENS_CSS) -> dict[str, dict[str, str]]:
    """Every token's declared value in each theme (dark overrides light), var() unresolved."""
    css = re.sub(r"/\*.*?\*/", "", path.read_text(encoding="utf-8"), flags=re.S)
    light = _block(css, ":root")
    return {"light": light, "dark": {**light, **_block(css, "[data-theme='dark']")}}


def colour(theme: str, token: str, path: Path = TOKENS_CSS) -> str:
    """A token's #rrggbb value in a theme, following var() as the browser does. `token` may omit
    the leading dashes ("chart-positive")."""
    name = token if token.startswith("--") else f"--{token}"
    values = themes(path)[theme]
    seen: set[str] = set()
    while True:
        if name not in values:
            raise KeyError(f"{name} is not a token in the {theme} theme")
        value = values[name]
        reference = _VAR.match(value)
        if not reference:
            break
        if name in seen:
            raise ValueError(f"var() cycle at {name}")
        seen.add(name)
        name = reference.group(1)
    if not _HEX.match(value):
        raise ValueError(f"{name} in {theme} is not a #rrggbb colour: {value}")
    return value.lower()


def is_token(token: str, path: Path = TOKENS_CSS) -> bool:
    name = token if token.startswith("--") else f"--{token}"
    return name in themes(path)["light"]


def luminance(hex_colour: str) -> float:
    channels = []
    for i in (1, 3, 5):
        c = int(hex_colour[i : i + 2], 16) / 255
        channels.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    r, g, b = channels
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    """WCAG 2.1 contrast ratio of two #rrggbb colours."""
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)
