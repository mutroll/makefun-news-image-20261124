#!/usr/bin/env python3
"""news-image-20261124 (rebuild) -- 'The World in One Day: Tuesday 24 November 2026'.

Draws a 1024x1024 news poster with the Python standard library only.
The scene is rendered into a 2048x2048 framebuffer and box-downscaled
by a factor of two, which anti-aliases every edge and keeps the bold
condensed stroke type legible even at a 300 px viewing width.
Deterministic: no randomness, no clock, no network.
"""

import os
import struct
import zlib

# ---------------------------------------------------------------- canvas

SS = 2048            # supersampled render size
OUT = 1024           # final poster size

INK = (22, 32, 44)
PAPER = (246, 241, 229)
WHITE = (255, 255, 255)
RED = (178, 34, 43)
GREY = (62, 72, 82)

buf = bytearray(SS * SS * 3)


def px(x, y, rgb):
    if 0 <= x < SS and 0 <= y < SS:
        i = (y * SS + x) * 3
        buf[i] = rgb[0]
        buf[i + 1] = rgb[1]
        buf[i + 2] = rgb[2]


def fill_rect(x, y, w, h, rgb):
    x0 = max(0, int(x))
    y0 = max(0, int(y))
    x1 = min(SS, int(x + w))
    y1 = min(SS, int(y + h))
    if x1 <= x0 or y1 <= y0:
        return
    row = bytes(rgb) * (x1 - x0)
    n = len(row)
    for yy in range(y0, y1):
        i = (yy * SS + x0) * 3
        buf[i:i + n] = row


def fill_circle(cx, cy, r, rgb):
    r = int(r)
    cx = int(cx)
    cy = int(cy)
    for yy in range(cy - r, cy + r + 1):
        dy = yy - cy
        rem = r * r - dy * dy
        if rem < 0:
            continue
        dx = int(rem ** 0.5)
        fill_rect(cx - dx, yy, dx * 2 + 1, 1, rgb)


def thick_line(x0, y0, x1, y1, width, rgb):
    """A line drawn as a chain of stamped discs (round caps and joins)."""
    dx = x1 - x0
    dy = y1 - y0
    dist = max(abs(dx), abs(dy))
    steps = max(1, int(dist / max(2.0, width * 0.30)))
    r = width / 2.0
    for s in range(steps + 1):
        t = s / steps
        fill_circle(x0 + dx * t, y0 + dy * t, r, rgb)


def poly(points, width, rgb):
    for a, b in zip(points, points[1:]):
        thick_line(a[0], a[1], b[0], b[1], width, rgb)


def outline_rect(x, y, w, h, width, rgb):
    fill_rect(x, y, w, width, rgb)
    fill_rect(x, y + h - width, w, width, rgb)
    fill_rect(x, y, width, h, rgb)
    fill_rect(x + w - width, y, width, h, rgb)


# ---------------------------------------------------------------- type
# A bold condensed stroke alphabet on a 5 x 7 grid (y grows downward).
# Strokes are drawn thick at supersample resolution, then downscaled,
# so the letterforms stay smooth and readable at small sizes.

