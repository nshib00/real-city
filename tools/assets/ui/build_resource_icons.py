"""Векторные предметные миниатюры. Игровые модели и старые рендеры не изменяются."""
import json
import re
from pathlib import Path
from build_icon_set import ROOT, PATHS

# Индивидуальное сопоставление каталога предметной геометрии и цвета материала.
GROUPS = {
 'wood': ('#b78553', 'wood elderwood-heart'),
 'stone': ('#9aa6a2', 'stone iron_ore coal kaolin clay'),
 'coins': ('#e4ba5c', 'coins'),
 'people': ('#d7b991', 'population'),
 'crystal': ('#7dcad8', 'aeolian-crystal light_crystal memory_shard'),
 'leaf': ('#91b969', 'windleaf super-windleaf herbs oil_plants'),
 'seed': ('#d2ae65', 'seeds super-seeds'),
 'grain': ('#e0cba2', 'sand sulfur blue_salt emerald_dust quiet_powder'),
 'drop': ('#d79b47', 'resin oleoresin amber_essence'),
 'stalk': ('#9fb87c', 'flax reed sugar_cane'),
 'thread': ('#c4ad84', 'fiber super-fiber'),
 'mushroom': ('#c59580', 'mushrooms super-mushrooms'),
 'jar': ('#7fada3', 'dyes paints plant_oil'),
 'block': ('#c28969', 'brick stone_block concrete reinforced_concrete'),
 'plank': ('#c49661', 'planks premium_planks'),
 'rope': ('#ceb586', 'rope fine_rope'),
 'sheet': ('#c5cfb4', 'fabric paper glass star_glass'),
 'tile': ('#c9896a', 'tile rune_tile'),
 'ingot': ('#9caeac', 'metal iron iron_ingot steel copper gold_ingot aeolian_alloy'),
 'production': ('#c8b080', 'copper_parts mechanism super_mechanism'),
 'repair': ('#b5c3be', 'tools'),
 'sack': ('#b8ae99', 'cement'),
 'beam': ('#9eafab', 'reinforced_beams'),
 'shield': ('#a3b8bb', 'armor_plates'),
 'circuit': ('#78b3ad', 'electronics'),
 'charge': ('#d2a070', 'explosives shaped_charge shock_charge resonance_charge'),
 'barrel': ('#8a9c9a', 'oil fuel'),
 'fruit': ('#9cc5ac', 'crystal_fruit'),
 'flower': ('#c9a3bd', 'rare_flowers'),
 'heart': ('#a5a49b', 'stone_heart'),
 'knife': ('#b8c8c5', 'throwing_knives'),
 'trap': ('#a9a69a', 'hunting_traps'),
 'bomb': ('#ad9990', 'blackpowder_bomb firebomb breach_bomb'),
 'mine': ('#94a39b', 'siege_mine'),
}
SHAPES = dict(PATHS, **{
 'leaf': 'M4 20Q2 3 21 3Q21 21 4 20Z M4 20 16 8 M9 15V8 M12 12H18',
 'seed': 'M4 15Q4 4 13 4Q17 15 4 15Z M13 20Q10 12 19 10Q24 18 13 20Z',
 'grain': 'M3 19 8 9 12 12 16 7 21 19Z M7 16H8 M12 18H13 M17 14H18',
 'drop': 'M12 2Q21 12 20 16Q18 23 10 21Q1 19 5 12Z M9 14 8 17 11 19',
 'stalk': 'M6 22 10 3 M12 22 17 2 M18 21 21 7 M7 14 3 9 M15 11 11 6 M19 15 15 12',
 'thread': 'M4 5Q17 1 20 5L16 20Q7 23 4 19Z M4 9 19 9 M4 13 18 13 M4 17H16',
 'mushroom': 'M2 12Q3 2 12 2Q21 2 22 12Z M9 12 7 21H17L15 12 M8 7H9 M15 6H16',
 'jar': 'M8 2H16V6L20 9V20L17 22H7L4 20V9L8 6Z M4 12H20 M9 16H15',
 'block': 'M3 8 15 3 21 7V17L9 22 3 18Z M3 8 9 12 21 7 M9 12V22',
 'plank': 'M3 9 17 2 21 6 7 13Z M3 13 7 17 21 10 M3 17 7 21 21 14 M9 8 16 5',
 'rope': 'M7 3Q20 0 21 9Q22 20 12 21Q2 22 3 13Q4 5 12 6Q19 7 16 14Q12 19 8 14 M7 3 10 5 M17 4 15 7 M20 13 16 12 M14 21 13 17 M4 17 8 16',
 'sheet': 'M3 8 17 2 21 16 7 22Z M7 11 16 7 M8 15 17 11 M9 19 18 15',
 'tile': 'M3 7 16 2 21 16 8 22Q2 18 3 7Z M8 22Q11 14 6 6 M16 2 6 6',
 'ingot': 'M6 5H18L22 15 17 20H5L2 15Z M6 5 10 15H22 M10 15 5 20',
 'sack': 'M7 3H17L15 7 21 17 18 22H6L3 17 9 7Z M8 8H16 M8 17H16',
 'beam': 'M3 7 17 2 21 5 7 10V16L21 11V15L7 21 3 18Z M7 10 21 5',
 'circuit': 'M5 4H19V20H5Z M9 8H15V15H9Z M2 7H5 M2 13H5 M19 10H22 M19 17H22 M9 15V20',
 'charge': 'M3 7 8 3H17L21 7V19H3Z M3 7H21 M8 11 12 16 16 11 M12 16V20',
 'barrel': 'M5 4Q12 1 19 4V20Q12 23 5 20Z M5 8H19 M5 17H19 M10 11H14V14H10Z',
 'fruit': 'M12 7Q21 3 21 13L16 21H8L3 13Q3 3 12 7Z M12 7V2H18 M12 7 9 13 12 21 16 13Z',
 'flower': 'M12 21V12 M12 12Q1 15 3 7Q4 2 9 5Q11 0 15 4Q23 1 22 9Q22 16 12 12Z M10 8H14V11H10 M12 19 19 15',
 'heart': 'M12 6 7 2 2 7 4 14 12 22 20 14 22 7 17 2Z M7 2 10 10 4 14 M10 10 17 2 M10 10 12 22 16 12 22 7',
 'knife': 'M5 22 2 19 9 12 9 7 20 2 18 13 13 14Z M9 12 13 14 M10 11 17 5',
 'trap': 'M3 7 6 3 9 7 12 3 15 7 18 3 21 7V17L18 21 15 17 12 21 9 17 6 21 3 17Z M3 12H21 M9 9H15V15H9Z',
 'bomb': 'M8 6V3H15V6L21 11V18L17 22H7L3 18V11Z M15 3 18 1 21 3 M7 12H17 M10 9V19',
 'mine': 'M2 16 5 10H19L22 16V20H2Z M8 10V6H16V10 M12 6V2 M5 16H19',
})

