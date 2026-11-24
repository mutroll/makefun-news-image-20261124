#!/usr/bin/env python3
"""news-image-20261124: poster of Tuesday 24 November 2026 world news.

Draws a 1024x1024 newspaper poster with a pure-Python PNG encoder
(standard library only: zlib, struct, math, os). Deterministic: no
clock, no randomness, no network, no files read. Writes entry.png to
/output (or $MAKEFUN_OUTPUT_DIR).

Six stories, each verified as a 24 November 2026 event (happened or
first reported that day in some time zone, or scheduled for that day
and labelled as happening today):
  1. Russian drone briefly enters Polish airspace in a night attack
     on western Ukraine (Reuters, Nov 24).
  2. FIFA confirms the 2031 and 2035 Women's World Cup hosts at its
     Extraordinary Congress, held Tuesday 24 Nov (NZT): a USA-led
     bid gets 2031, the UK gets 2035.
  3. World Chess Championship Game 1 begins today in Geneva:
     Gukesh defends the crown against Sindarov (15:00 CET).
  4. The Beaver Supermoon peaks today at 14:53 UTC, near the
     Pleiades - the first supermoon since January.
  5. Oxfam / CEOBS report: the war has left Gaza's soil, air and
     water toxic for decades (reported across Asia on 24 Nov).
  6. Nvidia's board brings Jensen Huang back as CEO; the shares
     surge about a third (reported in 24 Nov morning papers).
"""
import math
import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER = (247, 243, 230)
PAPER2 = (238, 232, 214)
NAVY = (18, 36, 70)
NAVY2 = (10, 22, 46)
GOLD = (198, 158, 38)
GOLD_L = (226, 196, 96)
INK = (24, 24, 24)
WHITE = (255, 255, 255)
MUTE = (96, 104, 116)
RED = (178, 44, 44)
GREEN = (46, 125, 50)
GREEN_L = (120, 190, 95)
TEAL = (16, 122, 120)
SKY = (146, 196, 228)
SKY_D = (38, 74, 110)
NIGHT = (12, 20, 44)
MOON = (250, 240, 205)
CRATER = (214, 198, 150)
PITCH = (46, 125, 62)
PITCH2 = (36, 100, 50)
BROWN = (122, 84, 52)
SAND = (205, 178, 130)
TOXIC = (120, 180, 40)
GREY = (150, 150, 148)
SMOKE = (120, 120, 118)

# ------------------------------------------------------------- 5x7 glyphs
# One glyph per character: 7 rows of 5 cells, "#" = ink. Authored here
# from the shapes of the letters themselves.
GLYPHS = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "+": ("00000", "00100", "00100", "01110", "00100", "00100", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "*": ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
}


def glyph_width(text, scale):
    """Pixel width of text at the given scale (1 blank column per glyph)."""
    return len(text) * 6 * scale - scale if text else 0