GLYPHS = {
    "A": [[(0, 7), (2.5, 0), (5, 7)], [(1.2, 4.6), (3.8, 4.6)]],
    "B": [[(0, 0), (0, 7)], [(0, 0), (2.8, 0), (4, 1.2), (4, 2.3), (2.8, 3.4), (0, 3.4)],
          [(2.8, 3.4), (4.2, 4.4), (4.2, 5.8), (2.8, 7), (0, 7)]],
    "C": [[(4.6, 1.2), (3, 0.2), (1.2, 0.6), (0.2, 2.2), (0.2, 4.8), (1.2, 6.4), (3, 6.8), (4.6, 5.8)]],
    "D": [[(0, 0), (0, 7)], [(0, 0), (2.6, 0), (4.2, 1.6), (4.2, 5.4), (2.6, 7), (0, 7)]],
    "E": [[(4.6, 0), (0, 0), (0, 7), (4.6, 7)], [(0, 3.4), (3.8, 3.4)]],
    "F": [[(4.6, 0), (0, 0), (0, 7)], [(0, 3.4), (3.6, 3.4)]],
    "G": [[(4.6, 1.2), (3, 0.2), (1.2, 0.6), (0.2, 2.2), (0.2, 4.8), (1.2, 6.4), (3, 6.8), (4.6, 6.2), (4.6, 4), (2.8, 4)]],
    "H": [[(0, 0), (0, 7)], [(5, 0), (5, 7)], [(0, 3.5), (5, 3.5)]],
    "I": [[(2.5, 0), (2.5, 7)], [(0.6, 0), (4.4, 0)], [(0.6, 7), (4.4, 7)]],
    "J": [[(4.6, 0), (4.6, 5.4), (3.4, 6.8), (1.4, 6.8), (0.2, 5.6)]],
    "K": [[(0, 0), (0, 7)], [(4.6, 0), (0.4, 3.4)], [(1.6, 2.6), (4.6, 7)]],
    "L": [[(0, 0), (0, 7), (4.6, 7)]],
    "M": [[(0, 7), (0, 0), (2.5, 3.2), (5, 0), (5, 7)]],
    "N": [[(0, 7), (0, 0), (5, 7), (5, 0)]],
    "O": [[(1.2, 0.6), (3, 0), (4.4, 1.4), (4.6, 3.5), (4.4, 5.6), (3, 7), (1.6, 7), (0.4, 5.6), (0.2, 3.5), (0.4, 1.4), (1.2, 0.6)]],
    "P": [[(0, 7), (0, 0), (3, 0), (4.4, 1.2), (4.4, 2.6), (3, 3.8), (0, 3.8)]],
    "Q": [[(1.2, 0.6), (3, 0), (4.4, 1.4), (4.6, 3.5), (4.4, 5.6), (3, 7), (1.6, 7), (0.4, 5.6), (0.2, 3.5), (0.4, 1.4), (1.2, 0.6)],
          [(2.8, 4.8), (4.8, 7.2)]],
    "R": [[(0, 7), (0, 0), (3, 0), (4.4, 1.2), (4.4, 2.6), (3, 3.8), (0, 3.8)], [(2.4, 3.8), (4.6, 7)]],
    "S": [[(4.4, 1.2), (2.8, 0.2), (1, 0.8), (0.6, 2.2), (1.6, 3.2), (3.6, 3.8), (4.4, 5), (3.8, 6.4), (2, 6.9), (0.4, 6)]],
    "T": [[(0, 0), (5, 0)], [(2.5, 0), (2.5, 7)]],
    "U": [[(0, 0), (0, 5.2), (1, 6.6), (3, 6.9), (4.2, 6.4), (5, 5.2), (5, 0)]],
    "V": [[(0, 0), (2.5, 7), (5, 0)]],
    "W": [[(0, 0), (1, 7), (2.5, 2.6), (4, 7), (5, 0)]],
    "X": [[(0, 0), (5, 7)], [(5, 0), (0, 7)]],
    "Y": [[(0, 0), (2.5, 3.2), (5, 0)], [(2.5, 3.2), (2.5, 7)]],
    "Z": [[(0, 0), (5, 0), (0, 7), (5, 7)]],
    "0": [[(1.4, 0.4), (3.2, 0), (4.4, 1.2), (4.6, 3.5), (4.4, 5.8), (3.2, 7), (1.4, 6.6), (0.4, 5.4), (0.2, 3.5), (0.4, 1.6), (1.4, 0.4)]],
    "1": [[(1.2, 1.4), (2.8, 0), (2.8, 7)], [(0.8, 7), (4.4, 7)]],
    "2": [[(0.4, 1.6), (1.2, 0.4), (3, 0.2), (4.4, 1.4), (4.2, 2.8), (0.2, 7), (4.6, 7)]],
    "3": [[(0.4, 1), (1.6, 0.2), (3.4, 0.4), (4.2, 1.6), (3.4, 3), (1.8, 3.2)],
          [(3.4, 3), (4.4, 4.2), (4, 6), (2.6, 6.9), (0.6, 6.2)]],
    "4": [[(3.4, 7), (3.4, 0), (0, 4.8), (5, 4.8)]],
    "5": [[(4.4, 0), (0.6, 0), (0.4, 3), (2.8, 2.8), (4.4, 4.2), (4, 6), (2.4, 6.9), (0.4, 6)]],
    "6": [[(4.2, 1.2), (2.6, 0.2), (1, 1), (0.2, 3.4), (0.4, 5.6), (1.6, 6.8), (3.2, 6.8), (4.4, 5.6), (4.4, 4), (3, 3.2), (0.6, 3.6)]],
    "7": [[(0.2, 0), (4.8, 0), (2.2, 7)]],
    "8": [[(1.6, 3.3), (0.8, 2.6), (0.8, 1.2), (2, 0.2), (3.6, 0.2), (4.4, 1.2), (4.4, 2.6), (3.4, 3.3), (1.6, 3.3)],
          [(1.6, 3.3), (0.6, 4.4), (0.8, 6), (2, 6.9), (3.8, 6.9), (4.6, 6), (4.4, 4.4), (3.4, 3.3)]],
    "9": [[(0.6, 5.8), (2.4, 6.8), (4, 6), (4.8, 3.6), (4.6, 1.4), (3.4, 0.2), (1.8, 0.2), (0.6, 1.4), (0.6, 2.8), (2, 3.8), (4.4, 3.4)]],
    ",": [[(2.8, 6.0), (2.1, 7.4)]],
    ":": [],
    ";": [[(2.8, 6.0), (2.1, 7.4)]],
    "'": [[(2.5, 0), (2.3, 1.6)]],
    "-": [[(0.8, 3.5), (4.2, 3.5)]],
    "+": [[(0.8, 3.5), (4.2, 3.5)], [(2.5, 1.8), (2.5, 5.2)]],
    "/": [[(4.6, 0), (0.4, 7)]],
}

