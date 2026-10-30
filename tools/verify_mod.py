"""Offline checks for the whole mod (everything that can be checked without launching Minecraft).
Run:  python3 tools/verify_mod.py     (exit code 0 = all passed)
"""
import glob
import json
import math
import os
import random
import re
import subprocess
import sys
import tomllib
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
RES = os.path.join(ROOT, 'src', 'main', 'resources')
ASSETS = os.path.join(RES, 'assets', 'hagoyama')
JAVA = os.path.join(ROOT, 'src', 'main', 'java', 'com', 'hagoyama')
sys.path.insert(0, HERE)
import preview  # noqa

PASS, FAIL = [], []


def check(ok, what):
    (PASS if ok else FAIL).append(what)
    if not ok:
        print('  FAIL:', what)


def jload(path):
    with open(path) as f:
        return json.load(f)


def read(path):
    with open(path) as f:
        return f.read()


def section(name):
    print('==', name)


# --------------------------------------------------------------------------------------------
section('json files parse')
for p in glob.glob(os.path.join(RES, '**', '*.json'), recursive=True) + [os.path.join(RES, 'pack.mcmeta')]:
    try:
        jload(p)
        check(True, p)
    except Exception as e:  # noqa
        check(False, 'invalid json %s: %s' % (p, e))

section('pack / mods.toml')
check(jload(os.path.join(RES, 'pack.mcmeta'))['pack']['description'] == 'Monster Hunter', 'pack.mcmeta says Monster Hunter')
toml = tomllib.loads(read(os.path.join(RES, 'META-INF', 'mods.toml')))
check(toml['mods'][0]['displayName'] == 'Monster Hunter', 'mods.toml displayName is Monster Hunter')
check(toml['mods'][0]['modId'] == 'hagoyama', 'mod id unchanged')
deps = {d['modId']: d for d in toml['dependencies']['hagoyama']}
for need, mandatory in (('forge', True), ('minecraft', True), ('geckolib', True), ('playeranimator', True), ('curios', False)):
    check(need in deps and deps[need]['mandatory'] == mandatory, 'dependency %s mandatory=%s' % (need, mandatory))

section('language file covers every name')
lang = jload(os.path.join(ASSETS, 'lang', 'en_us.json'))
for k in ('itemGroup.hagoyama', 'item.hagoyama.hagoyama', 'entity.hagoyama.james', 'entity.hagoyama.shadow_figure',
          'item.hagoyama.james_spawn_egg', 'item.hagoyama.james_sweater', 'item.hagoyama.james_trousers',
          'item.hagoyama.james_boots', 'key.hagoyama.switch_move', 'key.hagoyama.zoom', 'key.categories.hagoyama'):
    check(k in lang and lang[k].strip() != '', 'lang key ' + k)
check(lang['itemGroup.hagoyama'] == 'Monster Hunter', 'creative tab is called Monster Hunter')
check(lang['entity.hagoyama.james'] == 'James', 'wielder is named James')
all_java = {os.path.basename(p): read(p) for p in glob.glob(os.path.join(JAVA, '**', '*.java'), recursive=True)}
for name, src in all_java.items():
    for m in re.finditer(r'translatable\("([a-zA-Z0-9_.]+)"', src):
        key = m.group(1)
        if '.minecraft.' in key or key.startswith('chat.'):
            continue                                   # vanilla keys
        check(key in lang, 'lang key used in %s: %s' % (name, key))

section('textures')
def size(rel):
    return Image.open(os.path.join(ASSETS, rel)).size
for rel, sz in (('textures/entity/james.png', (128, 128)), ('textures/entity/shadow_figure.png', (128, 128)),
                ('textures/entity/shadow_figure_glowmask.png', (128, 128)), ('textures/models/armor/james_layer_1.png', (128, 64)),
                ('textures/models/armor/james_layer_2.png', (128, 64)), ('textures/gui/clear_eye_bar.png', (64, 32)),
                ('textures/item/hagoyama.png', (32, 32)), ('textures/item/james_sweater.png', (32, 32)),
                ('textures/item/james_trousers.png', (32, 32)), ('textures/item/james_boots.png', (32, 32))):
    check(os.path.exists(os.path.join(ASSETS, rel)) and size(rel) == sz, '%s is %s' % (rel, sz))
