#!/usr/bin/env python3
"""Green Home Games — spring-mound painter (this site only).

Haystack of moss on a night-purple field. A tall cream door is cut
into the hill; one ember sits on the doorstep. After-winter home,
not a lodge, not a face, not logs, not a sword, not a sling.

Workshop is a 1600px milles sheet. Silhouette is a cosine-power
hayrick with ridge knolls and lobed moss clumps. Door is an arched
slot punched in cream, timber sleeve around it. Ember is concentric
ellipses on the threshold — never a chimney tongue.

Outputs under assets/icons/:
  green-home-games.ico, icon-192.png, icon-512.png, icon-maskable-512.png
"""

from __future__ import annotations

import math
import struct
import sys
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ICON_DIR = ROOT / "assets" / "icons"

NIGHT = (0x3A, 0x2A, 0x6A)
MOSS = (0x3D, 0x6B, 0x38)
CREAM = (0xF4, 0xE6, 0xC3)
EMBER = (0xF5, 0xC4, 0x00)
TIMBER = (0x5C, 0x3A, 0x1A)

# Local inks — green-family, not lodge-brown body, not ice, not sling-V.
MOSS_INK = (0x1E, 0x38, 0x1C)
MOSS_SHADE = (0x2B, 0x52, 0x2A)
MOSS_LIT = (0x58, 0x8C, 0x4A)
MOSS_TUFT = (0x4A, 0x7A, 0x42)
CREAM_WARM = (0xFF, 0xF2, 0xD2)
THRESHOLD = (0x4A, 0x2C, 0x12)
EMBER_GLOW = (0xF5, 0xC4, 0x00)
EMBER_CORE = (0xFF, 0xF0, 0xB0)
GROUND = (0x2A, 0x1E, 0x4A)

MILLES = 1000.0
WORK = 1600
ICO_FACES = (16, 24, 32, 48, 64, 128, 256)


def _need_pil():
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        import subprocess

        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "pillow"])
        from PIL import Image, ImageDraw
    return Image, ImageDraw


def _rgba(rgb: tuple[int, int, int], a: int = 255) -> tuple[int, int, int, int]:
    return (rgb[0], rgb[1], rgb[2], a)


def _px(v: float, work: int) -> int:
    return int(round(v * work / MILLES))


def _pt(xy: tuple[float, float], work: int) -> tuple[int, int]:
    return (_px(xy[0], work), _px(xy[1], work))


def _poly(pts: list[tuple[float, float]], work: int) -> list[tuple[int, int]]:
    return [_pt(p, work) for p in pts]


def _hayrick(u: float) -> float:
    """Height 0..1 for u in [-1, 1]. Fat loaf / haystack, not a peak, not a circle."""
    u = max(-1.0, min(1.0, u))
    c = math.cos(0.5 * math.pi * u)
    # Sub-linear power keeps the crown flat so 32px reads as a dome, not a mountain.
    return max(0.0, c ** 0.56)


def _ridge_knolls(u: float) -> float:
    """Two small moss ear-bumps on the shoulders — silhouette only, no face."""
    left = math.exp(-((u + 0.42) / 0.075) ** 2)
    right = math.exp(-((u - 0.42) / 0.075) ** 2)
    return 0.048 * left + 0.045 * right


def _moss_scallop(u: float) -> float:
    """Soft tuft ripple along the ridge. Dies at the feet and at the crown."""
    edge = abs(u)
    return 0.014 * math.sin(3.0 * math.pi * (u + 1.0)) * ((1.0 - u * u) ** 1.6) * min(1.0, edge * 3.0)


def spring_mound(
    cx: float,
    base: float,
    half_w: float,
    height: float,
    n: int = 128,
) -> list[tuple[float, float]]:
    """Closed hayrick outline, left-to-right over the ridge, then the skirt."""
    ridge: list[tuple[float, float]] = []
    for i in range(n + 1):
        u = -1.0 + 2.0 * i / n
        h = _hayrick(u) + _ridge_knolls(u) + _moss_scallop(u)
        x = cx + half_w * u
        y = base - height * h
        ridge.append((x, y))
    # Slight belly on the ground so the hill sits, not floats.
    left = (cx - half_w * 1.02, base + 6)
    right = (cx + half_w * 1.02, base + 6)
    return [left] + ridge + [right]


def mound_shell(
    u0: float,
    u1: float,
    cx: float,
    base: float,
    half_w: float,
    height: float,
    inset: float,
    n: int = 56,
) -> list[tuple[float, float]]:
    """Lit or shaded inner shell following a slice of the ridge."""
    outer: list[tuple[float, float]] = []
    inner: list[tuple[float, float]] = []
    for i in range(n + 1):
        u = u0 + (u1 - u0) * i / n
        h = _hayrick(u) + _ridge_knolls(u) + _moss_scallop(u)
        x = cx + half_w * u
        y = base - height * h
        outer.append((x, y))
        # Pull toward a point inside the hill so the shell has thickness.
        ix = cx + half_w * u * (1.0 - inset)
        iy = base - height * h * (1.0 - inset * 1.15) + 8
        inner.append((ix, iy))
    inner.reverse()
    return outer + inner


