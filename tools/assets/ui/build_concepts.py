"""Воспроизводимые SVG-схемы фазы 1; это макеты, не браузерные снимки."""
import base64
import html
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'docs/assets/ui/concepts'
FONT = '&quot;Trebuchet MS&quot;, &quot;Segoe UI&quot;, ui-sans-serif, system-ui, sans-serif'


def rect(x, y, w, h, fill='#FFF8E8', stroke='#20332F'):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'


def text(x, y, value, size=16):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="#20302B">{html.escape(value)}</text>'


def image(path, x, y, w, h):
    data = base64.b64encode((ROOT / 'frontend/public' / path).read_bytes()).decode()
    return f'<image x="{x}" y="{y}" width="{w}" height="{h}" href="data:image/png;base64,{data}"/>'


def save(name, w, h, parts):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" font-family="{FONT}" role="img"><title>Эолия: проектная схема, не снимок браузера</title>' + ''.join(parts) + '</svg>')


def layout(w, h, variant):
    mobile = w < 760
    p = [rect(0, 0, w, h, '#86A65C')]
    for y in range(90, h-50, 64):
        for x in range(16, w-40, 84):
            p.append(f'<path d="M{x},{y}l40,-20 40,20 -40,20Z" fill="#96B26A" stroke="#688953"/>')
    p += [image('assets/buildings/center/town_hall/town_hall_l01_active.png', w*.35, h*.2, 160, 180),
          image('assets/buildings/housing/dugout/dugout_l01_construction.png', w*.3, h*.5, 115, 110)]
    if mobile:
        p += [rect(8, 8, w-16, 96), text(20, 33, 'Эолия · связь установлена'), text(20, 62, 'Монеты 5000 · Древесина 5000'), text(20, 89, 'Камень 5000')]
        ix, iy, iw, ih = 8, h-356, w-16, 230
        tx, ty, tw, th = 8, h-118, 210, 46
    else:
        p += [rect(8, 8, w-16, 64), text(24, 46, 'Эолия     Монеты 5000     Древесина 5000     Камень 5000     Связь установлена')]
        if variant == 'edge':
            ix, iy, iw, ih = w-288, 94, 272, h-170
            tx, ty, tw, th = 8, 94, 104, 112
        else:
            ix, iy, iw, ih = w-436, h-336, 420, 260
            tx, ty, tw, th = 8, h-128, 220, 52
    p += [rect(tx, ty, tw, th), text(tx+8, ty+29, 'Выбор / Строить', 13), rect(ix, iy, iw, ih), text(ix+14, iy+28, 'Землянка · уровень 1'), text(ix+14, iy+61, '◉ Ваш объект · ◷ Строится', 14), text(ix+14, iy+92, 'Монеты: 50, Древесина: 3', 14), text(ix+14, iy+122, 'Время: 10 с · 1×1 · Жители +1', 14), rect(ix+14, iy+144, min(iw-28, 220), 44, '#286447'), f'<text x="{ix+24}" y="{iy+172}" fill="#FFF8E8" font-size="14">Открыть объект</text>', rect(8, h-60, w-16, 52), text(20, h-28, 'События: заявка принята в макете', 13)]
    # Прямоугольники схемы не пересекаются: метрика относится только к схеме.
    covered = (w-16)*(96 if mobile else 64) + iw*ih + tw*th + (w-16)*52
    save(f'{variant}-{w}.svg', w, h, p)
    return f'| {variant} | {w}×{h} | {100*(1-covered/(w*h)):.1f}% |'


rows = [layout(1440, 900, 'edge'), layout(1440, 900, 'desk'), layout(1024, 768, 'edge'), layout(390, 844, 'mobile')]
(OUT / 'geometry.md').write_text('# Геометрия схем\n\nДоля карты вне прямоугольников HUD; не DOM-измерение, не показатель доступности всех тайлов. Не учитывает вырезы и рамку. Скорость чтения не измерена.\n\n| Вариант | Размер | Карта вне HUD |\n|---|---|---|\n' + '\n'.join(rows) + '\n')

materials = [
    ('Дерево', 'assets/resources/icons/wood.png', 'Каркас: узкая тёмная рейка'),
    ('Ткань', 'assets/resources/icons/fabric.png', 'Мягкая подложка сообщений'),
    ('Камень', 'assets/resources/icons/stone.png', 'Непрозрачная рабочая поверхность'),
    ('Латунь: ориентир медь', 'assets/resources/icons/copper.png', 'Только крепления; латунного ассета нет'),
    ('Кристалл', 'assets/resources/icons/aeolian-crystal.png', 'Технология, не выбор и не угроза'),
    ('Руины', 'assets/terrain/tiles/ruins.png', 'Разрыв контура и след разрушения'),
]
p = [rect(0, 0, 1080, 700, '#F2E6C8'), text(24, 38, 'Эолия: материалы и их роль в интерфейсе', 24)]
for i, (name, path, note) in enumerate(materials):
    x, y = 24 + i % 3 * 352, 60 + i // 3 * 235
    p += [rect(x, y, 332, 220), image(path, x+16, y+12, 120, 120), text(x+14, y+158, name), text(x+14, y+193, note, 12)]
p += [image('assets/buildings/center/town_hall/town_hall_l01_active.png', 24, 535, 140, 145), image('assets/buildings/industry/weaving_yard/weaving_yard_l01_active.png', 190, 535, 140, 145), text(365, 580, 'Ратуша и ткацкий двор: объём остаётся на карте.'), text(365, 612, 'В UI переносим материал и крепления, а не фасад здания.')]
save('moodboard.svg', 1080, 700, p)
print('\n'.join(rows))