DOTS = {  # punctuation drawn as filled dots: char -> [(gx, gy), ...]
    ".": [(2.5, 6.6)],
    ":": [(2.5, 1.6), (2.5, 5.6)],
    ";": [(2.5, 1.6)],
    "·": [(2.5, 3.5)],
}

XSCALE = 0.72          # horizontal condensation of the letterforms
ADVANCE = 4.4          # glyph advance, in grid units


def text_width(text, cap):
    unit = cap / 7.0
    return len(text) * ADVANCE * unit


def draw_text(x, y, text, cap, rgb):
    """Draw text with its cap-height top at y. Returns the drawn width."""
    unit = cap / 7.0
    width = max(3.0, cap * 0.17)
    cx = float(x)
    for ch in text:
        if ch == "%":
            for (gx, gy) in ((1.05, 1.15), (3.95, 5.85)):
                pts = []
                for k in range(13):
                    ang = k * 0.5236
                    pts.append((cx + (gx + 0.9 * _cos(ang)) * unit * XSCALE,
                                y + (gy + 0.9 * _sin(ang)) * unit))
                poly(pts, width, rgb)
            thick_line(cx + 4.6 * unit * XSCALE, y, cx + 0.4 * unit * XSCALE,
                       y + 7 * unit, width, rgb)
        elif ch in DOTS:
            for (gx, gy) in DOTS[ch]:
                fill_circle(cx + gx * unit * XSCALE, y + gy * unit,
                            width * 0.66, rgb)
        elif ch in GLYPHS:
            for stroke in GLYPHS[ch]:
                pts = [(cx + gx * unit * XSCALE, y + gy * unit)
                       for (gx, gy) in stroke]
                if len(pts) == 1:
                    fill_circle(pts[0][0], pts[0][1], width * 0.66, rgb)
                else:
                    poly(pts, width, rgb)
        cx += ADVANCE * unit
    return cx - x