check(not os.path.exists(os.path.join(ASSETS, 'textures/entity/hagoyama_wielder.png')), 'old wielder texture removed')

# the sword really is black: nearly every opaque pixel is dark, apart from the red eye gem
sw = np.array(Image.open(os.path.join(ASSETS, 'textures/item/hagoyama.png')).convert('RGBA')).reshape(-1, 4)
sw = sw[sw[:, 3] > 0]
lum = sw[:, :3].astype(float) @ np.array([0.299, 0.587, 0.114])
reddish = (sw[:, 0] > 120) & (sw[:, 1] < 110)
dark = (lum < 70) | reddish
check(dark.mean() > 0.95, 'sword icon is black (%.0f%% dark pixels)' % (100 * dark.mean()))
check(reddish.sum() >= 3, 'sword has its red eye gem')
check(reddish.sum() <= 30, 'only the eye is red')

# shadow eyes: red, round, glowing (glowmask is eyes only)
gm = np.array(Image.open(os.path.join(ASSETS, 'textures/entity/shadow_figure_glowmask.png')).convert('RGBA'))
ys, xs = np.nonzero(gm[:, :, 3])
check(len(xs) > 40, 'glowmask has eye pixels')
check(gm[:, :, 0][gm[:, :, 3] > 0].min() >= 0x8f and gm[:, :, 2][gm[:, :, 3] > 0].max() < 0xe0, 'glowmask pixels are red')
for cx in (5.4 + 64, 14.6 + 64):                      # each eye is a filled disc (round, no holes)
    cy = 9.6
    inside = [(x, y) for x, y in zip(xs, ys) if math.hypot(x + .5 - cx, y + .5 - cy) < 3.0]
    check(len(inside) >= 20, 'eye at x=%.0f is a solid disc (%d px)' % (cx, len(inside)))
w = xs.max() - xs.min() + 1
check(abs((14.6 - 5.4) + 2 * 3.3 - w) < 2, 'two eyes spaced as designed')

section('models: bones, UV coverage, texture size')
def tex_alpha(rel):
    return np.array(Image.open(os.path.join(ASSETS, rel)).convert('RGBA'))[:, :, 3]
for name in ('james', 'shadow_figure'):
    geo = jload(os.path.join(ASSETS, 'geo/entity/%s.geo.json' % name))
    g = geo['minecraft:geometry'][0]
    desc = g['description']
    bones = {b['name']: b for b in g['bones']}
    alpha = tex_alpha('textures/entity/%s.png' % name)
    th, tw = alpha.shape
    check((tw, th) == (desc['texture_width'], desc['texture_height']), '%s geo texture size matches png' % name)
    check(desc['identifier'] == 'geometry.' + name, '%s identifier' % name)
    for b in bones.values():
        check(b.get('parent') is None or b['parent'] in bones, '%s bone %s has a valid parent' % (name, b['name']))
    check(len([b for b in bones.values() if not b.get('parent')]) == 1, '%s has exactly one root bone' % name)
    holes = 0
    for bn, b in bones.items():
        for c in b.get('cubes', []):
            check(all(s > 0 for s in c['size']), '%s/%s cube has positive size' % (name, bn))
            for face, (x, y, ww, hh) in preview.face_rects(c).items():
                inb = 0 <= x and 0 <= y and x + ww <= tw and y + hh <= th
                check(inb, '%s/%s face %s UV in bounds %s' % (name, bn, face, (x, y, ww, hh)))
                if not inb:
                    continue
                cover = (alpha[int(y):int(y + hh), int(x):int(x + ww)] > 0).mean()
                overlay = bool(c.get('inflate'))
                if cover == 0 and not overlay and not (bn == 'head' and face == 'down'):
                    holes += 1
                    check(False, '%s/%s face %s samples only transparent texels (invisible face)' % (name, bn, face))
    check(holes == 0, '%s: no invisible base faces' % name)
    # the front-view "body is still a Minecraft square": James keeps the vanilla humanoid parts and sizes at 2x
    if name == 'james':
        sizes = {bn: bones[bn]['cubes'][0]['size'] for bn in ('body', 'head', 'right_arm', 'left_arm', 'right_leg', 'left_leg')}
        check(sizes['head'] == [16, 16, 16] and sizes['body'] == [16, 24, 8], 'james head/body are standard Minecraft boxes (2x)')
        check(all(sizes[k] == [8, 24, 8] for k in ('right_arm', 'left_arm', 'right_leg', 'left_leg')), 'james arms/legs are standard boxes (2x)')
        check(len(bones['head']['cubes']) > 20, 'james has spiky hair cubes')
        check('sword' in bones and bones['sword']['parent'] == 'right_arm', 'sword is in the right hand')
    # every box-UV cube must also fit its whole UV footprint inside the texture
    for bn, b in bones.items():
        for c in b.get('cubes', []):
            if isinstance(c['uv'], list):
                w_, h_, d_ = c['size']
                check(c['uv'][0] + 2 * (w_ + d_) <= tw and c['uv'][1] + d_ + h_ <= th, '%s/%s box UV footprint fits' % (name, bn))