# Родственные материалы различаются конструкцией, а не только оттенком/насечкой.
VARIANTS = {
 'clay': 'M3 17 6 9 11 6 18 8 22 17 16 21H8Z M6 9 12 13 18 8 M12 13 16 21',
 'iron_ore': 'M2 15 8 3 17 5 22 17 13 22Z M8 3 12 10 2 15 M12 10 22 17 M9 12 13 14 16 11',
 'coal': 'M3 10 9 4 18 3 22 12 17 21 6 20Z M3 10 13 12 18 3 M13 12 17 21 M8 17 11 16',
 'kaolin': 'M3 19 5 10 10 8 13 3 19 6 22 19Z M5 10 12 13 19 6 M12 13 14 19',
 'elderwood-heart': 'M3 7 13 2 21 7V17L11 22 3 17Z M3 7 11 12 21 7 M11 12V22 M6 10V16L9 18 M15 13V17L18 15',
 'memory_shard': 'M4 6 17 2 21 17 8 22Z M4 6 15 10 8 22 M15 10 17 2 M10 8 16 6',
 'light_crystal': 'M12 1 18 8 16 19 12 23 8 19 6 8Z M12 1V23 M6 8H18 M2 12H4 M20 12H22',
 'herbs': 'M12 22V6 M12 17Q3 19 3 12Q10 10 12 17 M12 12Q20 13 21 6Q14 4 12 12 M12 7 8 3 13 2 15 5Z',
 'oil_plants': 'M12 22V10 M12 18Q3 17 3 11L12 15 M12 14 20 9 20 16Z M8 4 12 2 16 4V9L12 12 8 9Z',
 'super-windleaf': 'M4 21Q1 10 6 3L10 7 17 2 22 8Q21 22 4 21Z M4 21 16 9 M9 16V10 M13 12H19',
 'super-seeds': 'M3 17Q1 5 12 2L16 6Q19 19 3 17Z M9 22Q11 12 21 10Q24 20 15 23Z M7 9 10 6',
 'blue_salt': 'M3 19 6 11 10 14 13 4 18 6 22 19Z M13 4 14 15 18 6 M6 11 8 18',
 'emerald_dust': 'M3 20 7 15 11 17 15 13 21 20Z M9 12 7 7 12 3 17 7 15 12Z M7 7H17 M12 3V12',
 'quiet_powder': 'M5 4H17L20 8 18 22H6L3 8Z M3 8H20 M7 18 10 13 12 15 15 11 17 18Z',
 'sulfur': 'M2 19 5 11 10 8 16 11 19 7 22 19Z M5 11 12 13 10 8 M12 13 16 11 18 19',
 'oleoresin': 'M12 2 18 8 21 16 17 22H7L3 16 7 8Z M12 2 10 13 14 18 17 12',
 'amber_essence': 'M8 2H16V6L19 8V20L12 23 5 20V8L8 6Z M5 12H19 M12 14 9 18 12 21 15 18Z',
 'reed': 'M6 22V3H9V10H6 M14 22V1H17V8H14 M20 22V7 M6 17 2 12 M14 14 10 10 M20 18 23 14',
 'sugar_cane': 'M4 21 9 2 13 3 8 22Z M13 22 17 3 21 4 18 23Z M6 14 10 15 M8 7 12 8 M15 14H19 M17 7H21',
 'super-fiber': 'M4 5 12 2 21 6 17 21 9 23 3 18Z M4 5 9 9 21 6 M9 9V23 M9 13 19 10 M9 17 18 14 M9 21 17 18',
 'super-mushrooms': 'M2 10Q4 1 12 2Q20 1 22 10L17 13H7Z M10 13 8 22H16L14 13 M6 7H8 M15 6H18 M19 20H23V17Q21 13 19 17Z',
 'paints': 'M3 6H11V21H3Z M13 3H21V18H13Z M3 9H11 M13 6H21 M6 13H8 M16 10H18',
 'plant_oil': 'M8 2H16V6L19 9V21H5V9L8 6Z M5 13H19 M12 19Q8 14 12 12Q16 14 12 19Z',
 'stone_block': 'M2 9 13 3 22 8V18L11 23 2 18Z M2 9 11 13 22 8 M11 13V23 M6 6 15 10 M16 11V20',
 'concrete': 'M3 8 17 3 22 8V18L8 22 3 17Z M3 8 8 12 22 8 M8 12V22 M11 16H12 M16 12H17 M17 18H18',
 'reinforced_concrete': 'M3 10 15 5 21 9V19L9 23 3 19Z M3 10 9 14 21 9 M9 14V23 M7 8V2 M13 5V1 M18 7V2',
 'premium_planks': 'M2 11 16 2 21 6 7 15Z M2 15 7 19 21 10 M5 20 8 23 22 14 M10 8 15 5 M12 16 16 13',
 'fine_rope': 'M3 7Q10 0 18 3Q24 7 20 14Q16 20 9 17Q2 14 6 8Q10 4 15 7Q19 10 14 13 M5 18 4 23 M9 19 11 23 M8 3 9 7 M19 6 16 8',
 'paper': 'M5 2H17L21 6V22H5Z M17 2V6H21 M8 10H17 M8 14H17 M8 18H13',
 'glass': 'M3 8 16 2 22 16 9 22Z M3 8 9 22 M8 9 13 6 M10 14 16 9',
 'star_glass': 'M4 7 16 2 22 16 10 22Z M9 9 13 7 15 11 19 12 15 15 14 19 11 16 7 15 10 12Z',
 'rune_tile': 'M3 6 16 2 21 17 9 22Q4 19 3 6Z M9 22Q11 14 6 6 M10 8 14 7 17 16 14 17 12 13 16 12',
 'iron': 'M4 6H20V11H15V17H20V22H4V17H9V11H4Z',
 'metal': 'M3 9 16 3 21 6V19L8 23 3 19Z M3 9 8 12 21 6 M8 12V23 M12 13V18 M17 11V16',
 'steel': 'M3 6 17 2 22 6V10L9 14V18L22 14V18L9 23 3 19V15L6 14V11L3 10Z M9 14 6 11 M9 18 3 15',
 'aeolian_alloy': 'M4 5H17L22 13 18 20H6L2 13Z M4 5 9 13H22 M9 13 6 20 M12 6 15 9 18 7 M13 16H17',
 'copper_parts': 'M3 4H10V10H3Z M14 2H21V8H14Z M6 14H13V21H6Z M16 12H22V18H16Z M10 7H14 M9 10V14 M13 17H16',
 'super_mechanism': 'M4 8H8V3H16V8H21V16H16V21H8V16H4Z M8 10 12 6 16 10V14L12 18 8 14Z M1 12H4 M21 12H23',
 'shaped_charge': 'M3 6 18 2 22 6V20L7 23 3 18Z M3 6 7 10 22 6 M7 10V23 M11 14 18 11 15 18Z',
 'shock_charge': 'M5 5H19V22H5Z M9 5V2H15V5 M13 8 9 14H14L11 20 17 12H12Z',
 'resonance_charge': 'M6 3H18L22 12 18 21H6L2 12Z M9 7H15L18 12 15 17H9L6 12Z M12 9V15',
 'fuel': 'M5 5H19L22 8V22H3V8Z M9 5V2H15V5 M6 10H18 M12 12 16 18 12 21 8 18Z',
 'firebomb': 'M8 8 6 4 11 6 14 1 16 7 20 5 18 10 21 15 18 22H6L3 15Z M12 12 9 18 12 21 16 17Z',
 'breach_bomb': 'M3 7 16 2 22 6V18L9 23 3 18Z M3 7 9 12 22 6 M9 12V23 M13 12 17 10 17 15 20 14 14 20Z',
}

