from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageEnhance


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "frontend" / "public" / "assets" / "buildings"
SIZE = (512, 384)
STATES = ("active", "construction", "damaged")


def rgba(hex_color, alpha=255):
    value = hex_color.lstrip("#")
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4)) + (alpha,)


def new_sprite():
    image = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    shadow = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(shadow)
    draw.ellipse((124, 276, 390, 350), fill=(0, 0, 0, 82))
    image.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(12)))
    return image, ImageDraw.Draw(image)


def iso_poly(cx, cy, w, h):
    return [(cx, cy - h // 2), (cx + w // 2, cy), (cx, cy + h // 2), (cx - w // 2, cy)]


def base(draw, cx=256, cy=292, w=278, h=112, color="#6db857"):
    top = iso_poly(cx, cy, w, h)
    lower = [(x, y + 24) for x, y in top]
    draw.polygon([top[3], top[2], lower[2], lower[3]], fill=rgba("#3f7f3e"))
    draw.polygon([top[1], top[2], lower[2], lower[1]], fill=rgba("#2d6535"))
    draw.polygon(top, fill=rgba(color))
    draw.line(top + [top[0]], fill=rgba("#d7ffc0", 145), width=3)


def tint_state(image, state):
    if state == "construction":
        overlay = Image.new("RGBA", SIZE, (232, 187, 73, 34))
        image = Image.alpha_composite(image, overlay)
        draw = ImageDraw.Draw(image)
        for x in range(84, 430, 42):
            draw.line([(x, 270), (x + 56, 326)], fill=rgba("#f4d36f", 150), width=6)
    if state == "damaged":
        image = ImageEnhance.Color(image).enhance(0.7)
        image = ImageEnhance.Brightness(image).enhance(0.78)
        draw = ImageDraw.Draw(image)
        for points in (
            [(196, 180), (220, 190), (198, 202), (224, 217)],
            [(290, 154), (310, 168), (292, 182), (318, 196)],
            [(246, 236), (270, 246), (252, 262), (282, 272)],
        ):
            draw.line(points, fill=rgba("#1d1714", 190), width=5, joint="curve")
    return image


def draw_roof(draw, cx, y, w, h, color, side="#74472e"):
    draw.polygon([(cx, y - h), (cx + w // 2, y), (cx, y + h // 2), (cx - w // 2, y)], fill=rgba(color))
    draw.polygon([(cx + w // 2, y), (cx, y + h // 2), (cx, y + h // 2 + 24), (cx + w // 2, y + 24)], fill=rgba(side))
    draw.line([(cx, y - h), (cx + w // 2, y), (cx, y + h // 2), (cx - w // 2, y), (cx, y - h)], fill=rgba("#fff4b2", 80), width=3)


def town_hall(level, state):
    image, draw = new_sprite()
    scale = 1 + (level - 1) * 0.045
    base(draw, w=int(288 * scale), h=int(116 * scale), color="#669d5a")
    body_w = int(148 * scale)
    body_h = int(102 * scale)
    x0 = 256 - body_w // 2
    y0 = 202 - body_h // 2
    draw.rounded_rectangle((x0, y0, x0 + body_w, y0 + body_h), radius=8, fill=rgba("#b98b55"))
    draw.polygon([(x0 + body_w, y0), (x0 + body_w + 34, y0 + 20), (x0 + body_w + 34, y0 + body_h + 20), (x0 + body_w, y0 + body_h)], fill=rgba("#8d6546"))
    draw_roof(draw, 256, y0 + 12, int(204 * scale), int(70 * scale), "#8b3f34", "#6f302e")
    tower_h = int(104 * scale)
    draw.rounded_rectangle((224, y0 - tower_h + 30, 288, y0 + 26), radius=7, fill=rgba("#d4b06a"))
    draw_roof(draw, 256, y0 - tower_h + 38, 94, 52, "#9f4936", "#713128")
    draw.rectangle((244, y0 + 38, 268, y0 + body_h), fill=rgba("#4f3228"))
    for x in (x0 + 24, x0 + body_w - 44):
        draw.rectangle((x, y0 + 34, x + 24, y0 + 58), fill=rgba("#6fd0dc"))
    if level >= 4:
        draw.rectangle((303, y0 + 60, 316, y0 + body_h + 10), fill=rgba("#5f4432"))
        draw.polygon([(309, y0 + 36), (333, y0 + 68), (285, y0 + 68)], fill=rgba("#8b3f34"))
    return tint_state(image, state)


def dugout(level, state):
    image, draw = new_sprite()
    scale = 1 + (level - 1) * 0.06
    base(draw, w=int(240 * scale), h=int(96 * scale), color="#5b9b48")
    draw.ellipse((148, 210, 364, 306), fill=rgba("#7b5538"))
    draw.pieslice((148, 162, 364, 306), 180, 360, fill=rgba("#47843c"))
    draw.pieslice((174, 176, 338, 292), 180, 360, fill=rgba("#5aa24b"))
    draw.rectangle((236, 245, 276, 306), fill=rgba("#513322"))
    if level >= 3:
        draw.rectangle((176, 238, 202, 272), fill=rgba("#d39a52"))
        draw.line([(174, 244), (204, 244)], fill=rgba("#74482a"), width=5)
    return tint_state(image, state)


def wood_house(level, state):
    image, draw = new_sprite()
    scale = 1 + (level - 1) * 0.05
    base(draw, w=int(258 * scale), h=int(104 * scale), color="#69a653")
    body_w = int(142 * scale)
    body_h = int(86 * scale)
    x0 = 256 - body_w // 2
    y0 = 216 - body_h // 2
    draw.rounded_rectangle((x0, y0, x0 + body_w, y0 + body_h), radius=7, fill=rgba("#a86e3d"))
    for y in range(y0 + 13, y0 + body_h, 18):
        draw.line([(x0 + 8, y), (x0 + body_w - 8, y)], fill=rgba("#6f4329", 130), width=4)
    draw_roof(draw, 256, y0 + 6, int(196 * scale), int(62 * scale), "#596b45", "#455438")
    draw.rectangle((240, y0 + 38, 272, y0 + body_h), fill=rgba("#4e3020"))
    draw.rectangle((x0 + 24, y0 + 32, x0 + 50, y0 + 56), fill=rgba("#6fd0dc"))
    if level >= 4:
        draw.rectangle((314, y0 - 38, 330, y0 + 8), fill=rgba("#7b5538"))
        draw.polygon([(322, y0 - 62), (344, y0 - 28), (300, y0 - 28)], fill=rgba("#596b45"))
    return tint_state(image, state)


def lumber_yard(level, state):
    del level
    image, draw = new_sprite()
    base(draw, w=284, h=110, color="#6a9e55")
    for i, y in enumerate((258, 277, 296)):
        draw.rounded_rectangle((154 + i * 16, y - 12, 306 + i * 16, y + 10), radius=9, fill=rgba("#8b5a35"))
        draw.ellipse((146 + i * 16, y - 12, 168 + i * 16, y + 10), fill=rgba("#c28a52"))
    draw.rectangle((194, 194, 318, 260), fill=rgba("#9b663e"))
    draw.polygon([(194, 194), (256, 148), (318, 194)], fill=rgba("#597f4a"))
    draw.polygon([(318, 194), (346, 214), (346, 278), (318, 260)], fill=rgba("#6d472e"))
    draw.line([(176, 226), (350, 278)], fill=rgba("#4d382a"), width=8)
    draw.line([(350, 226), (180, 286)], fill=rgba("#4d382a"), width=8)
    return tint_state(image, state)


BUILDERS = {
    ("center/town_hall", "town_hall", 10): town_hall,
    ("housing/dugout", "dugout", 5): dugout,
    ("housing/wood_house", "wood_house", 6): wood_house,
    ("industry/lumber_yard", "lumber_yard", 13): lumber_yard,
}


def main():
    for (folder, name, levels), builder in BUILDERS.items():
        target = OUT_DIR / folder
        target.mkdir(parents=True, exist_ok=True)
        for level in range(1, levels + 1):
            for state in STATES:
                builder(level, state).save(target / f"{name}_l{level:02d}_{state}.png")


if __name__ == "__main__":
    main()
