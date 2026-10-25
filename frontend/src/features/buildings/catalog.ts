import { buildingCatalog } from '../../../../shared/catalog/buildings'
import type { BuildingCatalogItem as SharedBuildingCatalogItem } from '../../../../shared/catalog/buildings'
import type { BuildingKind, PlacedBuilding } from '../../game/state/useGameStore'
import { resolveBuildingSpriteAsset } from '../../game/renderers/buildingRegistry'

export type BuildCatalogItem = {
  kind: BuildingKind
  category: SharedBuildingCatalogItem['category']
  name: string
  description: string
  time: string
  population: number
  footprint: { width: number; height: number }
  cost: readonly { resource: string; label: string; amount: number }[]
  previewImage?: string
  free?: boolean
}

export function buildTimeToSeconds(time: string) {
  if (time === 'мгновенно') {
    return 0
  }
  const [minutes, seconds] = time.split(':').map(Number)
  return minutes * 60 + seconds
}

const descriptions: Record<BuildingKind, string> = {
  town_hall: 'Центр города. Открывает строительство и задает лимит построек.',
  dugout: 'Первое жилье для жителей и рабочих.',
  field_bed: 'Дает материалы урожая и монеты после стадий роста.',
  seed_garden: 'Производит семена и редкий супер-урожай для полевых цепочек.',
  herb_bed: 'Выращивает травы и редкие цветы для алхимии и восстановления.',
  mushroom_grove: 'Лесная грядка для грибов и редких грибных урожаев.',
  flax_field: 'Источник льна и волокна для ткани, веревок и мешков.',
  reed_bed: 'Речная грядка для тростника, бумаги и простых конструкций.',
  dye_garden: 'Выращивает красильные культуры и редкие цветы.',
  oilseed_field: 'Дает масличные растения для масла и ламповых цепочек.',
  sugar_bed: 'Выращивает сахарный стебель для торговли, алхимии и событий.',
  crystal_greenhouse: 'Поздняя оранжерея для кристальных плодов.',
  warehouse: 'Складирует производственные запасы без лимитов ресурсов.',
  coin_storage: 'Увеличивает лимит монет. Остальные ресурсы лимита не имеют.',
  workshop: 'Обжигает кирпичи, собирает охотничьи капканы и пороховые бомбы.',
  brick_kiln: 'Перерабатывает глину и уголь в кирпичи для стен и городских зданий.',
  brick_yard: 'Обжигает глину в кирпичи на отдельном производственном дворе.',
  glass_workshop: 'Плавит песок и уголь в стекло для домов, оптики и поздних улучшений.',
  forge: 'Куёт метательные клинки из железных слитков, дерева и угля.',
  weaving_yard: 'Превращает волокно и лен в ткань и веревки.',
  dye_works: 'Готовит красители, флаги и городские товары из ткани и растений.',
  mechanical_workshop: 'Собирает механизмы из слитков, меди и деталей.',
  optical_workshop: 'Создает линзы и точные приборы из стекла и светокристаллов.',
  mint: 'Позднее экономическое здание для монет, печатей и рыночных бонусов.',
  market: 'Будущая торговля и обмен ресурсами.',
  tower: 'Базовая оборона границы.',
  defense_cannon: 'Стационарная пушка против диких монстров. Тратит камень, с 7 уровня — взрывчатку.',
  defense_stakes: 'Колья: ловушка на проходе с тремя зарядами и колющим уроном.',
  defense_resin_snare: 'Смоляная западня замедляет монстров и наносит урон при входе.',
  defense_bolt_thrower: 'Болтомёт поражает диких монстров без расхода боеприпасов.',
  defense_storm_coil: 'Грозовая катушка расходует бензин и задерживает атаку монстра.',
  defense_automaton_bay: 'База роботов-защитников. Сборка и ремонт пока недоступны.',
  defense_guardian_enclosure: 'База существ-защитников. Выращивание и лечение пока недоступны.',
  wooden_wall: 'Первая стадия стены: 3 уровня деревянной стены, затем каменная ветка.',
  stone_wall: 'Каменная стадия стены: 4 уровня перед бетонной веткой.',
  concrete_wall: 'Бетонная стадия стены: 3 уровня перед современной стеной.',
  modern_wall: 'Современная стадия стены: 5 уровней поздней обороны.',
  road: 'Базовая логистика без расхода лимита построек.',
  standard_road: 'Улучшенная городская дорога для устойчивых маршрутов снабжения.',
  paved_road: 'Дорогая и прочная мостовая для важных магистралей.',
  alliance_house: 'Позволяет создать союз, открыть казну, роли и общие баффы.',
  lumber_yard: 'Перерабатывает древесину в доски, а с третьего уровня может произвести премиум-доску.',
  sand_quarry: 'Добывает песок, монеты и с 3 уровня имеет шанс синей соли.',
  mine: 'Добывает камень, уголь, рудные примеси и редкие глубинные находки.',
  clay_quarry: 'Добывает глину для кирпича, цемента и черепицы.',
  iron_mine: 'Добывает железную руду для литейных и механических цепочек.',
  copper_mine: 'Добывает медь для деталей, механизмов и электроники.',
  resin_kiln: 'Перерабатывает древесину в смолу и редкую живицу.',
  sulfur_spring: 'Промышленный источник серы для химии и взрывчатки.',
  oil_well: 'Добывает нефть на нефтяных клетках для топливной экономики.',
  stone_cutters: 'Дробит добытый камень в каменные блоки.',
  tile_factory: 'Делает черепицу и позднюю руническую черепицу.',
  cement_workshop: 'Производит цемент из камня, глины и угля.',
  concrete_plant: 'Смешивает бетон и поздний железобетон.',
  rope_yard: 'Производит веревки для логистики, мостов, складов и караванов.',
  paper_workshop: 'Делает бумагу для архивов, чертежей и договоров.',
  paint_workshop: 'Производит краски для декора, флагов и рыночных улучшений.',
  oil_press: 'Выжимает масло для ламп, механизмов и производственных ускорений.',
  foundry: 'Плавит руду и уголь в железо, слитки и общий металл.',
  steelworks: 'Производит сталь и усиленные балки для поздних зданий.',
  electronics_workshop: 'Собирает электронику и импульсные заряды.',
  oil_refinery: 'Перерабатывает нефть в бензин для заводов средних и поздних уровней.',
  chemical_workshop: 'Производит химические материалы и огненные бомбы.',
  military_factory: 'Производит взрывчатку, защитные пластины и направленные заряды.',
  precision_workshop: 'Собирает супер-механизмы и эолиевые сплавы.',
  siege_yard: 'Собирает осадные мины и проломные бомбы.',
  resonance_laboratory: 'Собирает резонансные заряды для борьбы с мировыми угрозами.',
  wood_house: 'Апгрейд жилья из Землянки.',
  stone_house: 'Апгрейд деревянного дома с развилкой веток.',
  apartment_house: 'Плотное городское жилье.',
  villa: 'Престижная ветка жилья.',
  palace: 'Высшая стадия виллы.',
  residential_skyscraper: 'Высшая стадия многоквартирной ветки.',
}

