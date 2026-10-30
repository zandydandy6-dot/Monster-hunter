"""GeckoLib models + animations (James, shadow figure) and PlayerAnimator sword animations.

Models are authored at 2x vanilla scale (1 unit = 1/32 block) so the 128x128 skin gets 16x16 face texels;
the renderers call withScale(0.5F) to bring them back to normal size.
Run:  python3 tools/gen_models.py
"""
import json
import math
import os

RES = os.path.join(os.path.dirname(__file__), '..', 'src', 'main', 'resources', 'assets', 'hagoyama')


def write(rel, data):
    path = os.path.normpath(os.path.join(RES, rel))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=1)
    return path


def r(v):
    return round(v, 3)


def cube(origin, size, uv, inflate=None):
    c = {'origin': [r(v) for v in origin], 'size': [r(v) for v in size], 'uv': uv}
    if inflate:
        c['inflate'] = inflate
    return c


def tile_uv(rect, face=None):
    """Per-face UV where every face samples the same texture tile (uniform noise tiles)."""
    x, y, w, h = rect
    f = {'uv': [x, y], 'uv_size': [w, h]}
    return {k: dict(f) for k in ('north', 'east', 'south', 'west', 'up', 'down')}


def bone(name, parent, pivot, cubes=None):
    b = {'name': name, 'pivot': [r(v) for v in pivot]}
    if parent:
        b['parent'] = parent
    if cubes:
        b['cubes'] = cubes
    return b


def geo(identifier, tw, th, bones):
    return {
        'format_version': '1.12.0',
        'minecraft:geometry': [{
            'description': {'identifier': identifier, 'texture_width': tw, 'texture_height': th,
                            'visible_bounds_width': 6, 'visible_bounds_height': 6,
                            'visible_bounds_offset': [0, 1.5, 0]},
            'bones': bones}]}


# ------------------------------------------------------------------ voxel spikes ---------
def spike(base, direction, length, size, rect):
    """Stack of shrinking axis-aligned cubes (no rotation => no rotation-order ambiguity)."""
    d = [direction[0], direction[1], direction[2]]
    n = math.sqrt(sum(v * v for v in d))
    d = [v / n for v in d]
    cubes, dist, s = [], 0.0, size
    i = 0
    while dist < length and s > 0.9:
        c = [base[k] + d[k] * dist for k in range(3)]
        cubes.append(cube([c[0] - s / 2, c[1] - s / 2, c[2] - s / 2], [s, s, s], tile_uv(rect)))
        dist += s * 0.72
        s = max(1.0, s * 0.8)
        i += 1
    return cubes


HAIR_TILE = (112, 32, 16, 16)
BLADE_TILE = (112, 48, 16, 16)
GUARD_TILE = (112, 64, 16, 16)
GRIP_TILE = (112, 80, 16, 8)
EYE_TILE = (112, 88, 16, 8)

SPIKES = [
    # base centre (x,y,z), direction, length, base size       (head spans x+-8, y 48..64, z+-8)
    ((0, 63, -2), (0, 1, -0.25), 15, 6.5), ((-4, 63, 1), (-0.45, 1, 0), 13, 5.5), ((4, 63, 1), (0.45, 1, 0), 13, 5.5),
    ((0, 63, 4), (0, 1, 0.4), 12, 5.5), ((-5, 62, -4), (-0.7, 0.8, -0.3), 11, 5), ((5, 62, -4), (0.7, 0.8, -0.3), 11, 5),
    ((-8.5, 58, 0), (-1, 0.35, 0), 13, 6), ((8.5, 58, -1), (1, 0.35, 0), 16, 6.5),
    ((-8.5, 54, 3), (-1, -0.2, 0.4), 10, 5), ((8.5, 54, 3), (1, -0.1, 0.4), 11, 5),
    ((0, 60, 8.5), (0, 0.3, 1), 13, 6), ((-4, 57, 8.5), (-0.4, -0.1, 1), 11, 5.5), ((4, 57, 8.5), (0.4, -0.1, 1), 11, 5.5),
    ((0, 54, 8.5), (0, -0.5, 1), 10, 5), ((-3, 62, -8.6), (-0.1, 0.2, -1), 6, 3.8), ((3, 62, -8.6), (0.1, 0.2, -1), 6, 3.8),
]


