# Реестр иконок интерфейса Эолии

Актуальное решение пользователя 31.10.2026: ResourceIcon снова использует прежние предметные изображения `assets/resources/icons/*.png` (каолин — SVG). Таблица нового ресурсного набора ниже сохранена как история редизайна: её SVG больше не подключены в игру, включая малые размеры. Исторические имена: quiet_powder → silent_powder, plant_oil → vegetable_oil, oleoresin → sap; fine_rope использует rope, tile — runic_tile. Функциональные знаки интерфейса сохраняются.

Источник: оригинальная геометрия проекта, `tools/assets/ui/build_icon_set.py` и `build_resource_icons.py`. Внешние наборы не использованы. Генератор этого реестра: `build_icon_manifest.py`.

Функциональные SVG: сетка 24×24, линия 1.8, `currentColor`, 16/20/24 px. Миниатюры: прозрачный SVG 32×32, экспорт 64 px, 30–64 px в интерфейсе; при контейнере ≤20 px используется монохромный знак. Смысловые подписи принадлежат кнопке/ResourceIcon. Серверные механики и игровые модели сохранены.

## Функциональные потребители

| Прежнее имя импорта | Новый файл в assets/ui/icons | Потребители | Статус |
|---|---|---|---|
| MousePointer2 | `select.svg` | `frontend/src/stories/design-main.tsx`, `frontend/src/features/tools/ToolBar.tsx` | Подключён |
| Castle | `build.svg` | `frontend/src/features/tools/ToolBar.tsx`, `frontend/src/features/player/levels.ts` | Подключён |
| Hammer | `hammer.svg` | `frontend/src/stories/design-main.tsx`, `frontend/src/stories/ComponentStates.tsx`, `frontend/src/features/alliance/AlliancePanel.tsx`, `frontend/src/features/inspector/Inspector.tsx`, `frontend/src/features/player/levels.ts` | Подключён |
| Repair | `repair.svg` | `frontend/src/features/tools/ToolBar.tsx`, `frontend/src/features/inspector/Inspector.tsx` | Подключён |
| Swords | `attack.svg` | `frontend/src/stories/design-main.tsx`, `frontend/src/features/tools/ToolBar.tsx`, `frontend/src/features/inspector/Inspector.tsx` | Подключён |
| Route | `road.svg` | `frontend/src/features/tools/ToolBar.tsx`, `frontend/src/features/inspector/Inspector.tsx`, `frontend/src/features/player/levels.ts` | Подключён |
| HandCoins | `market.svg` | `frontend/src/features/hud/ResourceBar.tsx` | Подключён |
| Coins | `coins.svg` | `frontend/src/features/alliance/AlliancePanel.tsx` | Подключён |
| Handshake | `alliance.svg` | `frontend/src/features/player/levels.ts` | Подключён |
| MessageSquare | `chat.svg` | `frontend/src/features/event-log/EventLog.tsx` | Подключён |
| Landmark | `center.svg` | `frontend/src/features/world-map/MapWidget.tsx`, `frontend/src/features/player/levels.ts` | Подключён |
| Map | `world.svg` | `frontend/src/features/buildings/BuildMenu.tsx`, `frontend/src/features/world-map/MapWidget.tsx`, `frontend/src/features/notifications/NotificationCenter.tsx`, `frontend/src/features/event-log/EventLog.tsx` | Подключён |
| MapPinned | `world.svg` | `frontend/src/features/player/levels.ts` | Подключён |
| UserRound | `profile.svg` | `frontend/src/features/player/ProfilePanel.tsx` | Подключён |
| Bell | `events.svg` | `frontend/src/features/notifications/NotificationCenter.tsx`, `frontend/src/features/player/ProfilePanel.tsx` | Подключён |
| Settings | `settings.svg` | `frontend/src/features/settings/AudioSettings.tsx`, `frontend/src/features/player/ProfilePanel.tsx` | Подключён |
| SlidersHorizontal | `settings.svg` | `frontend/src/features/settings/AudioSettings.tsx` | Подключён |
| Building2 | `housing.svg` | `frontend/src/features/buildings/BuildMenu.tsx`, `frontend/src/features/hud/ResourceBar.tsx` | Подключён |
| UsersRound | `people.svg` | `frontend/src/features/buildings/BuildMenu.tsx`, `frontend/src/features/hud/ResourceBar.tsx` | Подключён |
| Shield | `shield.svg` | `frontend/src/features/alliance/AlliancePanel.tsx`, `frontend/src/features/inspector/Inspector.tsx`, `frontend/src/features/player/levels.ts`, `frontend/src/features/admin/AdminPanel.tsx` | Подключён |
| ShieldAlert | `damage.svg` | `frontend/src/features/player/ProfilePanel.tsx` | Подключён |
| Warehouse | `storage.svg` | `frontend/src/features/player/levels.ts` | Подключён |
| Box | `storage.svg` | `frontend/src/features/inspector/Inspector.tsx` | Подключён |
| Package | `shortage.svg` | `frontend/src/features/resources/ResourceIcon.tsx` | Подключён |
| LandPlot | `fields.svg` | `frontend/src/features/player/levels.ts` | Подключён |
| Sprout | `fields.svg` | `frontend/src/features/inspector/Inspector.tsx` | Подключён |
| Gem | `crystal.svg` | `frontend/src/features/inspector/Inspector.tsx`, `frontend/src/features/player/levels.ts` | Подключён |
| Clock | `clock.svg` | `frontend/src/features/buildings/BuildMenu.tsx` | Подключён |
| X | `cancel.svg` | `frontend/src/features/buildings/BuildMenu.tsx`, `frontend/src/features/world-map/MapWidget.tsx` | Подключён |
| Check | `check.svg` | `frontend/src/features/buildings/BuildMenu.tsx` | Подключён |
| ChevronLeft | `left.svg` | `frontend/src/features/buildings/BuildMenu.tsx` | Подключён |
| ChevronRight | `right.svg` | `frontend/src/features/buildings/BuildMenu.tsx` | Подключён |
| ChevronUp | `up.svg` | `frontend/src/features/notifications/NotificationCenter.tsx`, `frontend/src/features/event-log/EventLog.tsx` | Подключён |
| ChevronDown | `down.svg` | `frontend/src/features/notifications/NotificationCenter.tsx`, `frontend/src/features/event-log/EventLog.tsx` | Подключён |
| Eye | `eye.svg` | `frontend/src/features/buildings/BuildMenu.tsx` | Подключён |
| Volume2 | `sound.svg` | `frontend/src/features/tools/ToolBar.tsx` | Подключён |
| VolumeX | `mute.svg` | `frontend/src/features/tools/ToolBar.tsx` | Подключён |
| Waves | `waves.svg` | `frontend/src/features/tools/ToolBar.tsx` | Подключён |
| Move | `move.svg` | `frontend/src/features/inspector/Inspector.tsx` | Подключён |
| RotateCw | `rotate.svg` | `frontend/src/features/inspector/Inspector.tsx` | Подключён |
| Trash2 | `trash.svg` | `frontend/src/features/inspector/Inspector.tsx` | Подключён |
| TrendingUp | `trend.svg` | `frontend/src/features/inspector/Inspector.tsx` | Подключён |
| Star | `star.svg` | `frontend/src/features/inspector/Inspector.tsx`, `frontend/src/features/player/ProfilePanel.tsx` | Подключён |
| LogOut | `logout.svg` | `frontend/src/features/player/ProfilePanel.tsx` | Подключён |
| MonitorCog | `monitor.svg` | `frontend/src/features/player/ProfilePanel.tsx` | Подключён |
| Gauge | `gauge.svg` | `frontend/src/features/alliance/AlliancePanel.tsx` | Подключён |
| TowerControl | `tower.svg` | `frontend/src/features/player/levels.ts` | Подключён |
| Crown | `crown.svg` | `frontend/src/features/player/levels.ts` | Подключён |
| Trophy | `trophy.svg` | `frontend/src/features/player/levels.ts` | Подключён |
| Network | `network.svg` | `frontend/src/features/player/levels.ts` | Подключён |
| Tent | `tent.svg` | `frontend/src/features/player/levels.ts` | Подключён |

