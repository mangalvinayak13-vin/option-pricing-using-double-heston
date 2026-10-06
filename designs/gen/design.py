"""What every design module declares."""
from __future__ import annotations

from dataclasses import dataclass, field

from kit import Ink


@dataclass
class Design:
    num: int
    slug: str
    name: str
    concept: str
    memorable: str
    layout: str
    light: dict
    dark: dict
    fonts_url: str
    display_font: str
    body_font: str
    type_sample: str
    type_note: str
    ink: Ink
    css: str = ""
    rail_side: str = "l"
    default_dark: bool = True
    icon_fills: dict = field(default_factory=dict)
    pages: dict = field(default_factory=dict)

    def plan_note(self) -> str:
        def pal(t):
            return ", ".join(f"{k} {t[k]}" for k in ("bg", "surf", "ink", "muted", "acc", "line"))
        return (f"{self.name}. {self.concept}\n\nLayout: {self.layout}\nThe memorable thing: {self.memorable}\n"
                f"Type: {self.type_note}\nLight: {pal(self.light)}\nDark: {pal(self.dark)}\n"
                f"Magnet rail on the {'left' if self.rail_side == 'l' else 'right'} edge. Live prices on these boards are "
                "NSE closing prices from 25 Sep 2026; every chart is drawn from real data or the project's pricer.")

    def icon_style(self, kind: str) -> dict:
        return self.icon_fills.get(kind, {"fill": "var(--raised)", "ink": "var(--ink)"})


TOKENS = ["bg", "surf", "raised", "line", "grid", "ink", "body", "muted", "acc", "on_acc", "up", "down", "on_up",
          "track_off", "ferro", "ferro_hi"]


def check_tokens(d: Design):
    for theme in (d.light, d.dark):
        missing = [k for k in TOKENS if k not in theme]
        if missing:
            raise ValueError(f"{d.name}: missing tokens {missing}")
