"""Offline preview of the GeckoLib models: reads the real geo/animation JSON + textures and rasterises them.
Not a Minecraft renderer - it follows the vanilla box-UV layout, so it catches wrong UVs, missing faces,
floating parts and silly poses. Run:  python3 tools/preview.py   (writes PNGs to /home/claude/preview)
"""
import json
import math
import os
import sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from artlib import box_faces  # noqa

RES = os.path.join(os.path.dirname(__file__), '..', 'src', 'main', 'resources', 'assets', 'hagoyama')
FACE_NAME = {'north': 'front', 'south': 'back', 'west': 'right', 'east': 'left', 'up': 'top', 'down': 'bottom'}


def load_json(rel):
    with open(os.path.join(RES, rel)) as f:
        return json.load(f)


def load_tex(rel):
    return np.array(Image.open(os.path.join(RES, rel)).convert('RGBA'))


def bones_of(geo):
    g = geo['minecraft:geometry'][0]
    return {b['name']: b for b in g['bones']}, g['description']


def face_rects(cube):
    """{face: (x, y, w, h)} texture rect of every face of a cube."""
    uv = cube['uv']
    if isinstance(uv, dict):
        return {k: (v['uv'][0], v['uv'][1], v['uv_size'][0], v['uv_size'][1]) for k, v in uv.items()}
    w, h, d = cube['size']
    f = box_faces(uv[0], uv[1], int(w), int(h), int(d))
    return {k: f[v] for k, v in FACE_NAME.items()}


def corners(cube):
    inf = cube.get('inflate', 0) or 0
    ox, oy, oz = cube['origin']
    sx, sy, sz = cube['size']
    x0, x1, y0, y1, z0, z1 = ox - inf, ox + sx + inf, oy - inf, oy + sy + inf, oz - inf, oz + sz + inf
    return {
        'north': [(x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (x0, y0, z0)],
        'south': [(x1, y1, z1), (x0, y1, z1), (x0, y0, z1), (x1, y0, z1)],
        'west': [(x0, y1, z1), (x0, y1, z0), (x0, y0, z0), (x0, y0, z1)],
        'east': [(x1, y1, z0), (x1, y1, z1), (x1, y0, z1), (x1, y0, z0)],
        'up': [(x0, y1, z1), (x1, y1, z1), (x1, y1, z0), (x0, y1, z0)],
        'down': [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)],
    }


def rot_matrix(rx, ry, rz):
    """Z*Y*X order (GeckoLib's rotationZYX). Angles in degrees; rx sign flipped so negative = arm forward."""
    ax, ay, az = math.radians(-rx), math.radians(ry), math.radians(rz)
    cx, sx, cy, sy, cz, sz = math.cos(ax), math.sin(ax), math.cos(ay), math.sin(ay), math.cos(az), math.sin(az)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def sample_anim(anim, t):
    """-> {bone: (rot[3], pos[3])} at time t (linear)."""
    out = {}
    for bname, ch in anim.get('bones', {}).items():
        rot, pos = np.zeros(3), np.zeros(3)
        for key, target in (('rotation', 'rot'), ('position', 'pos')):
            frames = ch.get(key)
            if not frames:
                continue
            ks = sorted((float(k), np.array(v, float)) for k, v in frames.items())
            if t <= ks[0][0]:
                v = ks[0][1]
            elif t >= ks[-1][0]:
                v = ks[-1][1]
            else:
                v = ks[-1][1]
                for (t0, v0), (t1, v1) in zip(ks, ks[1:]):
                    if t0 <= t <= t1:
                        v = v0 + (v1 - v0) * ((t - t0) / (t1 - t0))
                        break
            if target == 'rot':
                rot = v
            else:
                pos = v
        out[bname] = (rot, pos)
    return out


def bone_point(bones, name, p, pose):
    """Apply bone + parent animation transforms to a model-space point."""
    p = np.array(p, float)
    b = name
    while b:
        bone = bones[b]
        rot, pos = pose.get(b, (np.zeros(3), np.zeros(3)))
        pv = np.array(bone['pivot'], float)
        if rot.any():
            p = rot_matrix(*rot) @ (p - pv) + pv
        p = p + pos
        b = bone.get('parent')
    return p


