# -*- coding: utf-8 -*-
"""Turn Unity particle prefabs into a particle spec the web runtime can play.

A prefab is a YAML document per component. The ones that matter are
ParticleSystem (class 198) and ParticleSystemRenderer (class 199); the renderer
points at a material by GUID, and the material points at a texture by GUID,
which lands back on a PNG in singles/.

Unity stores every "how much" as a MinMaxCurve - a constant, a range, or a
curve - and every "what colour" as a MinMaxGradient. Both are flattened here
into something small and obvious: {v: 3} for a constant, {min, max} for a
range, {keys: [[t, v], ...]} for a curve.

    python tools/parse_particles.py <unity_dir> <library_dir>

Writes <library_dir>/particles.json.
"""
import json
import os
import re
import sys

import yaml

DOC_RE = re.compile(r'^--- !u!(\d+) &(\d+)', re.M)
PARTICLE_SYSTEM, PARTICLE_RENDERER, GAME_OBJECT = 198, 199, 1

# ShapeModule.type - only the ones this art actually uses are named.
SHAPES = {0: 'sphere', 1: 'sphere_shell', 2: 'hemisphere', 4: 'cone', 5: 'box',
          7: 'circle', 10: 'edge', 15: 'cone_volume'}
RENDER_MODES = {0: 'billboard', 1: 'stretched', 2: 'horizontal', 3: 'vertical', 4: 'mesh'}


def docs(text):
    """(classID, body dict) for each YAML document in a Unity asset."""
    marks = list(DOC_RE.finditer(text))
    for n, m in enumerate(marks):
        end = marks[n + 1].start() if n + 1 < len(marks) else len(text)
        cls = int(m.group(1))
        yield cls, text[text.index('\n', m.start()) + 1:end], int(m.group(2))


def load(body):
    try:
        d = yaml.safe_load(body)
    except Exception:
        return None
    if not isinstance(d, dict) or not d:
        return None
    return next(iter(d.values()))


def num(value, fallback=0.0):
    """Unity 2018+ wraps some plain numbers in a struct; accept either form."""
    if isinstance(value, dict):
        for key in ('value', 'scalar', 'x'):
            if key in value:
                return num(value[key], fallback)
        return fallback
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def curve(mm):
    """Flatten a MinMaxCurve. None when it is a plain 0."""
    if not isinstance(mm, dict):
        return None
    state = mm.get('minMaxState', 0)
    scalar = mm.get('scalar', 0)
    lo = mm.get('minScalar', 0)
    if state == 0:
        return {'v': round(float(scalar), 4)}
    if state == 3:
        a, b = sorted((float(lo), float(scalar)))
        return {'min': round(a, 4), 'max': round(b, 4)}
    keys = ((mm.get('maxCurve') or {}).get('m_Curve')) or []
    pts = [[round(float(k.get('time', 0)), 4), round(float(k.get('value', 0)) * float(scalar), 4)]
           for k in keys if isinstance(k, dict)]
    return {'keys': pts} if pts else {'v': round(float(scalar), 4)}


def rgba(c):
    if not isinstance(c, dict):
        return None
    return [round(min(1.0, max(0.0, float(c.get(k, 0)))), 4) for k in 'rgba']


def gradient(mg):
    """Flatten a MinMaxGradient into [[t, [r,g,b,a]], ...] or a single colour."""
    if not isinstance(mg, dict):
        return None
    state = mg.get('minMaxState', 0)
    if state in (0, 2):
        return {'color': rgba(mg.get('maxColor'))}
    grad = mg.get('maxGradient') or {}
    n_col = int(grad.get('m_NumColorKeys', 0) or 0)
    n_alpha = int(grad.get('m_NumAlphaKeys', 0) or 0)
    stops = []
    for i in range(max(n_col, 1)):
        col = rgba(grad.get('key%d' % i)) or [1, 1, 1, 1]
        t = float(grad.get('ctime%d' % i, 0)) / 65535.0
        stops.append([round(t, 4), col])
    alphas = []
    for i in range(max(n_alpha, 1)):
        col = grad.get('key%d' % i) or {}
        t = float(grad.get('atime%d' % i, 0)) / 65535.0
        alphas.append([round(t, 4), round(float(col.get('a', 1)), 4)])
    return {'stops': stops, 'alpha': alphas}


def material_index(unity_dir, guids):
    """material GUID -> {texture pathname, tint, blend}.

    The extractor names each file with a short GUID prefix, so the full GUID a
    renderer references is recovered from the guid map.
    """
    by_prefix = {}
    for full in guids:
        by_prefix.setdefault(full[:8], full)

    out = {}
    mdir = os.path.join(unity_dir, 'materials')
    for name in os.listdir(mdir):
        short = name.split('.')[-2] if name.count('.') >= 2 else None
        guid = by_prefix.get(short, short)
        text = open(os.path.join(mdir, name), encoding='utf-8', errors='replace').read()
        mat = load(re.sub(r'^%YAML.*?\n---.*?\n', '', text, flags=re.S)) or {}
        saved = mat.get('m_SavedProperties') or {}
        tex_guid = None
        for env in saved.get('m_TexEnvs') or []:
            if not isinstance(env, dict):
                continue
            for key, val in env.items():
                if key == '_MainTex' and isinstance(val, dict):
                    tex_guid = (val.get('m_Texture') or {}).get('guid')
        tint = None
        for col in saved.get('m_Colors') or []:
            if isinstance(col, dict):
                for key, val in col.items():
                    if key in ('_TintColor', '_Color') and tint is None:
                        tint = rgba(val)
        floats = {}
        for fl in saved.get('m_Floats') or []:
            if isinstance(fl, dict):
                floats.update(fl)
        src, dst = floats.get('_SrcBlend'), floats.get('_DstBlend')
        out[guid] = {
            'texture': guids.get(tex_guid or ''), 'tint': tint,
            'srcBlend': src, 'dstBlend': dst,
        }
    # A material file may be referenced by the GUID in its own name.
    return {k: v for k, v in out.items() if k}


