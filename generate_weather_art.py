"""
Procedurally draws the 8-bit style weather animations into animations/<name>/<frame>.png

Every animation is 40x40 on a black background (same as the thunder animation)
and uses a small fixed palette so the frames compress very well.

Run from the repo root:
    python generate_weather_art.py
    python image_convert.py
"""

import math
from pathlib import Path
from PIL import Image

W = H = 40

# ---------------------------------------------------------------- palette
BLACK = (0, 0, 0)

SUN_HI = (255, 248, 160)
SUN = (252, 208, 48)
SUN_EDGE = (232, 136, 24)
RAY = (248, 176, 0)
RAY_HI = (255, 232, 96)

# Fair weather clouds (white)
CLOUD_W_HI = (248, 248, 248)
CLOUD_W = (200, 208, 224)
CLOUD_W_LO = (128, 136, 168)

# Grey clouds (overcast / snow)
CLOUD_G_HI = (176, 184, 200)
CLOUD_G = (128, 136, 160)
CLOUD_G_LO = (80, 88, 112)

# Dark rain clouds (close to the thunder cloud colours)
CLOUD_D_HI = (112, 120, 144)
CLOUD_D = (72, 80, 104)
CLOUD_D_LO = (48, 52, 72)

RAIN = (64, 72, 152)
RAIN_HI = (120, 160, 248)
DRIZZLE = (96, 152, 232)
SNOW = (248, 248, 248)
SNOW_LO = (168, 200, 248)

CLOUD_WHITE = (CLOUD_W_HI, CLOUD_W, CLOUD_W_LO)
CLOUD_GREY = (CLOUD_G_HI, CLOUD_G, CLOUD_G_LO)
CLOUD_DARK = (CLOUD_D_HI, CLOUD_D, CLOUD_D_LO)


# ---------------------------------------------------------------- helpers
class Canvas:
    def __init__(self):
        self.px = [[BLACK] * W for _ in range(H)]

    def set(self, x, y, c):
        if 0 <= x < W and 0 <= y < H:
            self.px[y][x] = c

    def image(self):
        img = Image.new("RGB", (W, H))
        img.putdata([c for row in self.px for c in row])
        return img


