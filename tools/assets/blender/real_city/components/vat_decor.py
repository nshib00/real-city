"""Reusable cast-metal vat ornaments for Real City industry assets."""

from __future__ import annotations

import math

from .. import geometry as g
from .common import mat


def add_circumferential_stripe(name, collection, mats, *, radius, z, width=0.045, role="copper", arc=1.0, start=0.0):
    """A raised metal strip, open or closed, attached to a round vat wall."""
    segments = max(8, round(32 * arc))
    verts, faces = [], []
    for i in range(segments + 1):
        angle = start + math.tau * arc * i / segments
        for r, h in ((radius - 0.008, -width / 2), (radius + 0.014, -width / 2),
                     (radius + 0.014, width / 2), (radius - 0.008, width / 2)):
            verts.append((r * math.cos(angle), r * math.sin(angle), z + h))
        if i:
            a, b = (i - 1) * 4, i * 4
            faces.extend(((a, b, b + 1, a + 1), (a + 1, b + 1, b + 2, a + 2),
                          (a + 2, b + 2, b + 3, a + 3)))
    g.mesh(name, collection, verts, faces, mat(mats, role, "copper"))


def add_radial_ribs(name, collection, mats, *, radius, height, count=8, role="metal_worn", missing=()):
    """Substantial external strips, fixed from the lower band to the lip."""
    for i in range(count):
        if i in missing:
            continue
        angle = math.tau * i / count
        x, y = radius * math.cos(angle), radius * math.sin(angle)
        rib = g.box(f"{name}_{i}", collection, (x, y, 0.25 + height * 0.48),
                    (0.08, 0.055, height * 0.87), mat(mats, role, "metal_worn"), bevel=0.012)
        rib.rotation_euler.z = angle + math.pi / 2


def add_gilded_threads(name, collection, mats, *, radius, lower_z, upper_z, count=6, strands=2):
    """Thin gilded helical inlay across the vat casing; late upgrade ornament."""
    gold = mat(mats, "roof_gold")
    for strand in range(strands):
        for i in range(count):
            a = math.tau * (i + strand * 0.48) / count
            b = a + 0.11 + strand * 0.04
            z0 = lower_z + strand * 0.075
            z1 = upper_z - strand * 0.045
            g.beam(f"{name}_{strand}_{i}", collection,
                   ((radius + 0.033) * math.cos(a), (radius + 0.033) * math.sin(a), z0),
                   ((radius + 0.033) * math.cos(b), (radius + 0.033) * math.sin(b), z1),
                   0.025, gold)


def add_heat_shield_medallions(name, collection, mats, *, radius, z, count=4):
    """Copper shields and gold rivet heads placed on the outer casing."""
    for i in range(count):
        a = math.tau * (i + 0.5) / count
        x, y = (radius + 0.026) * math.cos(a), (radius + 0.026) * math.sin(a)
        shield = g.box(f"{name}_shield_{i}", collection, (x, y, z), (0.16, 0.035, 0.13),
                       mat(mats, "copper"), bevel=0.017)
        shield.rotation_euler.z = a + math.pi / 2
        g.sphere(f"{name}_rivet_{i}", collection,
                 ((radius + 0.057) * math.cos(a), (radius + 0.057) * math.sin(a), z),
                 (0.03, 0.03, 0.03), mat(mats, "roof_gold"), segments=8, ring_count=4)
