"""Regression tests for ground geometry, placement and material drift."""
import copy
import json
import struct
import tempfile
import unittest
from pathlib import Path

from validate_building_ground import ROOT, ground_signature, read_glb


class GroundSignatureTests(unittest.TestCase):
    def setUp(self):
        self.source = ROOT / 'frontend/public/assets/buildings/industry/lumber_yard/lumber_yard_l01_active.glb'
        self.doc, self.binary = read_glb(self.source)
        self.expected = ground_signature(self.source)
        self.ground = next(n for n in self.doc['nodes'] if 'tile_base' in n.get('name', ''))

    def signature(self, doc):
        encoded = json.dumps(doc).encode()
        encoded += b' ' * (-len(encoded) % 4)
        binary = self.binary + b'\0' * (-len(self.binary) % 4)
        raw = struct.pack('<4sII', b'glTF', 2, 28 + len(encoded) + len(binary))
        raw += struct.pack('<II', len(encoded), 0x4e4f534a) + encoded
        raw += struct.pack('<II', len(binary), 0x004e4942) + binary
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'test.glb'
            path.write_bytes(raw)
            return ground_signature(path)

    def test_names_do_not_change_ground(self):
        self.ground['name'] += '.999'
        for material in self.doc['materials']:
            material['name'] = 'renamed'
        self.assertEqual(self.expected, self.signature(self.doc))

    def test_translation_drift(self):
        self.ground['translation'][0] += 0.1
        self.assertNotEqual(self.expected, self.signature(self.doc))

    def test_material_drift(self):
        primitive = self.doc['meshes'][self.ground['mesh']]['primitives'][0]
        self.doc['materials'][primitive['material']]['pbrMetallicRoughness']['baseColorFactor'][0] = 0
        self.assertNotEqual(self.expected, self.signature(self.doc))

    def test_extra_scorched_ground(self):
        extra = copy.deepcopy(self.ground)
        extra['name'] = 'scorched_ground'
        self.doc['nodes'].append(extra)
        self.assertNotEqual(self.expected, self.signature(self.doc))

    def test_geometry_drift(self):
        primitive = self.doc['meshes'][self.ground['mesh']]['primitives'][0]
        item = self.doc['accessors'][primitive['attributes']['POSITION']]
        view = self.doc['bufferViews'][item['bufferView']]
        offset = view.get('byteOffset', 0) + item.get('byteOffset', 0)
        data = bytearray(self.binary)
        struct.pack_into('<f', data, offset, 17)
        self.binary = bytes(data)
        self.assertNotEqual(self.expected, self.signature(self.doc))


if __name__ == '__main__':
    unittest.main()