def cloud_mask(puffs, bottom, dx=0, dy=0):
    """Union of circles (cx, cy, r) cut flat at `bottom`. Returns a set of (x, y)."""
    mask = set()
    for cx, cy, r in puffs:
        cx += dx
        cy += dy
        for y in range(math.floor(cy - r), math.ceil(cy + r) + 1):
            for x in range(math.floor(cx - r), math.ceil(cx + r) + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r + 0.5 and y <= bottom + dy:
                    mask.add((x, y))
    return mask


def draw_cloud(cv, puffs, bottom, colors, dx=0, dy=0):
    hi, base, lo = colors
    mask = cloud_mask(puffs, bottom, dx, dy)
    for x, y in mask:
        if (x, y - 1) not in mask or (x - 1, y - 1) not in mask and (x, y - 2) not in mask:
            c = hi  # top rim
        elif y >= bottom + dy - 2 or (x, y + 2) not in mask:
            c = lo  # underside shadow
        else:
            c = base
        cv.set(x, y, c)


def draw_sun(cv, cx, cy, r, frame, ray_inner, ray_outer):
    """8 straight rays (no jaggies). They pulse over a 4 frame cycle:
    0: straight rays long, 1: all medium, 2: diagonal rays long, 3: all medium."""
    straight_len = [ray_outer, ray_outer - 1, ray_outer - 3, ray_outer - 1][frame % 4]
    diag_len = [ray_outer - 3, ray_outer - 1, ray_outer, ray_outer - 1][frame % 4]
    for k in range(8):
        a = k * math.pi / 4
        diagonal = k % 2 == 1
        # Diagonals step in whole pixels so they stay 1px clean lines
        outer = round(diag_len / math.sqrt(2)) if diagonal else straight_len
        inner = round(ray_inner / math.sqrt(2)) if diagonal else ray_inner
        ux, uy = round(math.cos(a)) if not diagonal else (1 if math.cos(a) > 0 else -1),             round(math.sin(a)) if not diagonal else (1 if math.sin(a) > 0 else -1)
        for t in range(inner, outer + 1):
            cv.set(cx + ux * t, cy + uy * t, RAY_HI if t == outer else RAY)

    for y in range(cy - r - 1, cy + r + 2):
        for x in range(cx - r - 1, cx + r + 2):
            d2 = (x - cx) ** 2 + (y - cy) ** 2
            if d2 > r * r + 0.5:
                continue
            if d2 > (r - 1.2) ** 2 and (x - cx) + (y - cy) > -1:
                c = SUN_EDGE  # shaded bottom-right rim
            elif (x - cx + r * 0.35) ** 2 + (y - cy + r * 0.35) ** 2 <= (r * 0.35) ** 2 + 0.5:
                c = SUN_HI  # shine top-left
            else:
                c = SUN
            cv.set(x, y, c)


def falling(cv, drops, y_top, y_bot, offset, draw):
    """Each drop (x, y0) moves down by `offset` and wraps inside [y_top, y_bot)."""
    span = y_bot - y_top
    for i, (x, y0) in enumerate(drops):
        y = y_top + (y0 - y_top + offset) % span
        draw(cv, x, y, i)


# ---------------------------------------------------------------- animations
def sunny(frames=4):
    out = []
    for f in range(frames):
        cv = Canvas()
        # Rays pulse in and out over 4 frames
        draw_sun(cv, 20, 20, 9, f, 12, 18)
        out.append(cv)
    return out


BIG_CLOUD = [(10, 26, 6), (18, 21, 8), (27, 24, 7), (33, 28, 5)]


def partial_cloud(frames=4):
    bob = [0, 1, 2, 1]
    out = []
    for f in range(frames):
        cv = Canvas()
        draw_sun(cv, 25, 13, 7, f, 10, 13)
        draw_cloud(cv, [(9, 27, 5), (16, 23, 7), (24, 26, 6), (29, 29, 4)], 32, CLOUD_WHITE, dx=bob[f] - 1)
        out.append(cv)
    return out


def cloud(frames=4):
    bob = [0, 1, 2, 1]
    out = []
    for f in range(frames):
        cv = Canvas()
        # Small grey cloud behind, drifting opposite to the front one
        draw_cloud(cv, [(22, 13, 5), (28, 10, 6), (33, 13, 4)], 16, CLOUD_GREY, dx=1 - bob[f])
        draw_cloud(cv, BIG_CLOUD, 32, CLOUD_WHITE, dx=bob[f] - 1, dy=-3)
        out.append(cv)
    return out


RAIN_CLOUD = [(9, 13, 6), (17, 9, 8), (26, 11, 7), (32, 15, 5)]
RAIN_CLOUD_BOTTOM = 19


def rain(frames=4):
    # 3px streaks, 5px per frame, 20px span -> 4 frame loop
    drops = [(5, 20), (9, 30), (13, 24), (17, 35), (21, 22), (25, 31), (29, 26), (33, 37), (37, 23),
             (7, 36), (19, 28), (31, 33)]

    def streak(cv, x, y, i):
        for k in range(3):
            cv.set(x - (k // 2), y - k, RAIN_HI if k == 0 else RAIN)

    out = []
    for f in range(frames):
        cv = Canvas()
        falling(cv, drops, 18, 38, f * 5, streak)
        draw_cloud(cv, RAIN_CLOUD, RAIN_CLOUD_BOTTOM, CLOUD_DARK)
        out.append(cv)
    return out


def drizzle(frames=8):
    # Small 1x2 drops, 2px per frame, 16px span -> 8 frame loop
    drops = [(7, 22), (14, 30), (20, 25), (27, 33), (33, 27), (11, 36), (24, 21), (30, 37)]

    def drop(cv, x, y, i):
        cv.set(x, y, DRIZZLE)
        cv.set(x, y - 1, DRIZZLE)

    out = []
    for f in range(frames):
        cv = Canvas()
        falling(cv, drops, 22, 38, f * 2, drop)
        draw_cloud(cv, RAIN_CLOUD, RAIN_CLOUD_BOTTOM, CLOUD_DARK)
        out.append(cv)
    return out


def snow(frames=8):
    # Flakes fall 2px per frame over a 16px span and sway left/right
    flakes = [(6, 22, True), (13, 31, False), (19, 25, True), (26, 34, False), (32, 23, True),
              (36, 30, False), (9, 28, False), (23, 37, True), (29, 28, False)]
    sway = [0, 0, 1, 1, 0, 0, -1, -1]

    out = []
    for f in range(frames):
        cv = Canvas()

        def flake(cv, x, y, i):
            big = flakes[i][2]
            x += sway[(f + i * 3) % len(sway)]
            if big:
                cv.set(x, y, SNOW)
                for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    cv.set(x + ox, y + oy, SNOW_LO)
            else:
                cv.set(x, y, SNOW)

        falling(cv, [(x, y) for x, y, _ in flakes], 22, 38, f * 2, flake)
        draw_cloud(cv, RAIN_CLOUD, RAIN_CLOUD_BOTTOM, CLOUD_GREY)
        out.append(cv)
    return out


STORM_CLOUD = [(7, 12, 6), (14, 8, 7), (23, 10, 7), (30, 13, 6), (35, 16, 4)]
STORM_CLOUD_BOTTOM = 19

# Storm cloud: darkest of all, lit up during a lightning flash
CLOUD_STORM = ((72, 76, 100), (56, 60, 80), (40, 44, 56))
CLOUD_STORM_LIT = ((200, 200, 232), (144, 144, 184), (96, 96, 136))

BOLT_HI = (255, 248, 176)
BOLT = (252, 208, 32)
BOLT_EDGE = (200, 120, 16)
BOLT_DIM = (184, 136, 24)

# Lightning bolt outlines (polygon points), big strike and a small flicker
BOLT_BIG = [(23, 11), (15, 26), (20, 26), (15, 39), (28, 21), (22, 21), (27, 11)]
BOLT_SMALL = [(22, 15), (17, 26), (21, 26), (18, 33), (26, 23), (22, 23), (25, 15)]


def draw_bolt(cv, points, dim=False):
    from PIL import ImageDraw
    mask_img = Image.new("1", (W, H), 0)
    ImageDraw.Draw(mask_img).polygon(points, fill=1)
    mask = {(x, y) for y in range(H) for x in range(W) if mask_img.getpixel((x, y))}
    for x, y in mask:
        if dim:
            c = BOLT_DIM
        elif (x - 1, y) not in mask:
            c = BOLT_HI  # lit left edge
        elif (x + 1, y) not in mask or (x, y + 1) not in mask:
            c = BOLT_EDGE  # shaded right / bottom edge
        else:
            c = BOLT
        cv.set(x, y, c)


# Bolts the ESP32 picks from at random: (outline, x offset)
STRIKES = [(BOLT_BIG, 0), (BOLT_BIG, -9), (BOLT_SMALL, 9)]
THUNDER_RAIN_PHASES = 4
# Per strike: flash (cloud lit + bolt), bolt, fading bolt
THUNDER_STATES = 1 + 3 * len(STRIKES)


def thunder():
    """Not a fixed loop: frames are a lookup grid the firmware picks from at random.

    frame = rain_phase * THUNDER_STATES + state
        state 0          -> no lightning
        state 1 + 3*b    -> bolt b with the cloud lit up by the flash
        state 2 + 3*b    -> bolt b
        state 3 + 3*b    -> bolt b fading out
    Keep these numbers in sync with THUNDER_* in display.cpp.
    """
    # Heavy slanted rain like the original thunder art: 5px per frame over 20px -> 4 phase cycle
    drops = [(4, 21), (8, 31), (12, 25), (16, 36), (20, 22), (24, 32), (28, 27), (32, 37), (36, 24),
             (6, 37), (18, 29), (30, 33), (34, 29), (10, 22)]

    def streak(cv, x, y, lit):
        for k in range(3):
            cv.set(x - (k // 2), y - k, (176, 200, 255) if lit else (RAIN_HI if k == 0 else RAIN))

    out = []
    for phase in range(THUNDER_RAIN_PHASES):
        for state in range(THUNDER_STATES):
            strike, step = divmod(state - 1, 3) if state else (None, None)
            flash = step == 0
            cv = Canvas()
            falling(cv, drops, 18, 38, phase * 5, lambda cv, x, y, i: streak(cv, x, y, flash))
            draw_cloud(cv, STORM_CLOUD, STORM_CLOUD_BOTTOM, CLOUD_STORM_LIT if flash else CLOUD_STORM)
            if strike is not None:
                outline, dx = STRIKES[strike]
                draw_bolt(cv, [(x + dx, y) for x, y in outline], dim=step == 2)
            out.append(cv)
    return out


ANIMATIONS = {
    "sunny": sunny,
    "partial_cloud": partial_cloud,
    "cloud": cloud,
    "drizzle": drizzle,
    "rain": rain,
    "snow": snow,
    "thunder": thunder,
}

if __name__ == "__main__":
    for name, fn in ANIMATIONS.items():
        folder = Path("animations") / name
        folder.mkdir(parents=True, exist_ok=True)
        for old in folder.glob("*.png"):
            old.unlink()
        for i, cv in enumerate(fn()):
            cv.image().save(folder / f"{i}.png")
        print(f"Wrote {name}")
