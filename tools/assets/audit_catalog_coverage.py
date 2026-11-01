#!/usr/bin/env python3
"""Составить матрицу файлов из каталога и manifest; не подменяет runtime/art QA."""
from __future__ import annotations

import argparse
import html
import json
import re
from collections import defaultdict
from pathlib import Path

from asset_validation_common import ROOT, load_manifests, resolve_asset_path


def build_report():
    runtime = (ROOT / 'frontend/src/game/renderers/buildingAssetManifests.ts').read_text()
    aliases = dict(re.findall(r"kind:\s*'([^']+)'\s*,\s*assetId:\s*'([^']+)'", runtime))
    families = defaultdict(list)
    for manifest in load_manifests():
        families[manifest.asset_id].append(manifest)
    catalog = json.loads((ROOT / 'data/buildings/catalog-v2.json').read_text())['buildings']
    rows = []
    contacts = []
    for building in catalog:
        kind = building['type']
        asset_id = aliases.get(kind, kind)
        manifests = families[asset_id]
        levels = sorted({building['level'], *(item['level'] for item in building.get('upgradeLevels', []))})
        manifest_rows = []
        for manifest in manifests:
            items = defaultdict(list)
            ids = []
            missing_files = []
            for item in manifest.items:
                items[(item.get('level'), item.get('state'))].append(item)
                if item.get('id'):
                    ids.append(item['id'])
                for field in ('png', 'glb'):
                    if item.get(field):
                        path = resolve_asset_path(manifest.directory, item[field])
                        if not path or not path.is_file():
                            missing_files.append(item[field])
            matrix = []
            for level in levels:
                for state in manifest.states:
                    variants = items[(level, state)]
                    paths = [resolve_asset_path(manifest.directory, item.get('png')) for item in variants if item.get('png')]
                    exists = any(path and path.is_file() for path in paths)
                    matrix.append({'level': level, 'state': state, 'png_present': exists})
            footprint = manifest.data.get('footprint')
            source = {name: manifest.data[name] for name in ('provenance', 'source', 'license', 'author') if name in manifest.data}
            manifest_rows.append({
                'path': str(manifest.path.relative_to(ROOT)), 'states': list(manifest.states),
                'matrix': matrix, 'missing_files': sorted(set(missing_files)),
                'duplicate_ids': sorted({value for value in ids if ids.count(value) > 1}),
                'footprint': footprint, 'catalog_footprint': building.get('footprint'),
                'footprint_matches': footprint == building.get('footprint') if footprint else None,
                'declared_provenance': source,
                'rights_review': 'требует проверки',
            })
            for item in manifest.items:
                if item.get('state') == 'active' and item.get('level') in (levels[0], levels[-1]) and item.get('png'):
                    path = resolve_asset_path(manifest.directory, item['png'])
                    if path and path.is_file():
                        contacts.append((kind, item.get('level'), str(path.relative_to(ROOT))))
        rows.append({'kind': kind, 'asset_id': asset_id, 'name': building['name'], 'levels': levels, 'manifests': manifest_rows, 'fallback': 'runtime-геометрия; отдельная визуальная приёмка обязательна'})
    return {'scope': 'Файлы manifest; не доказывает выбор runtime resolver, покрытие модульных форм, якоря, сортировку и права.', 'buildings': rows}, contacts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    report, contacts = build_report()
    (args.output_dir / 'building-coverage.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    lines = ['# Матрица визуального каталога', '', 'Сгенерировано `tools/assets/audit_catalog_coverage.py`. ' + report['scope'], '', '| Тип | Уровни | Манифесты | Отсутствует PNG в матрицах | Файлов отсутствует |', '|---|---|---|---|---|']
    for row in report['buildings']:
        manifests = row['manifests']
        lines.append(f"| `{row['kind']}` | {min(row['levels'])}–{max(row['levels'])} | {len(manifests)} | {sum(not cell['png_present'] for manifest in manifests for cell in manifest['matrix']) if manifests else 'нет manifest'} | {sum(len(manifest['missing_files']) for manifest in manifests)} |")
    lines += ['', 'Подробная матрица уровней/состояний, дубли ID, footprint и дословно объявленное происхождение — в `building-coverage.json`. Отсутствие уровневого PNG у модульной дороги не доказывает отсутствие runtime-отображения. Заимствование визуала другого уровня/состояния не считается отдельным финальным ассетом.', '', 'Контактный лист: `building-contact-sheet.html`, требует локального HTTP-сервера из корня репозитория. Это входные материалы для ревью, не принятые скриншоты игры. Пустое declared_provenance означает отсутствие сведений в manifest; наличие source/license ещё не подтверждает права.']
    (args.output_dir / 'building-coverage.md').write_text('\n'.join(lines) + '\n')
    cards = ''.join(f'<figure><img loading="lazy" src="/{html.escape(path, quote=True)}" alt="{html.escape(kind)}"><figcaption>{html.escape(kind)} · {level}</figcaption></figure>' for kind, level, path in contacts)
    (args.output_dir / 'building-contact-sheet.html').write_text('<!doctype html><html lang="ru"><meta charset="utf-8"><title>Контактный лист построек</title><style>body{background:#293e38;color:#f9f4df;font:16px sans-serif}main{display:flex;flex-wrap:wrap}figure{width:240px;margin:8px}img{width:100%;height:180px;object-fit:contain}</style><h1>Начальные и поздние уровни: active</h1><p>Проверка файлов, не игровая сцена. Остальные состояния — в JSON.</p><main>' + cards + '</main></html>')
    print(f"Каталог: {len(report['buildings'])}; контактных изображений: {len(contacts)}")


if __name__ == '__main__':
    main()