Дополнительные знаки статусов и категорий подключены через `AeolianIcon` в ActionState и BuildMenu. Auth и рынок используют текстовые действия; буквенных иконок для замены там нет. Совместимые имена экспортов не означают сохранение рисунков Lucide.

## Ресурсный каталог

| Ключ | Название | Новый файл | Семейство | Статус |
|---|---|---|---|---|
| `stone_heart` | Каменное сердце | `assets/ui/resources/stone_heart.svg` | heart | Подключён |
| `fine_rope` | Качественная веревка | `assets/ui/resources/fine_rope.svg` | rope | Подключён |
| `throwing_knives` | Метательные клинки | `assets/ui/resources/throwing_knives.svg` | knife | Подключён |
| `hunting_traps` | Охотничий капкан | `assets/ui/resources/hunting_traps.svg` | trap | Подключён |
| `blackpowder_bomb` | Пороховая бомба | `assets/ui/resources/blackpowder_bomb.svg` | bomb | Подключён |
| `shaped_charge` | Направленный заряд | `assets/ui/resources/shaped_charge.svg` | charge | Подключён |
| `firebomb` | Огненная бомба | `assets/ui/resources/firebomb.svg` | bomb | Подключён |
| `shock_charge` | Импульсный заряд | `assets/ui/resources/shock_charge.svg` | charge | Подключён |
| `siege_mine` | Осадная мина | `assets/ui/resources/siege_mine.svg` | mine | Подключён |
| `breach_bomb` | Проломная бомба | `assets/ui/resources/breach_bomb.svg` | bomb | Подключён |
| `resonance_charge` | Резонансный заряд | `assets/ui/resources/resonance_charge.svg` | charge | Подключён |
| `coins` | Монеты | `assets/ui/resources/coins.svg` | coins | Подключён |
| `population` | Жители | `assets/ui/resources/population.svg` | people | Подключён |
| `aeolian-crystal` | Эолийские кристаллы | `assets/ui/resources/aeolian-crystal.svg` | crystal | Подключён |
| `wood` | Древесина | `assets/ui/resources/wood.svg` | wood | Подключён |
| `clay` | Глина | `assets/ui/resources/clay.svg` | stone | Подключён |
| `stone` | Камень | `assets/ui/resources/stone.svg` | stone | Подключён |
| `windleaf` | Ветролист | `assets/ui/resources/windleaf.svg` | leaf | Подключён |
| `seeds` | Семена | `assets/ui/resources/seeds.svg` | seed | Подключён |
| `sand` | Песок | `assets/ui/resources/sand.svg` | grain | Подключён |
| `resin` | Смола | `assets/ui/resources/resin.svg` | drop | Подключён |
| `flax` | Лен | `assets/ui/resources/flax.svg` | stalk | Подключён |
| `fiber` | Волокно | `assets/ui/resources/fiber.svg` | thread | Подключён |
| `reed` | Тростник | `assets/ui/resources/reed.svg` | stalk | Подключён |
| `herbs` | Травы | `assets/ui/resources/herbs.svg` | leaf | Подключён |
| `mushrooms` | Грибы | `assets/ui/resources/mushrooms.svg` | mushroom | Подключён |
| `oil_plants` | Масличные растения | `assets/ui/resources/oil_plants.svg` | leaf | Подключён |
| `sugar_cane` | Сахарный тростник | `assets/ui/resources/sugar_cane.svg` | stalk | Подключён |
| `coal` | Уголь | `assets/ui/resources/coal.svg` | stone | Подключён |
| `iron_ore` | Железная руда | `assets/ui/resources/iron_ore.svg` | stone | Подключён |
| `copper` | Медь | `assets/ui/resources/copper.svg` | ingot | Подключён |
| `dyes` | Красители | `assets/ui/resources/dyes.svg` | jar | Подключён |
| `brick` | Кирпич | `assets/ui/resources/brick.svg` | block | Подключён |
| `planks` | Доски | `assets/ui/resources/planks.svg` | plank | Подключён |
| `stone_block` | Каменный блок | `assets/ui/resources/stone_block.svg` | block | Подключён |
| `rope` | Веревка | `assets/ui/resources/rope.svg` | rope | Подключён |
| `fabric` | Ткань | `assets/ui/resources/fabric.svg` | sheet | Подключён |
| `paper` | Бумага | `assets/ui/resources/paper.svg` | sheet | Подключён |
| `tile` | Черепица | `assets/ui/resources/tile.svg` | tile | Подключён |
| `quiet_powder` | Тихий порошок | `assets/ui/resources/quiet_powder.svg` | grain | Подключён |
| `amber_essence` | Янтарная эссенция | `assets/ui/resources/amber_essence.svg` | drop | Подключён |
| `memory_shard` | Осколок памяти | `assets/ui/resources/memory_shard.svg` | crystal | Подключён |
| `glass` | Стекло | `assets/ui/resources/glass.svg` | sheet | Подключён |
| `metal` | Металл | `assets/ui/resources/metal.svg` | ingot | Подключён |
| `iron` | Железо | `assets/ui/resources/iron.svg` | ingot | Подключён |
| `iron_ingot` | Железный слиток | `assets/ui/resources/iron_ingot.svg` | ingot | Подключён |
| `copper_parts` | Медные детали | `assets/ui/resources/copper_parts.svg` | production | Подключён |
| `tools` | Инструменты | `assets/ui/resources/tools.svg` | repair | Подключён |
| `cement` | Цемент | `assets/ui/resources/cement.svg` | sack | Подключён |
| `concrete` | Бетон | `assets/ui/resources/concrete.svg` | block | Подключён |
| `steel` | Сталь | `assets/ui/resources/steel.svg` | ingot | Подключён |
| `mechanism` | Механизм | `assets/ui/resources/mechanism.svg` | production | Подключён |
| `premium_planks` | Премиум-доски | `assets/ui/resources/premium_planks.svg` | plank | Подключён |
| `reinforced_concrete` | Железобетон | `assets/ui/resources/reinforced_concrete.svg` | block | Подключён |
| `reinforced_beams` | Усиленные балки | `assets/ui/resources/reinforced_beams.svg` | beam | Подключён |
| `armor_plates` | Защитные пластины | `assets/ui/resources/armor_plates.svg` | shield | Подключён |
| `electronics` | Электроника | `assets/ui/resources/electronics.svg` | circuit | Подключён |
| `sulfur` | Сера | `assets/ui/resources/sulfur.svg` | grain | Подключён |
| `explosives` | Взрывчатка | `assets/ui/resources/explosives.svg` | charge | Подключён |
| `oil` | Нефть | `assets/ui/resources/oil.svg` | barrel | Подключён |
| `plant_oil` | Растительное масло | `assets/ui/resources/plant_oil.svg` | jar | Подключён |
| `paints` | Краски | `assets/ui/resources/paints.svg` | jar | Подключён |
| `oleoresin` | Живица | `assets/ui/resources/oleoresin.svg` | drop | Подключён |
| `aeolian_alloy` | Эолиевый сплав | `assets/ui/resources/aeolian_alloy.svg` | ingot | Подключён |
| `fuel` | Бензин | `assets/ui/resources/fuel.svg` | barrel | Подключён |
| `gold_ingot` | Золотой слиток | `assets/ui/resources/gold_ingot.svg` | ingot | Подключён |
| `crystal_fruit` | Кристальные плоды | `assets/ui/resources/crystal_fruit.svg` | fruit | Подключён |
| `super-seeds` | Супер-семена | `assets/ui/resources/super-seeds.svg` | seed | Подключён |
| `super-fiber` | Супер-волокно | `assets/ui/resources/super-fiber.svg` | thread | Подключён |
| `super-mushrooms` | Супер-грибы | `assets/ui/resources/super-mushrooms.svg` | mushroom | Подключён |
| `super-windleaf` | Супер-ветролист | `assets/ui/resources/super-windleaf.svg` | leaf | Подключён |
| `rare_flowers` | Редкие цветы | `assets/ui/resources/rare_flowers.svg` | flower | Подключён |
| `blue_salt` | Синяя соль | `assets/ui/resources/blue_salt.svg` | grain | Подключён |
| `kaolin` | Каолин | `assets/ui/resources/kaolin.svg` | stone | Подключён |
| `emerald_dust` | Изумрудная пыль | `assets/ui/resources/emerald_dust.svg` | grain | Подключён |
| `star_glass` | Звездное стекло | `assets/ui/resources/star_glass.svg` | sheet | Подключён |
| `light_crystal` | Светокристалл | `assets/ui/resources/light_crystal.svg` | crystal | Подключён |
| `super_mechanism` | Супер-механизм | `assets/ui/resources/super_mechanism.svg` | production | Подключён |
| `elderwood-heart` | Сердцевина древня | `assets/ui/resources/elderwood-heart.svg` | wood | Подключён |
| `rune_tile` | Руническая черепица | `assets/ui/resources/rune_tile.svg` | tile | Подключён |