def parse_prefab(path, mats, guids):
    text = open(path, encoding='utf-8', errors='replace').read()
    systems, renderers, names = {}, {}, {}
    for cls, body, fid in docs(text):
        if cls == GAME_OBJECT:
            go = load(body) or {}
            names[fid] = go.get('m_Name')
        elif cls == PARTICLE_SYSTEM:
            systems[fid] = load(body)
        elif cls == PARTICLE_RENDERER:
            renderers[fid] = load(body)
    if not systems:
        return None

    emitters = []
    for fid, ps in systems.items():
        if not isinstance(ps, dict):
            continue
        go_id = (ps.get('m_GameObject') or {}).get('fileID')
        init = ps.get('InitialModule') or {}
        emission = ps.get('EmissionModule') or {}
        shape = ps.get('ShapeModule') or {}
        size_mod = ps.get('SizeModule') or {}
        color_mod = ps.get('ColorModule') or {}
        vel = ps.get('VelocityModule') or {}

        rend = next((r for r in renderers.values()
                     if isinstance(r, dict)
                     and (r.get('m_GameObject') or {}).get('fileID') == go_id), None)
        mat_guid = None
        if rend:
            for entry in rend.get('m_Materials') or []:
                if isinstance(entry, dict) and entry.get('guid'):
                    mat_guid = entry['guid']
                    break
        mat = mats.get(mat_guid or '', {})
        tex_path = mat.get('texture')

        emitter = {
            'name': names.get(go_id) or 'emitter',
            'duration': round(num(ps.get('lengthInSec'), 1) or 1, 3),
            'looping': bool(ps.get('looping')),
            'maxParticles': int(num(init.get('maxNumParticles'), 100) or 100),
            'gravity': curve(init.get('gravityModifier')),
            'lifetime': curve(init.get('startLifetime')),
            'speed': curve(init.get('startSpeed')),
            'size': curve(init.get('startSize')),
            'rotation': curve(init.get('startRotation')),
            'color': gradient(init.get('startColor')),
            'rate': curve(emission.get('rateOverTime')) if emission.get('enabled') else None,
            'bursts': [[round(num(b.get('time')), 3),
                        int(num((b.get('countCurve') or {}).get('scalar')))]
                       for b in (emission.get('m_Bursts') or []) if isinstance(b, dict)],
            'shape': ({'type': SHAPES.get(shape.get('type'), str(shape.get('type'))),
                       'radius': round(num(shape.get('radius')), 3),
                       'angle': round(num(shape.get('angle')), 2)}
                      if shape.get('enabled') else None),
            'sizeOverLife': curve(size_mod.get('curve')) if size_mod.get('enabled') else None,
            'colorOverLife': gradient(color_mod.get('gradient')) if color_mod.get('enabled') else None,
            'velocity': ({'x': curve(vel.get('x')), 'y': curve(vel.get('y')),
                          'z': curve(vel.get('z'))} if vel.get('enabled') else None),
            'render': RENDER_MODES.get(rend.get('m_RenderMode') if rend else None, 'billboard'),
            'texture': os.path.splitext(os.path.basename(tex_path))[0] if tex_path else None,
            'tint': mat.get('tint'),
            'srcBlend': mat.get('srcBlend'),
            'dstBlend': mat.get('dstBlend'),
        }
        emitters.append({k: v for k, v in emitter.items()
                         if v is not None and v != [] and v != {}})

    return emitters or None


def main(unity_dir, library):
    with open(os.path.join(unity_dir, 'guids.json'), encoding='utf-8') as f:
        guids = json.load(f)
    mats = material_index(unity_dir, guids)
    print('materials indexed: %d (%d resolve to a texture)'
          % (len(mats), sum(1 for m in mats.values() if m.get('texture'))))

    pdir = os.path.join(unity_dir, 'prefabs')
    files = sorted(os.listdir(pdir))
    effects, skipped = {}, 0
    for n, name in enumerate(files, 1):
        try:
            emitters = parse_prefab(os.path.join(pdir, name), mats, guids)
        except Exception as exc:
            print('  parse failed: %s (%s)' % (name, type(exc).__name__))
            emitters = None
        if not emitters:
            skipped += 1
        else:
            effects[name.split('.')[0]] = {'emitters': emitters}
        if n % 50 == 0 or n == len(files):
            print('  [%d/%d] %d particle effects' % (n, len(files), len(effects)))

    out = os.path.join(library, 'particles.json')
    with open(out, 'w', encoding='utf-8') as f:
        json.dump({'version': 1, 'effects': effects}, f, ensure_ascii=False,
                  separators=(',', ':'))
    total = sum(len(e['emitters']) for e in effects.values())
    print('wrote %s: %d effects, %d emitters, %.1f KB (%d prefabs had no particles)'
          % (out, len(effects), total, os.path.getsize(out) / 1024, skipped))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