section('animations')
for name, need in (('james', ['idle', 'walk', 'slash_1', 'slash_2', 'slash_3']), ('shadow_figure', ['idle'])):
    anims = jload(os.path.join(ASSETS, 'animations/entity/%s.animation.json' % name))['animations']
    geo = jload(os.path.join(ASSETS, 'geo/entity/%s.geo.json' % name))['minecraft:geometry'][0]
    bones = {b['name'] for b in geo['bones']}
    for n in need:
        check('animation.%s.%s' % (name, n) in anims, 'animation.%s.%s exists' % (name, n))
    for an, a in anims.items():
        for bn, ch in a['bones'].items():
            check(bn in bones, '%s animates existing bone %s' % (an, bn))
            for kind, frames in ch.items():
                ts = [float(t) for t in frames]
                check(all(0 <= t <= a['animation_length'] + 1e-6 for t in ts), '%s/%s/%s keyframes inside length' % (an, bn, kind))
                check(all(len(v) == 3 and all(math.isfinite(x) for x in v) for v in frames.values()), '%s/%s/%s vectors ok' % (an, bn, kind))
        if an.endswith(('slash_1', 'slash_2', 'slash_3')):
            # a slash must end where it started so the arm does not snap when the walk/idle takes over
            for bn, ch in a['bones'].items():
                if 'rotation' in ch:
                    ks = sorted(ch['rotation'].items(), key=lambda kv: float(kv[0]))
                    check(ks[0][1] == ks[-1][1], '%s %s starts and ends in the same pose' % (an, bn))
    # Java refers to animation names - all must exist
    for fname, src in all_java.items():
        for m in re.finditer(r'"(animation\.%s\.[a-z0-9_]+)"' % name, src):
            check(m.group(1) in anims, '%s references %s' % (fname, m.group(1)))

section('player animation json (Player Animation Library)')
for n in (1, 2, 3):
    d = jload(os.path.join(ASSETS, 'player_animation/hagoyama_slash_%d.json' % n))
    e = d['emote']
    ticks = [m['tick'] for m in e['moves']]
    check(ticks == sorted(ticks) and len(set(ticks)) == len(ticks), 'slash %d ticks strictly increasing' % n)
    check(e['beginTick'] == ticks[0] and e['endTick'] == ticks[-1] and e['stopTick'] >= e['endTick'], 'slash %d timing' % n)
    check(e['endTick'] <= 14, 'slash %d is short enough to finish before the next swing (%d ticks)' % (n, e['endTick']))
    check(e['degrees'] is False and e['isLoop'] is False, 'slash %d radians, not looping' % n)
    for m in e['moves']:
        for part, v in m.items():
            if part in ('tick', 'easing', 'turn'):
                continue
            check(part in ('head', 'torso', 'rightArm', 'leftArm', 'rightLeg', 'leftLeg'), 'slash %d part name %s' % (n, part))
            check(all(math.isfinite(v[k]) and abs(v[k]) < 3.2 for k in ('pitch', 'yaw', 'roll')), 'slash %d angles sane' % n)
    check(ticks[0] == 0 and ticks[-1] == e['endTick'], 'slash %d spans its full length' % n)
    first, last = e['moves'][0]['rightArm'], e['moves'][-1]['rightArm']
    check(abs(first['pitch'] - last['pitch']) < 0.3, 'slash %d returns near the ready pose' % n)
