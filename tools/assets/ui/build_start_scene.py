"""Воспроизводимая авторская векторная диорама; запуск из корня репозитория."""
from pathlib import Path
from io import BytesIO
import cairosvg
from PIL import Image

OUT = Path('frontend/public/assets/ui/start')
OUT.mkdir(parents=True, exist_ok=True)
parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 720">',
         '<path fill="#d6cead" d="M40 420 480 180 920 420 480 670Z"/>']
def tile(x, y, color):
    cx, cy = 480 + (x-y)*62, 175+(x+y)*32
    parts.append(f'<path fill="{color}" stroke="#71825c" stroke-width="2" d="M{cx} {cy}l62 32-62 32-62-32Z"/>')
    return cx, cy+32
for y in range(7):
    for x in range(7):
        tile(x,y, '#cbb88b' if x==3 or y==4 else ['#9eb477','#aabe83','#91a86c'][(x+2*y)%3])
def house(cx,cy,w,h,roof):
    parts.extend([f'<path fill="#d9ca9e" stroke="#344f40" stroke-width="3" d="M{cx-w} {cy-h}l{w} -24 {w} 24v{h}l-{w} 25-{w}-25Z"/>',
                  f'<path fill="#b7a77c" d="M{cx} {cy-h+5}l{w} -5v{h}l-{w} 25Z"/>',
                  f'<path fill="{roof}" stroke="#344f40" stroke-width="3" d="M{cx-w-8} {cy-h}l{w+8} -55 {w+8} 55 -{w+8} 25Z"/>',
                  f'<path fill="#344f40" d="M{cx-10} {cy-20}l20-8v38l-20-9Z"/>',
                  f'<path fill="#f4d887" stroke="#344f40" stroke-width="3" d="M{cx-w+12} {cy-h+18}l19 8v20l-19-8Z"/>'])
house(480,365,65,95,'#286447')
parts.append('<path fill="#c89b51" stroke="#344f40" stroke-width="3" d="M480 215v-52l43 13-43 16Z"/>')
house(294,425,53,58,'#687b83')
parts.append('<path fill="#526052" d="M310 327v-43l19 6v47Z"/>')
for y in range(3):
    parts.append(f'<path stroke="#765b32" stroke-width="9" d="M510 {486+y*13}l103-53"/>')
    for x in range(5):
        cx,cy=523+x*19,480+y*13-x*10
        parts.append(f'<path stroke="#286447" stroke-width="5" d="M{cx} {cy}v-14m0 8-6-5m6 5 6-7"/>')
for cx,cy in [(600,280),(666,310),(728,344),(790,378),(725,410),(790,446),(235,346),(177,383)]:
    parts.append(f'<path stroke="#526052" stroke-width="9" d="M{cx} {cy}v-55"/><path fill="#286447" stroke="#20332f" stroke-width="3" d="M{cx} {cy-115}l-31 58h15l-23 28h78l-23-28h15Z"/>')
parts.append('</svg>')
svg=''.join(parts)
(OUT/'settlement.svg').write_text(svg)
for width in [480,960]:
    png=cairosvg.svg2png(bytestring=svg.encode(),output_width=width,output_height=width*3//4)
    Image.open(BytesIO(png)).save(OUT/f'settlement-{width}.webp',quality=85,method=6)
print({p.name:p.stat().st_size for p in OUT.iterdir()})