def moss_clump(
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    lobes: int,
    phase: float,
    n: int = 22,
) -> list[tuple[float, float]]:
    """Lobed polar blob — moss organism, not a stick and not a capsule log."""
    pts: list[tuple[float, float]] = []
    for i in range(n):
        t = 2.0 * math.pi * i / n
        rmod = 1.0 + 0.20 * math.cos(lobes * t + phase)
        pts.append((cx + rx * rmod * math.cos(t), cy + ry * rmod * math.sin(t)))
    return pts


def arch_door(
    cx: float,
    top: float,
    bot: float,
    half_w: float,
    n: int = 32,
) -> list[tuple[float, float]]:
    """Tall slit with a semicircle cap. Cream read at small sizes."""
    r = half_w
    arch_cy = top + r
    pts: list[tuple[float, float]] = [(cx - half_w, bot), (cx - half_w, arch_cy)]
    for i in range(n + 1):
        ang = math.pi - (math.pi * i / n)
        pts.append((cx + r * math.cos(ang), arch_cy - r * math.sin(ang)))
    pts.append((cx + half_w, bot))
    return pts


def _draw_poly(draw, pts: list[tuple[float, float]], work: int, fill) -> None:
    pix = _poly(pts, work)
    if len(pix) >= 3:
        draw.polygon(pix, fill=fill)


def _draw_ellipse(draw, cx: float, cy: float, rx: float, ry: float, work: int, fill) -> None:
    box = (
        _px(cx - rx, work),
        _px(cy - ry, work),
        _px(cx + rx, work),
        _px(cy + ry, work),
    )
    draw.ellipse(box, fill=fill)


def paint_mark(work: int, *, pad: float = 0.0):
    """Paint the milles composition onto a work×work RGBA square."""
    Image, ImageDraw = _need_pil()
    im = Image.new("RGBA", (work, work), _rgba(NIGHT))
    draw = ImageDraw.Draw(im, "RGBA")

    # Inset the whole hill for maskable safe-zone; 0 for the square mark.
    s = 1.0 - pad
    ox = MILLES * 0.5 * pad
    oy = MILLES * 0.06 * pad

    def xf(x: float, y: float) -> tuple[float, float]:
        return (ox + x * s, oy + y * s)

    def xpoly(pts: list[tuple[float, float]]) -> list[tuple[float, float]]:
        return [xf(*p) for p in pts]

    cx, base = 500.0, 848.0
    half_w, height = 438.0, 492.0

    mound = spring_mound(cx, base, half_w, height)
    ink = spring_mound(cx, base + 6, half_w + 16, height + 12)

    # Ground pool — sits the hill on the field. Not a snow bank.
    gcx, gcy = xf(cx, base + 16)
    _draw_ellipse(draw, gcx, gcy, 390 * s, 26 * s, work, _rgba(GROUND, 210))

    _draw_poly(draw, xpoly(ink), work, _rgba(MOSS_INK))
    _draw_poly(draw, xpoly(mound), work, _rgba(MOSS))

    lit = mound_shell(-1.0, 0.02, cx, base, half_w, height, 0.28)
    shade = mound_shell(0.12, 1.0, cx, base, half_w, height, 0.24)
    _draw_poly(draw, xpoly(lit), work, _rgba(MOSS_LIT, 145))
    _draw_poly(draw, xpoly(shade), work, _rgba(MOSS_SHADE, 155))

    # Deterministic moss flock on the hill face. Positions in (u, v, rx, ry, lobes, phase, tint).
    # v is 0 at skirt, 1 at ridge. Skip the door corridor (|u| < 0.18).
    flock = (
        (-0.62, 0.34, 58, 30, 5, 0.4, MOSS_TUFT),
        (-0.48, 0.55, 42, 24, 4, 1.1, MOSS_LIT),
        (-0.76, 0.20, 48, 22, 6, 2.2, MOSS_SHADE),
        (-0.30, 0.42, 38, 20, 5, 0.7, MOSS_TUFT),
        (0.60, 0.32, 54, 28, 5, 1.6, MOSS_SHADE),
        (0.46, 0.54, 40, 22, 4, 0.2, MOSS_TUFT),
        (0.74, 0.20, 44, 20, 6, 2.8, MOSS_INK),
        (0.32, 0.40, 36, 18, 5, 1.9, MOSS_SHADE),
        (-0.16, 0.70, 26, 14, 4, 0.9, MOSS_LIT),
        (0.18, 0.68, 24, 13, 5, 2.4, MOSS_TUFT),
        (-0.42, 0.16, 50, 18, 5, 0.1, MOSS_TUFT),
        (0.40, 0.14, 46, 16, 4, 1.4, MOSS_SHADE),
        (-0.58, 0.78, 24, 14, 5, 3.0, MOSS_LIT),
        (0.54, 0.76, 22, 13, 4, 0.6, MOSS_TUFT),
        (-0.82, 0.38, 32, 16, 6, 1.3, MOSS_SHADE),
        (0.80, 0.36, 30, 15, 5, 2.7, MOSS_INK),
        (-0.42, 0.90, 20, 12, 4, 0.5, MOSS_LIT),
        (0.42, 0.88, 18, 11, 5, 2.0, MOSS_TUFT),
    )
    for u, v, rx, ry, lobes, phase, tint in flock:
        h = _hayrick(u) + _ridge_knolls(u)
        x = cx + half_w * u * 0.86
        y = base - height * h * v * 0.92 - 18
        clump = moss_clump(x, y, rx, ry, lobes, phase)
        _draw_poly(draw, xpoly(clump), work, _rgba(tint, 175))

    # Door sleeve (timber) then cream slit. Wide enough to hold at 32px.
    door_top, door_bot, door_hw = 452.0, 828.0, 88.0
    sleeve = arch_door(cx, door_top - 16, door_bot + 8, door_hw + 18)
    cream = arch_door(cx, door_top, door_bot, door_hw)
    warm = arch_door(cx, door_top + 28, door_bot - 36, door_hw - 22)
    _draw_poly(draw, xpoly(sleeve), work, _rgba(TIMBER))
    _draw_poly(draw, xpoly(cream), work, _rgba(CREAM))
    _draw_poly(draw, xpoly(warm), work, _rgba(CREAM_WARM, 200))

    # Threshold plank — home, not a hanging tooth.
    step = [
        (cx - door_hw - 28, door_bot - 6),
        (cx + door_hw + 28, door_bot - 6),
        (cx + door_hw + 18, door_bot + 22),
        (cx - door_hw - 18, door_bot + 22),
    ]
    _draw_poly(draw, xpoly(step), work, _rgba(THRESHOLD))

    # Ember on the doorstep only. Concentric ellipses, not a flame tongue.
    ecx, ecy = xf(cx, door_bot + 6)
    _draw_ellipse(draw, ecx, ecy, 46 * s, 22 * s, work, _rgba(EMBER_GLOW, 90))
    _draw_ellipse(draw, ecx, ecy, 30 * s, 14 * s, work, _rgba(EMBER))
    _draw_ellipse(draw, ecx, ecy - 2 * s, 14 * s, 7 * s, work, _rgba(EMBER_CORE))

    return im


