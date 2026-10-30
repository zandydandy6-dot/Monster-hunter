"""Item icons (32x32), worn-armor layers (128x64, 2x vanilla) and the Clear Eye health-bar sprite.
Run:  python3 tools/gen_items.py
"""
import math
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from artlib import *  # noqa
import gen_james as J

ASSETS = os.path.join(os.path.dirname(__file__), '..', 'src', 'main', 'resources', 'assets', 'hagoyama', 'textures')
BLK = [hexc(c) for c in ('#030304', '#08080c', '#101018', '#1a1a26', '#2a2a3c', '#43435c', '#6d6d8c', '#a3a3c2')]
RED = [hexc(c) for c in ('#4a0406', '#8f0a0f', '#d8181c', '#ff3b30', '#ff8a5c')]


def out(*p):
    path = os.path.normpath(os.path.join(ASSETS, *p))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


# ---------------------------------------------------------------- black sword icon ------
def make_sword():
    T = Tex(32, 32)
    r2 = math.sqrt(2.0)
    for y in range(32):
        for x in range(32):
            X, Y = x + 0.5, 32 - (y + 0.5)
            s = (X + Y) / r2          # along the sword (hilt -> tip)
            t = (Y - X) / r2          # across (positive = upper-left side)
            c = None
            if 4.0 <= s < 7.6 and (t * t + (s - 5.8) ** 2 * 1.2) <= 4.2:        # pommel
                c = pick(BLK, 2.2 + (t < 0) * -0.6 + (t > 0.8) * 1.4)
            elif 7.6 <= s < 14.0 and abs(t) <= 1.5:                              # grip, wrapped
                c = pick(BLK, 1.2 + (int(s * 1.6) % 2 == 0) * 1.1)
            elif 14.0 <= s < 16.2 and abs(t) <= 6.2 - abs(s - 15.1) * 1.2:        # guard
                c = pick(BLK, 2.4 + (t > 0) * 0.6 + (abs(t) > 4.5) * 1.3)
            elif 16.2 <= s <= 41.6:                                              # blade
                hw = 2.7 if s < 35.5 else max(0.35, 2.7 - (s - 35.5) * 0.45)
                if abs(t) <= hw:
                    base = 2.4 + (fbm(x, y, 5, 4, 2) - 0.5) * 0.8
                    if t > hw - 1.0:
                        base -= 1.1                                              # shaded bevel
                    elif t < -(hw - 1.0):
                        base += 2.6                                              # lit edge
                    elif abs(t) < 0.55:
                        base -= 0.9                                              # fuller groove
                    c = pick(BLK, base)
                    if s > 40.3 and t < 0.3:
                        c = pick(BLK, 7)                                         # tip glint
            if c:
                T.put(x, y, c)
    # eye gem on the guard (round, red)
    for y in range(32):
        for x in range(32):
            X, Y = x + 0.5, 32 - (y + 0.5)
            s, t = (X + Y) / r2, (Y - X) / r2
            d = math.hypot(s - 15.1, t)
            if d <= 1.45:
                T.put(x, y, pick(RED, 3.3 - d * 1.5 + (t < -0.3 and s > 15.1) * 0.9))
    # dark outline so the black blade keeps a shape on dark slots
    snap = T.a[:, :, 3].copy()           # read from a snapshot so the outline cannot spread
    for y in range(32):
        for x in range(32):
            if snap[y, x]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < 32 and 0 <= ny < 32 and snap[ny, nx]:
                    T.put(x, y, (2, 2, 4))
                    break
    T.save(out('item', 'hagoyama.png'))


# ---------------------------------------------------------------- clothing icons --------
def seg_dist(px, py, ax, ay, bx, by):
    vx, vy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / (vx * vx + vy * vy)))
    return math.hypot(px - (ax + vx * t), py - (ay + vy * t))


def finish(T, mask, painter, outline):
    for y in range(32):
        for x in range(32):
            if mask[y][x]:
                T.put(x, y, painter(x, y))
    for y in range(32):
        for x in range(32):
            if mask[y][x]:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if not (0 <= nx < 32 and 0 <= ny < 32) or not mask[ny][nx]:
                        T.put(x, y, outline)
                        break