def _sin(a):
    # tiny deterministic trig table-free helpers (math is stdlib too,
    # but keeping them local makes the intent obvious)
    import math
    return math.sin(a)


def _cos(a):
    import math
    return math.cos(a)


def draw_centered(cx, y, text, cap, rgb):
    w = text_width(text, cap)
    draw_text(cx - w / 2.0, y, text, cap, rgb)
    return w


def wrap(text, cap, max_width):
    """Greedy word wrap using the real advance of the stroke font."""
    lines = []
    cur = ""
    for word in text.split(" "):
        trial = word if not cur else cur + " " + word
        if cur and text_width(trial, cap) > max_width:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- layout

MARGIN = 44
CONTENT_W = SS - 2 * MARGIN


def masthead():
    y = 36
    draw_centered(SS / 2, y, "THE WORLD IN ONE DAY", 44, RED)
    y += 66
    fill_rect(MARGIN, y, CONTENT_W, 6, INK)
    y += 22
    draw_centered(SS / 2, y, "TUESDAY", 190, INK)
    y += 232
    draw_centered(SS / 2, y, "24 NOVEMBER 2026", 88, RED)
    y += 118
    fill_rect(MARGIN, y, CONTENT_W, 6, INK)
    return y + 24


def footer(y):
    fill_rect(MARGIN, y, CONTENT_W, 6, INK)
    y += 22
    draw_text(MARGIN, y, "ALSO TODAY:", 48, RED)
    y += 64
    draw_text(MARGIN, y,
              "FRANCE: OFFICER FACES MURDER TRIAL OVER NAHEL SHOOTING",
              48, INK)
    y += 64
    draw_text(MARGIN, y,
              "UAE CRASH KILLS 11 · SHENZHOU-24 CREW UNVEILED IN CHINA",
              48, INK)
    return y + 66


# ---------------------------------------------------------------- art
# Simple bold flat illustrations, one per panel, drawn inside the
# panel's coloured strip.  All coordinates are relative to the strip.

def art_ukraine(sx, sy, sw, sh):
    dark = (52, 66, 84)
    base = sy + sh
    for i, (bw, bh) in enumerate(((120, 44), (100, 60), (130, 38))):
        bx = sx + 500 + i * 128
        fill_rect(bx, base - bh, bw, bh, dark)
        for wy in range(int(base - bh) + 9, int(base) - 10, 17):
            for wx in range(int(bx) + 11, int(bx + bw) - 13, 24):
                fill_rect(wx, wy, 10, 8, (250, 205, 92))
    # burst over the middle block
    cx, cy = sx + 500 + 128 + 50, base - 52
    for dx, dy in ((-38, -18), (0, -28), (38, -18), (-28, 12), (32, 10)):
        thick_line(cx, cy, cx + dx, cy + dy, 7, (232, 116, 32))
    fill_circle(cx, cy, 12, (245, 166, 35))


def art_gaza(sx, sy, sw, sh):
    base = sy + sh
    ruin = (110, 96, 84)
    heights = (40, 58, 28, 48, 22, 42)
    x = sx + 440
    for i, hh in enumerate(heights):
        bw = 72 if i % 2 == 0 else 56
        fill_rect(x, base - hh, bw, hh, ruin)
        if i % 3 == 1:  # a leaning, broken slab
            thick_line(x + 6, base - hh, x + bw - 12, base - hh + 16, 8, ruin)
        x += bw + 14
    for i in range(3):  # smoke
        fill_circle(sx + 520 + i * 120, sy + 18 - (i % 2) * 5, 12 - i, (168, 160, 148))
        fill_circle(sx + 538 + i * 120, sy + 27 - (i % 2) * 5, 9 - i, (178, 170, 158))


