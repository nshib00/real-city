"""Compare exported terrain geometry/materials between building states."""
import hashlib
import json
import re
import struct
import argparse
from pathlib import Path

from PIL import Image

from asset_validation_common import load_manifests, resolve_asset_path

ROOT = Path(__file__).resolve().parents[2]
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
        assert active.size == state.size and active.size in ((512, 384), (512, 512))
        width = active.size[0]
        assert active.mode == state.mode == 'RGBA'
        a = active.getchannel('A').point(lambda v: 255 if v >= 128 else 0)
        b = state.getchannel('A').point(lambda v: 255 if v >= 128 else 0)
        ab, bb = a.getbbox(), b.getbbox()
        assert ab and bb
        if abs(ab[3] - bb[3]) > 1:
            return False
        # The front edge is unobscured by the building in these centered tiles.
        for y in range(ab[3] - 12, ab[3] - 1):
            row_a = a.crop((0, y, width, y + 1)).getbbox()
            row_b = b.crop((0, y, width, y + 1)).getbbox()
            if not row_a or not row_b or any(abs(row_a[i] - row_b[i]) > 1 for i in (0, 2)):
                return False
        return True


def audit(paths=None, root=ROOT):
    results = []
    for manifest in load_manifests(paths):
        items = {}
        for item in manifest.items:
            level = item.get('level')
            state = item.get('state')
            if level is not None and state:
                items[(int(level), str(state))] = item
        for level in manifest.levels:
            active_item = items.get((level, 'active'))
            if not active_item:
                continue
            active = resolve_asset_path(manifest.directory, active_item.get('glb'))
            if not active or not active.exists():
                continue
            try:
                signature, count = ground_signature(active)
            except AssertionError as exc:
                results.append({'name': active.stem, 'asset_id': manifest.asset_id, 'level': level, 'ground_found': False, 'error': str(exc)})
                continue
            for state in manifest.states:
                if state == 'active':
                    continue
                item = items.get((level, state))
                if not item:
                    continue
                path = resolve_asset_path(manifest.directory, item.get('glb'))
                if not path or not path.exists():
                    continue
                try:
                    other, other_count = ground_signature(path)
                    matches_active = signature == other
                    ground_found = True
                    error = None
                except AssertionError as exc:
                    other_count = 0
                    matches_active = False
                    ground_found = False
                    error = str(exc)
                active_png = resolve_asset_path(manifest.directory, active_item.get('png'))
                state_png = resolve_asset_path(manifest.directory, item.get('png'))
                aligned = bool(active_png and state_png and active_png.exists() and state_png.exists() and sprite_alignment(active_png, state_png))
                results.append({'name': path.stem, 'asset_id': manifest.asset_id, 'level': level, 'state': state,
                                'ground_found': ground_found, 'matches_active': matches_active,
                                'active_parts': count, 'state_parts': other_count,
                                'sprite_aligned': aligned, 'error': error})
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paths', nargs='*', help='Manifest files or asset directories. Defaults to all building manifests.')
    parser.add_argument('--report', default=str(ROOT / 'frontend/public/assets/buildings/ground-validation.json'))
    args = parser.parse_args()
    results = audit(args.paths)
    failures = [r for r in results if not r.get('ground_found') or not r.get('matches_active') or not r.get('sprite_aligned')]
    print(json.dumps({'states': len(results), 'mismatches': failures}, indent=2))
    if failures:
        raise SystemExit(1)
    Path(args.report).write_text(json.dumps(results, indent=2) + '\n')
