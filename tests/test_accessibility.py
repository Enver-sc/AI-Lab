"""Gezielte Barrierefreiheits-Regressionstests (kein vollstaendiger WCAG/EN-301-549-
Katalog) -- siehe AGENTS.md, Abschnitt "Barrierefreiheit". Prueft die konkreten,
automatisierbaren Punkte: Farbkontrast der Design-Tokens, kein unterdruecktes
Fokus-Outline, prefers-reduced-motion wird respektiert.
"""
import re
from pathlib import Path

STYLE_CSS = (Path(__file__).resolve().parent.parent / "app" / "static" / "css" / "style.css").read_text(encoding="utf-8")

WCAG_AA_NORMAL_TEXT = 4.5


def _linearize(channel: int) -> float:
    value = channel / 255
    return value / 12.92 if value <= 0.03928 else ((value + 0.055) / 1.055) ** 2.4


def _relative_luminance(hex_color: str) -> float:
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _linearize(r) + 0.7152 * _linearize(g) + 0.0722 * _linearize(b)


def contrast_ratio(color_a: str, color_b: str) -> float:
    lum_a, lum_b = _relative_luminance(color_a), _relative_luminance(color_b)
    lighter, darker = max(lum_a, lum_b), min(lum_a, lum_b)
    return (lighter + 0.05) / (darker + 0.05)


def _load_root_tokens() -> dict:
    match = re.search(r":root\{([^}]*)\}", STYLE_CSS)
    assert match, "Keine :root{...}-Deklaration in style.css gefunden."
    tokens = {}
    for name, value in re.findall(r"--([a-z0-9-]+):(#[0-9a-fA-F]{6})", match.group(1)):
        tokens[name] = value
    return tokens


TOKENS = _load_root_tokens()

# Tatsaechlich im Dashboard verwendete Text-auf-Untergrund-Kombinationen (siehe
# style.css: body-Text auf --bg, Kacheln auf --surface/--surface2, .metrics
# .green/.yellow/.red-Statusfarben, Ring-/Batteriefarben).
TEXT_ON_BACKGROUND_PAIRS = [
    ("text", "bg"), ("muted", "bg"), ("green", "bg"), ("yellow", "bg"), ("red", "bg"), ("blue", "bg"),
    ("text", "surface"), ("muted", "surface"), ("green", "surface"), ("yellow", "surface"),
    ("red", "surface"), ("blue", "surface"),
    ("muted", "surface2"), ("green", "surface2"),
]


def test_root_tokens_are_present():
    for name in ("bg", "surface", "surface2", "text", "muted", "green", "yellow", "red", "blue"):
        assert name in TOKENS, f"Farb-Token --{name} fehlt in :root -- Testannahmen stimmen nicht mehr."


def test_text_color_combinations_meet_wcag_aa_contrast():
    failures = []
    for foreground, background in TEXT_ON_BACKGROUND_PAIRS:
        ratio = contrast_ratio(TOKENS[foreground], TOKENS[background])
        if ratio < WCAG_AA_NORMAL_TEXT:
            failures.append(f"--{foreground} auf --{background}: {ratio:.2f}:1 (< {WCAG_AA_NORMAL_TEXT}:1)")
    assert not failures, "WCAG-AA-Kontrast unterschritten:\n" + "\n".join(failures)


def test_focus_outline_is_not_suppressed():
    # outline:none/0 ohne eigenen sichtbaren Fokusstil wuerde Tastaturnutzung
    # unbrauchbar machen (WCAG 2.4.7) -- Browser-Standard-Fokusring ist bewusst
    # die aktuelle Loesung, darf nicht versehentlich wegoptimiert werden.
    assert not re.search(r"outline\s*:\s*(none|0)\b", STYLE_CSS), \
        "outline:none/0 gefunden -- unterdrueckt sichtbare Tastatur-Fokusanzeige."


def test_prefers_reduced_motion_is_respected():
    assert "prefers-reduced-motion" in STYLE_CSS, (
        "Keine prefers-reduced-motion-Media-Query in style.css -- Ring-/Toast-"
        "Uebergaenge wuerden fuer Nutzer mit reduzierter Bewegungseinstellung "
        "nicht abgeschaltet."
    )