def james_geo():
    head_cubes = [cube([-8, 48, -8], [16, 16, 16], [0, 0]),
                  cube([-8, 48, -8], [16, 16, 16], [64, 0], 1.0)]
    for base, dr, ln, sz in SPIKES:
        head_cubes += spike(base, dr, ln, sz, HAIR_TILE)
    # --- the black Hagoyama sword, baked into the right hand (blade points forward = -Z) ---
    sw = [
        cube([-13.2, 25.3, -7], [2.4, 2.4, 14], tile_uv(GRIP_TILE)),             # grip through the fist
        cube([-13.6, 24.8, 7], [3.2, 3.4, 2.6], tile_uv(GUARD_TILE)),            # pommel
        cube([-13.2, 22.4, -9.5], [2.4, 8.2, 2], tile_uv(GUARD_TILE)),           # cross-guard
        cube([-13.0, 23.6, -31.5], [2.0, 5.8, 22], tile_uv(BLADE_TILE)),         # blade (about one block long)
        cube([-12.8, 24.2, -36.5], [1.6, 4.6, 5.0], tile_uv(BLADE_TILE)),        # tip steps
        cube([-12.6, 24.9, -40.5], [1.2, 3.2, 4.0], tile_uv(BLADE_TILE)),
        cube([-12.4, 25.5, -43.5], [0.8, 2.0, 3.0], tile_uv(BLADE_TILE)),
        cube([-13.9, 25.4, -9.2], [0.7, 2.2, 1.2], tile_uv(EYE_TILE)),           # red eye gems (both sides)
        cube([-10.8, 25.4, -9.2], [0.7, 2.2, 1.2], tile_uv(EYE_TILE)),
    ]
    bones = [
        bone('root', None, [0, 0, 0]),
        bone('body', 'root', [0, 24, 0], [cube([-8, 24, -4], [16, 24, 8], [32, 32]),
                                          cube([-8, 24, -4], [16, 24, 8], [32, 64], 0.5)]),
        bone('head', 'body', [0, 48, 0], head_cubes),
        bone('right_arm', 'body', [-10, 44, 0], [cube([-16, 24, -4], [8, 24, 8], [80, 32]),
                                                  cube([-16, 24, -4], [8, 24, 8], [80, 64], 0.5)]),
        bone('sword', 'right_arm', [-12, 26.5, 0], sw),
        bone('left_arm', 'body', [10, 44, 0], [cube([8, 24, -4], [8, 24, 8], [64, 96]),
                                                cube([8, 24, -4], [8, 24, 8], [96, 96], 0.5)]),
        bone('right_leg', 'root', [-3.8, 24, 0], [cube([-7.8, 0, -4], [8, 24, 8], [0, 32]),
                                                   cube([-7.8, 0, -4], [8, 24, 8], [0, 64], 0.5)]),
        bone('left_leg', 'root', [3.8, 24, 0], [cube([-0.2, 0, -4], [8, 24, 8], [32, 96]),
                                                 cube([-0.2, 0, -4], [8, 24, 8], [0, 96], 0.5)]),
    ]
    return geo('geometry.james', 128, 128, bones)


# ------------------------------------------------------------------ animations -----------
def kf(frames):
    return {('%.2f' % t): list(v) for t, v in frames}


def anim(length, loop, bones):
    return {'loop': loop, 'animation_length': length, 'bones': bones}