def render(geo, tex, pose=None, yaw=0.0, scale=4.0, size=(260, 320), ground=0.0, ycenter=None, hide=()):
    bones, desc = bones_of(geo)
    pose = pose or {}
    W, H = size
    img = np.zeros((H, W, 4), np.uint8)
    zbuf = np.full((H, W), -1e9)
    th, tw = tex.shape[:2]
    cy_, sy_ = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    if ycenter is None:
        ycenter = 32
    L = np.array([0.35, 0.8, 0.6]); L /= np.linalg.norm(L)
    for bname, bone in bones.items():
        if bname in hide:
            continue
        for cube in bone.get('cubes', []):
            cs = corners(cube)
            rects = face_rects(cube)
            cc = np.array(cube['origin']) + np.array(cube['size']) / 2
            cc = bone_point(bones, bname, cc, pose)
            for face, pts in cs.items():
                P = [bone_point(bones, bname, p, pose) for p in pts]
                Wd = [np.array([p[0], p[1], -p[2]]) for p in P]          # model (front=-z) -> world (front=+z)
                cw = np.array([cc[0], cc[1], -cc[2]])
                fc = sum(Wd) / 4
                n = np.cross(Wd[1] - Wd[0], Wd[3] - Wd[0]); nn = np.linalg.norm(n)
                if nn == 0:
                    continue
                n = n / nn
                if np.dot(n, fc - cw) < 0:
                    n = -n
                scr = []
                for w in Wd:
                    x = w[0] * cy_ + w[2] * sy_
                    z = -w[0] * sy_ + w[2] * cy_
                    scr.append((W / 2 + x * scale, H - 14 - (w[1] - ground) * scale, z))
                nrot = np.array([n[0] * cy_ + n[2] * sy_, n[1], -n[0] * sy_ + n[2] * cy_])
                if nrot[2] < -0.05:
                    continue                                                 # back-face
                light = 0.5 + 0.5 * max(0.0, float(np.dot(nrot, L)))
                rx, ry, rw, rh = rects[face]
                # (s,t) at TL, TR, BR, BL
                st = [(0, 0), (1, 0), (1, 1), (0, 1)]
                for tri in ((0, 1, 2), (0, 2, 3)):
                    A, B, C = [scr[i] for i in tri]
                    minx, maxx = int(max(0, math.floor(min(A[0], B[0], C[0])))), int(min(W - 1, math.ceil(max(A[0], B[0], C[0]))))
                    miny, maxy = int(max(0, math.floor(min(A[1], B[1], C[1])))), int(min(H - 1, math.ceil(max(A[1], B[1], C[1]))))
                    den = (B[1] - C[1]) * (A[0] - C[0]) + (C[0] - B[0]) * (A[1] - C[1])
                    if abs(den) < 1e-9:
                        continue
                    for py in range(miny, maxy + 1):
                        for px in range(minx, maxx + 1):
                            qx, qy = px + 0.5, py + 0.5
                            l1 = ((B[1] - C[1]) * (qx - C[0]) + (C[0] - B[0]) * (qy - C[1])) / den
                            l2 = ((C[1] - A[1]) * (qx - C[0]) + (A[0] - C[0]) * (qy - C[1])) / den
                            l3 = 1 - l1 - l2
                            if l1 < -1e-4 or l2 < -1e-4 or l3 < -1e-4:
                                continue
                            z = l1 * A[2] + l2 * B[2] + l3 * C[2]
                            if z <= zbuf[py, px]:
                                continue
                            s = l1 * st[tri[0]][0] + l2 * st[tri[1]][0] + l3 * st[tri[2]][0]
                            t = l1 * st[tri[0]][1] + l2 * st[tri[1]][1] + l3 * st[tri[2]][1]
                            tx = int(min(rx + rw - 1, max(rx, math.floor(rx + s * rw))))
                            ty = int(min(ry + rh - 1, max(ry, math.floor(ry + t * rh))))
                            if tx >= tw or ty >= th:
                                continue
                            texel = tex[ty, tx]
                            if texel[3] < 26:
                                continue
                            zbuf[py, px] = z
                            img[py, px] = (int(texel[0] * light), int(texel[1] * light), int(texel[2] * light), 255)
    return Image.fromarray(img, 'RGBA')


def sheet(images, bg=(88, 92, 104), pad=6):
    w = sum(i.width for i in images) + pad * (len(images) + 1)
    h = max(i.height for i in images) + 2 * pad
    out = Image.new('RGBA', (w, h), bg + (255,))
    x = pad
    for im in images:
        out.alpha_composite(im, (x, pad))
        x += im.width + pad
    return out


def main():
    outdir = '/home/claude/preview'
    os.makedirs(outdir, exist_ok=True)
    jg, jt = load_json('geo/entity/james.geo.json'), load_tex('textures/entity/james.png')
    ja = load_json('animations/entity/james.animation.json')['animations']
    views = [render(jg, jt, yaw=y, scale=3.6, size=(230, 330)) for y in (0, 35, 90, 180)]
    sheet(views).convert('RGB').save(outdir + '/james_views.png')
    poses = []
    for name, t in (('animation.james.idle', 0), ('animation.james.walk', 0.25), ('animation.james.slash_1', 0.14),
                    ('animation.james.slash_1', 0.3), ('animation.james.slash_2', 0.3), ('animation.james.slash_3', 0.2)):
        poses.append(render(jg, jt, pose=sample_anim(ja[name], t), yaw=35, scale=3.2, size=(220, 330)))
    sheet(poses).convert('RGB').save(outdir + '/james_poses.png')
    sg, st_ = load_json('geo/entity/shadow_figure.geo.json'), load_tex('textures/entity/shadow_figure.png')
    sa = load_json('animations/entity/shadow_figure.animation.json')['animations']['animation.shadow_figure.idle']
    sv = [render(sg, st_, yaw=y, scale=3.6, size=(230, 340)) for y in (0, 40)]
    sv.append(render(sg, st_, pose=sample_anim(sa, 3.0), yaw=0, scale=3.6, size=(230, 340)))
    glow = load_tex('textures/entity/shadow_figure_glowmask.png')
    sv.append(render(sg, glow, yaw=0, scale=3.6, size=(230, 340)))
    sheet(sv, bg=(70, 74, 86)).convert('RGB').save(outdir + '/shadow_views.png')
    print('previews written to', outdir)


if __name__ == '__main__':
    main()