def make_sweater():
    T = Tex(32, 32)
    m = [[False] * 32 for _ in range(32)]
    kind = [[0] * 32 for _ in range(32)]     # 0 body, 1 collar, 2 cuff, 3 hem, 4 neck skin
    for y in range(32):
        for x in range(32):
            px, py = x + 0.5, y + 0.5
            body = 9 <= px <= 23 and 7 <= py <= 27
            sl = seg_dist(px, py, 9.5, 9.5, 3.5, 21.5) <= 3.3 or seg_dist(px, py, 22.5, 9.5, 28.5, 21.5) <= 3.3
            if body or sl:
                m[y][x] = True
            if m[y][x]:
                if ((px - 16) / 4.4) ** 2 + ((py - 7.2) / 3.2) ** 2 <= 1.0 and py < 9.5:
                    kind[y][x] = 4
                elif ((px - 16) / 5.6) ** 2 + ((py - 7.2) / 4.2) ** 2 <= 1.0 and py < 10.5:
                    kind[y][x] = 1
                elif py >= 24.5 and body:
                    kind[y][x] = 3
                elif seg_dist(px, py, 3.5, 21.5, 28.5, 21.5) < 0.1 or (sl and (py > 19.2)):
                    kind[y][x] = 2
    for y in range(32):
        for x in range(32):
            if kind[y][x] == 4:
                m[y][x] = False   # open neckline (transparent)
    def paint(x, y):
        k = kind[y][x]
        if k == 1:
            return J.wool(x, y, 3, 1.0 if x % 2 == 0 else 0.3, False)
        if k == 2:
            return J.wool(x, y, 4, 1.0 if x % 2 == 0 else 0.3, False)
        if k == 3:
            return J.wool(x, y, 5, 1.1 if x % 2 == 0 else 0.4, False)
        shade = -0.5 * ((x - 16) / 12.0) ** 2 - 0.35 * (y / 32.0) + 0.25
        return J.wool(x, y, 6, shade)
    finish(T, m, paint, hexc('#0b2540'))
    T.save(out('item', 'james_sweater.png'))


def make_trousers():
    T = Tex(32, 32)
    m = [[False] * 32 for _ in range(32)]
    kind = [[0] * 32 for _ in range(32)]
    for y in range(32):
        for x in range(32):
            px, py = x + 0.5, y + 0.5
            waist = 9 <= px <= 23 and 4 <= py <= 8
            left = 9 <= px <= 15.4 and 8 <= py <= 29
            right = 16.6 <= px <= 23 and 8 <= py <= 29
            crotch = 9 <= px <= 23 and 8 <= py <= 14.5
            if waist or left or right or crotch:
                m[y][x] = True
                if py <= 6.0:
                    kind[y][x] = 1
                elif py >= 26.5:
                    kind[y][x] = 2
    def paint(x, y):
        k = kind[y][x]
        if k == 1:
            return pick(J.DENIM, 1.5 + (x % 3 == 0) * 1.4 + (fbm(x, y, 2, 3, 2) - 0.5))
        if k == 2:
            return J.denim(x, y, 8, 1.1)
        c = J.denim(x, y, 9, -0.2 + (0.4 if x < 16 else -0.2))
        if x in (15, 16) and y > 14:
            return pick(J.DENIM, 0.8)
        return c
    finish(T, m, paint, hexc('#0a1f36'))
    # waistband button + fly
    T.put(15, 5, hexc('#d9b45a')); T.put(16, 5, hexc('#a98534'))
    for y in range(8, 14):
        T.put(16, y, pick(J.DENIM, 0.9))
    T.save(out('item', 'james_trousers.png'))


def make_boots():
    T = Tex(32, 32)
    m = [[False] * 32 for _ in range(32)]
    kind = [[0] * 32 for _ in range(32)]
    for ox in (2, 17):
        for y in range(32):
            for x in range(32):
                lx, ly = x - ox, y
                shaft = 1 <= lx <= 6 and 6 <= ly <= 20
                foot = 1 <= lx <= 12 and 17 <= ly <= 24
                toe = 11 <= lx <= 13 and 19 <= ly <= 24
                if shaft or foot or toe:
                    m[y][x] = True
                    if ly <= 8:
                        kind[y][x] = 1
                    elif ly >= 23:
                        kind[y][x] = 2
    def paint(x, y):
        k = kind[y][x]
        if k == 1:
            return pick(J.LEATHER, 5.3 - (y % 2) * 0.4 + (fbm(x, y, 3, 3, 2) - 0.5))
        if k == 2:
            return pick(J.LEATHER, 0.6 + h2(x, y, 4) * 0.8)
        c = J.leather(x, y, 5, -0.2 + (0.5 if (x % 15) < 4 else 0))
        return c
    finish(T, m, paint, hexc('#1b0e06'))
    for ox in (2, 17):          # laces
        for y in (11, 14, 17):
            T.put(ox + 4, y, pick(J.LEATHER, 6.2)); T.put(ox + 3, y + 1, pick(J.LEATHER, 5.6))
    T.save(out('item', 'james_boots.png'))


