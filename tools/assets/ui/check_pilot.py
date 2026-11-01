"""Экспорт безопасного SVG и проверка бюджета пилотных ассетов."""
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET
from PIL import Image

root = Path(__file__).resolve().parents[3]
source = Path(__file__).with_name('select.svg')
target = root / 'frontend/public/assets/ui/pilot'
target.mkdir(parents=True, exist_ok=True)
tree = ET.parse(source)
allowed = {'svg', 'path'}
for node in tree.iter():
    assert node.tag.split('}')[-1] in allowed, node.tag
    assert all(key in {'viewBox', 'fill', 'stroke', 'stroke-width', 'stroke-linecap', 'stroke-linejoin', 'd'} for key in node.attrib), node.attrib
assert tree.getroot().attrib['viewBox'] == '0 0 24 24'
assert source.stat().st_size <= 2048
shutil.copyfile(source, target / 'select.svg')
with Image.open(target / 'stone.png') as image:
    assert image.size == (64, 64)
    assert image.mode == 'RGBA'
    alpha = image.getchannel('A')
    assert alpha.getextrema() == (0, 255), 'Нужны прозрачный фон и видимый предмет'
    box = alpha.getbbox()
    assert box and box[0] > 0 and box[1] > 0 and box[2] < 64 and box[3] < 64, 'Предмет касается края'
assert (target / 'stone.png').stat().st_size <= 16 * 1024
print('Пилот: SVG ≤ 2 KiB; PNG 64×64 RGBA ≤ 16 KiB; прозрачность и поля проверены')
