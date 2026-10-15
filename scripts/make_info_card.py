"""Neofetch-style info card SVG, sized to sit beside the meme gif.

Usage: python scripts/make_info_card.py
Reads the gif's intrinsic size from its header and makes the card exactly as tall
as the gif renders at GIF_DISPLAY_W, so the two README table columns line up.
Writes assets/info-card.svg. SMIL only; see svg_fx.py for the rules.
"""
import struct
from html import escape
from pathlib import Path

from svg_fx import BEGIN, GREEN, MONO, MUTED, TEXT, blink_cursor, f, key_times, matrix_rain, window

ROOT = Path(__file__).resolve().parent.parent
GIF = ROOT / "assets" / "meme.gif"
OUT = ROOT / "assets" / "info-card.svg"

# README widths: gif + card stay well under the ~790px profile column
# (table cell padding adds ~52px on top of these).
GIF_DISPLAY_W = 300
CARD_W = 420

USER, HOST = "raj", "tejash-veer46"
# (key, value, priority) - lowest priority lines are dropped first if the card is short.
INFO = [
    ("OS", "Windows 11 · Ubuntu (CI runners)", 9),
    ("Host", "LTM · SDET-1", 5),
    ("Uptime", "Around 2 yrs breaking things on purpose", 2),
    ("Shell", "TypeScript · Java · SQL", 8),
    ("Stack", "Playwright · Selenium · Cucumber", 9),
    ("Perf", "JMeter · Postman · SOAP UI · Claude/GHCP", 4),
    ("Web", "React · Node.js · Express · Supabase", 6),
    ("CI/CD", "Jenkins · GitHub Actions · Docker", 7),
    ("Ships", "test frameworks · AI test-gen agents", 9),
    ("Projects", "BaFive · AskMosaic RAG copilot", 3),
    ("GitHub", "github.com/tejash-veer46", 8),
    ("LinkedIn", "in/raj-tejashwy-1ba788206", 8),
    ("Mail", "rajtejashwy@gmail.com", 7),
]
NEOFETCH_COLORS = ["#484f58", "#ff7b72", "#3fb950", "#d29922", "#58a6ff", "#bc8cff", "#39c5cf", "#f0f6fc"]


def gif_size(path):
    if not path.exists():
        print(f"{path.name} not found; sizing the card for a square gif")
        return 1, 1
    head = path.read_bytes()[:10]
    if head[:6] not in (b"GIF87a", b"GIF89a"):
        raise SystemExit(f"{path} is not a GIF")
    return struct.unpack("<HH", head[6:10])


def main():
    gw, gh = gif_size(GIF)
    H = round(gh * GIF_DISPLAY_W / gw)
    W, BAR = CARD_W, 30
    top, bottom = BAR + 14, 12

    lines = list(INFO)
    # In line_h units: header baseline 0.75, rule 1, blocks 0.5 gap + 0.8 tall, prompt baseline 1.2 below.
    fixed_rows = 0.75 + 1 + 0.5 + 0.8 + 1.2
    while True:
        line_h = (H - top - bottom) / (len(lines) + fixed_rows)
        if line_h >= 14.5 or len(lines) <= 4:
            break
        lines.remove(min(lines, key=lambda l: l[2]))
    line_h = min(line_h, 22)
    fs = round(min(12.5, line_h * 0.8), 1)
    cw = fs * 0.6

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
           f'role="img" aria-label="{USER}@{HOST} system info">']
    svg.append(window(0, 0, W, H, f"{USER}@{HOST}: ~ neofetch", "ic-clip", bar=BAR))
    svg.append(matrix_rain(0, BAR, W, H - BAR, "ic-clip", seed=HOST + "card", opacity=0.13))

    x = 18
    key_w = (max(len(k) for k, *_ in lines) + 2) * cw
    y = top + line_h * 0.75
    t = 0.25

    def reveal(body, delay):
        """Fade + slide in. Static state: in place, fully opaque."""
        dur = delay + 0.35
        kt = key_times(0, delay / dur, 1)
        return (f'<g>{body}<animate attributeName="opacity" values="0;0;1" keyTimes="{kt}" dur="{f(dur)}s" '
                f'begin="{BEGIN}" fill="freeze"/><animateTransform attributeName="transform" type="translate" '
                f'values="-10 0;-10 0;0 0" keyTimes="{kt}" dur="{f(dur)}s" begin="{BEGIN}" fill="freeze"/></g>')

    head = f"{USER}@{HOST}"
    svg.append(reveal(
        f'<text x="{x}" y="{f(y)}" font-family="{MONO}" font-size="{fs}" font-weight="bold">'
        f'<tspan fill="{GREEN}">{USER}</tspan><tspan fill="{TEXT}">@</tspan><tspan fill="{GREEN}">{HOST}</tspan></text>', t))
    y += line_h
    t += 0.1
    svg.append(reveal(f'<text x="{x}" y="{f(y)}" font-family="{MONO}" font-size="{fs}" fill="{MUTED}">'
                      f'{"-" * len(head)}</text>', t))
    for key, val, _ in lines:
        y += line_h
        t += 0.12
        svg.append(reveal(
            f'<text x="{x}" y="{f(y)}" font-family="{MONO}" font-size="{fs}" font-weight="bold" fill="{GREEN}">{escape(key)}</text>'
            f'<text x="{f(x + key_w)}" y="{f(y)}" font-family="{MONO}" font-size="{fs}" fill="{TEXT}">{escape(val)}</text>', t))

    y += line_h * 0.5
    t += 0.15
    sq = min(line_h * 0.8, 16)
    blocks = "".join(f'<rect x="{f(x + i * (sq + 2))}" y="{f(y)}" width="{f(sq)}" height="{f(sq)}" rx="2" fill="{c}"/>'
                     for i, c in enumerate(NEOFETCH_COLORS))
    svg.append(reveal(blocks, t))

    # Prompt pinned to the bottom edge, with the blinking block cursor.
    py = H - bottom
    prompt = f"{USER}@github:~$"
    svg.append(f'<text x="{x}" y="{f(py)}" font-family="{MONO}" font-size="{fs}" fill="{GREEN}" '
               f'textLength="{f(len(prompt) * cw)}" lengthAdjust="spacingAndGlyphs">{prompt}</text>')
    svg.append(blink_cursor(x + (len(prompt) + 1) * cw, py - fs * 0.85, round(cw, 1), round(fs * 1.05, 1)))

    svg.append("</svg>")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(svg), encoding="utf-8")
    dropped = [k for k, *_ in INFO if k not in {l[0] for l in lines}]
    print(f"wrote {OUT} ({W}x{H} to match {gw}x{gh} gif at {GIF_DISPLAY_W}px; dropped: {dropped or 'none'})")


if __name__ == "__main__":
    main()
