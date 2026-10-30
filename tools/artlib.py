"""Tiny pixel-art toolkit shared by the texture generators (numpy + Pillow only)."""
import math
import numpy as np
from PIL import Image


def hexc(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def h2(x, y, s=0):
    """Deterministic hash noise in [0,1)."""
    n = (int(x) * 374761393 + int(y) * 668265263 + int(s) * 2147483647) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    n ^= n >> 16
    return (n & 0xFFFF) / 65536.0


def _smooth(t):
    return t * t * (3 - 2 * t)


def vnoise(x, y, scale=4.0, seed=0):
    """Smooth value noise in [0,1]."""
    fx, fy = x / scale, y / scale
    x0, y0 = math.floor(fx), math.floor(fy)
    tx, ty = _smooth(fx - x0), _smooth(fy - y0)
    a, b = h2(x0, y0, seed), h2(x0 + 1, y0, seed)
    c, d = h2(x0, y0 + 1, seed), h2(x0 + 1, y0 + 1, seed)
    return (a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + d * tx) * ty


def fbm(x, y, seed=0, base=6.0, octaves=3):
    tot, amp, norm, sc = 0.0, 1.0, 0.0, base
    for o in range(octaves):
        tot += vnoise(x, y, sc, seed + o * 17) * amp
        norm += amp
        amp *= 0.5
        sc *= 0.5
    return tot / norm


def pick(ramp, t):
    """Pick from a dark->light colour list with a float index (clamped)."""
    i = int(round(t))
    i = max(0, min(len(ramp) - 1, i))
    return ramp[i]


class Tex:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.a = np.zeros((h, w, 4), np.uint8)

    def put(self, x, y, c, a=255):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.a[y, x] = (c[0], c[1], c[2], a)

    def clear(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.a[y, x] = (0, 0, 0, 0)

    def get(self, x, y):
        return tuple(int(v) for v in self.a[y, x])

    def paint(self, rect, fn):
        """fn(lx, ly) -> (r,g,b) | (r,g,b,a) | None (leave transparent)."""
        x0, y0, w, h = rect
        for ly in range(h):
            for lx in range(w):
                c = fn(lx, ly)
                if c is None:
                    continue
                self.put(x0 + lx, y0 + ly, c[:3], c[3] if len(c) > 3 else 255)

    def save(self, path):
        Image.fromarray(self.a, 'RGBA').save(path, optimize=True)


def box_faces(u, v, w, h, d):
    """Java/Bedrock box-UV layout -> dict of face rects (x, y, w, h).
    right = character's right side, left = character's left side."""
    return {
        'top': (u + d, v, w, d),
        'bottom': (u + d + w, v, w, d),
        'right': (u, v + d, d, h),
        'front': (u + d, v + d, w, h),
        'left': (u + d + w, v + d, d, h),
        'back': (u + 2 * d + w, v + d, w, h),
    }


def box_extent(u, v, w, h, d):
    return (u, v, 2 * d + 2 * w, d + h)


def lerp_c(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))
