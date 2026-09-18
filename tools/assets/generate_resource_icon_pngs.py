"""Generate fallback PNG resource icons for documented resources.

This script is intentionally independent from Blender. It keeps runtime icons
available when Blender MCP/CLI is unavailable, while preserving existing GLB
metadata in manifest.json.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "frontend" / "public" / "assets" / "resources" / "icons"
SIZE = 256
STYLE = (
    "transparent close-up bright fantasy stylized mid-poly isometric resource icons "
    "without bottom backplates, following docs/visual-style-guide.md; "
    "png fallback additions generated without Blender"
)


RESOURCES = [
    ("flax", "Лен", "raw"),
    ("reed", "Тростник", "raw"),
    ("fiber", "Волокно", "raw"),
    ("dyes", "Красители", "raw"),
    ("oil_plants", "Масличные растения", "raw"),
    ("sugar_cane", "Сахарный стебель", "raw"),
    ("rare_flowers", "Редкие цветы", "rare"),
    ("crystal_fruit", "Кристальные плоды", "rare"),
    ("sap", "Живица", "raw"),
    ("premium_planks", "Премиум-доски", "crafted"),
    ("rope", "Веревка", "crafted"),
    ("iron_ingot", "Железный слиток", "crafted"),
    ("gold_ingot", "Золотой слиток", "crafted"),
    ("reinforced_concrete", "Железобетон", "crafted"),
    ("copper_parts", "Медные детали", "crafted"),
    ("tools", "Инструменты", "crafted"),
    ("paper", "Бумага", "crafted"),
    ("paints", "Краски", "crafted"),
    ("vegetable_oil", "Масло", "crafted"),
    ("mechanisms", "Механизмы", "crafted"),
    ("super-mechanisms", "Супер-механизмы", "rare"),
    ("lenses", "Линзы", "crafted"),
    ("reinforced_beams", "Усиленные балки", "crafted"),
    ("armor_plates", "Защитные пластины", "crafted"),
    ("light_crystal", "Светокристаллы", "rare"),
    ("amber_essence", "Янтарная эссенция", "rare"),
    ("emerald_dust", "Изумрудная пыль", "rare"),
    ("blue_salt", "Синяя соль", "rare"),
    ("star_glass", "Звездное стекло", "rare"),
    ("stone_heart", "Каменное сердце", "rare"),
    ("aeolian_alloy", "Эолиевый сплав", "rare"),
    ("printing_plate", "Печатная пластина", "crafted"),
    ("runic_tile", "Руническая черепица", "rare"),
    ("silent_powder", "Тихий порошок", "rare"),
    ("memory_shard", "Осколки памяти", "rare"),
    ("super-windleaf", "Супер-ветролист", "rare"),
    ("influence_seal", "Знаки влияния", "rare"),
    ("monster_trophy", "Трофеи монстров", "rare"),
    ("relic_fragment", "Реликтовые фрагменты", "rare"),
    ("festival_token", "Праздничные жетоны", "rare"),
]

CATEGORY_COLORS = {
    "basic": ((216, 164, 65), (255, 224, 120)),
    "raw": ((86, 151, 84), (164, 226, 112)),
    "crafted": ((76, 130, 164), (172, 218, 236)),
    "fuel": ((177, 95, 42), (255, 178, 65)),
    "rare": ((126, 72, 190), (105, 235, 255)),
}


def ellipse(draw: ImageDraw.ImageDraw, cx: float, cy: float, rx: float, ry: float, fill, outline=None, width=1):
    draw.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=fill, outline=outline, width=width)


def poly(draw: ImageDraw.ImageDraw, points, fill, outline=None, width=1):
    draw.polygon(points, fill=fill)
    if outline:
        draw.line(points + [points[0]], fill=outline, width=width, joint="curve")


def rect(draw: ImageDraw.ImageDraw, xy, fill, outline=None, width=1, radius=10):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def line(draw: ImageDraw.ImageDraw, xy, fill, width=4):
    draw.line(xy, fill=fill, width=width, joint="curve")


def add_soft_shadow(base: Image.Image, shape: Image.Image):
    shadow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    alpha = shape.getchannel("A").filter(ImageFilter.GaussianBlur(7))
    shadow.putalpha(alpha.point(lambda value: int(value * 0.32)))
    base.alpha_composite(shadow, (5, 8))
    base.alpha_composite(shape)


def crystal_points(cx, top, height, width):
    mid = top + height * 0.64
    bottom = top + height
    return [
        (cx, top),
        (cx + width * 0.48, top + height * 0.18),
        (cx + width * 0.42, mid),
        (cx, bottom),
        (cx - width * 0.42, mid),
        (cx - width * 0.48, top + height * 0.18),
    ]


def draw_crystal(draw, cx, top, height, width, color, glow):
    pts = crystal_points(cx, top, height, width)
    poly(draw, pts, color, outline=(72, 45, 108, 230), width=3)
    poly(draw, [pts[0], pts[1], pts[2], (cx, top + height * 0.66)], (255, 255, 255, 62))
    poly(draw, [pts[0], (cx, top + height * 0.66), pts[4], pts[5]], (120, 72, 210, 92))
    line(draw, [(cx, top + 12), (cx, top + height - 10)], glow, width=max(3, int(width * 0.08)))
    line(draw, [(cx - width * 0.21, top + height * 0.29), (cx + width * 0.22, top + height * 0.19)], (255, 255, 255, 180), width=4)


def draw_leaf(draw, cx, cy, length, width, color, angle):
    pts = []
    for t in [i / 10 for i in range(11)]:
        y = -length / 2 + length * t
        curve = math.sin(t * math.pi)
        pts.append((-width * curve, y))
    for t in [i / 10 for i in reversed(range(11))]:
        y = -length / 2 + length * t
        curve = math.sin(t * math.pi)
        pts.append((width * curve, y))
    ca, sa = math.cos(angle), math.sin(angle)
    final = [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in pts]
    poly(draw, final, color, outline=(41, 104, 48, 230), width=3)
    line(draw, [(cx - length * 0.42 * sa, cy + length * 0.42 * ca), (cx + length * 0.42 * sa, cy - length * 0.42 * ca)], (204, 255, 150, 210), width=3)


def draw_backplate(img: Image.Image, category: str):
    d = ImageDraw.Draw(img)
    outer, inner = CATEGORY_COLORS.get(category, CATEGORY_COLORS["crafted"])
    ellipse(d, 128, 140, 108, 82, (*outer, 46))
    ellipse(d, 128, 137, 98, 74, (24, 31, 29, 38))
    d.arc((32, 50, 224, 218), 198, 342, fill=(*inner, 130), width=8)


def draw_icon(resource_id: str, category: str) -> Image.Image:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw_backplate(img, category)
    shape = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(shape)

    if resource_id == "aeolian-crystal":
        glow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        for box, alpha in [((62, 48, 194, 208), 40), ((82, 38, 174, 218), 24)]:
            gd.ellipse(box, fill=(151, 77, 255, alpha))
        img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(10)))
        for args in [(94, 74, 126, 46), (132, 38, 168, 56), (169, 84, 118, 40), (65, 108, 82, 28)]:
            draw_crystal(d, args[0], args[1], args[2], args[3], (154, 93, 228, 222), (218, 244, 255, 220))
        for x, y in [(112, 56), (147, 71), (164, 116), (91, 128)]:
            ellipse(d, x, y, 4, 4, (255, 255, 255, 220))
    elif "crystal" in resource_id or resource_id in {"light_crystal", "star_glass"}:
        color = (145, 226, 255, 205) if resource_id != "star_glass" else (114, 111, 230, 205)
        for args in [(91, 82, 112, 36), (132, 54, 150, 48), (170, 96, 100, 34)]:
            draw_crystal(d, *args, color, (245, 255, 255, 210))
    elif resource_id in {"flax", "reed", "sugar_cane"}:
        colors = {"flax": (91, 171, 84, 255), "reed": (129, 185, 91, 255), "sugar_cane": (166, 216, 92, 255)}
        for i, x in enumerate([74, 98, 124, 150, 176]):
            line(d, [(x, 190), (x + (i - 2) * 6, 58 + i * 5)], (63, 119, 54, 255), width=8)
            ellipse(d, x + (i - 2) * 6, 58 + i * 5, 9, 14, colors[resource_id])
        rect(d, (80, 178, 178, 194), (173, 112, 54, 255), radius=6)
    elif resource_id in {"fiber", "rope"}:
        color = (224, 196, 132, 255) if resource_id == "rope" else (244, 222, 158, 255)
        for r in [54, 39, 24]:
            d.arc((128 - r, 128 - r, 128 + r, 128 + r), 25, 330, fill=color, width=12)
        line(d, [(88, 154), (176, 102)], (150, 104, 55, 255), width=5)
    elif resource_id in {"dyes", "paints"}:
        for i, color in enumerate([(220, 61, 86, 255), (62, 162, 219, 255), (244, 198, 65, 255)]):
            ellipse(d, 86 + i * 42, 128 - i * 10, 30, 38, color)
            ellipse(d, 76 + i * 42, 113 - i * 10, 7, 10, (255, 255, 255, 120))
    elif resource_id in {"oil_plants", "rare_flowers"}:
        petal = (226, 93, 190, 255) if resource_id == "rare_flowers" else (245, 200, 58, 255)
        for cx, cy in [(98, 126), (134, 104), (158, 144)]:
            for a in range(0, 360, 72):
                ellipse(d, cx + math.cos(math.radians(a)) * 17, cy + math.sin(math.radians(a)) * 12, 11, 16, petal)
            ellipse(d, cx, cy, 8, 8, (255, 218, 80, 255))
        line(d, [(94, 178), (154, 138), (176, 184)], (53, 137, 62, 255), width=7)
    elif resource_id in {"sap", "amber_essence", "vegetable_oil"}:
        liquid = {"sap": (255, 160, 46, 220), "amber_essence": (255, 184, 58, 228), "vegetable_oil": (241, 194, 55, 220)}[resource_id]
        ellipse(d, 128, 137, 51, 67, (139, 221, 240, 86), outline=(210, 251, 255, 190), width=5)
        ellipse(d, 128, 158, 43, 31, liquid)
        rect(d, (110, 52, 146, 102), (136, 218, 238, 96), outline=(210, 251, 255, 170), radius=12)
        ellipse(d, 113, 106, 7, 18, (255, 255, 255, 120))
    elif resource_id in {"premium_planks", "reinforced_beams"}:
        wood = (232, 179, 94, 255)
        for i in range(3):
            rect(d, (58 + i * 12, 96 + i * 22, 190 + i * 2, 116 + i * 22), wood, outline=(126, 78, 37, 255), width=3, radius=5)
            line(d, [(82, 105 + i * 22), (170, 101 + i * 22)], (255, 230, 145, 180), width=3)
        if resource_id == "premium_planks":
            draw_crystal(d, 172, 66, 74, 22, (166, 103, 234, 220), (240, 255, 255, 210))
        else:
            line(d, [(62, 151), (190, 89)], (138, 158, 166, 255), width=8)
    elif resource_id in {"iron_ingot", "gold_ingot", "aeolian_alloy"}:
        fill = {"iron_ingot": (148, 160, 164, 255), "gold_ingot": (242, 181, 62, 255), "aeolian_alloy": (164, 190, 205, 255)}[resource_id]
        for i, (x, y) in enumerate([(70, 143), (103, 112), (136, 146)]):
            poly(d, [(x, y), (x + 70, y - 12), (x + 88, y + 20), (x + 15, y + 35)], fill, outline=(82, 79, 78, 255), width=3)
            line(d, [(x + 16, y + 3), (x + 67, y - 5)], (255, 255, 255, 120), width=3)
        if resource_id == "aeolian_alloy":
            line(d, [(94, 82), (170, 177)], (105, 235, 255, 180), width=5)
    elif resource_id in {"copper_parts", "mechanisms", "super-mechanisms"}:
        metal = (216, 113, 51, 255) if resource_id == "copper_parts" else (157, 169, 174, 255)
        for cx, cy, r in [(104, 122, 37), (153, 143, 31)]:
            ellipse(d, cx, cy, r, r, metal, outline=(78, 83, 84, 255), width=5)
            ellipse(d, cx, cy, r * 0.38, r * 0.38, (40, 48, 51, 255))
            for a in range(0, 360, 45):
                line(d, [(cx, cy), (cx + math.cos(math.radians(a)) * r, cy + math.sin(math.radians(a)) * r)], (241, 222, 160, 130), width=4)
        if resource_id == "super-mechanisms":
            draw_crystal(d, 129, 51, 74, 24, (165, 95, 235, 230), (230, 255, 255, 220))
    elif resource_id in {"tools", "armor_plates", "printing_plate"}:
        if resource_id == "tools":
            line(d, [(78, 174), (170, 82)], (114, 74, 43, 255), width=15)
            poly(d, [(155, 61), (198, 82), (178, 112), (137, 92)], (154, 166, 170, 255), outline=(71, 77, 80, 255), width=4)
        else:
            poly(d, [(75, 91), (135, 62), (188, 91), (176, 171), (130, 198), (84, 170)], (151, 166, 174, 255), outline=(68, 76, 82, 255), width=5)
            line(d, [(98, 116), (162, 90), (152, 160), (106, 174)], (225, 238, 240, 110), width=5)
            if resource_id == "printing_plate":
                line(d, [(106, 117), (152, 117), (112, 145), (160, 151)], (82, 62, 116, 180), width=5)
    elif resource_id in {"paper", "memory_shard"}:
        for i in range(3):
            rect(d, (76 + i * 13, 72 + i * 18, 170 + i * 13, 154 + i * 18), (238, 224, 184, 255), outline=(129, 105, 71, 255), width=3, radius=7)
            line(d, [(94 + i * 13, 102 + i * 18), (146 + i * 13, 94 + i * 18)], (145, 116, 83, 180), width=3)
        if resource_id == "memory_shard":
            draw_crystal(d, 132, 63, 119, 33, (126, 146, 247, 178), (255, 255, 255, 190))
    elif resource_id == "lenses":
        ellipse(d, 111, 128, 42, 42, (124, 220, 244, 125), outline=(200, 246, 255, 245), width=7)
        ellipse(d, 154, 124, 31, 31, (124, 220, 244, 110), outline=(200, 246, 255, 225), width=6)
        line(d, [(81, 164), (55, 190)], (126, 85, 46, 255), width=12)
        line(d, [(126, 119), (95, 144)], (255, 255, 255, 145), width=5)
    elif resource_id in {"reinforced_concrete", "stone_heart"}:
        if resource_id == "stone_heart":
            poly(d, [(128, 67), (179, 112), (161, 177), (128, 199), (95, 177), (77, 112)], (116, 122, 124, 255), outline=(58, 66, 69, 255), width=5)
            line(d, [(103, 134), (151, 112), (133, 172)], (255, 180, 77, 200), width=6)
        else:
            rect(d, (65, 86, 186, 175), (122, 133, 134, 255), outline=(61, 73, 76, 255), width=5, radius=12)
            for x in [87, 128, 169]:
                line(d, [(x, 79), (x - 30, 182)], (170, 181, 178, 255), width=5)
            line(d, [(75, 123), (181, 104)], (86, 95, 97, 180), width=4)
    elif resource_id in {"blue_salt", "silent_powder", "emerald_dust"}:
        color = {"blue_salt": (80, 179, 255, 255), "silent_powder": (170, 163, 190, 255), "emerald_dust": (67, 218, 139, 255)}[resource_id]
        ellipse(d, 128, 151, 64, 32, color, outline=(70, 80, 92, 210), width=3)
        for i in range(13):
            x = 72 + (i * 17) % 112
            y = 115 + ((i * 29) % 54)
            ellipse(d, x, y, 5 + i % 4, 4 + i % 3, color)
        if resource_id == "emerald_dust":
            draw_crystal(d, 132, 62, 78, 26, (65, 233, 145, 200), (235, 255, 242, 210))
    elif resource_id == "runic_tile":
        for i, x in enumerate([78, 119, 160]):
            poly(d, [(x, 88), (x + 38, 100), (x + 31, 166), (x - 9, 158)], (178, 76, 61, 255), outline=(83, 47, 42, 255), width=3)
            line(d, [(x + 9, 122), (x + 25, 129), (x + 13, 146)], (95, 235, 255, 180), width=4)
    elif resource_id in {"influence_seal", "festival_token"}:
        fill = (107, 188, 226, 255) if resource_id == "influence_seal" else (243, 183, 62, 255)
        ellipse(d, 128, 130, 58, 58, fill, outline=(80, 67, 89, 255), width=6)
        for a in range(0, 360, 60):
            line(d, [(128, 130), (128 + math.cos(math.radians(a)) * 44, 130 + math.sin(math.radians(a)) * 44)], (255, 255, 255, 100), width=4)
        ellipse(d, 128, 130, 20, 20, (255, 255, 255, 110))
    elif resource_id in {"monster_trophy", "relic_fragment"}:
        if resource_id == "monster_trophy":
            poly(d, [(91, 87), (129, 62), (167, 87), (154, 171), (128, 194), (102, 171)], (162, 116, 74, 255), outline=(73, 55, 43, 255), width=5)
            for x in [99, 157]:
                poly(d, [(x, 92), (x + (128 - x) * 0.2, 132), (x + (128 - x) * 0.45, 97)], (232, 218, 176, 255), outline=(94, 80, 62, 255), width=3)
        else:
            draw_crystal(d, 129, 62, 126, 42, (156, 122, 237, 190), (255, 255, 255, 170))
            line(d, [(92, 158), (164, 91)], (255, 206, 99, 190), width=5)
    elif resource_id == "super-windleaf":
        for angle, scale in [(-0.55, 1.0), (0, 1.15), (0.55, 1.0)]:
            draw_leaf(d, 128, 127, 142 * scale, 35 * scale, (83, 228, 91, 245), angle)
        line(d, [(79, 177), (181, 86)], (115, 245, 255, 180), width=6)
    else:
        ellipse(d, 128, 128, 62, 52, (146, 170, 177, 255), outline=(62, 69, 72, 255), width=5)

    add_soft_shadow(img, shape)
    return img


def alpha_bounds(image: Image.Image):
    return image.getchannel("A").getbbox()


def merge_manifest(resources):
    manifest_path = OUT_DIR / "manifest.json"
    existing = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {"resources": []}
    by_id = {item["id"]: item for item in existing.get("resources", [])}
    for resource_id, name, category in resources:
        entry = by_id.get(resource_id, {})
        by_id[resource_id] = {
            **entry,
            "id": resource_id,
            "name": name,
            "category": category,
            "file": f"{resource_id}.png",
            "generator": "png-fallback",
        }
        if (OUT_DIR / f"{resource_id}.glb").exists():
            by_id[resource_id].setdefault("model", f"{resource_id}.glb")
    ordered_existing = [item["id"] for item in existing.get("resources", [])]
    ordered_new = [item[0] for item in resources if item[0] not in ordered_existing]
    ordered_ids = ordered_existing + ordered_new
    manifest = {
        "style": STYLE,
        "size": SIZE,
        "resources": [by_id[resource_id] for resource_id in ordered_ids],
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def render_review(resources):
    cols = 8
    cell_w, cell_h = 160, 188
    rows = math.ceil(len(resources) / cols)
    sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), "#243b35")
    draw = ImageDraw.Draw(sheet)
    small = Image.new("RGB", (cols * cell_w, rows * 86), "#243b35")
    small_draw = ImageDraw.Draw(small)
    for index, (resource_id, _name, _category) in enumerate(resources):
        with Image.open(OUT_DIR / f"{resource_id}.png") as icon:
            x = (index % cols) * cell_w
            y = (index // cols) * cell_h
            thumb = icon.resize((128, 128), Image.Resampling.LANCZOS)
            sheet.paste(thumb, (x + 16, y + 8), thumb)
            draw.text((x + 8, y + 146), resource_id, fill="white")
            sy = (index // cols) * 86
            for size, offset in ((24, 8), (32, 44), (48, 88)):
                preview = icon.resize((size, size), Image.Resampling.LANCZOS)
                small.paste(preview, (x + offset, sy + 7), preview)
            small_draw.text((x + 8, sy + 60), resource_id, fill="white")
    sheet.save(OUT_DIR / "resource_icons_docs_fallback_review.png")
    small.save(OUT_DIR / "resource_icons_docs_fallback_small_review.png")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    targets = [("aeolian-crystal", "Эолийские кристаллы", "basic"), *RESOURCES]
    report = []
    for resource_id, _name, category in targets:
        image = draw_icon(resource_id, category)
        path = OUT_DIR / f"{resource_id}.png"
        image.save(path)
        box = alpha_bounds(image)
        if not box or image.size != (SIZE, SIZE) or image.getpixel((0, 0))[3] != 0:
            raise AssertionError(resource_id)
        if min(box[:2]) < 12 or max(box[2:]) > 244:
            raise AssertionError((resource_id, box))
        report.append({"id": resource_id, "file": path.name, "alpha_bounds": box, "bytes": path.stat().st_size})
    manifest = merge_manifest(targets)
    render_review(targets)
    (OUT_DIR / "docs-fallback-validation.json").write_text(
        json.dumps({"icons": report, "manifest_resources": len(manifest["resources"])}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"icons": len(report), "manifest_resources": len(manifest["resources"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