def art_solomons(sx, sy, sw, sh):
    green = (58, 138, 84)
    cy = sy + sh * 0.60
    for cx, r in ((sx + sw * 0.60, 44), (sx + sw * 0.66, 32), (sx + sw * 0.86, 38), (sx + sw * 0.91, 26)):
        fill_circle(cx, cy, r * 0.52, green)
        fill_circle(cx - r * 0.5, cy + 3, r * 0.36, green)
        fill_circle(cx + r * 0.5, cy + 3, r * 0.36, green)
    # a bold arrow of change sweeping between the two island groups
    pts = [(sx + sw * (0.66 + t * 0.14), cy - 34 + 22 * (t - 0.5) ** 2 * 4 - 22)
           for t in (0.0, 0.25, 0.5, 0.75, 1.0)]
    poly(pts, 9, WHITE)
    hx, hy = pts[-1]
    poly([(hx - 20, hy - 3), (hx + 3, hy + 1), (hx - 15, hy + 15)], 9, WHITE)


def art_markets(sx, sy, sw, sh):
    base = sy + sh - 8
    green = (34, 139, 76)
    for i, bh in enumerate((16, 26, 36, 50)):
        fill_rect(sx + 500 + i * 104, base - bh, 62, bh, green)
    pts = [(sx + 520, base - 30), (sx + 624, base - 42), (sx + 728, base - 40),
           (sx + 850, base - 62)]
    poly(pts, 10, RED)
    hx, hy = pts[-1]
    poly([(hx - 28, hy + 2), (hx + 5, hy - 3), (hx - 5, hy + 24)], 10, RED)


def art_health(sx, sy, sw, sh):
    cx, cy = sx + 610, sy + sh / 2
    for k in range(8):
        ang = k * 0.7854
        x2 = cx + 38 * _cos(ang)
        y2 = cy + 38 * _sin(ang)
        thick_line(cx, cy, x2, y2, 7, RED)
        fill_circle(x2, y2, 7, RED)
    fill_circle(cx, cy, 25, RED)
    fill_circle(cx - 8, cy - 7, 5, WHITE)
    fill_circle(cx + 9, cy + 5, 4, WHITE)
    # medical cross badge
    bx, by = sx + sw - 90, cy
    fill_circle(bx, by, 27, (34, 120, 160))
    fill_rect(bx - 6, by - 16, 12, 32, WHITE)
    fill_rect(bx - 16, by - 6, 32, 12, WHITE)


def art_hanoi(sx, sy, sw, sh):
    base = sy + sh
    dark = (88, 74, 60)
    fill_rect(sx + 500, base - 46, 150, 46, dark)
    fill_rect(sx + 770, base - 36, 130, 36, dark)
    for wx in range(int(sx) + 516, int(sx) + 624, 28):
        fill_rect(wx, base - 34, 12, 10, (250, 205, 92))
    cx, cy = sx + sw * 0.76, sy + sh * 0.40
    for dx, dy in ((-46, 0), (46, 0), (0, -24), (0, 22), (-34, -17), (34, -17), (-34, 16), (34, 16)):
        thick_line(cx, cy, cx + dx, cy + dy, 8, (232, 116, 32))
    fill_circle(cx, cy, 14, (245, 166, 35))
    for i in range(3):
        fill_circle(cx + 66 + i * 30, cy - 18 - i * 4, 11 - i * 2, (168, 158, 146))


