"""Compare exported terrain geometry/materials between all building states."""
import hashlib
import json
import re
import struct
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
FAMILIES = {
    'dugout': ('housing/dugout', 5, False),
    'wood_house': ('housing/wood_house', 6, False),
    'town_hall': ('center/town_hall', 10, False),
    'lumber_yard': ('industry/lumber_yard', 13, True),
}
GROUND = re.compile(r'earth_tile|grass_tile|tile_base|work_yard|path_stone|sawdust_lane|scorched_ground')


def read_glb(path):
    raw = path.read_bytes()
    assert raw[:4] == b'glTF', path
    size = struct.unpack_from('<I', raw, 12)[0]
    doc = json.loads(raw[20:20 + size])
    return doc, raw[28 + size:]


def accessor(doc, binary, index):
    item = doc['accessors'][index]
    view = doc['bufferViews'][item['bufferView']]
    fmt = {5126: 'f', 5125: 'I', 5123: 'H', 5121: 'B', 5122: 'h', 5120: 'b'}[item['componentType']]
    width = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[item['type']]
    unpack = struct.Struct('<' + fmt * width)
    start = view.get('byteOffset', 0) + item.get('byteOffset', 0)
    stride = view.get('byteStride', unpack.size)
    return [tuple(round(v, 6) for v in unpack.unpack_from(binary, start + i * stride)) for i in range(item['count'])]


def ground_signature(path, pattern=GROUND):
    doc, binary = read_glb(path)
    parents = {child: i for i, n in enumerate(doc['nodes']) for child in n.get('children', [])}
    parts = []
    for i, node in enumerate(doc['nodes']):
        if 'mesh' not in node or not pattern.search(node.get('name', '')):
            continue
        transforms = []
        current = i
        while True:
            n = doc['nodes'][current]
            transforms.append({k: n[k] for k in ('matrix', 'translation', 'rotation', 'scale') if k in n})
            if current not in parents:
                break
            current = parents[current]
        primitives = []
        for p in doc['meshes'][node['mesh']]['primitives']:
            material = dict(doc['materials'][p['material']])
            material.pop('name', None)
            primitives.append({'attributes': {k: accessor(doc, binary, v) for k, v in p['attributes'].items()},
                               'indices': accessor(doc, binary, p['indices']), 'material': material})
        parts.append(json.dumps({'transforms': transforms, 'primitives': primitives}, sort_keys=True))
    assert parts, ('No ground found', path)
    return hashlib.sha256(json.dumps(sorted(parts)).encode()).hexdigest(), len(parts)


def sprite_alignment(active_path, state_path):
    with Image.open(active_path) as active, Image.open(state_path) as state:
        assert active.size == state.size == (512, 384)
        assert active.mode == state.mode == 'RGBA'
        a = active.getchannel('A').point(lambda v: 255 if v >= 128 else 0)
        b = state.getchannel('A').point(lambda v: 255 if v >= 128 else 0)
        ab, bb = a.getbbox(), b.getbbox()
        assert ab and bb
        if abs(ab[3] - bb[3]) > 1:
            return False
        # The front edge is unobscured by the building in these centered tiles.
        for y in range(ab[3] - 12, ab[3] - 1):
            row_a = a.crop((0, y, 512, y + 1)).getbbox()
            row_b = b.crop((0, y, 512, y + 1)).getbbox()
            if not row_a or not row_b or any(abs(row_a[i] - row_b[i]) > 1 for i in (0, 2)):
                return False
        return True


def audit(root=ROOT):
    results = []
    for kind, (folder, levels, public) in FAMILIES.items():
        directory = root / ('frontend/public/assets/buildings' if public else 'frontend/src/assets/buildings') / folder
        for level in range(1, levels + 1):
            prefix = f'{kind}_l{level:02d}'
            active = directory / (prefix + '_active.glb')
            signature, count = ground_signature(active)
            for state in ('construction', 'damaged'):
                path = directory / (prefix + '_' + state + '.glb')
                other, other_count = ground_signature(path)
                png = root / 'frontend/public/assets/buildings' / folder
                results.append({'name': path.stem, 'matches_active': signature == other,
                                'active_parts': count, 'state_parts': other_count,
                                'sprite_aligned': sprite_alignment(png / (active.stem + '.png'), png / (path.stem + '.png'))})
    return results


if __name__ == '__main__':
    results = audit()
    failures = [r for r in results if not r['matches_active'] or not r['sprite_aligned']]
    print(json.dumps({'active_levels': sum(f[1] for f in FAMILIES.values()), 'states': len(results), 'mismatches': failures}, indent=2))
    if failures:
        raise SystemExit(1)
    (ROOT / 'frontend/public/assets/buildings/ground-validation.json').write_text(json.dumps(results, indent=2) + '\n')