def james_anims():
    P = lambda *a: a
    idle = anim(4.0, True, {
        'body': {'position': kf([(0, P(0, 0, 0)), (2, P(0, -0.5, 0)), (4, P(0, 0, 0))]),
                 'rotation': kf([(0, P(0, 0, 0)), (2, P(1.5, -2, 0)), (4, P(0, 0, 0))])},
        'head': {'rotation': kf([(0, P(0, 0, 0)), (2, P(-2, 3, 1)), (4, P(0, 0, 0))])},
        'right_arm': {'rotation': kf([(0, P(-30, 0, -4)), (2, P(-34, 0, -6)), (4, P(-30, 0, -4))])},
        'left_arm': {'rotation': kf([(0, P(-6, 0, 5)), (2, P(-9, 0, 7)), (4, P(-6, 0, 5))])},
    })
    walk = anim(1.0, True, {
        'body': {'position': kf([(0, P(0, 0, 0)), (0.25, P(0, -0.8, 0)), (0.5, P(0, 0, 0)), (0.75, P(0, -0.8, 0)), (1, P(0, 0, 0))]),
                 'rotation': kf([(0, P(3, 3, 0)), (0.5, P(3, -3, 0)), (1, P(3, 3, 0))])},
        'right_leg': {'rotation': kf([(0, P(32, 0, 0)), (0.5, P(-32, 0, 0)), (1, P(32, 0, 0))])},
        'left_leg': {'rotation': kf([(0, P(-32, 0, 0)), (0.5, P(32, 0, 0)), (1, P(-32, 0, 0))])},
        'left_arm': {'rotation': kf([(0, P(28, 0, 4)), (0.5, P(-28, 0, 4)), (1, P(28, 0, 4))])},
        'right_arm': {'rotation': kf([(0, P(-34, 0, -4)), (0.5, P(-26, 0, -4)), (1, P(-34, 0, -4))])},
    })
    slash1 = anim(0.6, False, {   # diagonal cut, shoulder -> opposite hip
        'body': {'rotation': kf([(0, P(0, 0, 0)), (0.14, P(-4, 28, 0)), (0.3, P(8, -34, 0)), (0.45, P(4, -16, 0)), (0.6, P(0, 0, 0))])},
        'head': {'rotation': kf([(0, P(0, 0, 0)), (0.14, P(0, -14, 0)), (0.3, P(4, 16, 0)), (0.6, P(0, 0, 0))])},
        'right_arm': {'rotation': kf([(0, P(-30, 0, -4)), (0.14, P(-140, 10, -22)), (0.3, P(-62, -30, 12)), (0.45, P(-44, -16, 6)), (0.6, P(-30, 0, -4))])},
        'left_arm': {'rotation': kf([(0, P(-6, 0, 5)), (0.14, P(-30, 0, 18)), (0.3, P(20, 0, 8)), (0.6, P(-6, 0, 5))])},
    })
    slash2 = anim(0.6, False, {   # backhand sweep
        'body': {'rotation': kf([(0, P(0, 0, 0)), (0.14, P(0, -32, 0)), (0.3, P(4, 40, 0)), (0.45, P(0, 18, 0)), (0.6, P(0, 0, 0))])},
        'right_arm': {'rotation': kf([(0, P(-30, 0, -4)), (0.14, P(-78, 36, -34)), (0.3, P(-82, -52, 20)), (0.45, P(-50, -20, 8)), (0.6, P(-30, 0, -4))])},
        'left_arm': {'rotation': kf([(0, P(-6, 0, 5)), (0.14, P(10, 0, 26)), (0.3, P(-34, 0, 10)), (0.6, P(-6, 0, 5))])},
    })
    slash3 = anim(0.7, False, {   # overhead chop
        'body': {'rotation': kf([(0, P(0, 0, 0)), (0.2, P(-12, 0, 0)), (0.34, P(22, 0, 0)), (0.5, P(10, 0, 0)), (0.7, P(0, 0, 0))]),
                 'position': kf([(0, P(0, 0, 0)), (0.34, P(0, -2, -3)), (0.7, P(0, 0, 0))])},
        'right_arm': {'rotation': kf([(0, P(-30, 0, -4)), (0.2, P(-172, 0, -10)), (0.34, P(-40, 0, -2)), (0.5, P(-30, 0, -2)), (0.7, P(-30, 0, -4))])},
        'left_arm': {'rotation': kf([(0, P(-6, 0, 5)), (0.2, P(-150, 0, 14)), (0.34, P(-34, 0, 8)), (0.7, P(-6, 0, 5))])},
    })
    return {'format_version': '1.8.0', 'animations': {
        'animation.james.idle': idle, 'animation.james.walk': walk,
        'animation.james.slash_1': slash1, 'animation.james.slash_2': slash2, 'animation.james.slash_3': slash3}}