PANELS = [
    {
        "tag": "CONFLICT · UKRAINE",
        "head": "RUSSIA HITS ZAPORIZHZHIA",
        "sub": "OVERNIGHT ATTACK: 2 DEAD, 22 WOUNDED",
        "accent": (178, 34, 43),
        "strip": (203, 216, 230),
        "art": art_ukraine,
    },
    {
        "tag": "CONFLICT · GAZA",
        "head": "ISRAELI STRIKE KILLS 3 IN GAZA",
        "sub": "NEAR KHAN YOUNIS POLICE POST, MEDICS SAY",
        "accent": (146, 64, 32),
        "strip": (233, 221, 197),
        "art": art_gaza,
    },
    {
        "tag": "DIPLOMACY · PACIFIC",
        "head": "SOLOMONS END CHINA PACT",
        "sub": "CANBERRA TREATY TO REPLACE 2022 BEIJING PACT",
        "accent": (24, 110, 122),
        "strip": (170, 206, 222),
        "art": art_solomons,
    },
    {
        "tag": "MARKETS · ASIA",
        "head": "ASIA STOCKS JUMP ON TECH RALLY",
        "sub": "KOSPI +6.3%, NIKKEI +4% IN BROAD TECH SURGE",
        "accent": (34, 120, 70),
        "strip": (222, 238, 224),
        "art": art_markets,
    },
    {
        "tag": "HEALTH · PENNSYLVANIA",
        "head": "9TH MEASLES DEATH REPORTED",
        "sub": "OUTBREAK TOPS 1,600 CASES ACROSS 46 COUNTIES",
        "accent": (150, 40, 90),
        "strip": (248, 226, 232),
        "art": art_health,
    },
    {
        "tag": "DISASTER · VIETNAM",
        "head": "HANOI EXPLOSION KILLS 6",
        "sub": "10 HURT IN 8 AM BLAST AT FOOD SHOP IN DONG DA",
        "accent": (196, 110, 20),
        "strip": (240, 228, 204),
        "art": art_hanoi,
    },
]


def draw_panels(top, bottom):
    gap = 22
    rows = 3
    ph = (bottom - top - gap * (rows - 1)) / rows
    pw = (CONTENT_W - gap) / 2
    for i, panel in enumerate(PANELS):
        r, c = divmod(i, 2)
        x = MARGIN + c * (pw + gap)
        y = top + r * (ph + gap)
        draw_panel(x, y, pw, ph, panel)


def draw_panel(x, y, w, h, panel):
    fill_rect(x, y, w, h, WHITE)
    outline_rect(x, y, w, h, 5, INK)
    accent = panel["accent"]
    # illustration strip
    sx, sy, sw, sh = x + 26, y + 18, w - 52, 72
    fill_rect(sx, sy, sw, sh, panel["strip"])
    if panel.get("art"):
        panel["art"](sx, sy, sw, sh)
    # category tag pill over the strip's top-left corner
    tag = panel["tag"]
    tw = text_width(tag, 34) + 40
    fill_rect(sx + 12, sy + 13, tw, 46, accent)
    draw_text(sx + 32, sy + 19, tag, 34, WHITE)
    # headline
    ty = sy + sh + 14
    for line in wrap(panel["head"], 76, w - 72):
        draw_text(x + 36, ty, line, 76, INK)
        ty += 90
    # sub-line
    ty += 2
    for line in wrap(panel["sub"], 54, w - 72):
        draw_text(x + 36, ty, line, 54, GREY)
        ty += 64


# ---------------------------------------------------------------- png out

def downscale():
    """Box-downscale the 2048 buffer to 1024 (2x2 average)."""
    out = bytearray(OUT * OUT * 3)
    for oy in range(OUT):
        r0 = (oy * 2) * SS * 3
        r1 = r0 + SS * 3
        a = bytes(buf[r0:r0 + SS * 3])
        b = bytes(buf[r1:r1 + SS * 3])
        base = oy * OUT * 3
        for ch in range(3):
            s0 = a[ch::3]
            s1 = b[ch::3]
            vals = bytes((s0[i] + s0[i + 1] + s1[i] + s1[i + 1]) // 4
                         for i in range(0, SS, 2))
            out[base + ch:base + OUT * 3:3] = vals
    return bytes(out)


def write_png(path, pixels):
    raw = bytearray()
    stride = OUT * 3
    for yy in range(OUT):
        raw.append(0)
        raw += pixels[yy * stride:(yy + 1) * stride]

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", OUT, OUT, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 6))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as fh:
        fh.write(png)


def main():
    fill_rect(0, 0, SS, SS, PAPER)
    top = masthead()
    bottom = SS - 270
    draw_panels(top, bottom)
    footer(bottom + 18)
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    write_png(os.path.join(out_dir, "entry.png"), downscale())


if __name__ == "__main__":
    main()
