"""Листы проверки ассетов; не являются скриншотами игрового интерфейса."""
import html
import json
import subprocess
from pathlib import Path
from build_icon_set import ROOT
from PIL import Image, ImageDraw

def main():
    ui = ROOT / 'frontend/public/assets/ui'
    review = ROOT / 'docs/assets/ui/review/icons'
    review.mkdir(parents=True, exist_ok=True)
    icons = json.loads((ui / 'icons/manifest.json').read_text())['icons']
    resources = json.loads((ui / 'resources/manifest.json').read_text())['resources']
    cards = []
    for key in icons:
        svg = (ui / f'icons/{key}.svg').read_text()
        small = (ui / f'icons/small/{key}.svg').read_text()
        cards.append(f'<article><b>{key}</b>'+''.join(f'<span style="--size:{size}px">{small if size == 16 else svg}</span>' for size in (16, 20, 32, 64))+'</article>')
    for item in resources:
        svg = (ui / 'resources' / item['file']).read_text()
        cards.append(f'<article><b>{html.escape(item["name"])}</b>'+''.join(f'<span style="--size:{size}px">{svg}</span>' for size in (16, 20, 32, 64))+'</article>')
    body = ''.join(cards)
    (review / 'index.html').write_text('<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Эолия — лист проверки знаков</title><style>body{margin:16px;font:16px "Trebuchet MS","Segoe UI",sans-serif}section{padding:16px;display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:12px}article{border:1px solid;padding:8px;display:flex;align-items:center;gap:10px;min-height:80px}b{width:100px;font-size:12px;overflow-wrap:anywhere}span{display:inline-flex;width:var(--size);height:var(--size);flex-shrink:0}svg{width:100%;height:100%}.dark{background:#293e38;color:#f9f4df}.light{background:#f3ead1;color:#293e38}.gray{filter:grayscale(1)}</style><h1>Проверка ассетов — не скриншоты игры</h1><p>16 / 20 / 32 / 64 px. Проверить при масштабе 100 / 200%, DPR 1 / 2. На ресурсах малый режим компонента проверяется отдельно в игре.</p><h2>Тёмный фон</h2><section class="dark">'+body+'</section><h2>Светлый фон</h2><section class="light">'+body+'</section><h2>Без цвета</h2><section class="dark gray">'+body+'</section></html>')
    # Детерминированный экспорт пилота: прозрачный PNG/WebP и обзорный лист.
    pilot = ['select', 'build', 'repair', 'attack', 'market', 'alliance', 'chat', 'wood', 'stone', 'coins', 'shield', 'offline']
    sheet = Image.new('RGB', (720, 240), '#293e38')
    draw = ImageDraw.Draw(sheet)
    for i, key in enumerate(pilot):
        svg = (ui / f'icons/{key}.svg').read_text().replace('currentColor', '#f9f4df')
        target = review / f'{key}.png'
        subprocess.run(['convert', '-background', 'none', '-size', '64x64', 'svg:-', str(target)], input=svg.encode(), check=True, capture_output=True)
        img = Image.open(target).convert('RGBA')
        img.save(review / f'{key}.webp', lossless=True)
        x, y = (i % 6) * 120 + 28, (i // 6) * 120 + 12
        sheet.paste(img, (x, y), img)
        draw.text((x-8, y+72), key, fill='#f9f4df')
    sheet.save(review / 'pilot.png')
    sheet = Image.new('RGB', (960, 800), '#293e38')
    draw = ImageDraw.Draw(sheet)
    for i, item in enumerate(resources):
        target = review / 'resource-sample.png' if i == 0 else Path('/tmp/aeolian-resource-review.png')
        subprocess.run(['convert', '-background', 'none', '-size', '64x64', str(ui / 'resources' / item['file']), str(target)], check=True, capture_output=True)
        img = Image.open(target).convert('RGBA')
        if i == 0: img.save(review / 'resource-sample.webp', lossless=True)
        x, y = (i % 10)*96+16, (i // 10)*100+4
        sheet.paste(img, (x, y), img)
        draw.text((x-12, y+68), item['id'][:15], fill='#f9f4df')
    sheet.save(review / 'resources.png')

if __name__ == '__main__':
    main()