const straightPreviewKinds = new Set<BuildingKind>([
  'wooden_wall', 'stone_wall', 'concrete_wall', 'modern_wall',
  'road', 'standard_road', 'paved_road',
])

function previewImage(kind: BuildingKind, shape?: string) {
  return resolveBuildingSpriteAsset({
    id: `${kind}-preview`,
    kind,
    name: kind,
    level: 1,
    tile: { x: 0, y: 0 },
    owner: 'preview',
    status: 'active',
    state: 'active',
    health: 100,
    maxHealth: 100,
    startedAt: 0,
    completesAt: null,
  } satisfies PlacedBuilding, { shape }) ?? undefined
}

export const buildCatalog = buildingCatalog
  .filter((item) => item.firstLevel)
  .map((item: SharedBuildingCatalogItem) => ({
    kind: item.type as BuildingKind,
    category: item.category,
    name: item.name,
    description: descriptions[item.type as BuildingKind],
    time: formatSeconds(item.buildSeconds),
    population: item.population,
    footprint: item.footprint,
    cost: item.cost.map((cost) => ({ resource: cost.resource, label: resourceLabel(cost.resource), amount: cost.amount })),
    previewImage: previewImage(item.type as BuildingKind, straightPreviewKinds.has(item.type as BuildingKind) ? 'straight_ew' : undefined),
    free: item.type === 'town_hall',
  })) satisfies BuildCatalogItem[]

function formatSeconds(seconds: number) {
  if (seconds <= 0) {
    return 'мгновенно'
  }
  const minutes = Math.floor(seconds / 60)
  const rest = seconds % 60
  return `${String(minutes).padStart(2, '0')}:${String(rest).padStart(2, '0')}`
}

function resourceLabel(resource: string) {
  const labels: Record<string, string> = {
    coins: 'Монеты',
    wood: 'Древесина',
    flax: 'Лен',
    windleaf: 'Ветролист',
    stone: 'Камень',
    stone_block: 'Каменный блок',
    brick: 'Кирпич',
    planks: 'Доски',
    premium_planks: 'Премиум-доски',
    copper_parts: 'Медные детали',
    reinforced_concrete: 'Железобетон',
    mechanism: 'Механизм',
    super_mechanism: 'Супер-механизм',
    rune_tile: 'Руническая черепица',
    rope: 'Веревка',
    iron_ingot: 'Железный слиток',
    gold_ingot: 'Золотой слиток',
    mushrooms: 'Грибы',
    'super-mushrooms': 'Супер-грибы',
    'super-windleaf': 'Супер-ветролист',
    emerald_dust: 'Изумрудная пыль',
    metal: 'Металл',
    glass: 'Стекло',
    concrete: 'Бетон',
    steel: 'Сталь',
    electronics: 'Электроника',
    clay: 'Глина',
    coal: 'Уголь',
    sand: 'Песок',
    seeds: 'Семена',
    iron_ore: 'Железная руда',
    copper: 'Медь',
    resin: 'Смола',
    oil: 'Нефть',
    fuel: 'Бензин',
    cement: 'Цемент',
    iron: 'Железо',
    sulfur: 'Сера',
    fabric: 'Ткань',
    herbs: 'Травы',
    dyes: 'Красители',
    oil_plants: 'Масличные растения',
    sugar_cane: 'Сахарный тростник',
    crystal_fruit: 'Кристальные плоды',
    light_crystal: 'Светокристалл',
    aeolian_alloy: 'Эолиевый сплав',
    tools: 'Инструменты',
    explosives: 'Взрывчатка',
    armor_plates: 'Защитные пластины',
    reinforced_beams: 'Усиленные балки',
    blue_salt: 'Синяя соль',
    star_glass: 'Звездное стекло',
  }
  return labels[resource] ?? resource
}
