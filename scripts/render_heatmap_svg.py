"""Render data/contributions.json as an animated terminal-style heatmap SVG.

Usage: python scripts/render_heatmap_svg.py
Writes assets/heatmap.svg. SMIL only; see svg_fx.py for the rules.
"""
import hashlib
import json
import random
from datetime import date
from pathlib import Path

from svg_fx import (BEGIN, GREEN, MONO, MUTED, TEXT, f, key_times, matrix_rain,
                    moving_cursor, typed_text, window)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "contributions.json"
OUT = ROOT / "assets" / "heatmap.svg"

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
FLASH = "#b8ffbf"
SHIMMER = "#8dffa0"

CELL, GAP = 10, 3
PITCH = CELL + GAP
PAD = 20
BAR = 30
GRID_X = PAD + 32
GRID_Y = BAR + 34

# Timeline: the scan beam's first pass and the pop-in wave travel together.
WAVE_START, WAVE_SPAN = 0.35, 2.1
BEAM_DUR = 9.0
POP = 0.42


def h01(s):
    return int(hashlib.md5(s.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def main():
    data = json.loads(DATA.read_text())
    days = data["days"]
    first = date.fromisoformat(days[0]["date"])
    lead = (first.weekday() + 1) % 7  # Sunday-first rows
    cells = []
    for i, d in enumerate(days):
        idx = i + lead
        cells.append({**d, "col": idx // 7, "row": idx % 7})
    ncols = cells[-1]["col"] + 1

    grid_w = ncols * PITCH - GAP
    W = GRID_X + grid_w + PAD
    H = GRID_Y + 7 * PITCH - GAP + 50
    rng = random.Random(data["username"])

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
           f'role="img" aria-label="{data["username"]}: {data["total"]} contributions in the last year">']
    svg.append(window(0, 0, W, H, f'{data["username"]}@github: ~/contributions', "hm-clip", bar=BAR))
    svg.append(matrix_rain(0, BAR, W, H - BAR, "hm-clip", seed=data["username"] + "hm", opacity=0.22))

    # Month labels on the first column containing the 1st..7th of a month.
    last_label_col = -10
    for c in cells:
        dt = date.fromisoformat(c["date"])
        if c["row"] == 0 and dt.day <= 7 and c["col"] - last_label_col >= 3:
            svg.append(f'<text x="{GRID_X + c["col"] * PITCH}" y="{GRID_Y - 8}" font-family="{MONO}" '
                       f'font-size="10" fill="{MUTED}">{dt.strftime("%b")}</text>')
            last_label_col = c["col"]
    for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        svg.append(f'<text x="{GRID_X - 6}" y="{GRID_Y + row * PITCH + CELL - 1}" text-anchor="end" '
                   f'font-family="{MONO}" font-size="10" fill="{MUTED}">{name}</text>')

    # Cells: pop in with overshoot + green flash as the wave passes, bright ones shimmer forever.
    half = CELL / 2
    glints = []
    svg.append('<g>')
    for c in cells:
        cx = GRID_X + c["col"] * PITCH + half
        cy = GRID_Y + c["row"] * PITCH + half
        color = PALETTE[c["level"]]
        d = WAVE_START + WAVE_SPAN * (c["col"] / max(ncols - 1, 1)) + c["row"] * 0.012
        pop_dur = d + POP
        flash_dur = d + 0.7
        anims = [
            f'<animateTransform attributeName="transform" type="scale" values="0;0;1.35;0.9;1" '
            f'keyTimes="{key_times(0, d / pop_dur, (d + 0.2) / pop_dur, (d + 0.32) / pop_dur, 1)}" '
            f'dur="{f(pop_dur)}s" begin="{BEGIN}" fill="freeze"/>',
            f'<animate attributeName="fill" values="{color};{color};{FLASH};{color}" '
            f'keyTimes="{key_times(0, d / flash_dur, (d + 0.12) / flash_dur, 1)}" '
            f'dur="{f(flash_dur)}s" begin="{BEGIN}" fill="freeze"/>',
        ]
        if c["level"] >= 3:
            sd = rng.uniform(2.8, 6.0)
            p = rng.uniform(0.1, 0.8)
            anims.append(
                f'<animate attributeName="fill" values="{color};{color};{SHIMMER};{color};{color}" '
                f'keyTimes="{key_times(0, p, p + 0.08, p + 0.18, 1)}" dur="{f(sd)}s" '
                f'begin="{f(WAVE_START + WAVE_SPAN + 0.8)}s" repeatCount="indefinite"/>')
        svg.append(f'<g transform="translate({f(cx)} {f(cy)})"><rect x="{-half}" y="{-half}" width="{CELL}" '
                   f'height="{CELL}" rx="2" fill="{color}">{"".join(anims)}</rect></g>')
        if c["level"] > 0 and h01(c["date"]) < 0.35:
            glints.append((cx, cy, c["date"]))
    svg.append('</g>')

    # Ghost scan beam: rides with the first wave, then idles off-grid until the next 9s loop.
    beam_w = 46
    x_from, x_to = GRID_X - beam_w - 10, GRID_X + grid_w + 10
    t_sweep = (WAVE_SPAN + 0.3) / BEAM_DUR
    svg.append(
        f'<defs><linearGradient id="beam" x1="0" x2="1"><stop offset="0" stop-color="{GREEN}" stop-opacity="0"/>'
        f'<stop offset="0.75" stop-color="{GREEN}" stop-opacity="0.28"/><stop offset="0.97" stop-color="#d7ffd9" '
        f'stop-opacity="0.55"/><stop offset="1" stop-color="{GREEN}" stop-opacity="0"/></linearGradient></defs>'
        f'<rect x="{-beam_w - 40}" y="{GRID_Y - 6}" width="{beam_w}" height="{7 * PITCH + 9}" fill="url(#beam)" '
        f'clip-path="url(#hm-clip)"><animate attributeName="x" values="{x_from};{x_to};{x_to}" '
        f'keyTimes="{key_times(0, t_sweep, 1)}" dur="{f(BEAM_DUR)}s" begin="{f(WAVE_START - 0.3)}s" '
        f'repeatCount="indefinite"/></rect>')

    # Star glints on a deterministic subset: short flash, long hold.
    star = "M0,-6 L1.3,-1.3 L6,0 L1.3,1.3 L0,6 L-1.3,1.3 L-6,0 L-1.3,-1.3 Z"
    for cx, cy, key in sorted(glints, key=lambda g: h01(g[2] + "s"))[:8]:
        dur = 4.5 + h01(key + "d") * 5
        p = 0.35 + h01(key + "p") * 0.55
        kt = key_times(0, p, p + 0.035, p + 0.09, 1)
        svg.append(
            f'<g transform="translate({f(cx)} {f(cy)})"><path d="{star}" fill="#f0fff0">'
            f'<animate attributeName="opacity" values="0;0;1;0;0" keyTimes="{kt}" dur="{f(dur)}s" '
            f'begin="{BEGIN}" repeatCount="indefinite"/>'
            f'<animateTransform attributeName="transform" type="scale" values="0.2;0.2;1.15;0.2;0.2" keyTimes="{kt}" '
            f'dur="{f(dur)}s" begin="{BEGIN}" repeatCount="indefinite"/></path></g>')

    # Footer: total typing itself out, legend on the right.
    fy = H - 18
    svg.append(f'<text x="{PAD}" y="{fy}" font-family="{MONO}" font-size="12" fill="{GREEN}">$</text>')
    total_text = f'{data["total"]} contributions in the last year'
    typed, _, _ = typed_text(PAD + 14, fy, total_text, start=WAVE_START + WAVE_SPAN + 0.3,
                             per_char=0.045, font_size=12, fill=TEXT)
    svg.append(typed)
    svg.append(moving_cursor(PAD + 14, fy - 10, 7.2, len(total_text), WAVE_START + WAVE_SPAN + 0.3,
                             0.045, 7, 12))

    lx = W - PAD - 5 * PITCH - 34
    svg.append(f'<text x="{lx - 6}" y="{fy}" text-anchor="end" font-family="{MONO}" font-size="10" '
               f'fill="{MUTED}">Less</text>')
    for i, col in enumerate(PALETTE):
        svg.append(f'<rect x="{lx + i * PITCH}" y="{fy - 9}" width="{CELL}" height="{CELL}" rx="2" fill="{col}"/>')
    svg.append(f'<text x="{lx + 5 * PITCH + 3}" y="{fy}" font-family="{MONO}" font-size="10" '
               f'fill="{MUTED}">More</text>')

    svg.append("</svg>")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(svg), encoding="utf-8")
    print(f"wrote {OUT} ({W}x{H}, {len(cells)} cells, {OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
