from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "frontend" / "public" / "assets" / "buildings" / "storage" / "coin_storage"
SIZE = (512, 384)
LEVELS = range(1, 4)
STATES = ("active", "construction", "damaged", "ruined")


def rgba(hex_color: str, alpha: int = 255):
    value = hex_color.lstrip("#")
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4)) + (alpha,)


def new_sprite():
    image = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    shadow = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(shadow)
    draw.ellipse((126, 278, 386, 350), fill=(0, 0, 0, 76))
    image.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(12)))
    return image, ImageDraw.Draw(image)


def iso_poly(cx: int, cy: int, w: int, h: int):
    return [(cx, cy - h // 2), (cx + w // 2, cy), (cx, cy + h // 2), (cx - w // 2, cy)]


def base(draw: ImageDraw.ImageDraw, level: int):
    width = 252 + level * 12
    height = 104 + level * 4
    top = iso_poly(256, 292, width, height)
    lower = [(x, y + 22) for x, y in top]
    draw.polygon([top[3], top[2], lower[2], lower[3]], fill=rgba("#3e803e"))
    draw.polygon([top[1], top[2], lower[2], lower[1]], fill=rgba("#2f6638"))
    draw.polygon(top, fill=rgba("#67b452"))
    draw.line(top + [top[0]], fill=rgba("#d9ffc8", 135), width=3)
    path = iso_poly(256, 296, 150 + level * 8, 48)
    draw.polygon(path, fill=rgba("#b79058", 210))
    draw.line(path + [path[0]], fill=rgba("#fff0b8", 80), width=2)


def draw_chest(draw: ImageDraw.ImageDraw, cx: int, y: int, w: int, h: int, level: int, damaged: bool = False):
    x0 = cx - w // 2
    x1 = cx + w // 2
    body = "#8b5a35" if not damaged else "#63402f"
    side = "#65442f" if not damaged else "#3f302b"
    trim = "#e2b946" if level < 3 else "#f0cf60"
    metal = "#837768" if level == 1 else "#9b9381"

    draw.rounded_rectangle((x0, y, x1, y + h), radius=8, fill=rgba(body))
    draw.polygon([(x1, y + 8), (x1 + 28, y + 24), (x1 + 28, y + h + 20), (x1, y + h)], fill=rgba(side))
    draw.polygon([(x0 + 6, y - 28), (x1 - 6, y - 28), (x1 + 26, y + 8), (x0 + 28, y + 8)], fill=rgba("#a36b3b" if not damaged else "#5a3a2f"))
    draw.arc((x0 + 6, y - 54, x1 - 6, y + 26), 180, 360, fill=rgba("#f5d271", 210), width=7)
    draw.rectangle((x0 + 12, y + 12, x1 - 12, y + 24), fill=rgba(trim))
    draw.rectangle((x0 + 18, y + h - 20, x1 - 18, y + h - 10), fill=rgba(trim))
    draw.rectangle((cx - 13, y + 26, cx + 13, y + 54), fill=rgba(metal))
    draw.rectangle((cx - 7, y + 35, cx + 7, y + 48), fill=rgba("#4b3b2e"))
    for offset in (-44, 44):
        draw.rectangle((cx + offset - 6, y + 8, cx + offset + 6, y + h - 6), fill=rgba(trim, 230))


def draw_guard_post(draw: ImageDraw.ImageDraw, x: int, y: int, level: int):
    draw.rectangle((x - 8, y - 46, x + 8, y + 10), fill=rgba("#6c4931"))
    draw.polygon([(x, y - 76), (x + 26, y - 42), (x - 26, y - 42)], fill=rgba("#6f8e55" if level < 3 else "#4d8d8c"))
    draw.rectangle((x - 17, y - 44, x + 17, y - 32), fill=rgba("#d0a640"))


def draw_coin_pile(draw: ImageDraw.ImageDraw, cx: int, cy: int, count: int, damaged: bool = False):
    color = "#efc14c" if not damaged else "#a67e3c"
    edge = "#fff2a8" if not damaged else "#6f552e"
    for index in range(count):
        x = cx + (index % 5) * 13 - 26
        y = cy - (index // 5) * 7 + (index % 2) * 3
        draw.ellipse((x - 9, y - 5, x + 9, y + 5), fill=rgba(color), outline=rgba(edge, 180), width=2)


def draw_scaffold(draw: ImageDraw.ImageDraw, level: int):
    x0 = 176 - level * 4
    x1 = 338 + level * 5
    y0 = 175 - level * 4
    y1 = 275
    wood = rgba("#9b6b3d")
    for x in (x0, x1, 220, 292):
        draw.line([(x, y0), (x, y1)], fill=wood, width=6)
    draw.line([(x0 - 8, y0 + 28), (x1 + 12, y0 + 4)], fill=wood, width=6)
    draw.line([(x0, y0 + 64), (x1 + 6, y0 + 44)], fill=wood, width=6)
    draw.line([(x0, y1 - 8), (x1, y1 - 36)], fill=wood, width=6)
    draw.rectangle((152, 276, 212, 294), fill=rgba("#c59755"))
    draw.rectangle((310, 276, 376, 294), fill=rgba("#958b7b"))


def draw_coin_storage(level: int, state: str):
    image, draw = new_sprite()
    damaged = state in ("damaged", "ruined")
    construction = state == "construction"
    base(draw, level)

    if construction:
        draw_chest(draw, 254, 209, 102 + level * 12, 52 + level * 5, level)
        draw.rectangle((204, 176, 304, 212), fill=rgba("#b48a53"))
        draw.rectangle((222, 166, 332, 184), fill=rgba("#d9b665"))
        draw_scaffold(draw, level)
        draw_coin_pile(draw, 264, 283, 5 + level * 2)
        return image

    width = 116 + level * 22
    height = 66 + level * 9
    draw_chest(draw, 254, 204 - level * 8, width, height, level, damaged)

    if level >= 2:
        draw_guard_post(draw, 176, 259, level)
        draw_guard_post(draw, 342, 257, level)
        draw.rectangle((192, 247, 326, 257), fill=rgba("#d6ad47" if not damaged else "#756046"))

    if level >= 3:
        draw.polygon([(214, 174), (258, 144), (306, 174), (304, 186), (214, 186)], fill=rgba("#c9c1a9" if not damaged else "#777066"))
        draw.rectangle((248, 145, 268, 181), fill=rgba("#f0cf60"))
        draw.polygon([(258, 126), (274, 152), (242, 152)], fill=rgba("#b06df2", 225))
        draw.line([(258, 126), (258, 152)], fill=rgba("#fff2ff", 120), width=2)

    draw_coin_pile(draw, 178, 287, 5 + level * 2, damaged)
    draw_coin_pile(draw, 334, 287, 4 + level, damaged)

    if damaged:
        draw.line([(202, 198), (224, 210), (210, 228), (238, 242)], fill=rgba("#1d1714", 210), width=5)
        draw.line([(288, 172), (306, 190), (292, 207), (320, 222)], fill=rgba("#1d1714", 210), width=5)
        draw.polygon([(304, 248), (354, 262), (336, 290), (292, 278)], fill=rgba("#4b3429", 230))
        if state == "ruined":
            image = ImageEnhance.Brightness(image).enhance(0.82)
            draw.rectangle((226, 216, 302, 260), fill=rgba("#2f2723", 115))
    return image


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for level in LEVELS:
        for state in STATES:
            draw_coin_storage(level, state).save(OUT_DIR / f"coin_storage_l{level:02d}_{state}.png")


if __name__ == "__main__":
    main()
