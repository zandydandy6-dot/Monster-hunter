"""Shadow figure (the trance 'person'): near-black smoke with two round, glowing red eyes.
Texture is 128x128: a 32x32 smoke tile used by every cube face, plus the 20x22 face at (64,0).
A second image (_glowmask) holds only the eyes; GeckoLib draws it full-bright.
Run:  python3 tools/gen_shadow.py
"""
import math
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from artlib import *  # noqa

OUT = os.path.join(os.path.dirname(__file__), '..', 'src', 'main', 'resources', 'assets', 'hagoyama', 'textures', 'entity')
SMOKE = [hexc(c) for c in ('#020203', '#05050a', '#0a0a12', '#10101c', '#181828', '#232338')]
TILE = (0, 0, 32, 32)
FACE = (64, 0, 20, 22)
EYE_R = 3.3
EYES = ((5.4, 9.6), (14.6, 9.6))      # centres inside the 20x22 face


def smoke(x, y, seed):
    t = 1.2 + fbm(x * 0.8, y * 0.45, seed, 9, 3) * 2.6 + (h2(x, y, seed + 4) - 0.5) * 0.7
    if fbm(x * 0.5, y * 0.3 + 40, seed + 9, 7, 2) > 0.66:
        t += 1.3                                   # lighter wisps drifting through the dark
    return pick(SMOKE, t)


def eye_pixel(lx, ly):
    """Returns (r,g,b) for the round red eye, or None outside every eye."""
    for cx, cy in EYES:
        dx, dy = lx + 0.5 - cx, ly + 0.5 - cy
        d = math.hypot(dx, dy)
        if d <= EYE_R:
            if d > EYE_R - 0.9:
                return hexc('#8f0c10')             # darker rim
            if abs(dx + 1.1) < 0.6 and abs(dy + 1.1) < 0.6:
                return hexc('#ffd8c0')             # one catch-light pixel
            if d < 1.7:
                return hexc('#ff5a3c')             # hot centre
            return hexc('#ff2a22')
    return None


def main():
    os.makedirs(OUT, exist_ok=True)
    T = Tex(128, 128)
    T.paint(TILE, lambda x, y: smoke(x, y, 7))
    # face: smoke, hollowed cheeks, faint red bleed around each eye, then the eyes
    def face(x, y):
        e = eye_pixel(x, y)
        if e:
            return e
        base = smoke(x, y, 21)
        for cx, cy in EYES:
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if EYE_R < d < EYE_R + 2.4:
                k = 1.0 - (d - EYE_R) / 2.4
                return lerp_c(base, hexc('#5a0c10'), 0.55 * k)
        return base
    T.paint(FACE, face)
    T.save(os.path.join(OUT, 'shadow_figure.png'))

    G = Tex(128, 128)
    G.paint(FACE, lambda x, y: eye_pixel(x, y))
    G.save(os.path.join(OUT, 'shadow_figure_glowmask.png'))
    print('shadow textures written')


if __name__ == '__main__':
    main()