for fname, src in all_java.items():
    for m in re.finditer(r'"hagoyama_slash_"', src):
        check(all(os.path.exists(os.path.join(ASSETS, 'player_animation/hagoyama_slash_%d.json' % k)) for k in (1, 2, 3)), fname + ' slash files exist')

section('loot: exactly one clothing piece per kill')
loot = jload(os.path.join(RES, 'data/hagoyama/loot_tables/entities/james.json'))
check(loot['type'] == 'minecraft:entity' and len(loot['pools']) == 1, 'single pool')
pool = loot['pools'][0]
check(pool['rolls'] == 1 and pool.get('bonus_rolls', 0) == 0, 'exactly one roll, no bonus rolls')
names = [e['name'] for e in pool['entries']]
check(sorted(names) == ['hagoyama:james_boots', 'hagoyama:james_sweater', 'hagoyama:james_trousers'], 'entries are the 3 clothes')
check(all('conditions' not in e for e in pool['entries']) and 'conditions' not in pool, 'no condition can make it drop nothing')
rng = random.Random(1)
counts = {n: 0 for n in names}
for _ in range(30000):
    tot = sum(e['weight'] for e in pool['entries'])
    r = rng.uniform(0, tot)
    for e in pool['entries']:
        r -= e['weight']
        if r <= 0:
            counts[e['name']] += 1
            break
check(sum(counts.values()) == 30000 and all(9000 < v < 11000 for v in counts.values()), 'simulated kills: always one drop, evenly split %s' % counts)
for n in names:
    item = n.split(':')[1]
    check(os.path.exists(os.path.join(ASSETS, 'models/item/%s.json' % item)), 'item model for ' + item)
    check(os.path.exists(os.path.join(ASSETS, 'textures/item/%s.png' % item)), 'item texture for ' + item)
    check('"%s"' % item in all_java['JamesClothing.java'], 'item %s registered in code' % item)

section('worn clothes (armor layers)')
src = all_java['JamesClothing.java']
check('MODID + ":james"' in src, 'armor material name is hagoyama:james')
for layer in (1, 2):
    a = np.array(Image.open(os.path.join(ASSETS, 'textures/models/armor/james_layer_%d.png' % layer)).convert('RGBA'))[:, :, 3]
    check((a > 0).sum() > 800, 'armor layer %d has art' % layer)
a1 = np.array(Image.open(os.path.join(ASSETS, 'textures/models/armor/james_layer_1.png')).convert('RGBA'))[:, :, 3]
a2 = np.array(Image.open(os.path.join(ASSETS, 'textures/models/armor/james_layer_2.png')).convert('RGBA'))[:, :, 3]
body, arm, leg = preview.box_faces(32, 32, 16, 24, 8), preview.box_faces(80, 32, 8, 24, 8), preview.box_faces(0, 32, 8, 24, 8)
def cov(a, r):
    x, y, w, h = r
    return (a[y:y + h, x:x + w] > 0).mean()
check(cov(a1, body['front']) > 0.8 and cov(a1, body['back']) > 0.8, 'sweater covers the torso (layer 1)')
check(cov(a1, arm['front']) > 0.6 and cov(a1, arm['right']) > 0.6, 'sweater covers the sleeves (layer 1)')
check(cov(a1, leg['front']) > 0.15 and cov(a1, leg['front']) < 0.5, 'boots only cover the bottom of the leg (layer 1)')
check(cov(a2, leg['front']) > 0.9 and cov(a2, leg['right']) > 0.9, 'trousers cover the whole leg (layer 2)')
check(cov(a2, body['front']) < 0.5, 'trousers do not cover the chest (layer 2)')

