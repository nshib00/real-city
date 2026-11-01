"""Инвентаризация используемых знаков, ресурсов и оставшихся текстовых маркеров."""
import json
import re
from build_icon_set import ROOT, ALIASES

def main():
    ui = ROOT / 'frontend/public/assets/ui'
    resources = json.loads((ui / 'resources/manifest.json').read_text())['resources']
    consumers = {name: [] for name in ALIASES}
    markers = []
    for file in (ROOT / 'frontend/src').rglob('*'):
        if file.suffix not in ('.ts', '.tsx') or 'test.' in file.name: continue
        text = file.read_text()
        if '/ui/icons' in text:
            for name in consumers:
                if re.search(r'\b'+name+r'\b', text): consumers[name].append(str(file.relative_to(ROOT)))
        for i, line in enumerate(text.splitlines(), 1):
            signs = sorted(set(re.findall(r'[\u2190-\u27ff\U0001f300-\U0001faff]', line)))
            if signs: markers.append((str(file.relative_to(ROOT)), i, ' '.join(signs)))
    lines = ['# Реестр иконок интерфейса Эолии', '', 'Источник: оригинальная геометрия проекта, `tools/assets/ui/build_icon_set.py` и `build_resource_icons.py`. Внешние наборы не использованы. Генератор этого реестра: `build_icon_manifest.py`.', '', 'Функциональные SVG: сетка 24×24, линия 1.8, `currentColor`, 16/20/24 px. Миниатюры: прозрачный SVG 32×32, экспорт 64 px, 30–64 px в интерфейсе; при контейнере ≤20 px используется монохромный знак. Смысловые подписи принадлежат кнопке/ResourceIcon. Серверные механики и игровые модели сохранены.', '', '## Функциональные потребители', '', '| Прежнее имя импорта | Новый файл в assets/ui/icons | Потребители | Статус |', '|---|---|---|---|']
    for name, key in ALIASES.items():
        lines.append(f'| {name} | `{key}.svg` | '+', '.join(f'`{f}`' for f in consumers[name])+' | Подключён |')
    lines += ['', 'Дополнительные знаки статусов и категорий подключены через `AeolianIcon` в ActionState и BuildMenu. Auth и рынок используют текстовые действия; буквенных иконок для замены там нет. Совместимые имена экспортов не означают сохранение рисунков Lucide.', '', '## Ресурсный каталог', '', '| Ключ | Название | Новый файл | Семейство | Статус |', '|---|---|---|---|---|']
    for item in resources:
        lines.append(f'| `{item["id"]}` | {item["name"]} | `assets/ui/resources/{item["file"]}` | {item["shape"]} | Подключён |')
    lines += ['', 'Старые PNG/GLB не удалены: это существующие игровые/исходные ассеты. ResourceIcon больше не обращается к старому набору. Unknown id получает shortage; ошибка загрузки — встроенный Package/shortage без дополнительного запроса.', '', '## Текстовые маркеры', '', 'Следующие символы сохранены как текстовые разделители, счётчики, навигационные стрелки или индикаторы непрочитанного; рядом остаётся смысловая подпись. Они не служат заменой предметной иконки.', '', '| Файл | Строка | Символы |', '|---|---|---|']
    lines += [f'| `{file}` | {line} | {signs} |' for file, line, signs in markers]
    lines += ['', '## Приёмка', '', 'Программно проверяются покрытие каталога, безопасный SVG, отсутствие внешних ссылок/шрифтов, отсутствие прямых импортов старого набора, fallback, подписи и бюджет. Пилот: `docs/assets/ui/review/icons/pilot.png`; полный лист: `index.html`; миниатюры: `resources.png`. Это листы ассетов, не снимки игрового мира.', '', 'Не закрыты: пользовательское распознавание без подписей, все сочетания бейджей владения/редкости, отдельная оптическая версия каждого функционального знака для 16 px, DPR 1/2 и масштаб 200% в игре, симуляции цветового зрения, реальные фоны травы/воды/руин/зданий.']
    (ROOT / 'docs/art/ui-icon-manifest.md').write_text('\n'.join(lines)+'\n')

if __name__ == '__main__': main()
