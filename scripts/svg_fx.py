"""Shared SMIL-only SVG helpers for the profile art.

Rules every effect here follows (GitHub serves README images through camo,
where CSS @keyframes inside an SVG never run):
  * animate only with <animate>/<animateTransform>;
  * an element's static attributes are its finished, visible state;
  * hidden-at-first states exist only inside a running animation;
  * timelines start at begin="0.01s", never 0, so a cached image whose clock is
    paused at t=0 shows the static (visible) state instead of a hidden first value.
"""
import math
import random

BEGIN = "0.01s"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'DejaVu Sans Mono','Liberation Mono',monospace"

BG = "#0d1117"
BORDER = "#30363d"
TITLEBAR = "#161b22"
TEXT = "#c9d1d9"
MUTED = "#8b949e"
GREEN = "#39d353"

# Half-width katakana, digits and a few safe symbols: nothing that needs XML escaping.
RAIN_GLYPHS = [chr(c) for c in range(0xFF66, 0xFF9E)] + list("0123456789Z:=+*-")


def f(x):
    """Compact number formatting."""
    s = f"{x:.3f}".rstrip("0").rstrip(".")
    return s if s not in ("-0", "") else "0"


def key_times(*ts):
    return ";".join(f(min(max(t, 0.0), 1.0)) for t in ts)


def window(x, y, w, h, title, clip_id, radius=10, bar=30):
    """Panel background, macOS titlebar dots and a clip path for the body."""
    parts = [
        f'<defs><clipPath id="{clip_id}"><rect x="{x}" y="{y + bar}" width="{w}" height="{h - bar}" '
        f'rx="{radius}"/></clipPath></defs>',
        f'<rect x="{x + .5}" y="{y + .5}" width="{w - 1}" height="{h - 1}" rx="{radius}" fill="{BG}" stroke="{BORDER}"/>',
        f'<path d="M{x + radius},{y + .5} H{x + w - radius} A{radius - .5},{radius - .5} 0 0 1 {x + w - .5},{y + radius} '
        f'V{y + bar} H{x + .5} V{y + radius} A{radius - .5},{radius - .5} 0 0 1 {x + radius},{y + .5} Z" fill="{TITLEBAR}"/>',
        f'<line x1="{x + 1}" y1="{y + bar}" x2="{x + w - 1}" y2="{y + bar}" stroke="{BORDER}"/>',
    ]
    for i, c in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        parts.append(f'<circle cx="{x + 18 + i * 18}" cy="{y + bar / 2}" r="5.5" fill="{c}"/>')
    parts.append(f'<text x="{x + w / 2}" y="{y + bar / 2 + 4}" text-anchor="middle" font-family="{MONO}" '
                 f'font-size="12" fill="{MUTED}">{title}</text>')
    return "\n".join(parts)


def matrix_rain(x, y, w, h, clip_id, seed, col_w=14, line_h=14, tick=0.12, opacity=0.32):
    """Full-panel falling-glyph background, clipped to the panel body.

    Every column steps with calcMode="discrete" on one shared tick, so the whole
    rain repaints once per tick instead of every frame. Columns share the same
    duration and step count; each just starts its value list at a different
    phase, which keeps them desynchronised without any delayed begin.
    """
    rng = random.Random(seed)
    cols = int(w // col_w)
    trail_max = 10
    steps = math.ceil(h / line_h) + trail_max + 6
    dur = f(steps * tick)
    out = [f'<g clip-path="url(#{clip_id})" opacity="{opacity}" font-family="{MONO}" font-size="12" text-anchor="middle">']
    for c in range(cols):
        trail = rng.randint(5, trail_max)
        cx = x + col_w / 2 + c * col_w + (w - cols * col_w) / 2
        phase = rng.randrange(steps)
        top = y - trail * line_h
        offsets = [((k + phase) % steps) * line_h for k in range(steps)]
        values = ";".join(f"0 {o}" for o in offsets)
        spans = []
        for i in range(trail):
            g = rng.choice(RAIN_GLYPHS)
            if i == trail - 1:
                fill, op = "#d7ffd9", 1
            else:
                fill, op = "#00ff41", f(0.15 + 0.85 * (i + 1) / trail)
            spans.append(f'<tspan x="{f(cx)}" dy="{line_h}" fill="{fill}" fill-opacity="{op}">{g}</tspan>')
        out.append(
            f'<text y="{f(top)}" transform="translate(0 {offsets[0]})">{"".join(spans)}'
            f'<animateTransform attributeName="transform" type="translate" calcMode="discrete" '
            f'values="{values}" dur="{dur}s" begin="{BEGIN}" repeatCount="indefinite"/></text>'
        )
    out.append("</g>")
    return "\n".join(out)


def blink_cursor(x, y, w, h, fill=GREEN, period=1.06):
    """Block cursor. Static opacity is 0: it is only ever visible while SMIL runs,
    which makes it the canary for 'is the animation actually playing'."""
    return (f'<rect x="{f(x)}" y="{f(y)}" width="{w}" height="{h}" fill="{fill}" opacity="0">'
            f'<animate attributeName="opacity" values="1;0" calcMode="discrete" dur="{period}s" '
            f'begin="{BEGIN}" repeatCount="indefinite"/></rect>')


def typed_text(x, y, text, start, per_char, font_size, fill, char_w=None, extra=""):
    """Text that types itself out, one tspan per character.

    Each character's static fill-opacity is 1 (fully typed); its animation holds
    it at 0 until its turn. textLength pins the advance width so a cursor placed
    at x + len*char_w lines up regardless of which monospace font the viewer has.
    Returns (svg, end_x, end_time).
    """
    char_w = char_w or font_size * 0.6
    spans = []
    for i, ch in enumerate(text):
        t = start + i * per_char
        dur = t + 0.05
        spans.append(
            f'<tspan>{ch}<animate attributeName="fill-opacity" values="0;0;1" '
            f'keyTimes="{key_times(0, t / dur, 1)}" dur="{f(dur)}s" begin="{BEGIN}" fill="freeze"/></tspan>'
        )
    length = len(text) * char_w
    svg = (f'<text x="{f(x)}" y="{f(y)}" font-family="{MONO}" font-size="{font_size}" fill="{fill}" '
           f'textLength="{f(length)}" lengthAdjust="spacingAndGlyphs" xml:space="preserve"{extra}>{"".join(spans)}</text>')
    return svg, x + length, start + len(text) * per_char


def moving_cursor(x0, y, char_w, n, start, per_char, w, h, fill=GREEN):
    """Blinking cursor that rides along with typed_text, ending after the last char."""
    xs = [x0 + i * char_w for i in range(n + 1)]
    end = start + n * per_char
    dur = end + 0.01
    times = [0] + [(start + i * per_char) / dur for i in range(n + 1)]
    values = [xs[0]] + xs
    return (f'<rect x="{f(xs[-1] + 2)}" y="{f(y)}" width="{w}" height="{h}" fill="{fill}" opacity="0">'
            f'<animate attributeName="x" calcMode="discrete" values="{";".join(f(v + 2) for v in values)}" '
            f'keyTimes="{key_times(*times)}" dur="{f(dur)}s" begin="{BEGIN}" fill="freeze"/>'
            f'<animate attributeName="opacity" values="1;0" calcMode="discrete" dur="1.06s" '
            f'begin="{BEGIN}" repeatCount="indefinite"/></rect>')
