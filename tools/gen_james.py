"""James entity texture, 128x128 = the vanilla 64x64 skin layout at 2x resolution.
Right column x=112..127, y=32..95 is a tile strip for the extra cubes (hair spikes, sword).
Run:  python3 tools/gen_james.py   (writes into src/main/resources/assets/hagoyama/textures/entity)
"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from artlib import *  # noqa

OUT = os.path.join(os.path.dirname(__file__), '..', 'src', 'main', 'resources', 'assets', 'hagoyama', 'textures', 'entity')

# ---- palettes (dark -> light), sampled from the reference drawing then shaded -------------
HAIR = [hexc(c) for c in ('#0c4684', '#1769b4', '#2386d6', '#43b4f7', '#6ccbff', '#a6e2ff', '#d9f4ff')]
SKIN = [hexc(c) for c in ('#6e3d1c', '#8a4f26', '#a8652f', '#c58048', '#d99a60', '#e8b47e', '#f4cc9e')]
WOOL = [hexc(c) for c in ('#12395c', '#1a4d79', '#22639a', '#2a72a8', '#3687bf', '#4f9fd4', '#7bbfe9')]
DENIM = [hexc(c) for c in ('#122f50', '#1a4068', '#235287', '#2c64a0', '#3b7bb6', '#5a99cf')]
LEATHER = [hexc(c) for c in ('#26160b', '#432913', '#6a4121', '#8c5a2b', '#b97a3e', '#d99b5a', '#efbc7e')]
OUTLINE = hexc('#07203d')  # deep navy for hair edges (the drawing's black outline, softened)
BLACK = hexc('#08090d')
WHITE = hexc('#f6f9ff')
IRIS_L, IRIS_M, IRIS_D = hexc('#a8d8ff'), hexc('#6fb4f0'), hexc('#3f86c8')
MOUTH, MOUTH_IN = hexc('#4a1d14'), hexc('#7a2e24')

# ---- layout (2x of the 64x64 player skin) -------------------------------------------------
HEAD = box_faces(0, 0, 16, 16, 16)
HAT = box_faces(64, 0, 16, 16, 16)
BODY = box_faces(32, 32, 16, 24, 8)
JACKET = box_faces(32, 64, 16, 24, 8)
RARM = box_faces(80, 32, 8, 24, 8)
RSLEEVE = box_faces(80, 64, 8, 24, 8)
LARM = box_faces(64, 96, 8, 24, 8)
LSLEEVE = box_faces(96, 96, 8, 24, 8)
RLEG = box_faces(0, 32, 8, 24, 8)
RPANTS = box_faces(0, 64, 8, 24, 8)
LLEG = box_faces(32, 96, 8, 24, 8)
LPANTS = box_faces(0, 96, 8, 24, 8)

# extra tiles (x, y, w, h)
TILE_HAIR = (112, 32, 16, 16)
TILE_BLADE = (112, 48, 16, 16)
TILE_GUARD = (112, 64, 16, 16)
TILE_GRIP = (112, 80, 16, 8)
TILE_EYE = (112, 88, 16, 8)


def shade_skin(x, y, seed, shade=0.0, amp=0.9):
    return pick(SKIN, 3 + shade + (fbm(x, y, seed, 5, 3) - 0.5) * amp * 2 + (h2(x, y, seed + 9) - 0.5) * 0.5)


def shade_hair(x, y, seed, shade=0.0, strands=True):
    t = 3 + shade
    if strands:
        t += (h2(x, 0, seed) - 0.5) * 1.7            # vertical strands
        t += (h2(x, y // 3, seed + 3) - 0.5) * 0.7
    band = (x * 0.8 + y * 0.45) % 13
    t += max(0.0, 1.0 - abs(band - 6.5) / 2.6) * 1.1  # diagonal sheen
    t += (fbm(x, y, seed + 5, 6, 2) - 0.5) * 0.8
    return pick(HAIR, t)


def knit_offset(x, y):
    """Cable-knit: ribs at the sides of every 8px repeat, a crossing braid in the middle."""
    c = x % 8
    if c in (0, 1, 6, 7):
        return 0.7 if x % 2 == 0 else -0.7
    k = c - 2
    p = (y // 2) % 4
    if k == p or k == 3 - p:
        return 1.1
    return -0.35


def wool(x, y, seed, shade=0.0, pattern=True):
    t = 3 + shade
    if pattern:
        t += knit_offset(x, y) * 0.85
    t += (fbm(x, y, seed, 4, 2) - 0.5) * 0.9
    r = h2(x, y, seed + 31)
    if r > 0.965:
        t += 1.6          # loose fibre
    elif r < 0.02:
        t -= 1.2
    return pick(WOOL, t)


def denim(x, y, seed, shade=0.0):
    t = 3 + shade + ((x + y) % 3 == 0) * 0.55 - ((x + y) % 3 == 1) * 0.25
    t += (fbm(x, y, seed, 5, 3) - 0.5) * 1.1
    if h2(x, y, seed + 7) > 0.97:
        t += 1.4
    return pick(DENIM, t)


def leather(x, y, seed, shade=0.0):
    t = 4 + shade + (fbm(x * 1.7, y, seed, 4, 3) - 0.5) * 1.5 + (h2(x, y, seed + 2) - 0.5) * 0.6
    return pick(LEATHER, t)


def outline_pass(T, rect, color):
    """Darken opaque pixels that touch a transparent one inside the same rect (soft outline)."""
    x0, y0, w, h = rect
    sub = T.a[y0:y0 + h, x0:x0 + w, 3].copy()
    for y in range(h):
        for x in range(w):
            if sub[y, x] == 0:
                continue
            edge = False
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and sub[ny, nx] == 0:
                    edge = True
            if edge:
                T.put(x0 + x, y0 + y, color)


# =========================================================================================
def paint_head(T):
    # ---- base layer --------------------------------------------------------------------
    F = HEAD
    # skin everywhere, hair colour on top/back so nothing shows through the cap
    T.paint(F['top'], lambda x, y: shade_hair(x, y, 11))
    T.paint(F['bottom'], lambda x, y: shade_skin(x, y, 12, -0.8))
    T.paint(F['back'], lambda x, y: shade_hair(x, y, 13, -0.4))
    for side, flip in (('right', False), ('left', True)):
        def side_px(x, y, flip=flip):
            fx = 15 - x if flip else x           # fx: 0 = back edge, 15 = front edge
            hair = y <= 5 or (fx <= 5 and y <= 11) or (fx >= 13 and 6 <= y <= 9)
            if hair:
                return shade_hair(x, y, 14 if not flip else 15, -0.2)
            ear = 6 <= fx <= 10 and 7 <= y <= 10
            if ear:
                inner = 7 <= fx <= 9 and 8 <= y <= 9
                return pick(SKIN, 2.2 if inner else 3.4 + (fx == 10) * -0.8)
            return shade_skin(x, y, 16, -0.3 if fx < 8 else 0.0)
        T.paint(F[side], side_px)

    # front face: skin + hand-placed features
    feat = {}
    for ex in (2, 9):                    # eye block origin x for each eye (left = viewer's left)
        mir = ex == 9
        def xx(dx, mir=mir, ex=ex):
            return ex + (4 - dx if mir else dx)
        for dx in range(0, 6):           # lash line above the eye
            if not (dx == 5):
                feat[(xx(dx) if dx < 5 else xx(4), 5)] = BLACK
        feat[(1 if not mir else 14, 6)] = BLACK          # outer flick
        # eye interior 5x3
        rows = {
            6: [WHITE, hexc('#f2f9ff'), IRIS_L, IRIS_L, WHITE],
            7: [WHITE, IRIS_L, BLACK, IRIS_M, WHITE],
            8: [hexc('#d2e2f5'), IRIS_M, BLACK, IRIS_D, hexc('#d2e2f5')],
        }
        for y, cols in rows.items():
            for dx, c in enumerate(cols):
                feat[(xx(dx), y)] = c
        for dx in range(5):              # lower lid
            feat[(xx(dx), 9)] = BLACK if 1 <= dx <= 3 else pick(SKIN, 1.5)
    feat[(7, 10)] = pick(SKIN, 1.6); feat[(8, 10)] = pick(SKIN, 1.6)
    feat[(7, 11)] = pick(SKIN, 2.3); feat[(8, 11)] = pick(SKIN, 2.3)
    for px in (6, 9):
        feat[(px, 12)] = pick(SKIN, 2.0); feat[(px, 13)] = pick(SKIN, 2.0)
    feat[(7, 12)] = MOUTH; feat[(8, 12)] = MOUTH
    feat[(7, 13)] = MOUTH_IN; feat[(8, 13)] = MOUTH_IN
    feat[(7, 14)] = pick(SKIN, 2.4); feat[(8, 14)] = pick(SKIN, 2.4)
    for cx in (3, 4, 11, 12):            # cheek highlights
        feat[(cx, 11)] = pick(SKIN, 4.3)

    def front_px(x, y):
        if (x, y) in feat:
            return feat[(x, y)]
        edge = 0.0
        if x <= 1 or x >= 14:
            edge -= 0.5
        if y >= 14:
            edge -= 0.6
        return shade_skin(x, y, 17, edge, 0.7)
    T.paint(F['front'], front_px)

    # ---- hair overlay (hat layer) --------------------------------------------------------
    H = HAT
    T.paint(H['top'], lambda x, y: shade_hair(x, y, 21, 0.3))
    T.paint(H['bottom'], lambda x, y: None)
    bang_len = [5, 4, 4, 3, 4, 5, 3, 2, 2, 3, 5, 4, 4, 3, 4, 5]
    T.paint(H['front'], lambda x, y: shade_hair(x, y, 22, 0.2) if y < bang_len[x] else None)
    def back_px(x, y):
        jag = 11 + int(h2(x, 3, 23) * 3)
        return shade_hair(x, y, 24, -0.3) if y <= jag else None
    T.paint(H['back'], back_px)
    for side, flip in (('right', False), ('left', True)):
        def hside(x, y, flip=flip):
            fx = 15 - x if flip else x
            if y <= 5 or (fx <= 5 and y <= 10 + int(h2(fx, 5, 25) * 2)) or (fx >= 13 and 6 <= y <= 8 + int(h2(fx, 6, 26) * 2)):
                return shade_hair(x, y, 27 if not flip else 28, 0.0)
            return None
        T.paint(H[side], hside)
    for key in ('front', 'back', 'right', 'left'):
        outline_pass(T, H[key], OUTLINE)
    # keep the outline off the top row of the side/front faces (those edges are hidden by the cap)
    T.paint(H['front'], lambda x, y: shade_hair(x, y, 29, 0.25) if y == 0 else (T.get(H['front'][0] + x, H['front'][1] + y)[:3] if T.get(H['front'][0] + x, H['front'][1] + y)[3] else None))


def paint_body(T):
    F = BODY
    def front(x, y):
        # crew neckline: skin under the chin, ribbed collar around it
        if y <= 1 and 5 <= x <= 10:
            return pick(SKIN, 2.2 if y == 0 else 3.0)
        if y <= 2:
            return wool(x, y, 40, 0.8, False)
        if y >= 20:
            return wool(x, y, 41, 0.9 - (y - 20) * 0.1, False) if x % 2 == 0 else wool(x, y, 41, 0.2, False)
        edge = -0.7 * (abs(x - 7.5) / 8.0) ** 2 - 0.25 * (y / 24.0)
        return wool(x, y, 42, edge)
    T.paint(F['front'], front)
    T.paint(F['back'], lambda x, y: wool(x, y, 43, -0.55 + (0.5 if y <= 2 or y >= 20 else 0), y > 2 and y < 20))
    for side in ('right', 'left'):
        T.paint(F[side], lambda x, y, s=side: wool(x + (3 if s == 'left' else 0), y, 44, -0.5 - 0.3 * (x / 8.0 if s == 'left' else 1 - x / 8.0)))
    T.paint(F['top'], lambda x, y: wool(x, y, 45, 0.6, False))
    T.paint(F['bottom'], lambda x, y: wool(x, y, 46, -0.9, False))


def hand_px(x, y, seed, shade=0.0):
    # knuckle creases on the front/back of the hand
    c = shade_skin(x, y, seed, shade, 0.8)
    if y == 22 and x in (2, 4, 6):
        return pick(SKIN, 2.0)
    return c


def paint_arm(T, F, seed, left):
    # sleeve rows 0..16 knit, 17..19 cuff rib, 20..23 hand
    def px(x, y, face):
        sh = -0.45 if face in ('right', 'left') and ((face == 'right') != left) else -0.15
        if y >= 20:
            return hand_px(x, y, seed + 3, sh)
        if y >= 17:
            return wool(x, y, seed + 1, 0.8 if (x % 2 == 0) else 0.25, False)
        return wool(x + (seed % 5), y, seed, sh - 0.25 * (y / 17.0))
    for face in ('front', 'back', 'right', 'left'):
        T.paint(F[face], lambda x, y, f=face: px(x, y, f))
    T.paint(F['top'], lambda x, y: wool(x, y, seed + 2, 0.5, False))
    T.paint(F['bottom'], lambda x, y: shade_skin(x, y, seed + 4, -0.6))


def paint_leg(T, F, seed, left):
    # pants rows 0..16, cuff 17..18, boot 19..23 (boot top lip at 19)
    def px(x, y, face):
        sh = -0.5 if face in ('right', 'left') else -0.1
        if y >= 19:
            c = leather(x, y, seed + 3, sh)
            if y == 19:
                return pick(LEATHER, 5.2)                  # folded top edge
            if y == 23:
                return pick(LEATHER, 1.0)                  # welt
            if face == 'front':
                if x in (3, 4) and y in (20, 21, 22) and y % 2 == 0:
                    return pick(LEATHER, 6)                # lace crossings
                if y >= 21 and 1 <= x <= 6:
                    return leather(x, y, seed + 3, sh + 0.5)  # toe cap
            return c
        if y >= 17:
            return denim(x, y, seed + 1, 0.9 if y == 17 else 0.2)   # rolled cuff
        d = denim(x, y, seed, sh - 0.3 * (y / 17.0))
        if face in ('right', 'left') and x == (7 if (face == 'right') != left else 0) and y % 2 == 0:
            return pick(DENIM, 5)                          # outer seam stitching
        return d
    for face in ('front', 'back', 'right', 'left'):
        T.paint(F[face], lambda x, y, f=face: px(x, y, f))
    T.paint(F['top'], lambda x, y: denim(x, y, seed + 2, -0.2))
    T.paint(F['bottom'], lambda x, y: pick(LEATHER, 0.6 + h2(x, y, seed) * 1.2))


def paint_overlays(T):
    # sweater: collar ring + hem band (raised ribbing); neckline stays open at the front
    J = JACKET
    def jfront(x, y):
        if y <= 1:
            if 5 <= x <= 10:
                return None
            return wool(x, y, 50, 1.0 if x % 2 == 0 else 0.4, False)
        if y == 2 and not (5 <= x <= 10):
            return wool(x, y, 51, -0.4, False)
        if 20 <= y <= 23:
            return wool(x, y, 52, 1.2 if x % 2 == 0 else 0.5, False)
        if y == 19:
            return wool(x, y, 53, -0.9, False)
        return None
    def jother(x, y, seed):
        if y <= 1:
            return wool(x, y, seed, 1.0 if x % 2 == 0 else 0.4, False)
        if 20 <= y <= 23:
            return wool(x, y, seed + 1, 1.2 if x % 2 == 0 else 0.5, False)
        if y == 19:
            return wool(x, y, seed + 2, -0.9, False)
        return None
    T.paint(J['front'], jfront)
    for f, s in (('back', 54), ('right', 55), ('left', 56)):
        T.paint(J[f], lambda x, y, s=s: jother(x, y, s))
    T.paint(J['top'], lambda x, y: wool(x, y, 57, 0.8, False))
    T.paint(J['bottom'], lambda x, y: wool(x, y, 58, 0.2, False))

    for S, seed in ((RSLEEVE, 60), (LSLEEVE, 70)):
        for f in ('front', 'back', 'right', 'left'):
            def sl(x, y, seed=seed):
                if 16 <= y <= 18:
                    return wool(x, y, seed, 1.1 if x % 2 == 0 else 0.4, False)
                if y == 15:
                    return wool(x, y, seed + 1, -0.8, False)
                return None
            T.paint(S[f], sl)
        T.paint(S['top'], lambda x, y, seed=seed: wool(x, y, seed + 2, 0.7, False))
        T.paint(S['bottom'], lambda x, y: None)

    for P, seed in ((RPANTS, 80), (LPANTS, 90)):
        for f in ('front', 'back', 'right', 'left'):
            def pn(x, y, seed=seed):
                if 16 <= y <= 18:
                    return denim(x, y, seed, 1.3 if y == 16 else 0.5)
                if y == 15:
                    return denim(x, y, seed + 1, -0.9)
                return None
            T.paint(P[f], pn)
        T.paint(P['top'], lambda x, y: None)
        T.paint(P['bottom'], lambda x, y: None)


def paint_tiles(T):
    # hair strand tile (stretched over spike faces)
    T.paint(TILE_HAIR, lambda x, y: shade_hair(x, y, 100, 0.0))
    for y in range(0, 16, 1):          # a few darker root pixels on the bottom rows
        pass
    # blade: near-black steel (used by the baked-in sword)
    BLK = [hexc(c) for c in ('#050507', '#0a0a10', '#11111a', '#1a1a26', '#272738', '#3b3b52', '#5a5a78')]
    T.paint(TILE_BLADE, lambda x, y: pick(BLK, 2.2 + (fbm(x * 1.5, y, 110, 4, 2) - 0.5) * 1.8 + (0.8 if y in (0, 15) else 0)))
    # guard / pommel: black with dull gunmetal edges
    T.paint(TILE_GUARD, lambda x, y: pick(BLK, 1.6 + (fbm(x, y, 120, 3, 2) - 0.5) * 1.6 + (1.2 if x in (0, 15) or y in (0, 15) else 0)))
    # grip: dark wrapped leather
    T.paint(TILE_GRIP, lambda x, y: pick(BLK, 1.0 + ((x + y) % 3 == 0) * 1.3 + (h2(x, y, 130) - 0.5) * 0.6))
    # eye gem: glowing red, orange core
    RED = [hexc(c) for c in ('#5a0508', '#9c0b10', '#d8181c', '#ff3b30', '#ff7a55')]
    T.paint(TILE_EYE, lambda x, y: pick(RED, 3.0 - (abs(x - 7.5) / 7.5) * 2.2 - (abs(y - 3.5) / 3.5) * 1.2))


def main():
    os.makedirs(OUT, exist_ok=True)
    T = Tex(128, 128)
    paint_head(T)
    paint_body(T)
    paint_arm(T, RARM, 1, False)
    paint_arm(T, LARM, 6, True)
    paint_leg(T, RLEG, 2, False)
    paint_leg(T, LLEG, 7, True)
    paint_overlays(T)
    paint_tiles(T)
    path = os.path.join(OUT, 'james.png')
    T.save(path)
    print('wrote', os.path.normpath(path))


if __name__ == '__main__':
    main()