# ------------------------------------------------------------------ shadow figure --------
SHADOW_TILE = (0, 0, 32, 32)
SHADOW_FACE = (64, 0, 20, 22)


def shadow_cube(origin, size):
    return cube(origin, size, tile_uv(SHADOW_TILE))


def shadow_geo():
    head = [shadow_cube([-10, 54, -9], [20, 22, 18])]
    # face: the front (north) face gets the unique 20x22 face art, the rest use the smoke tile
    head[0]['uv']['north'] = {'uv': [SHADOW_FACE[0], SHADOW_FACE[1]], 'uv_size': [SHADOW_FACE[2], SHADOW_FACE[3]]}
    for sx in (-1, 1):                       # horns, stepped
        head += [shadow_cube([sx * 6.5 - 1.6, 76, -1.6], [3.2, 6, 3.2]),
                 shadow_cube([sx * 7.8 - 1.2, 82, -1.2], [2.4, 6, 2.4]),
                 shadow_cube([sx * 9.2 - 0.8, 88, -0.8], [1.6, 5, 1.6])]
    def arm(sx):
        cx = sx * 10.25
        cubes = [shadow_cube([cx - 2.25, 14, -2], [4.5, 38, 4])]
        for dx in (-1.65, 0, 1.65):
            cubes.append(shadow_cube([cx + dx - 0.55, 6, -0.55], [1.1, 8.5, 1.1]))
        return cubes
    bones = [
        bone('root', None, [0, 0, 0]),
        bone('robe', 'root', [0, 20, 0], [shadow_cube([-8, 20, -4.5], [16, 12, 9]), shadow_cube([-7, 11, -4], [14, 9, 8]),
                                          shadow_cube([-5, 4, -3], [10, 7, 6]), shadow_cube([-2.5, 0, -1.5], [5, 4, 3])]),
        bone('body', 'root', [0, 32, 0], [shadow_cube([-7.5, 32, -4], [15, 22, 8])]),
        bone('head', 'body', [0, 54, 0], head),
        bone('right_arm', 'body', [-9.5, 52, 0], arm(-1)),
        bone('left_arm', 'body', [9.5, 52, 0], arm(1)),
    ]
    wisp_pos = [(-16, 30, 4), (17, 22, -6), (-13, 52, -12), (15, 60, 8), (-6, 70, 14), (8, 14, 12)]
    for i, p in enumerate(wisp_pos):
        bones.append(bone('wisp_%d' % (i + 1), 'root', p, [shadow_cube([p[0] - 1.5, p[1] - 1.5, p[2] - 1.5], [3, 3, 3])]))
    return geo('geometry.shadow_figure', 128, 128, bones)


def shadow_anims():
    P = lambda *a: a
    bones = {
        'body': {'rotation': kf([(0, P(0, 0, 0)), (3, P(2, 3, 1.5)), (6, P(0, 0, 0))]),
                 'position': kf([(0, P(0, 0, 0)), (3, P(0, 1.2, 0)), (6, P(0, 0, 0))])},
        'head': {'rotation': kf([(0, P(0, 0, 0)), (3, P(-3, -5, 0)), (6, P(0, 0, 0))])},
        'robe': {'rotation': kf([(0, P(0, 0, 0)), (3, P(0, 0, 4)), (6, P(0, 0, 0))])},
        'right_arm': {'rotation': kf([(0, P(0, 0, -4)), (3, P(6, 0, -9)), (6, P(0, 0, -4))])},
        'left_arm': {'rotation': kf([(0, P(0, 0, 4)), (3, P(-6, 0, 9)), (6, P(0, 0, 4))])},
    }
    for i in range(1, 7):
        ph = i * 0.9
        bones['wisp_%d' % i] = {'position': kf([(0, P(0, 0, 0)), (1.5, P(math.sin(ph) * 3, 4 + i, math.cos(ph) * 3)),
                                                   (3, P(0, 8 + i, 0)), (4.5, P(-math.sin(ph) * 3, 4, -math.cos(ph) * 3)), (6, P(0, 0, 0))])}
    return {'format_version': '1.8.0', 'animations': {'animation.shadow_figure.idle': anim(6.0, True, bones)}}


