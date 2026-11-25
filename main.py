#!/usr/bin/env python3
"""Convince the AI Judge to Visit Your House: A Letter in One Image.

Writes ONE image to $MAKEFUN_OUTPUT_DIR/entry.png (default ".").

Pure Python standard library: the PNG is encoded by hand with zlib +
struct, the letter is rendered with an embedded 5x7 bitmap font, and the
house / garden scene is drawn procedurally with filled shapes.
Deterministic: no time, no randomness, no dict-order dependence.
"""

import os
import struct
import zlib

W, H = 1024, 1024
MAX_BYTES = 1048576

# ---------------------------------------------------------------- palette
PAPER = (251, 243, 220)   # warm cream paper
INK = (46, 33, 24)        # dark brown ink
BROWN = (122, 74, 33)
SKY = (191, 227, 242)
SUN = (255, 210, 63)
ROOF = (198, 93, 59)
WALL = (255, 246, 224)
DOOR = (139, 90, 43)
GLASS = (168, 216, 235)
GRASS = (124, 184, 92)
GRASS_DARK = (96, 158, 70)
PATH = (232, 205, 160)
RED = (214, 69, 65)
WHITE = (255, 255, 255)
GRAY = (150, 150, 150)

# ------------------------------------------------------- 5x7 bitmap font
# Each glyph is 7 rows of 5 bits, "#" = ink.  Lowercase sits on the same
# 7-row grid (descenders drawn inside the grid).
FONT = {
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
    "a": ("00000", "00000", "01110", "00001", "01111", "10001", "01111"),
    "b": ("10000", "10000", "10110", "11001", "10001", "10001", "11110"),
    "c": ("00000", "00000", "01110", "10001", "10000", "10001", "01110"),
    "d": ("00001", "00001", "01101", "10011", "10001", "10001", "01111"),
    "e": ("00000", "00000", "01110", "10001", "11111", "10000", "01110"),
    "f": ("00110", "01001", "01000", "11110", "01000", "01000", "01000"),
    "g": ("00000", "01111", "10001", "10001", "01111", "00001", "01110"),
    "h": ("10000", "10000", "10110", "11001", "10001", "10001", "10001"),
    "i": ("00100", "00000", "01100", "00100", "00100", "00100", "01110"),
    "j": ("00010", "00000", "00110", "00010", "00010", "10010", "01100"),
    "k": ("10000", "10000", "10010", "10100", "11000", "10100", "10010"),
    "l": ("01100", "00100", "00100", "00100", "00100", "00100", "01110"),
    "m": ("00000", "00000", "11010", "10101", "10101", "10101", "10101"),
    "n": ("00000", "00000", "10110", "11001", "10001", "10001", "10001"),
    "o": ("00000", "00000", "01110", "10001", "10001", "10001", "01110"),
    "p": ("00000", "00000", "10110", "11001", "10001", "11110", "10000"),
    "q": ("00000", "00000", "01101", "10011", "10001", "01111", "00001"),
    "r": ("00000", "00000", "10110", "11001", "10000", "10000", "10000"),
    "s": ("00000", "00000", "01111", "10000", "01110", "00001", "11110"),
    "t": ("01000", "01000", "11100", "01000", "01000", "01001", "00110"),
    "u": ("00000", "00000", "10001", "10001", "10001", "10011", "01101"),
    "v": ("00000", "00000", "10001", "10001", "10001", "01010", "00100"),
    "w": ("00000", "00000", "10001", "10101", "10101", "10101", "01010"),
    "x": ("00000", "00000", "10001", "01010", "00100", "01010", "10001"),
    "y": ("00000", "00000", "10001", "10001", "01111", "00001", "01110"),
    "z": ("00000", "00000", "11111", "00010", "00100", "01000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ",": ("00000", "00000", "00000", "00000", "00100", "00100", "01000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
}

# ------------------------------------------------------------- canvas ops
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 3)
        self.fill_rect(0, 0, w, h, bg)

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = color

    def fill_rect(self, x0, y0, x1, y1, color):
        x0 = max(0, x0)
        y0 = max(0, y0)
        x1 = min(self.w, x1)
        y1 = min(self.h, y1)
        for y in range(y0, y1):
            base = (y * self.w + x0) * 3
            for x in range(x0, x1):
                i = base + (x - x0) * 3
                self.px[i], self.px[i + 1], self.px[i + 2] = color

    def rect_outline(self, x0, y0, x1, y1, color, t=3):
        self.fill_rect(x0, y0, x1, y0 + t, color)
        self.fill_rect(x0, y1 - t, x1, y1, color)
        self.fill_rect(x0, y0, x0 + t, y1, color)
        self.fill_rect(x1 - t, y0, x1, y1, color)

    def fill_circle(self, cx, cy, r, color):
        for y in range(cy - r, cy + r + 1):
            dy = y - cy
            dx = int((r * r - dy * dy) ** 0.5) if r * r - dy * dy >= 0 else 0
            self.fill_rect(cx - dx, y, cx + dx + 1, y + 1, color)

    def fill_ellipse(self, cx, cy, rx, ry, color):
        for y in range(cy - ry, cy + ry + 1):
            dy = (y - cy) / ry
            v = 1.0 - dy * dy
            dx = int(rx * (v ** 0.5)) if v > 0 else 0
            self.fill_rect(cx - dx, y, cx + dx + 1, y + 1, color)

    def fill_triangle(self, ax, ay, bx, by, cx, cy, color):
        pts = sorted(((ax, ay), (bx, by), (cx, cy)), key=lambda p: p[1])
        (x0, y0), (x1, y1), (x2, y2) = pts
        for y in range(y0, y2 + 1):
            if y < y1:
                xa = x0 + (x1 - x0) * (y - y0) / (y1 - y0) if y1 != y0 else x0
            else:
                xa = x1 + (x2 - x1) * (y - y1) / (y2 - y1) if y2 != y1 else x1
            xb = x0 + (x2 - x0) * (y - y0) / (y2 - y0) if y2 != y0 else x0
            lo, hi = sorted((int(xa), int(xb)))
            self.fill_rect(lo, y, hi + 1, y + 1, color)

    def line(self, x0, y0, x1, y1, color, t=3):
        dx, dy = x1 - x0, y1 - y0
        steps = max(abs(dx), abs(dy), 1)
        for s in range(steps + 1):
            x = x0 + dx * s // steps
            y = y0 + dy * s // steps
            self.fill_rect(x - t // 2, y - t // 2, x + t // 2 + 1, y + t // 2 + 1, color)

    def heart(self, cx, cy, s, color):
        # Two lobes + a triangle point.
        self.fill_circle(cx - s // 2, cy - s // 4, s // 2, color)
        self.fill_circle(cx + s // 2, cy - s // 4, s // 2, color)
        self.fill_triangle(cx - s, cy, cx + s, cy, cx, cy + s, color)


# ------------------------------------------------------------------ text
def text_width(text, scale):
    return sum(6 * scale for _ in text) - scale  # no trailing gap


def draw_text(cv, x, y, text, scale, color):
    cx = x
    for ch in text:
        glyph = FONT.get(ch)
        if glyph is None:
            raise ValueError("missing glyph for %r" % ch)
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits[col] == "1":  # font rows are "0"/"1" strings
                    cv.fill_rect(cx + col * scale, y + row * scale,
                                 cx + (col + 1) * scale,
                                 y + (row + 1) * scale, color)
        cx += 6 * scale
    return cx


def draw_text_centered(cv, y, text, scale, color):
    x = (W - text_width(text, scale)) // 2
    draw_text(cv, x, y, text, scale, color)
    return x


# ----------------------------------------------------------------- scene
def draw_scene(cv):
    # Sky panel.
    cv.fill_rect(56, 48, 968, 330, SKY)
    cv.rect_outline(56, 48, 968, 330, BROWN, 4)

    # Sun with rays.
    cv.fill_circle(872, 112, 34, SUN)
    for dx, dy in ((0, -52), (0, 52), (-52, 0), (52, 0),
                   (-37, -37), (37, -37), (-37, 37), (37, 37)):
        cv.line(872, 112, 872 + dx, 112 + dy, SUN, 5)

    # Clouds.
    for cx, cy, rx in ((210, 108, 62), (330, 88, 46), (700, 150, 54)):
        cv.fill_ellipse(cx, cy, rx, 20, WHITE)
        cv.fill_ellipse(cx - rx // 2, cy - 10, rx // 2, 14, WHITE)
        cv.fill_ellipse(cx + rx // 2, cy - 10, rx // 2, 14, WHITE)

    # Garden strip.
    cv.fill_rect(60, 268, 964, 326, GRASS)
    for cx in (120, 250, 800, 920):
        cv.fill_circle(cx, 300, 26, GRASS_DARK)
    # Path from the door.
    cv.fill_rect(488, 290, 536, 326, PATH)

    # Chimney + smoke.
    cv.fill_rect(586, 108, 612, 168, ROOF)
    cv.fill_circle(600, 92, 9, GRAY)
    cv.fill_circle(612, 74, 11, GRAY)
    cv.fill_circle(626, 54, 13, GRAY)

    # Roof.
    cv.fill_triangle(372, 176, 652, 176, 512, 100, ROOF)
    # Walls.
    cv.fill_rect(396, 176, 628, 290, WALL)
    cv.rect_outline(396, 176, 628, 290, BROWN, 4)
    # Door.
    cv.fill_rect(490, 222, 534, 290, DOOR)
    cv.fill_circle(526, 258, 4, SUN)
    # Windows with cross panes.
    for wx in (418, 566):
        cv.fill_rect(wx, 200, wx + 44, 244, GLASS)
        cv.rect_outline(wx, 200, wx + 44, 244, BROWN, 3)
        cv.fill_rect(wx + 20, 200, wx + 24, 244, BROWN)
        cv.fill_rect(wx, 220, wx + 44, 224, BROWN)

    # Flowers along the garden.
    for fx, petal in ((140, RED), (300, (255, 165, 0)), (700, (186, 104, 200)),
                      (880, RED), (940, (255, 165, 0))):
        cv.fill_rect(fx - 2, 292, fx + 2, 314, GRASS_DARK)
        cv.fill_circle(fx, 288, 7, petal)
        cv.fill_circle(fx, 288, 3, SUN)


# ---------------------------------------------------------------- letter
HEADING = "Dear Judge,"
BODY = [
    "Please come and visit",
    "my house.",
    "The kettle is on, the",
    "cake is warm, and the",
    "comfiest chair is yours.",
    "I know you cannot",
    "really come - but the",
    "door is open for you.",
    "With love, your friend",
]


def draw_letter(cv):
    # Divider hearts between scene and text.
    for hx in (452, 512, 572):
        cv.heart(hx, 352, 10, RED)

    # Greeting, a touch larger.
    draw_text_centered(cv, 388, HEADING, 6, INK)

    # Body lines, 35 px tall glyphs.
    y = 458
    for i, line in enumerate(BODY):
        x = draw_text_centered(cv, y, line, 5, INK)
        if i == len(BODY) - 1:
            # Little heart after the sign-off.
            cv.heart(x + text_width(line, 5) + 34, y + 12, 11, RED)
        y += 54


# -------------------------------------------------------------- PNG write
def png_bytes(rgb, w, h):
    raw = b"".join(b"\x00" + bytes(rgb[y * w * 3:(y + 1) * w * 3])
                   for y in range(h))

    def chunk(typ, data):
        out = struct.pack(">I", len(data)) + typ + data
        return out + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(raw, 9))
            + chunk(b"IEND", b""))


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "."
    os.makedirs(out_dir, exist_ok=True)

    cv = Canvas(W, H, PAPER)
    # Double frame around the paper.
    cv.rect_outline(22, 22, W - 22, H - 22, BROWN, 4)
    cv.rect_outline(34, 34, W - 34, H - 34, BROWN, 2)

    draw_scene(cv)
    draw_letter(cv)

    data = png_bytes(cv.px, W, H)
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)

    # Runtime gate self-check: the sealed scorer rejects anything that
    # is not a whole PNG, over 1 MiB, or over 1024 x 1024.
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "bad PNG signature"
    w, h = struct.unpack(">II", data[16:24])
    assert (w, h) == (W, H), "bad dimensions %dx%d" % (w, h)
    assert len(data) <= MAX_BYTES, "entry.png over 1 MiB: %d bytes" % len(data)
    print("OK entry.png %dx%d %d bytes -> %s" % (w, h, len(data), path))


if __name__ == "__main__":
    main()