def main():
    catalog = re.findall(r"\{ id: '([^']+)', name: '([^']+)'", (ROOT / 'shared/catalog/resources.ts').read_text())
    profiles = {key: (shape, color) for shape, (color, keys) in GROUPS.items() for key in keys.split()}
    assert set(profiles) == {key for key, _ in catalog}, 'Каталог изменился: задайте силуэт нового ресурса'
    out = ROOT / 'frontend/public/assets/ui/resources'
    out.mkdir(parents=True, exist_ok=True)
    entries = []
    for key, name in catalog:
        shape, color = profiles[key]
        # Материалы сохраняют свой цвет; варианты одного предмета имеют отдельную насечку.
        if key in ('coal', 'oil'): color = '#637b7b'
        if key == 'copper': color = '#d7966e'
        if key == 'gold_ingot': color = '#e6c766'
        if key == 'blue_salt': color = '#80b8da'
        if key == 'emerald_dust': color = '#7fbd93'
        variant = GROUPS[shape][1].split().index(key)
        notch = ''.join(f'<path d="M{5+i*3} 23h1"/>' for i in range(variant))
        geometry = VARIANTS.get(key, SHAPES[shape])
        stroke = color if shape == 'stalk' else '#253d39'
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="64" height="64"><g transform="translate(4 3)" fill="{color}" stroke="{stroke}" stroke-width="1.5" stroke-linejoin="bevel" stroke-linecap="round"><path d="{geometry}"/>{notch}</g></svg>\n'
        (out / f'{key}.svg').write_text(svg)
        entries.append(dict(id=key, name=name, shape=shape, color=color, file=f'{key}.svg'))
    (out / 'manifest.json').write_text(json.dumps(dict(revision='aeolian-ui-1', resources=entries), ensure_ascii=False, indent=2)+'\n')
    # Малые знаки — монохромная геометрия без материальной заливки и насечек.
    (ROOT / 'frontend/src/shared/ui/resourceGlyphs.ts').write_text('// Генератор: tools/assets/ui/build_resource_icons.py\nexport const resourceGlyphs: Record<string, string> = '+json.dumps({key: VARIANTS.get(key, SHAPES[profiles[key][0]]) for key, _ in catalog}, indent=2)+'\n')

if __name__ == '__main__':
    main()