# ------------------------------------------------------------------ player animations ----
def pm(tick, **parts):
    m = {'tick': tick}
    for name, vals in parts.items():
        m[name] = vals
    return m


def A(pitch=0.0, yaw=0.0, roll=0.0):
    return {'x': 0.0, 'y': 0.0, 'z': 0.0, 'pitch': pitch, 'yaw': yaw, 'roll': roll}


def player_anim(name, end, stop, moves):
    return {'name': name, 'author': 'Monster Hunter', 'description': 'Hagoyama sword combo',
            'emote': {'beginTick': 0, 'endTick': end, 'stopTick': stop, 'isLoop': False, 'returnTick': 0,
                      'nsfw': False, 'degrees': False, 'moves': moves}}


def player_anims():
    out = {}
    out['hagoyama_slash_1'] = player_anim('hagoyama_slash_1', 11, 14, [
        pm(0, rightArm=A(-0.5, 0.0, 0.1), torso=A(0, 0, 0)),
        pm(2, rightArm=A(-2.55, 0.35, 0.55), leftArm=A(-0.5, 0, -0.3), torso=A(0, -0.35, 0)),
        pm(5, rightArm=A(-1.3, -0.85, -0.1), leftArm=A(0.3, 0, -0.2), torso=A(0.05, 0.5, 0)),
        pm(8, rightArm=A(-1.0, -0.5, 0.0), torso=A(0, 0.3, 0)),
        pm(11, rightArm=A(-0.3, 0.0, 0.1), torso=A(0, 0, 0))])
    out['hagoyama_slash_2'] = player_anim('hagoyama_slash_2', 11, 14, [
        pm(0, rightArm=A(-0.5, 0.0, 0.1), torso=A(0, 0, 0)),
        pm(2, rightArm=A(-1.35, 0.9, 0.9), leftArm=A(0.2, 0, -0.4), torso=A(0, 0.5, 0)),
        pm(5, rightArm=A(-1.45, -1.0, -0.4), leftArm=A(-0.6, 0, -0.3), torso=A(0, -0.55, 0)),
        pm(8, rightArm=A(-0.9, -0.4, 0.0), torso=A(0, -0.3, 0)),
        pm(11, rightArm=A(-0.3, 0.0, 0.1), torso=A(0, 0, 0))])
    out['hagoyama_slash_3'] = player_anim('hagoyama_slash_3', 13, 16, [
        pm(0, rightArm=A(-0.5, 0.0, 0.1), torso=A(0, 0, 0)),
        pm(3, rightArm=A(-3.0, 0.0, 0.2), leftArm=A(-2.6, 0.0, -0.2), torso=A(-0.25, 0, 0)),
        pm(6, rightArm=A(-0.7, 0.0, 0.0), leftArm=A(-0.7, 0.0, -0.1), torso=A(0.45, 0, 0)),
        pm(9, rightArm=A(-0.6, 0.0, 0.0), torso=A(0.25, 0, 0)),
        pm(13, rightArm=A(-0.3, 0.0, 0.1), torso=A(0, 0, 0))])
    return out


def main():
    print(write('geo/entity/james.geo.json', james_geo()))
    print(write('animations/entity/james.animation.json', james_anims()))
    print(write('geo/entity/shadow_figure.geo.json', shadow_geo()))
    print(write('animations/entity/shadow_figure.animation.json', shadow_anims()))
    for name, data in player_anims().items():
        print(write('player_animation/%s.json' % name, data))


if __name__ == '__main__':
    main()