section('worldgen / locate')
pf = jload(os.path.join(RES, 'data/hagoyama/worldgen/placed_feature/cave_shrine.json'))
types = [p['type'] for p in pf['placement']]
check('minecraft:rarity_filter' not in types and 'minecraft:biome' in types, 'placement no longer random per chunk (shrine position is computed)')
check(pf['feature'] == 'hagoyama:cave_shrine' and '"cave_shrine"' in all_java['HagoyamaMod.java'], 'feature id matches registration')
cmd = all_java['HagoyamaCommands.java']
check('literal("locate")' in cmd and 'ShrineLocator.nearest' in cmd, 'locate command wired to ShrineLocator')
check(re.search(r'literal\("locate"\)\.requires', cmd) is None, 'locate is usable by everyone')
for sub in ('trance', 'awaken', 'reset'):
    check(re.search(r'literal\("%s"\)\.requires\(s -> s\.hasPermission\(2\)\)' % sub, cmd) is not None, 'op-only subcommand ' + sub)
check('Commands.literal("hagoyama")\n' in cmd or 'Commands.literal("hagoyama").then' in cmd or 'literal("hagoyama")' in cmd and 'literal("hagoyama").requires' not in cmd, 'root command is open so locate works')
check('ShrineLocator.siteInChunk' in all_java['CaveShrineFeature.java'], 'feature places shrines exactly where the locator says')
check('hagoyama:hagoyama' in read(os.path.join(RES, 'data/curios/tags/items/back.json')), 'sword fits the Curios back slot')

section('java cross-references (own classes)')
own = {os.path.basename(p)[:-5] for p in glob.glob(os.path.join(JAVA, '**', '*.java'), recursive=True)}
members = {}
for fname, s in all_java.items():
    members[fname[:-5]] = s
bad = 0
for fname, s in all_java.items():
    for m in re.finditer(r'\b([A-Z][A-Za-z]+)\.([A-Za-z_][A-Za-z0-9_]*)\b', s):
        cls, mem = m.group(1), m.group(2)
        if cls in own and cls != fname[:-5] and cls in members:
            if not re.search(r'\b%s\b' % re.escape(mem), members[cls]):
                bad += 1
                check(False, '%s uses %s.%s which does not exist' % (fname, cls, mem))
check(bad == 0, 'every Class.member between our own classes exists')
check('Illusioner' not in all_java['Trance.java'], 'trance no longer uses the illusioner')
check('JamesSetup.SHADOW' in all_java['Trance.java'] and 'SHADOW' in all_java['JamesSetup.java'], 'trance spawns the shadow figure')
renderer_regs = all_java['JamesClientSetup.java']
check('JamesSetup.TYPE' in renderer_regs and 'JamesSetup.SHADOW' in renderer_regs, 'both renderers registered')
check('POSITION_COLOR_TEX' in all_java['ClientEvents.java'] and 'clear_eye_bar.png' in all_java['ClientEvents.java'], 'health bar uses the new texture')

section('java syntax + shrine math (JDK parser, JUnit-style tests)')
files = sorted(glob.glob(os.path.join(JAVA, '**', '*.java'), recursive=True))
r = subprocess.run(['java', os.path.join(HERE, 'test', 'ParseCheck.java')] + files, capture_output=True, text=True)
print('  ' + r.stdout.strip().replace('\n', '\n  '))
check(r.returncode == 0, 'all java files parse')
os.makedirs('/tmp/jout', exist_ok=True)
r = subprocess.run(['java', '-m', 'jdk.compiler/com.sun.tools.javac.Main', '-d', '/tmp/jout', os.path.join(JAVA, 'ShrineLocator.java'),
                    os.path.join(HERE, 'test', 'ShrineLocatorTest.java')], capture_output=True, text=True)
check(r.returncode == 0, 'ShrineLocator compiles on its own: ' + r.stderr[:200])
r = subprocess.run(['java', '-cp', '/tmp/jout', 'ShrineLocatorTest'], capture_output=True, text=True)
print('  ' + r.stdout.strip().replace('\n', '\n  '))
check(r.returncode == 0, 'ShrineLocator unit tests')

print('\n%d checks passed, %d failed' % (len(PASS), len(FAIL)))
sys.exit(1 if FAIL else 0)
