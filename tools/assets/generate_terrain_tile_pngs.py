from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "frontend" / "public" / "assets" / "terrain" / "tiles"
SIZE = 512
TERRAIN = ("grass", "forest", "water", "mountain", "oil_well", "ruins")


def iso(cx=256, cy=300, w=380, h=194):
    return [(cx, cy - h // 2), (cx + w // 2, cy), (cx, cy + h // 2), (cx - w // 2, cy)]


def shaded_base(draw, top_fill, stroke=(220, 255, 180, 120)):
    top = iso()
    lower = [(x, y + 34) for x, y in top]
    draw.polygon([top[3], top[2], lower[2], lower[3]], fill=(52, 126, 58, 255))
    draw.polygon([top[1], top[2], lower[2], lower[1]], fill=(39, 95, 47, 255))
    draw.polygon(top, fill=top_fill)
    draw.line(top + [top[0]], fill=stroke, width=4, joint="curve")


def soft_layer():
    image = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    shadow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.polygon(iso(cy=316, w=390, h=204), fill=(5, 18, 8, 88))
    shadow = shadow.filter(ImageFilter.GaussianBlur(11))
    image.alpha_composite(shadow)
    return image, ImageDraw.Draw(image)


def grass():
    image, draw = soft_layer()
    shaded_base(draw, (128, 219, 88, 255))
    for x, y, angle in [(176, 295, -20), (210, 327, 12), (294, 305, 18), (330, 280, -12)]:
        draw.line([(x, y), (x + angle // 3, y - 30)], fill=(53, 137, 56, 255), width=5)
        draw.line([(x + 3, y - 17), (x + 18, y - 31)], fill=(226, 255, 207, 168), width=3)
    draw.arc((126, 250, 386, 338), 190, 345, fill=(222, 255, 182, 70), width=8)
    return image


def tree(draw, x, y, scale):
    trunk_w = int(16 * scale)
    draw.rounded_rectangle((x - trunk_w // 2, y - int(18 * scale), x + trunk_w // 2, y + int(56 * scale)), radius=4, fill=(102, 58, 29, 255))
    draw.polygon([(x, y - int(118 * scale)), (x - int(58 * scale), y - int(20 * scale)), (x + int(58 * scale), y - int(20 * scale))], fill=(44, 127, 61, 255))
    draw.polygon([(x, y - int(158 * scale)), (x - int(70 * scale), y - int(52 * scale)), (x + int(70 * scale), y - int(52 * scale))], fill=(62, 170, 79, 255))
    draw.polygon([(x - int(22 * scale), y - int(126 * scale)), (x - int(56 * scale), y - int(64 * scale)), (x + int(8 * scale), y - int(64 * scale))], fill=(76, 195, 83, 230))


def forest():
    image, draw = soft_layer()
    shaded_base(draw, (70, 151, 65, 255), (202, 255, 162, 88))
    tree(draw, 192, 266, 0.78)
    tree(draw, 256, 254, 1.0)
    tree(draw, 326, 278, 0.72)
    draw.ellipse((208, 330, 237, 356), fill=(105, 196, 87, 255))
    draw.ellipse((303, 334, 329, 358), fill=(93, 182, 79, 255))
    return image


def water():
    image, draw = soft_layer()
    shaded_base(draw, (108, 198, 91, 255), (210, 255, 170, 88))
    band = [(74, 286), (382, 222), (438, 260), (130, 324)]
    draw.polygon(band, fill=(58, 174, 226, 228))
    draw.line([(96, 294), (408, 231)], fill=(200, 249, 255, 120), width=6)
    for offset in (0, 74, 154, 232):
        draw.line([(132 + offset, 292 - offset // 5), (180 + offset, 282 - offset // 5)], fill=(235, 255, 255, 190), width=5)
    return image


def mountain():
    image, draw = soft_layer()
    shaded_base(draw, (91, 166, 76, 255), (206, 255, 165, 88))
    draw.polygon([(220, 150), (132, 329), (316, 329)], fill=(129, 139, 138, 255))
    draw.polygon([(220, 150), (316, 329), (256, 338)], fill=(69, 83, 84, 255))
    draw.polygon([(220, 150), (188, 216), (245, 204)], fill=(238, 245, 231, 255))
    draw.polygon([(316, 198), (248, 334), (394, 329)], fill=(106, 116, 116, 255))
    draw.polygon([(316, 198), (394, 329), (342, 334)], fill=(71, 82, 83, 255))
    return image


def oil_well():
    image, draw = soft_layer()
    shaded_base(draw, (91, 166, 76, 255), (206, 255, 165, 88))
    draw.ellipse((178, 258, 360, 342), fill=(79, 51, 30, 255))
    draw.ellipse((198, 270, 342, 329), fill=(4, 6, 9, 245))
    draw.ellipse((225, 279, 307, 309), fill=(31, 40, 52, 132))
    for box in [(176, 278, 211, 302), (327, 292, 363, 318), (248, 331, 285, 350), (194, 324, 231, 346)]:
        draw.ellipse(box, fill=(116, 101, 74, 255))
    for x, y in [(160, 245), (370, 253), (176, 360), (354, 352)]:
        draw.line([(x, y), (x + 4, y - 36)], fill=(103, 67, 34, 255), width=7)
        draw.line([(x - 18, y - 25), (x + 24, y - 23)], fill=(255, 177, 46, 230), width=5)
    for box in [(236, 290, 247, 298), (292, 301, 301, 308), (267, 314, 274, 320)]:
        draw.ellipse(box, fill=(15, 22, 28, 255))
    return image


def ruins():
    image, draw = soft_layer()
    shaded_base(draw, (99, 171, 78, 255), (206, 255, 165, 88))
    for x, top, h in [(184, 240, 86), (242, 212, 126), (312, 252, 72)]:
        draw.rectangle((x - 16, top, x + 16, top + h), fill=(181, 157, 98, 255))
        draw.rectangle((x + 8, top, x + 16, top + h), fill=(129, 105, 65, 255))
    draw.polygon([(168, 214), (318, 230), (314, 256), (164, 240)], fill=(184, 157, 98, 255))
    draw.polygon([(260, 328), (324, 305), (371, 326), (303, 352)], fill=(106, 83, 52, 255))
    draw.ellipse((235, 300, 277, 342), fill=(250, 181, 48, 255))
    draw.ellipse((247, 312, 265, 330), fill=(255, 225, 114, 255))
    return image


BUILDERS = {
    "grass": grass,
    "forest": forest,
    "water": water,
    "mountain": mountain,
    "oil_well": oil_well,
    "ruins": ruins,
}


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for terrain in TERRAIN:
        BUILDERS[terrain]().save(OUT_DIR / f"{terrain}.png")


if __name__ == "__main__":
    main()