class Poster:
    """An RGB pixel buffer with small drawing helpers."""

    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.buf = bytearray(w * h * 3)
        self.cx0, self.cy0, self.cx1, self.cy1 = 0, 0, w, h
        self.fill(0, 0, w, h, bg)

    def set_clip(self, x, y, w, h):
        self.cx0, self.cy0 = max(0, x), max(0, y)
        self.cx1, self.cy1 = min(self.w, x + w), min(self.h, y + h)

    def clear_clip(self):
        self.cx0, self.cy0, self.cx1, self.cy1 = 0, 0, self.w, self.h

    def px(self, x, y, c):
        if self.cx0 <= x < self.cx1 and self.cy0 <= y < self.cy1:
            i = (y * self.w + x) * 3
            self.buf[i], self.buf[i + 1], self.buf[i + 2] = c

    def fill(self, x, y, w, h, c):
        x0, y0 = max(self.cx0, x), max(self.cy0, y)
        x1, y1 = min(self.cx1, x + w), min(self.cy1, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.buf[i], self.buf[i + 1], self.buf[i + 2] = c

    def hline(self, x, y, w, c, t=1):
        self.fill(x, y, w, t, c)

    def vline(self, x, y, h, c, t=1):
        self.fill(x, y, t, h, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err, x, y = dx - dy, x0, y0
        while True:
            self.fill(x - t // 2, y - t // 2, t, t, c)
            if x == x1 and y == y1:
                return
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

    def disc(self, cx, cy, r, c):
        for yy in range(cy - r, cy + r + 1):
            half = int(math.sqrt(max(0, r * r - (yy - cy) ** 2)))
            self.fill(cx - half, yy, half * 2 + 1, 1, c)

    def ring(self, cx, cy, r, c, t=2):
        for yy in range(cy - r, cy + r + 1):
            dx = int(math.sqrt(max(0, r * r - (yy - cy) ** 2)))
            self.fill(cx - dx, yy, t, 1, c)
            self.fill(cx + dx - t + 1, yy, t, 1, c)
        for xx in range(cx - r, cx + r + 1):
            dy = int(math.sqrt(max(0, r * r - (xx - cx) ** 2)))
            self.fill(xx, cy - dy, 1, t, c)
            self.fill(xx, cy + dy - t + 1, 1, t, c)

    def tri(self, x0, y0, x1, y1, x2, y2, c):
        ymin, ymax = min(y0, y1, y2), max(y0, y1, y2)
        for yy in range(ymin, ymax + 1):
            xs = []
            for (ax, ay, bx, by) in ((x0, y0, x1, y1), (x1, y1, x2, y2),
                                     (x2, y2, x0, y0)):
                if ay == by:
                    continue
                if min(ay, by) <= yy < max(ay, by):
                    xs.append(ax + (yy - ay) * (bx - ax) / (by - ay))
            if len(xs) >= 2:
                self.fill(int(min(xs)), yy, int(max(xs)) - int(min(xs)) + 1, 1, c)

    def text(self, x, y, s, scale, c, align="left", heavy=False):
        """Draw ASCII text; y is the top row. Returns the drawn width."""
        if align == "center":
            x -= glyph_width(s, scale) // 2
        elif align == "right":
            x -= glyph_width(s, scale)
        extra = (0, max(1, scale // 3)) if heavy else (0,)
        for ox in extra:
            cx = x + ox
            for ch in s:
                g = GLYPHS.get(ch.upper(), GLYPHS[" "])
                for row in range(7):
                    bits = g[row]
                    for col in range(5):
                        if bits[col] == "1":
                            self.fill(cx + col * scale, y + row * scale,
                                      scale, scale, c)
                cx += 6 * scale
        return glyph_width(s, scale)

    def wrapped(self, x, y, s, scale, c, max_w, leading):
        """Word-wrap text inside max_w; returns the y after the last line."""
        words, lines, cur = s.split(" "), [], ""
        for wd in words:
            trial = (cur + " " + wd).strip()
            if glyph_width(trial, scale) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = wd
        if cur:
            lines.append(cur)
        for ln in lines:
            self.text(x, y, ln, scale, c)
            y += leading
        return y


def chunk(kind, data):
    body = kind + data
    return (struct.pack(">I", len(data)) + body +
            struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF))


def write_png(poster, path):
    raw = bytearray()
    for yy in range(poster.h):
        raw.append(0)
        raw += poster.buf[yy * poster.w * 3:(yy + 1) * poster.w * 3]
    ihdr = struct.pack(">IIBBBBB", poster.w, poster.h, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
           chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


# ------------------------------------------------------------------- panels
# Each panel: picture band (top), headline, body lines. Geometry:
# panel w=322, picture h=180, headline scale 3, body scale 2.

def panel_frame(p, x, y, w, h, accent):
    p.fill(x, y, w, h, WHITE)
    p.fill(x, y, w, 5, accent)
    for t in range(2):
        p.hline(x, y + t, w, INK)
        p.hline(x, y + h - 1 - t, w, INK)
        p.vline(x + t, y, h, INK)
        p.vline(x + w - 1 - t, y, h, INK)


def panel_text(p, x, y, w, tag, head, body, accent):
    """Tag line, headline (scale 3) and body (scale 2) under the picture."""
    ty = y + 186
    p.text(x + 12, ty, tag, 2, accent, heavy=True)
    hy = ty + 22
    hy = p.wrapped(x + 12, hy, head, 3, INK, w - 24, 26)
    p.wrapped(x + 12, hy + 4, body, 2, MUTE, w - 24, 17)


def art_drone(p, x, y, w, h):
    """Night sky over Ukraine, a drone crossing a dashed border."""
    p.fill(x, y, w, h, NIGHT)
    for sx, sy in ((30, 26), (90, 60), (150, 18), (210, 48), (260, 22),
                   (60, 96), (180, 88), (290, 90), (120, 40)):
        p.disc(x + sx, y + sy, 2, WHITE)
    # radar arcs bottom-left
    for r in (34, 58, 82):
        p.ring(x + 40, y + h - 10, r, TEAL, 2)
    p.line(x + 40, y + h - 10, x + 40 + 58, y + h - 10 - 58, TEAL, 2)
    # dashed border, vertical, with Polish flag marker
    for yy in range(y + 8, y + h - 8, 14):
        p.fill(x + 210, yy, 4, 8, GOLD)
    p.fill(x + 196, y + 20, 32, 12, WHITE)
    p.fill(x + 196, y + 32, 32, 12, RED)
    # drone: light-grey body, four arms, red light (visible on night sky)
    dx, dy = x + 150, y + 70
    p.fill(dx - 26, dy - 4, 52, 8, (170, 170, 170))
    p.fill(dx - 6, dy - 12, 12, 24, (120, 120, 120))
    p.fill(dx - 34, dy - 10, 10, 3, WHITE)
    p.fill(dx + 24, dy - 10, 10, 3, WHITE)
    p.fill(dx - 34, dy + 7, 10, 3, WHITE)
    p.fill(dx + 24, dy + 7, 10, 3, WHITE)
    p.disc(dx, dy, 4, RED)
    # ground silhouette
    p.fill(x, y + h - 26, w, 26, (8, 14, 30))
    p.tri(x + 30, y + h - 26, x + 70, y + h - 26, x + 50, y + h - 52, (8, 14, 30))
    p.tri(x + 230, y + h - 26, x + 290, y + h - 26, x + 260, y + h - 58, (8, 14, 30))


def art_worldcup(p, x, y, w, h):
    """Green pitch, a ball and a gold cup, two small flags."""
    p.fill(x, y, w, h, PITCH)
    for i in range(0, w, 44):
        p.fill(x + i, y, 22, h, PITCH2)
    p.hline(x, y + h // 2, w, WHITE, 3)
    p.ring(x + w // 2, y + h // 2, 34, WHITE, 3)
    p.fill(x + 8, y + 8, w - 16, 3, WHITE)
    p.fill(x + 8, y + h - 11, w - 16, 3, WHITE)
    # football
    bx, by = x + 78, y + 88
    p.disc(bx, by, 30, WHITE)
    p.disc(bx, by, 30, WHITE)
    p.disc(bx - 8, by - 8, 6, INK)
    p.disc(bx + 12, by + 6, 5, INK)
    p.disc(bx - 2, by + 14, 5, INK)
    p.disc(bx + 8, by - 14, 4, INK)
    # gold trophy
    tx, ty = x + 218, y + 46
    p.fill(tx - 26, ty, 52, 10, GOLD)
    p.fill(tx - 20, ty + 10, 40, 26, GOLD_L)
    p.fill(tx - 6, ty + 36, 12, 22, GOLD)
    p.fill(tx - 20, ty + 58, 40, 8, GOLD)
    p.fill(tx - 30, ty + 2, 8, 18, GOLD)
    p.fill(tx + 22, ty + 2, 8, 18, GOLD)
    # small flags: USA stripes, UK cross
    fx, fy = x + 196, y + 128
    for i in range(5):
        p.fill(fx, fy + i * 6, 44, 3, RED if i % 2 == 0 else WHITE)
    p.fill(fx, fy, 18, 16, NAVY)
    ux, uy = x + 250, y + 128
    p.fill(ux, uy, 44, 30, NAVY)
    p.fill(ux + 18, uy, 8, 30, WHITE)
    p.fill(ux, uy + 11, 44, 8, WHITE)
    p.fill(ux + 20, uy, 4, 30, RED)
    p.fill(ux, uy + 13, 44, 4, RED)


def art_chess(p, x, y, w, h):
    """Checkerboard with a white king and a black king facing off."""
    p.fill(x, y, w, h, SAND)
    sq = 40
    ox, oy = x + 22, y + 14
    for r in range(4):
        for c in range(4):
            if (r + c) % 2 == 0:
                p.fill(ox + c * sq, oy + r * sq, sq, sq, (240, 222, 190))
            else:
                p.fill(ox + c * sq, oy + r * sq, sq, sq, (96, 64, 40))
    for t in range(2):
        p.hline(ox, oy + t, 160, INK)
        p.hline(ox, oy + 160 - 1 - t, 160, INK)
        p.vline(ox + t, oy, 160, INK)
        p.vline(ox + 160 - 1 - t, oy, 160, INK)
    # white king (left), black king (right)
    kx, ky = x + 210, y + 40
    p.fill(kx + 8, ky + 44, 44, 10, WHITE)
    p.fill(kx + 14, ky + 10, 32, 34, WHITE)
    p.tri(kx + 14, ky + 12, kx + 30, ky - 8, kx + 46, ky + 12, WHITE)
    p.disc(kx + 30, ky - 8, 4, GOLD)
    p.fill(kx + 27, ky - 18, 6, 10, GOLD)
    bx, by = x + 262, y + 96
    p.fill(bx + 8, by + 44, 44, 10, INK)
    p.fill(bx + 14, by + 10, 32, 34, INK)
    p.tri(bx + 14, by + 12, bx + 30, by - 8, bx + 46, by + 12, INK)
    p.disc(bx + 30, by - 8, 4, GOLD)
    p.fill(bx + 27, by - 18, 6, 10, GOLD)


def art_moon(p, x, y, w, h):
    """Beaver Supermoon over a dark horizon, Pleiades beside it."""
    p.fill(x, y, w, h, NIGHT)
    for sx, sy, r in ((28, 24, 2), (70, 48, 1), (120, 20, 2), (280, 60, 2),
                      (250, 26, 1), (40, 90, 1), (300, 110, 2), (150, 96, 1)):
        p.disc(x + sx, y + sy, r, WHITE)
    # Pleiades cluster, upper right
    for px, py, r in ((252, 34, 3), (268, 28, 2), (280, 40, 3), (262, 48, 2),
                      (246, 50, 2), (274, 56, 2), (258, 62, 1)):
        p.disc(x + px, y + py, r, WHITE)
    # the moon
    mx, my, mr = x + 118, y + 92, 58
    p.disc(mx, my, mr, MOON)
    p.disc(mx - 22, my - 14, 10, CRATER)
    p.disc(mx + 18, my + 6, 13, CRATER)
    p.disc(mx + 4, my - 28, 7, CRATER)
    p.disc(mx - 6, my + 24, 8, CRATER)
    p.disc(mx + 28, my - 22, 5, CRATER)
    # horizon with pines
    p.fill(x, y + h - 22, w, 22, (6, 12, 26))
    for tx in (36, 70, 230, 268, 296):
        p.tri(x + tx, y + h - 22, x + tx + 22, y + h - 22,
              x + tx + 11, y + h - 56, (6, 12, 26))


def art_gaza(p, x, y, w, h):
    """Cracked, poisoned ground under a smoke sky; warning triangle."""
    p.fill(x, y, w, h, (196, 188, 168))
    # smoke puffs
    for sx, sy, r in ((50, 34, 16), (90, 24, 20), (140, 36, 14),
                      (230, 30, 18), (270, 40, 12)):
        p.disc(x + sx, y + sy, r, SMOKE)
    # cracked earth
    p.fill(x, y + 78, w, h - 78, BROWN)
    p.line(x + 20, y + 78, x + 90, y + 130, (70, 46, 26), 3)
    p.line(x + 90, y + 130, x + 60, y + h - 6, (70, 46, 26), 3)
    p.line(x + 200, y + 78, x + 160, y + 140, (70, 46, 26), 3)
    p.line(x + 160, y + 140, x + 230, y + h - 10, (70, 46, 26), 3)
    p.line(x + 120, y + 78, x + 130, y + 120, (70, 46, 26), 2)
    # toxic pools
    p.disc(x + 250, y + 140, 16, TOXIC)
    p.disc(x + 60, y + 160, 12, TOXIC)
    # warning triangle with exclamation (point up)
    tx, ty = x + 138, y + 84
    p.tri(tx + 46, ty, tx, ty + 66, tx + 92, ty + 66, (255, 214, 0))
    p.fill(tx + 43, ty + 18, 6, 26, INK)
    p.fill(tx + 43, ty + 50, 6, 6, INK)
    # water drop, contaminated
    dx, dy = x + 268, y + 96
    p.disc(dx, dy, 12, (40, 110, 180))
    p.tri(dx - 12, dy - 2, dx + 12, dy - 2, dx, dy - 26, (40, 110, 180))
    p.disc(dx - 4, dy + 2, 3, WHITE)


def art_nvidia(p, x, y, w, h):
    """A chip and a steeply rising chart on a dark board."""
    p.fill(x, y, w, h, NAVY2)
    # grid
    for gx in range(x + 20, x + w - 10, 40):
        p.vline(gx, y + 10, h - 20, (28, 48, 84), 1)
    for gy in range(y + 16, y + h - 10, 30):
        p.hline(x + 10, gy, w - 20, (28, 48, 84), 1)
    # chip, left
    cx, cy = x + 34, y + 96
    for i in range(5):
        p.fill(cx - 8, cy + 8 + i * 10, 8, 4, GOLD)
        p.fill(cx + 52, cy + 8 + i * 10, 8, 4, GOLD)
    p.fill(cx, cy, 52, 52, (16, 28, 56))
    p.fill(cx + 4, cy + 4, 44, 44, (30, 52, 96))
    p.text(cx + 12, cy + 16, "NV", 3, (118, 200, 90), heavy=True)
    # rising chart, right
    pts = [(x + 110, y + 150), (x + 150, y + 138), (x + 180, y + 142),
           (x + 215, y + 108), (x + 250, y + 96), (x + 290, y + 52)]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        p.line(ax, ay, bx, by, (118, 200, 90), 4)
    for (px, py) in pts:
        p.disc(px, py, 4, (118, 200, 90))
    # arrow head at the top
    p.line(x + 290, y + 52, x + 272, y + 56, (118, 200, 90), 4)
    p.line(x + 290, y + 52, x + 286, y + 72, (118, 200, 90), 4)
    p.text(x + 108, y + 22, "+33%", 4, (118, 200, 90), heavy=True)


# ------------------------------------------------------------------- build
PANELS = [
    ("CONFLICT", "DRONE STRAYS INTO POLAND",
     "A Russian drone briefly enters Polish airspace during a night attack on western Ukraine.",
     art_drone, RED),
    ("SPORT", "WORLD CUP HOSTS NAMED",
     "FIFA: a USA-led bid gets 2031, the UK gets 2035 - its first World Cup since 1966.",
     art_worldcup, GREEN),
    ("CHESS", "TITLE MATCH BEGINS TODAY",
     "Gukesh defends the crown against Sindarov in Geneva. Game 1 at 15:00 CET, Sindarov White.",
     art_chess, NAVY),
    ("SKY", "BEAVER SUPERMOON TONIGHT",
     "The full moon peaks at 14:53 UTC, near the Pleiades - the first supermoon since January.",
     art_moon, SKY_D),
    ("MIDDLE EAST", "GAZA'S LAND POISONED",
     "Report: the war has left Gaza's soil, air and water toxic for decades to come.",
     art_gaza, BROWN),
    ("TECH", "HUANG IS BACK AT NVIDIA",
     "The board reinstates Jensen Huang as CEO; the shares surge about a third.",
     art_nvidia, TEAL),
]


def build():
    p = Poster(W, H, PAPER)
    # outer frame
    for t in range(4):
        p.hline(t, t, W - 2 * t, INK)
        p.hline(t, H - 1 - t, W - 2 * t, INK)
        p.vline(t, t, H - 2 * t, INK)
        p.vline(W - 1 - t, t, H - 2 * t, INK)

    # masthead
    p.fill(8, 8, W - 16, 150, NAVY)
    p.fill(8, 8, W - 16, 4, GOLD)
    p.fill(8, 154, W - 16, 4, GOLD)
    p.text(W // 2, 22, "THE WORLD IN ONE DAY", 3, GOLD_L, align="center")
    p.text(W // 2, 52, "TUESDAY", 5, WHITE, align="center", heavy=True)
    p.text(W // 2, 96, "24 NOVEMBER 2026", 7, GOLD_L, align="center", heavy=True)

    # panels: 3 columns x 2 rows
    px0, py0, gap = 16, 172, 12
    pw = (W - 2 * px0 - 2 * gap) // 3
    ph = 372
    for i, (tag, head, body, art, accent) in enumerate(PANELS):
        col, row = i % 3, i // 3
        x = px0 + col * (pw + gap)
        y = py0 + row * (ph + gap)
        panel_frame(p, x, y, pw, ph, accent)
        p.set_clip(x + 2, y + 2, pw - 4, 180)
        art(p, x + 2, y + 2, pw - 4, 180)
        p.clear_clip()
        panel_text(p, x, y, pw, tag, head, body, accent)

    # footer: also today
    fy = 172 + 2 * ph + gap + 8
    p.fill(16, fy, W - 32, 46, NAVY)
    p.text(28, fy + 13, "ALSO TODAY:", 2, GOLD_L, heavy=True)
    p.text(28 + glyph_width("ALSO TODAY: ", 2) + 8, fy + 13,
           "Guru Nanak's 557th Prakash Utsav - COP32 next, in Addis Ababa",
           2, WHITE)

    return p


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    poster = build()
    path = os.path.join(out_dir, "entry.png")
    size = write_png(poster, path)
    print("wrote %s (%d bytes)" % (path, size))


if __name__ == "__main__":
    main()
