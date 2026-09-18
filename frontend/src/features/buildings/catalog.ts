import { buildingCatalog } from '../../../../shared/catalog/buildings'
import type { BuildingCatalogItem as SharedBuildingCatalogItem } from '../../../../shared/catalog/buildings'
import type { BuildingKind } from '../../game/state/useGameStore'

export type BuildCatalogItem = {
  kind: BuildingKind
  category: SharedBuildingCatalogItem['category']
  name: string
  description: string
  time: string
  population: number
  footprint: { width: number; height: number }
  cost: readonly { resource: string; label: string; amount: number }[]
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
  warehouse: 'Складирует производственные запасы без лимитов ресурсов.',
  coin_storage: 'Увеличивает лимит монет. Остальные ресурсы лимита не имеют.',
  workshop: 'Открывает базовые производственные рецепты.',
  market: 'Будущая торговля и обмен ресурсами.',
  tower: 'Базовая оборона границы.',
  wooden_wall: 'Первая стадия стены: 3 уровня деревянной стены, затем каменная ветка.',
  stone_wall: 'Каменная стадия стены: 4 уровня перед бетонной веткой.',
  concrete_wall: 'Бетонная стадия стены: 3 уровня перед современной стеной.',
  modern_wall: 'Современная стадия стены: 5 уровней поздней обороны.',
  road: 'Базовая логистика без расхода лимита построек.',
  alliance_house: 'Позволяет создать союз, открыть казну, роли и общие баффы.',
  lumber_yard: 'Производит древесину для домов, складов и союзных взносов.',
  stone_cutters: 'Добывают камень и подготавливают сырье под кирпичи.',
  oil_refinery: 'Перерабатывает нефть в бензин для заводов средних и поздних уровней.',
  wood_house: 'Апгрейд жилья из Землянки.',
  stone_house: 'Апгрейд деревянного дома с развилкой веток.',
  apartment_house: 'Плотное городское жилье.',
  villa: 'Престижная ветка жилья.',
  palace: 'Высшая стадия виллы.',
  residential_skyscraper: 'Высшая стадия многоквартирной ветки.',
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
  }
  return labels[resource] ?? resource
}