def _down(im, size: int):
    Image = _need_pil()[0]
    return im.resize((size, size), Image.Resampling.LANCZOS)


def write_ico(path: Path, faces: list) -> None:
    """ICO with PNG payloads (Vista+). One entry per face size."""
    blobs: list[tuple[int, int, bytes]] = []
    for face in faces:
        buf = BytesIO()
        face.save(buf, format="PNG")
        w, h = face.size
        blobs.append((w, h, buf.getvalue()))
    offset = 6 + 16 * len(blobs)
    out = bytearray()
    out += struct.pack("<HHH", 0, 1, len(blobs))
    for w, h, data in blobs:
        out += struct.pack(
            "<BBBBHHII",
            0 if w >= 256 else w,
            0 if h >= 256 else h,
            0,
            0,
            1,
            32,
            len(data),
            offset,
        )
        offset += len(data)
    for _, _, data in blobs:
        out += data
    path.write_bytes(bytes(out))


def main() -> int:
    ICON_DIR.mkdir(parents=True, exist_ok=True)
    master = paint_mark(WORK, pad=0.0)
    maskable = paint_mark(WORK, pad=0.06)

    png_512 = _down(master, 512)
    png_192 = _down(master, 192)
    png_mask = _down(maskable, 512)

    png_512.save(ICON_DIR / "icon-512.png", format="PNG")
    png_192.save(ICON_DIR / "icon-192.png", format="PNG")
    png_mask.save(ICON_DIR / "icon-maskable-512.png", format="PNG")

    ico_faces = [_down(master, s) for s in ICO_FACES]
    write_ico(ICON_DIR / "green-home-games.ico", ico_faces)

    preview_32 = ICON_DIR / "preview-32.png"
    ico_faces[ICO_FACES.index(32)].save(preview_32, format="PNG")

    print("wrote", ICON_DIR / "green-home-games.ico")
    print("wrote", ICON_DIR / "icon-192.png")
    print("wrote", ICON_DIR / "icon-512.png")
    print("wrote", ICON_DIR / "icon-maskable-512.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