# ---------------------------------------------------------------- worn armour layers ----
def make_armor():
    # 2x vanilla armour layout; both layers 128x64
    L1 = Tex(128, 64)
    body = box_faces(32, 32, 16, 24, 8)
    arm = box_faces(80, 32, 8, 24, 8)
    leg = box_faces(0, 32, 8, 24, 8)
    # ---- layer 1: sweater on body + arm, boots on the leg rows 19..23 ----
    def sweater_front(x, y):
        if y <= 1 and 5 <= x <= 10:
            return None
        if y <= 2:
            return J.wool(x, y, 40, 0.9, False)
        if y >= 20:
            return J.wool(x, y, 41, 1.0 if x % 2 == 0 else 0.3, False)
        return J.wool(x, y, 42, -0.7 * (abs(x - 7.5) / 8.0) ** 2)
    L1.paint(body['front'], sweater_front)
    L1.paint(body['back'], lambda x, y: J.wool(x, y, 43, -0.5, 2 < y < 20))
    L1.paint(body['right'], lambda x, y: J.wool(x, y, 44, -0.6))
    L1.paint(body['left'], lambda x, y: J.wool(x + 3, y, 44, -0.6))
    L1.paint(body['top'], lambda x, y: J.wool(x, y, 45, 0.5, False))
    L1.paint(body['bottom'], lambda x, y: J.wool(x, y, 46, -0.8, False))
    def sleeve(x, y, seed, sh):
        if y >= 20:
            return None
        if y >= 17:
            return J.wool(x, y, seed + 1, 1.0 if x % 2 == 0 else 0.3, False)
        return J.wool(x + seed % 5, y, seed, sh - 0.25 * (y / 17.0))
    for face in ('front', 'back', 'right', 'left'):
        L1.paint(arm[face], lambda x, y: sleeve(x, y, 1, -0.2))
    L1.paint(arm['top'], lambda x, y: J.wool(x, y, 2, 0.5, False))
    L1.paint(arm['bottom'], lambda x, y: None)
    # boots (rows 19..23 of the leg)
    def boot(x, y, face):
        if y < 19:
            return None
        if y == 19:
            return pick(J.LEATHER, 5.2)
        if y == 23:
            return pick(J.LEATHER, 1.0)
        return J.leather(x, y, 53, -0.4 if face in ('right', 'left') else 0.0)
    for face in ('front', 'back', 'right', 'left'):
        L1.paint(leg[face], lambda x, y, f=face: boot(x, y, f))
    L1.paint(leg['bottom'], lambda x, y: pick(J.LEATHER, 0.6 + h2(x, y, 9) * 1.2))
    L1.save(out('models', 'armor', 'james_layer_1.png'))

    # ---- layer 2: trousers (hips on the body region, full leg) ----
    L2 = Tex(128, 64)
    def waist(x, y):
        if y < 14:
            return None
        if y <= 15:
            return pick(J.DENIM, 1.4 + (x % 3 == 0) * 1.3)
        return J.denim(x, y, 60, -0.2)
    for face in ('front', 'back', 'right', 'left'):
        L2.paint(body[face], waist)
    L2.paint(body['bottom'], lambda x, y: J.denim(x, y, 61, -0.7))
    def trouser(x, y, face):
        if 17 <= y <= 18:
            return J.denim(x, y, 62, 1.0 if y == 17 else 0.3)
        c = J.denim(x, y, 63, -0.4 if face in ('right', 'left') else 0.0)
        return c
    for face in ('front', 'back', 'right', 'left'):
        L2.paint(leg[face], lambda x, y, f=face: trouser(x, y, f))
    L2.paint(leg['top'], lambda x, y: J.denim(x, y, 64, -0.3))
    L2.paint(leg['bottom'], lambda x, y: J.denim(x, y, 65, -0.6))
    L2.save(out('models', 'armor', 'james_layer_2.png'))


