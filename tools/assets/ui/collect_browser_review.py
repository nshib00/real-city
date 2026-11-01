"""Сохраняет выбранные результаты Playwright; не заменяет визуальную приёмку."""
from pathlib import Path
import json
import shutil

ROOT = Path(__file__).resolve().parents[3]
TARGET = ROOT / 'docs/assets/ui/review/browser'
TARGET.mkdir(parents=True, exist_ok=True)
files = []

def copy(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    relative = str(destination.relative_to(ROOT))
    if relative not in files:
        files.append(relative)

for size in ('1440x900', '1024x768', '390x844', '320x700'):
    baseline = list((ROOT / 'frontend/design-results').glob(f'baseline-*-{size}/baseline.png'))
    if len(baseline) != 1:
        raise SystemExit(f'Нет единственного снимка {size}; сначала выполнить test:design')
    copy(baseline[0], ROOT / f'docs/assets/ui/baseline/{size}.png')
    for variant in ('edge', 'desk'):
        for source in (ROOT / 'frontend/design-results').glob(f'prototype-*-{size}/prototype-{variant}.png'):
            copy(source, TARGET / 'prototypes' / f'{size}-{variant}.png')

projects = ('320-dpr1', '390-dpr1', '768-dpr1', '1024-dpr1', '1440-dpr1', 'landscape', '390-dpr2', '1440-dpr2')
directories = list((ROOT / 'frontend/review-results').iterdir())
supplement = ROOT / 'output/playwright/world'
if supplement.exists():
    directories += list(supplement.iterdir())
for directory in directories:
    if not directory.is_dir():
        continue
    project = next((name for name in projects if directory.name.endswith('-' + name)), None)
    if not project:
        continue
    family = 'icons' if 'иконки-орна' in directory.name else 'vision' if 'цветовые-си' in directory.name else 'objects' if directory.name.startswith('world-review-') else 'interface'
    for source in sorted(directory.iterdir()):
        if source.suffix not in ('.png', '.json') or source.name.startswith('test-failed'):
            continue
        # Полные листы всех значков остаются в локальном output; в документации —
        # эталон 100% и состояния, без дублирования многомегапиксельных листов.
        if family == 'icons' and source.name.startswith('icons-') and (project != '1440-dpr1' or not source.name.endswith('-100.png')):
            continue
        if family == 'vision' and project not in ('1440-dpr1', '390-dpr2'):
            continue
        copy(source, TARGET / project / family / source.name)

(TARGET / 'manifest.json').write_text(json.dumps({'files': files, 'note': 'Проверка UI с изолированным API, не live-server smoke.'}, ensure_ascii=False, indent=2) + '\n')
print(f'Сохранено файлов: {len(files)}')