Старые PNG/GLB не удалены: это существующие игровые/исходные ассеты. ResourceIcon больше не обращается к старому набору. Unknown id получает shortage; ошибка загрузки — встроенный Package/shortage без дополнительного запроса.

## Текстовые маркеры

Следующие символы сохранены как текстовые разделители, счётчики, навигационные стрелки или индикаторы непрочитанного; рядом остаётся смысловая подпись. Они не служат заменой предметной иконки.

| Файл | Строка | Символы |
|---|---|---|
| `frontend/src/audio/realtimeAudio.ts` | 43 | → |
| `frontend/src/stories/AeolianPrototype.tsx` | 45 | ⚠ |
| `frontend/src/stories/AeolianPrototype.tsx` | 52 | ♣ |
| `frontend/src/stories/AeolianPrototype.tsx` | 64 | ⚠ ✓ |
| `frontend/src/stories/AeolianPrototype.tsx` | 68 | ◉ ◷ |
| `frontend/src/game/IsoMap.tsx` | 529 | ← ↑ → ↓ |
| `frontend/src/game/IsoMap.tsx` | 530 | − |
| `frontend/src/game/IsoMap.tsx` | 539 | ✓ |
| `frontend/src/game/IsoMap.tsx` | 600 | ▲ |
| `frontend/src/features/world-map/MapWidget.tsx` | 141 | ▲ |
| `frontend/src/features/world-map/MapWidget.tsx` | 146 | △ |
| `frontend/src/features/notifications/NotificationCenter.tsx` | 80 | ● |
| `frontend/src/features/notifications/NotificationCenter.tsx` | 81 | → |
| `frontend/src/features/player/PlayerBalloon.tsx` | 19 | ★ |
| `frontend/src/features/admin/AdminPanel.tsx` | 57 | → |

## Приёмка

Программно проверяются покрытие каталога, безопасный SVG, отсутствие внешних ссылок/шрифтов, отсутствие прямых импортов старого набора, fallback, подписи и бюджет. Пилот: `docs/assets/ui/review/icons/pilot.png`; полный лист: `index.html`; миниатюры: `resources.png`. Это листы ассетов, не снимки игрового мира.

Не закрыты: пользовательское распознавание без подписей, все сочетания бейджей владения/редкости, отдельная оптическая версия каждого функционального знака для 16 px, DPR 1/2 и масштаб 200% в игре, симуляции цветового зрения, реальные фоны травы/воды/руин/зданий.