# ---------------------------------------------------------------- health bar ------------
def make_bar():
    T = Tex(64, 32)
    STEEL = [hexc(c) for c in ('#07070a', '#14141c', '#23232e', '#34343f', '#4c4c5c', '#6f6f82', '#9a9aaf')]
    GOLD = [hexc(c) for c in ('#4a3412', '#7d5a1e', '#b8892f', '#e0b44e', '#f6d98a')]
    # frame 64x16: rounded rectangle plate with an eye emblem on the left
    def inside_round(x, y, x0, y0, x1, y1, r):
        if x < x0 or x > x1 or y < y0 or y > y1:
            return False
        cx = min(max(x, x0 + r), x1 - r)
        cy = min(max(y, y0 + r), y1 - r)
        return math.hypot(x - cx, y - cy) <= r + 0.35
    for y in range(16):
        for x in range(64):
            if not inside_round(x + 0.5, y + 0.5, 0.0, 0.5, 64.0, 15.5, 4.0):
                continue
            edge = not inside_round(x + 0.5, y + 0.5, 1.0, 1.5, 63.0, 14.5, 3.2)
            if edge:
                T.put(x, y, STEEL[0])
                continue
            hi = y <= 2 or not inside_round(x + 0.5, y + 0.5, 2.0, 2.5, 62.0, 13.5, 2.6)
            t = 3.0 + (fbm(x, y, 7, 3, 2) - 0.5) * 1.4 + (1.6 if y <= 2 else 0) - (1.2 if y >= 13 else 0) + (0.8 if hi and y > 2 else 0)
            T.put(x, y, pick(STEEL, t))
    # inner dark plate (where the gauge sits): x 14..61, y 4..11
    for y in range(4, 12):
        for x in range(14, 62):
            seg = (x - 14) % 8 == 7
            T.put(x, y, hexc('#0b0507') if not seg else hexc('#1a0b0e'))
    for x in range(14, 62):
        T.put(x, 3, STEEL[0]); T.put(x, 12, STEEL[5] if x % 2 == 0 else STEEL[4])
    for y in range(3, 13):
        T.put(13, y, STEEL[0]); T.put(62, y, STEEL[0])
    # gold rivets
    for (rx, ry) in ((16, 1), (30, 1), (46, 1), (60, 1), (16, 14), (46, 14), (60, 14)):
        T.put(rx, ry, GOLD[3]); T.put(rx + 1, ry, GOLD[1]); T.put(rx, ry + 1 if ry < 8 else ry - 1, GOLD[0])
    # eye emblem: circular red eye in a gold ring (x 1..12, y 2..13)
    cx, cy = 7.0, 8.0
    for y in range(16):
        for x in range(0, 14):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if d <= 6.2:
                if d > 5.0:
                    T.put(x, y, GOLD[min(4, max(0, int(3.2 - (y - 8) * 0.18 + (x < 7) * 0.8)))])
                elif d > 4.2:
                    T.put(x, y, STEEL[0])
                elif d > 1.6:
                    k = 3.4 - d * 0.42 + (y < 8) * 0.5
                    T.put(x, y, pick(RED, k))
                else:
                    T.put(x, y, hexc('#050203'))
    T.put(6, 6, hexc('#ffe0c8')); T.put(5, 7, hexc('#ff9a70'))     # catch-light
    # fill sprite at (0,16) 48x8: neutral grayscale so the health tint multiplies cleanly
    for y in range(8):
        for x in range(48):
            base = (255, 232, 214, 196, 182, 166, 148, 128)[y]
            base += int((h2(x, y, 3) - 0.5) * 14)
            if x % 8 == 7:
                base -= 26
            base = max(60, min(255, base))
            T.put(x, 16 + y, (base, base, base))
    T.save(out('gui', 'clear_eye_bar.png'))


if __name__ == '__main__':
    make_sword()
    make_sweater()
    make_trousers()
    make_boots()
    make_armor()
    make_bar()
    print('items, armour and bar written')
