"""Оригинальные векторные знаки Эолии; без внешних библиотек и загрузок."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'frontend/public/assets/ui/icons'
# Сетка 24, безопасное поле 2, собственная геометрия. Все линии — currentColor.
PATHS = {
 'ownership-own': 'M22 12A10 10 0 1 1 2 12A10 10 0 1 1 22 12Z M12 12h.01',
 'ownership-ally': 'M13 8H8A5 5 0 0 0 8 18H11 M11 6H16A5 5 0 0 1 16 16H13 M8 12H16',
 'ownership-foreign': 'M12 2 22 12 12 22 2 12Z',
 'ownership-neutral': 'M22 12A10 10 0 1 1 2 12A10 10 0 1 1 22 12Z',
 'threat': 'M12 2 22 21H2Z M12 8V14 M12 17v.01',
 'rarity-rare': 'M8 3H16L21 8V16L16 21H8L3 16V8Z M8 8H16V16H8Z',
 'status-building': 'M3 21H21 M5 21V10L12 3 19 10V21 M9 12H15 M9 16H15',
 'status-ready': 'M3 12 9 18 21 5 M3 21H21',
 'status-depleted': 'M3 5H21V19H3Z M7 12H17',
 'select': 'M4 3 18 11 12 13 9 20Z M14 17 19 20 22 17',
 'build': 'M3 17 12 21 21 17 12 13Z M7 12V8L12 4 17 8V12 M12 4V1',
 'hammer': 'M5 3H14L18 7 14 11H5V3 M10 11V21H14V11',
 'repair': 'M3 5V18H11V14H7V9 M14 3 12 7 15 10 20 8 18 4 M15 10 9 21 12 22 19 11',
 'attack': 'M3 8V3H8 M16 3H21V8 M21 16V21H16 M8 21H3V16 M7 15 11 10 13 13 18 7',
 'road': 'M3 17 7 13 11 17 7 21Z M8 11 12 7 16 11 12 15Z M13 5 17 1 21 5 17 9Z',
 'wall': 'M3 20V5H7V9H10V5H14V9H17V5H21V20Z M10 20V15H14V20',
 'market': 'M3 19H21L19 15H5Z M12 3V15 M5 6H19 M5 6 2 12H8Z M19 6 16 12H22Z',
 'alliance': 'M3 4 10 2 12 6V16L7 21 3 16Z M12 6 14 2 21 4V16L17 21 12 16 M8 10H16',
 'chat': 'M3 3H17V12H9L5 16V12H3Z M11 16H17L21 20V8H20',
 'city': 'M3 11 12 5 21 11 M5 11V21H19V11 M10 21V15H14V21 M12 5V2H18L16 4H12',
 'world': 'M3 5 9 3 15 6 21 4V19L15 21 9 18 3 20Z M9 3V18 M15 6V21',
 'profile': 'M8 2H16L14 7H10Z M5 12 9 7H15L19 12V18L15 22H9L5 18Z M9 18V16Q12 11 15 16V18 M12 10V11',
 'events': 'M5 2H17L20 5V22H5Z M8 7H14 M8 11H17 M8 15H17 M8 19H13 M2 7H5 M2 15H5',
 'settings': 'M4 5H20 M4 12H20 M4 19H20 M8 2V8 M16 9V15 M10 16V22',
 'housing': 'M2 11 12 3 22 11 M5 10V21H19V10 M10 21V14H14V21',
 'production': 'M4 8H8V4H16V8H20V16H16V20H8V16H4Z M9 9H15V15H9Z M1 12H4 M20 12H23',
 'fields': 'M3 17 12 21 21 17 M3 12 12 16 21 12 M12 12V6 M12 7Q4 7 5 2Q12 2 12 7 M12 9Q20 9 20 3Q13 3 12 9',
 'storage': 'M2 8 12 3 22 8 M5 10H19V21H5Z M5 14H19 M12 10V21',
 'shield': 'M4 3H20V13L16 19 12 22 8 19 4 13Z M8 7H16V12L12 17 8 12Z',
 'center': 'M3 10 12 5 21 10 M5 14 12 10 19 14 M7 18 12 14 17 18 M7 18V22H17V18 M12 5V2',
 'decor': 'M5 21Q3 5 20 3Q22 19 5 21 M5 21 15 10 M8 16V10 M11 13H17',
 'crystal': 'M12 2 20 8 17 19 12 22 6 17 4 8Z M12 2 9 10 12 22 M9 10 20 8 M9 10 6 17',
 'wood': 'M2 8 5 6 8 8V12L5 14 2 12Z M5 6 16 2 19 4V8L8 12 M9 15 12 13 15 15V19L12 21 9 19Z M12 13 19 10 22 12V16L15 19 M4 10H6 M11 17H13',
 'stone': 'M3 14 6 5 14 3 21 11 19 20 8 21Z M6 5 12 11 21 11 M12 11 8 21 M12 11 19 20',
 'coins': 'M3 12Q3 8 12 8Q21 8 21 12V18Q21 22 12 22Q3 22 3 18Z M3 12Q12 17 21 12 M7 8V4Q12 0 18 4V8 M10 5H14 M12 3V7',
 'people': 'M5 4H9V9H5Z M3 21V14L5 12H9L11 14V21 M15 6H19V11H15Z M13 21V16L15 14H19L21 16V21',
 'clock': 'M8 2H16 M12 2V5 M5 9 8 6H17L21 11V17L17 21H8L4 17V11 M12 9V14H17',
 'offline': 'M3 6H9V10H3Z M15 14H21V18H15Z M9 8H15V11 M9 13V16H15 M3 21 21 3',
 'lock': 'M7 10V6L10 3H14L17 6V10 M4 10H20V21H4Z M12 14V17',
 'shortage': 'M3 7 12 3 21 7V19L12 22 3 19Z M3 7 12 11 21 7 M8 16H16',
 'damage': 'M4 3H20V21H4Z M14 3 10 9 14 12 9 16 11 21',
 'cancel': 'M3 5 9 11 M15 13 21 19 M19 3 13 9 M11 15 5 21',
 'check': 'M3 12 9 19 21 5 M3 20H6',
 'left': 'M15 3 6 12 15 21 M6 12H21',
 'right': 'M9 3 18 12 9 21 M3 12H18',
 'up': 'M3 15 12 6 21 15 M12 6V22',
 'down': 'M3 9 12 18 21 9 M12 2V18',
 'eye': 'M2 12 7 6H17L22 12 17 18H7Z M10 9H14V15H10Z',
 'sound': 'M3 9H7L13 4V20L7 15H3Z M16 8 19 12 16 16 M20 4 23 12 20 20',
 'mute': 'M3 9H7L13 4V20L7 15H3Z M17 9 22 15 M22 9 17 15',
 'waves': 'M2 7Q6 2 10 7T18 7L22 4 M2 14Q6 9 10 14T18 14L22 11 M2 21Q6 16 10 21T18 21L22 18',
 'move': 'M3 12H21 M12 3V21 M3 12 6 9 M3 12 6 15 M21 12 18 9 M21 12 18 15 M12 3 9 6 M12 3 15 6 M12 21 9 18 M12 21 15 18',
 'rotate': 'M20 8 16 3H8L3 9V16L8 21H16L20 17 M20 2V8H14',
 'trash': 'M3 6H21 M8 6V3H16V6 M6 6 7 21H17L18 6 M10 10V17 M14 10V17',
 'trend': 'M3 21V4 M3 21H21 M6 16 11 11 14 14 21 5 M16 5H21V10',
 'star': 'M12 2 15 8 22 10 17 15 18 22 12 18 6 22 7 15 2 10 9 8Z',
 'logout': 'M12 3H4V21H12 M9 12H22 M17 7 22 12 17 17',
 'monitor': 'M3 3H21V16H3Z M8 22H16 M12 16V22 M7 7H17 M7 11H13',
 'gauge': 'M3 18V11L8 5H16L21 11V18Z M12 16 17 9 M7 12V14 M12 8V10',
 'tower': 'M5 3H9V7H15V3H19V11H17V21H7V11H5Z M10 21V16H14V21',
 'crown': 'M3 5 8 10 12 3 16 10 21 5 19 20H5Z M6 16H18',
 'trophy': 'M7 3H17V12L12 16 7 12Z M7 5H3V10L7 13 M17 5H21V10L17 13 M12 16V21 M7 21H17',
 'network': 'M9 2H15V8H9Z M2 16H8V22H2Z M16 16H22V22H16Z M12 8V12H5V16 M12 12H19V16',
 'tent': 'M2 21 12 3 22 21Z M8 21 12 13 16 21',
}
ALIASES = dict(MousePointer2='select', Castle='build', Hammer='hammer', Repair='repair', Swords='attack', Route='road', HandCoins='market', Coins='coins', Handshake='alliance', MessageSquare='chat', Landmark='center', Map='world', MapPinned='world', UserRound='profile', Bell='events', Settings='settings', SlidersHorizontal='settings', Building2='housing', UsersRound='people', Shield='shield', ShieldAlert='damage', Warehouse='storage', Box='storage', Package='shortage', LandPlot='fields', Sprout='fields', Gem='crystal', Clock='clock', X='cancel', Check='check', ChevronLeft='left', ChevronRight='right', ChevronUp='up', ChevronDown='down', Eye='eye', Volume2='sound', VolumeX='mute', Waves='waves', Move='move', RotateCw='rotate', Trash2='trash', TrendingUp='trend', Star='star', LogOut='logout', MonitorCog='monitor', Gauge='gauge', TowerControl='tower', Crown='crown', Trophy='trophy', Network='network', Tent='tent')

# Отдельная оптическая геометрия 16×16: меньше деталей, толщина 1.5 px.
SMALL = {
 'ownership-own':'M14 8A6 6 0 1 1 2 8A6 6 0 1 1 14 8Z M8 8h.01',
 'ownership-ally':'M9 4H6A3 3 0 0 0 6 10 M7 6H10A3 3 0 0 1 10 12 M6 8H10',
 'ownership-foreign':'M8 2 14 8 8 14 2 8Z',
 'ownership-neutral':'M14 8A6 6 0 1 1 2 8A6 6 0 1 1 14 8Z',
 'threat':'M8 2 14 14H2Z M8 6V9 M8 12v.01',
 'rarity-rare':'M5 2H11L14 5V11L11 14H5L2 11V5Z M6 6H10V10H6Z',
 'status-building':'M2 14H14 M4 14V7L8 2 12 7V14 M6 9H10',
 'status-ready':'M2 8 6 12 14 3 M2 14H14',
 'status-depleted':'M2 4H14V12H2Z M5 8H11',
 'select':'M3 2 13 8 8 9 6 14Z',
 'build':'M2 11 8 14 14 11 8 8Z M5 7V4L8 2 11 4V7',
 'hammer':'M3 2H10L13 5 10 8H3Z M7 8V14H10V8',
 'repair':'M2 3V12H6 M10 2 8 5 11 7 14 5 M10 7 6 14',
 'attack':'M2 5V2H5 M11 2H14V5 M14 11V14H11 M5 14H2V11 M5 11 11 5',
 'road':'M2 11 5 8 8 11 5 14Z M8 5 11 2 14 5 11 8Z',
 'wall':'M2 14V3H5V6H7V3H10V6H12V3H14V14Z',
 'market':'M8 2V13 M3 4H13 M3 4 2 9H6Z M13 4 10 9H14Z M4 14H12',
 'alliance':'M2 3 6 2 8 5V11L5 14 2 11Z M8 5 10 2 14 3V11L11 14 8 11',
 'chat':'M2 3H14V11H8L4 14V11H2Z',
 'city':'M2 7 8 3 14 7 M4 7V14H12V7 M7 14V10H9V14',
 'world':'M2 3 6 2 10 4 14 3V13L10 14 6 12 2 13Z M6 2V12 M10 4V14',
 'profile':'M6 2H10V6H6Z M3 14V11L6 8H10L13 11V14Z',
 'events':'M4 2H12V14H4Z M6 5H10 M6 8H10 M6 11H9',
 'settings':'M2 4H14 M2 8H14 M2 12H14 M5 2V6 M11 6V10 M6 10V14',
 'housing':'M2 7 8 2 14 7 M4 7V14H12V7 M7 14V10H9V14',
 'production':'M5 2H11V5H14V11H11V14H5V11H2V5H5Z M6 6H10V10H6Z',
 'fields':'M2 11 8 14 14 11 M2 8 8 11 14 8 M8 8V2 M8 5 4 3 M8 7 12 5',
 'storage':'M2 5 8 2 14 5 M3 7H13V14H3Z M3 10H13',
 'shield':'M3 2H13V9L8 14 3 9Z',
 'center':'M2 6 8 2 14 6 M4 9 8 6 12 9 M5 12 8 9 11 12V14H5Z',
 'decor':'M3 14Q2 3 14 2Q14 13 3 14 M3 14 10 7',
 'crystal':'M8 2 13 6 11 13 8 14 4 11 3 6Z M8 2 6 7 8 14 M6 7H13',
 'wood':'M2 6 5 4 8 6V11L5 13 2 11Z M5 4 11 2 14 4V8L8 11',
 'stone':'M2 9 5 3 10 2 14 8 12 14 5 13Z M5 3 8 8 14 8',
 'coins':'M2 6Q8 2 14 6V12Q8 16 2 12Z M2 6Q8 10 14 6',
 'people':'M3 2H6V6H3Z M2 14V9H7V14 M10 4H13V8H10Z M9 14V11H14V14',
 'clock':'M8 2A6 6 0 1 0 8 14A6 6 0 1 0 8 2 M8 5V8H11',
 'offline':'M2 4H6V7H2Z M10 9H14V12H10Z M3 14 13 2',
 'lock':'M5 7V4L7 2H9L11 4V7 M3 7H13V14H3Z',
 'shortage':'M2 5 8 2 14 5V12L8 14 2 12Z M5 9H11',
 'damage':'M3 2H13V14H3Z M9 2 6 7 10 9 7 14',
 'cancel':'M3 3 13 13 M13 3 3 13',
 'check':'M2 8 6 13 14 3',
 'left':'M10 2 4 8 10 14 M4 8H14',
 'right':'M6 2 12 8 6 14 M2 8H12',
 'up':'M2 10 8 4 14 10 M8 4V14',
 'down':'M2 6 8 12 14 6 M8 2V12',
 'eye':'M2 8 5 4H11L14 8 11 12H5Z M8 6V10',
 'sound':'M2 6H5L9 3V13L5 10H2Z M12 5 14 8 12 11',
 'mute':'M2 6H5L9 3V13L5 10H2Z M11 6 14 10 M14 6 11 10',
 'waves':'M2 4Q4 2 7 4T14 4 M2 8Q4 6 7 8T14 8 M2 12Q4 10 7 12T14 12',
 'move':'M2 8H14 M8 2V14 M2 8 4 6 M2 8 4 10 M14 8 12 6 M14 8 12 10 M8 2 6 4 M8 2 10 4 M8 14 6 12 M8 14 10 12',
 'rotate':'M13 5 10 2H5L2 6V11L5 14H10L13 12 M13 2V5H10',
 'trash':'M2 4H14 M5 4V2H11V4 M4 4V14H12V4 M8 7V11',
 'trend':'M2 2V14H14 M4 11 8 7 10 9 14 3 M11 3H14V6',
 'star':'M8 2 10 6 14 7 11 10 12 14 8 12 4 14 5 10 2 7 6 6Z',
 'logout':'M8 2H3V14H8 M6 8H14 M11 5 14 8 11 11',
 'monitor':'M2 2H14V11H2Z M8 11V14 M5 14H11',
 'gauge':'M2 13V8L5 3H11L14 8V13Z M8 11 11 6',
 'tower':'M3 2H6V5H10V2H13V8H11V14H5V8H3Z',
 'crown':'M2 4 5 7 8 2 11 7 14 4 12 14H4Z',
 'trophy':'M5 2H11V8L8 11 5 8Z M5 4H2V7L5 9 M11 4H14V7L11 9 M8 11V14 M5 14H11',
 'network':'M6 2H10V6H6Z M2 11H6V14H2Z M10 11H14V14H10Z M8 6V9H4V11 M8 9H12V11',
 'tent':'M2 14 8 2 14 14Z M6 14 8 9 10 14',
}

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    assert PATHS.keys() == SMALL.keys(), 'Для каждого знака нужна отдельная геометрия 16 px'
    (OUT / 'small').mkdir(exist_ok=True)
    (OUT / 'source').mkdir(exist_ok=True)
    for key, geometry in PATHS.items():
        (OUT / f'{key}.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="bevel" stroke-linecap="round"><path d="{geometry}"/></svg>\n')
        (OUT / 'small' / f'{key}.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="bevel" stroke-linecap="round"><path d="{SMALL[key]}"/></svg>\n')
    registry = ROOT / 'frontend/src/shared/ui/iconPaths.ts'
    registry.write_text('// Генератор: tools/assets/ui/build_icon_set.py\nexport const iconPaths = ' + json.dumps(PATHS, ensure_ascii=False, indent=2) + ' as const\n')
    (registry.parent / 'iconPaths16.ts').write_text('// Генератор: tools/assets/ui/build_icon_set.py\nexport const iconPaths16 = ' + json.dumps(SMALL, ensure_ascii=False, indent=2) + ' as const\n')
    exports = ROOT / 'frontend/src/shared/ui/icons.tsx'
    exports.write_text("// Совместимые имена потребителей; рисунки оригинальные, источник — iconPaths.\nimport { AeolianIcon, type AeolianIconProps } from './AeolianIcon'\n" + ''.join(f"export const {name} = (props: Omit<AeolianIconProps, 'name'>) => <AeolianIcon name=\"{key}\" {{...props}} />\n" for name, key in ALIASES.items()))
    consumers = []
    for file in (ROOT / 'frontend/src').rglob('*.tsx'):
        text = file.read_text()
        if "from 'lucide-react'" in text or '/ui/icons' in text or '/ui/AeolianIcon' in text:
            consumers.append(str(file.relative_to(ROOT)))
    manifest = {'revision': 'aeolian-ui-2', 'origin': 'Оригинальная геометрия проекта Эолия, 2026', 'grid': 24, 'workArea': 20, 'opticalOverhang': 1, 'stroke': 1.8, 'smallGrid': 16, 'smallStroke': 1.5, 'icons': list(PATHS), 'aliases': ALIASES, 'consumers': consumers}
    (OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')

if __name__ == '__main__':
    main()
