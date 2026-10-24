# Real City — План реализации

Пунктов плана выполнено: 5/67 (7.5%)

Этот план посвящён звуковым эффектам игрового клиента. Звуки создаются как оригинальные ассеты, а сервер по-прежнему определяет результаты строительства, экономики и боя. Фоновая музыка и озвучка персонажей не входят в объём плана. Сначала нужен слышимый игровой цикл — интерфейс, сбор, стройка и бой; окружение и редкие события добавляются после него.

## Подход к логированию

Звуковая подсистема работает на клиенте. Она не пишет лог на каждое воспроизведение и не меняет серверную симуляцию. В режиме разработки выводить структурированные сообщения `audio.asset_missing`, `audio.decode_failed`, `audio.context_blocked`, `audio.event_unmapped`, `audio.voice_limit_reached` с `sound_id`, типом события и кодом ошибки, без текста чата, токенов и координат частной активности. Повторяющиеся сообщения ограничивать по времени. В production собирать только агрегированные счётчики ошибок загрузки/декодирования и отключённого звука, если для клиентской телеметрии уже есть согласованный канал; не отправлять события о каждом клике. Отладочная панель должна показывать состояние `AudioContext`, активные голоса, занятость шин, кеш и последние ошибки. Источник игрового события и `event_id` остаются в существующем realtime-конверте; это позволяет проверить, почему звук сработал один раз.

Общий звуковой язык: тёплые дерево и земля для строительства и полей; сухие камень и металл для добычи и обороны; короткий медный звон для монет; приглушённый воздушный и кристаллический слой для редких находок. Все тембры оригинальные, без звуков или мелодических цитат из Gnomgrad. Интерфейсные сигналы короткие и тихие; награды заметнее; удар и предупреждение читаются поверх мира. Наведение на элемент, панорамирование и каждый тик таймера остаются без звука, чтобы не создавать постоянный шум.

Исходники хранить как WAV PCM 48 кГц, финальные короткие эффекты — преимущественно mono MP3; пространственный стереообраз формировать в браузере. Для атмосферных петель допустим stereo. Начальные ориентиры: клик 40–100 мс, подтверждение 120–350 мс, действие 150–600 мс, крупный итог 0.6–1.5 с; хвосты без обрезки, без цифрового клиппинга. Целевые громкости устанавливать прослушиванием по шинам, а пиковый запас исходников держать около −3 dBFS; численные значения уточнить в громкостной приёмке на наушниках, динамиках ноутбука и телефоне. Браузер может блокировать воспроизведение до жеста пользователя, поэтому аудиоинициализация происходит после первого взаимодействия: [MDN: autoplay](https://developer.mozilla.org/en-US/docs/Web/Media/Guides/Autoplay), [MDN: AudioContext.resume](https://developer.mozilla.org/en-US/docs/Web/API/AudioContext/resume). Выбор контейнеров и запасного кодека сверить с [MDN: audio codecs](https://developer.mozilla.org/en-US/docs/Web/Media/Guides/Formats/Audio_codecs).

## Фаза 0 — Реестр событий и художественные правила

| # | Что | Файлы | Статус |
|---|---|---|---|
| 0.1 | Составить матрицу `действие → подтверждение API/WS → sound_id → координата → кому слышно` по `BuildMenu`, `Inspector`, производству, инвентарю, чату, союзам, рынку и событиям `world`, `monster`, `cannon.shot`. Пометить отсутствующие события и отличать попытку от успешного результата. | `docs/audio/event-matrix.md`, `frontend/src/features/`, `shared/events/` | ✅ |
| 0.2 | Зафиксировать словарь семейств и идентификаторов (`ui.*`, `economy.*`, `build.*`, `world.*`, `combat.*`, `social.*`, `ambience.*`), приоритеты `critical/high/normal/low`, шин `ui/world/alerts/ambience`, правила вариаций, длительности и тихого режима. | `docs/audio/sound-style.md`, `frontend/src/audio/soundEvents.ts` | ✅ |
| 0.3 | Описать критерий событийности: локально сразу звучат только нейтральные действия интерфейса; успех, трата, награда, попадание и разрушение — после ответа сервера или подходящего WS-события; ошибки имеют отдельный сигнал. События удалённых игроков слышны лишь в видимой/близкой области, кроме критичных уведомлений для владельца. | `docs/audio/event-matrix.md`, `docs/audio/sound-style.md` | ✅ |
| 0.4 | Утвердить бюджет первого выпуска: короткие эффекты до 150 КБ на семейство в сжатом виде, суммарно ориентир до 5 МБ для всего каталога, начальная загрузка до 300 КБ; измерять реальный билд и пересматривать бюджет по слуховой оценке и мобильной сети. | `docs/audio/sound-style.md`, `frontend/scripts/check-asset-budget.mjs` | ✅ |
| 0.5 | Завести реестр происхождения каждого исходника: собственный синтез/запись, дата, автор, рецепт/путь, лицензия стороннего материала и право переработки; запретить бесконтрольные найденные в сети сэмплы. | `docs/audio/asset-register.md`, `tools/audio/recipes/` | ✅ |

---

## Фаза 1 — Инструменты создания и сборки звука в Linux

| # | Что | Файлы | Статус |
|---|---|---|---|
| 1.1 | Проверить доступность `python3`, FFmpeg, SoX и Audacity в WSL/Linux. Описать установку нужных пакетов и версии в руководстве; текущая среда содержит Python, но остальные утилиты нужно устанавливать при реализации. Базовый генератор должен работать через стандартную библиотеку Python (`math`, `random`, `wave`, `struct`), без обязательной внешней аудиомодели. | `docs/audio/production-guide.md`, `tools/audio/README.md` | ⏳ |
| 1.2 | Реализовать у Codex воспроизводимые Python-рецепты: генераторы синуса/треугольника/шума, огибающие ADSR, частотный сдвиг, фильтрация, слои, короткое отражение и seeded-вариации; любой `sound_id` пересобирается одной командой из рецепта. | `tools/audio/generate_sfx.py`, `tools/audio/recipes/*.json` | ⏳ |
| 1.3 | Добавить ручной путь для записанного Foley: хлопок по дереву, зерно в миске, монеты/металл, камешки, бумага/ткань; записывать в тихой комнате, чистить в [Audacity](https://www.audacityteam.org/manual/getting-started/export-your-audio/), резать и документировать, затем обрабатывать теми же сборочными скриптами. Синтез остаётся запасным вариантом для каждого эффекта. | `docs/audio/production-guide.md`, `tools/audio/recordings/`, `docs/audio/asset-register.md` | ⏳ |
| 1.4 | Написать конвейер `рецепт/запись → WAV master → очистка/trim/fade → проверка пиков и длины → MP3 → manifest`. Использовать FFmpeg для ресемплинга, fades, компрессии/нормализации и кодирования; зафиксировать команду и параметры. [FFmpeg: audio filters](https://ffmpeg.org/ffmpeg-filters.html). | `tools/audio/build_audio.py`, `tools/audio/validate_audio.py`, `tools/audio/master/`, `frontend/public/assets/audio/` | ⏳ |
| 1.5 | Для каждого короткого звука сделать 2–5 управляемых вариантов там, где действие повторяется часто; изменение высоты ±3–7%, атаки и фактуры без изменения узнаваемого сигнала. Варианты указывать в manifest, не плодить отдельные семейства без разницы в смысле. | `tools/audio/recipes/*.json`, `frontend/src/audio/soundManifest.ts` | ⏳ |
| 1.6 | Подготовить слепой сравнительный лист по двум вариантам ключевых эффектов (клик, монета, урожай, стройка, выстрел, получение урона), утвердить на малой и средней громкости, на наушниках и динамиках ноутбука; зафиксировать отобранные рецепты. | `docs/audio/listening-review.md`, `tools/audio/recipes/` | ⏳ |

---

## Фаза 2 — Каталог звуков интерфейса и обратной связи

Каждая строка ниже задаёт отдельный `sound_id` или явно названное семейство. Указанные времена — ориентиры для мастеринга, а не задержка интерфейса. Интерфейсные звуки воспроизводятся без панорамы и не должны маскировать предупреждения.

| # | Что | Файлы | Статус |
|---|---|---|---|
| 2.1 | `ui.click`: мягкий древесный щелчок + очень короткий светлый тон, 50–90 мс, 3 варианта; срабатывает на явном действии кнопки и иконки, с общим ограничителем 70 мс. Не привязывать ко всем `pointerdown`, чтобы не озвучивать перетаскивание. | `tools/audio/recipes/ui.json`, `frontend/src/shared/ui/`, `frontend/src/features/tools/ToolBar.tsx` | ⏳ |
| 2.2 | `ui.tab` / `ui.toggle.on` / `ui.toggle.off`: сухой приглушённый щелчок и пара близких по высоте тонов, 60–140 мс; вкладки, переключатели, разворот панелей, mute. При быстро меняющемся переключателе играть только конечное состояние. | `tools/audio/recipes/ui.json`, `frontend/src/features/buildings/BuildMenu.tsx`, `frontend/src/features/notifications/NotificationCenter.tsx` | ⏳ |
| 2.3 | `ui.panel.open` / `ui.panel.close` / `ui.dialog.open`: короткий шорох ткани/бумаги с мягким тоном, 120–220 мс; открыть меню, инспектор, диалог апгрейда. При автоматическом перепозиционировании и ререндере тишина. | `tools/audio/recipes/ui.json`, `frontend/src/features/inspector/Inspector.tsx`, `frontend/src/features/buildings/BuildMenu.tsx` | ⏳ |
| 2.4 | `ui.select.tile` / `ui.select.building` / `ui.select.monster`: едва слышный маркер клетки, более плотный деревянно-металлический маркер постройки, низкий шорох для монстра, 60–160 мс; только смена выделения, без звука при движении камеры. | `tools/audio/recipes/ui.json`, `frontend/src/game/IsoMap.tsx`, `frontend/src/game/renderer/PixiStage.tsx` | ⏳ |
| 2.5 | `ui.place.preview` / `ui.place.rotate` / `ui.place.cancel`: лёгкое касание сетки, трещотка на четверть оборота, обратный шорох; при каждом перемещении ghost-модели звука нет. | `tools/audio/recipes/ui.json`, `frontend/src/features/build-placement/`, `frontend/src/features/buildings/BuildMenu.tsx` | ⏳ |
| 2.6 | `ui.action.invalid` / `ui.resource.insufficient`: короткий глухой двойной тон без резкого писка, 120–250 мс; ошибка места, недоступная команда или нехватка ресурсов. Звучит один раз на завершённую попытку, не на каждый ререндер текста ошибки. | `tools/audio/recipes/ui.json`, `frontend/src/features/buildings/BuildMenu.tsx`, `frontend/src/features/inspector/Inspector.tsx` | ⏳ |
| 2.7 | `ui.confirm` / `ui.cancel` / `ui.toast.info` / `ui.toast.warning` / `ui.toast.error`: положительный мягкий двухнотный сигнал, нейтральный спад и три по приоритету различимых уведомления; 120–400 мс. У важного предупреждения собственный интервал повтора, ошибки не дублировать с `invalid`. | `tools/audio/recipes/ui.json`, `frontend/src/features/notifications/`, `frontend/src/features/event-log/` | ⏳ |

---

## Фаза 3 — Экономика, ресурсы, поля и производство

Для всех наград звук привязан к подтверждённому результату конкретного действия. `economy.inventory.changed` сам по себе слишком общий: по одной инвалидации кеша нельзя различить заработок, расход и обновление после входа. Для точной озвучки нужен результат mutation или специализированное событие с причиной и дельтой.

| # | Что | Файлы | Статус |
|---|---|---|---|
| 3.1 | `economy.coin.earned` / `economy.coin.spent` / `economy.coin.insufficient`: звон 2–4 медных дисков с коротким затуханием; заработок чуть выше, трата ниже, недостаток ресурсов использует общий предупреждающий мотив. Не играть за пассивный тик дохода; агрегировать пакетные выплаты в один сигнал. | `tools/audio/recipes/economy.json`, `frontend/src/features/economy/`, `frontend/src/features/hud/ResourceBar.tsx` | ⏳ |
| 3.2 | `economy.harvest.field`: шелест листьев + мягкое срезание + короткий звук семян/снопа, 250–500 мс, 4 варианта; только после успешного `harvestField`. Материал по группе: ветролист/травы/лён/камыш — сухой лист, грибы — влажный мягкий щелчок, сахарный тростник — плотный стебель, кристальная теплица — стеклянный обертон. | `tools/audio/recipes/harvest.json`, `frontend/src/features/inspector/Inspector.tsx`, `shared/catalog/buildings.ts` | ⏳ |
| 3.3 | `economy.crop.ready` / `economy.crop.expired`: лёгкий ростовой перелив и глухой увядающий шорох, до 350 мс; сигнал готовности только для поля игрока, один раз на переход состояния, не при каждом обновлении таймера и не для массовой фоновой симуляции. | `tools/audio/recipes/harvest.json`, `frontend/src/features/fields/`, `frontend/src/features/buildings/ConstructionTicker.tsx` | ⏳ |
| 3.4 | `economy.gather.wood` / `stone` / `ore` / `clay` / `sand`: короткий удар топора в древесину, скол камня, звон кирки, влажная глина и сыпучий песок; 180–450 мс, по 2–3 варианта. Звучит на подтверждённый сбор, не на каждую единицу полученного ресурса. | `tools/audio/recipes/gather.json`, `frontend/src/features/world/forestActions.ts`, `frontend/src/features/resources/`, `shared/catalog/resources.ts` | ⏳ |
| 3.5 | `economy.gather.oil` / `resin` / `crystal` / `rare`: насос и пузырь масла, вязкий отрыв смолы, стеклянный щелчок кристалла, отдельный сдержанный акцент редкой находки; 220–600 мс. Параметры выбираются по реальному типу награды. | `tools/audio/recipes/gather.json`, `frontend/src/features/resources/`, `shared/catalog/resources.ts` | ⏳ |
| 3.6 | `economy.node.claimed` / `node.depleted` / `node.respawned`: закрепление знака, тихой осыпание, мягкое возобновление; слышно владельцу или в видимой области, без множества звуков при загрузке чанка. | `tools/audio/recipes/world.json`, `frontend/src/features/resources/ResourceNodeSync.tsx`, `shared/events/world.ts` | ⏳ |
| 3.7 | `economy.production.started` / `production.ready` / `production.collected`: запуск механизма, один короткий колокольчик готовности и звяк тары; производства сгруппировать по дереву/камню/металлу/ткани/химии, не озвучивать каждый серверный тик. | `tools/audio/recipes/production.json`, `frontend/src/features/production/ProductionPanel.tsx`, `shared/catalog/buildings.ts` | ⏳ |
| 3.8 | `economy.storage.deposit` / `withdraw` / `full`: стук деревянного ящика, сдвиг крышки и сухой отказ; срабатывает лишь если в игре есть соответствующее подтверждённое действие. Не считать простое изменение счётчика инвентаря явным складированием. | `tools/audio/recipes/economy.json`, `frontend/src/features/inspector/Inspector.tsx`, `docs/buildings/storage/` | ⏳ |
| 3.9 | `economy.market.listed` / `bought` / `sold` / `cancelled`: бумага и печать при выставлении, монета + товар при исполнении, короткий возврат при отмене; различать создание ордера и фактическое исполнение по `market.order.*`. | `tools/audio/recipes/market.json`, `frontend/src/features/`, `shared/events/market.ts` | ⏳ |
| 3.10 | `economy.level.up` / `reward.rare`: 0.7–1.2 с умеренного праздничного мотива из 2–3 нот, без постоянного фанфарного цикла; играть только личному игроку после подтверждённого повышения/выдачи. | `tools/audio/recipes/reward.json`, `frontend/src/features/player/ProfilePanel.tsx`, `shared/events/` | ⏳ |

---

## Фаза 4 — Строительство, дороги и разрушение

| # | Что | Файлы | Статус |
|---|---|---|---|
| 4.1 | `build.placed` / `build.started`: касание фундамента + один удар молотка/скоба, 250–450 мс; после успешного размещения. При строительстве из нескольких стадий не играть его каждый тик. Проверить переходы `planned → building` в `world.building.*`. | `tools/audio/recipes/building.json`, `frontend/src/features/buildings/BuildMenu.tsx`, `shared/events/world.ts` | ⏳ |
| 4.2 | `build.completed`: два сухих удара + короткий тёплый восходящий сигнал, 450–800 мс; личному владельцу как уведомление даже вне видимой области, соседям — лишь приглушённый мирный звук рядом. Один раз при `building → active`, включая офлайн завершение при следующем входе только через уведомление, без лавины при первичной загрузке. | `tools/audio/recipes/building.json`, `frontend/src/features/buildings/BuildingSync.tsx`, `shared/events/world.ts` | ⏳ |
| 4.3 | `build.upgrade.started` / `build.upgrade.completed` / `build.rushed`: усиленный металлический стык, знакомый сигнал завершения с иной концовкой, краткий ускоряющий пролёт; отличать апгрейд от нового здания по причине события или ответу mutation. | `tools/audio/recipes/building.json`, `frontend/src/features/inspector/Inspector.tsx`, `shared/events/world.ts` | ⏳ |
| 4.4 | `build.repair.started` / `build.repaired` / `build.cancelled`: приглушённые инструмент и закрепление, обратный шорох дерева при отмене; добавлять событие только вместе с реальной механикой ремонта/отмены. | `tools/audio/recipes/building.json`, `frontend/src/features/inspector/Inspector.tsx`, `shared/events/world.ts` | ⏳ |
| 4.5 | `build.road.placed` / `build.wall.placed`: утрамбованная земля/плита для дороги, плотный деревянный/каменный стук для стены; параметр материала берётся из типа постройки. Пакетная прокладка дороги озвучивается по интервалу/серии, не по каждой клетке подряд. | `tools/audio/recipes/building.json`, `shared/catalog/buildings.ts`, `frontend/src/features/buildings/BuildMenu.tsx` | ⏳ |
| 4.6 | `build.damaged.light` / `heavy` / `ruined`: треск материала с нарастающим низким слоем; сильное попадание и обрушение отличаются от обычного клика, но не перекрывают критический сигнал. Степень урона рассчитывать из подтверждённой дельты HP; разрушение — из события удаления/перехода `ruined`, если причина известна. | `tools/audio/recipes/damage.json`, `frontend/src/features/world/realtime.ts`, `shared/events/world.ts` | ⏳ |
| 4.7 | `build.demolished`: контролируемый осыпающийся звук без боевого взрыва; запускать только после подтверждённого сноса по собственной команде, отдельно от разрушения атакой и удаления объекта из области видимости. | `tools/audio/recipes/building.json`, `frontend/src/features/inspector/Inspector.tsx`, `shared/events/world.ts` | ⏳ |

---

## Фаза 5 — Орудия, монстры, урон и угрозы

Звуки боя опираются на серверные `cannon.shot`, `monster.attacked`, `monster.damaged`, `monster.died`, `combat.resolved`. Событие `monster.moved` используется для движения модели, но не как команда воспроизвести шаг на каждый тик. Если в payload нет места попадания или типа повреждённого здания, сначала добавить минимальные поля/отдельное событие; не вычислять «попадание» по анимации клиента.

| # | Что | Файлы | Статус |
|---|---|---|---|
| 5.1 | `combat.weapon.cannon` / `impact.stone` / `impact.wood` / `impact.flesh`: низкий хлопок с механическим щелчком, воздушный пролёт только при различимой задержке, затем удар материала. Разделить выстрел и попадание лишь если серверная последовательность/время позволяют синхронизировать с визуальным снарядом. | `tools/audio/recipes/weapons.json`, `frontend/src/features/world/realtime.ts`, `frontend/src/game/`, `docs/buildings/defense/cannon.md` | ⏳ |
| 5.2 | `combat.weapon.tower` / `bolt_thrower` / `storm_coil`: для башни деревянный натяг/щелчок, для болтомёта тяжёлый спуск и пролёт, для грозовой катушки короткий электрический разряд с сухим хвостом; громкость и дальность по классу орудия. Тип берётся из `building_type` в `cannon.shot` или новом типизированном событии выстрела. | `tools/audio/recipes/weapons.json`, `docs/buildings/defense/`, `shared/events/world.ts` | ⏳ |
| 5.3 | `combat.defense.stakes` / `resin_snare` / `guardian_enclosure` / `automaton_bay`: короткий укол, вязкий хлопок ловушки, рычание/цепь стража и механический шаг/удар автомата; только фактическое срабатывание, а не нахождение монстра в радиусе. | `tools/audio/recipes/weapons.json`, `docs/buildings/defense/`, `shared/events/world.ts` | ⏳ |
| 5.4 | `combat.monster.aggro` / `attack` / `hit` / `death`: четыре функционально разных сигнала. Агро — короткое распознаваемое предупреждение один раз при входе в состояние; атака — в момент подтверждённого удара; получение урона — приглушённый импульс; смерть — короткий спад без длительной драматизации. | `tools/audio/recipes/monsters.json`, `frontend/src/features/world/realtime.ts`, `shared/events/monster.ts` | ⏳ |
| 5.5 | Тембры всех 8 типов монстров: налетчик — дыхание/кожа/металл; страж залежи — камень/жила; сторож руин — пыль/каменные пластины; лесной следопыт — ветви/шорох; споровый зверь — влажный пузырь/поры; железоспин — тяжёлый металл; тлеющий огонёк — воздушное потрескивание; древний колосс — низкий каменный раскол. Для каждого сделать вариант `aggro/attack/hit/death`, а шаги/idle — только где анимация и частота оправдывают их. | `tools/audio/recipes/monsters.json`, `shared/catalog/monsters.ts`, `frontend/src/game/` | ⏳ |
| 5.6 | `combat.monster.step` / `combat.monster.idle`: редкие пространственные слои с материалом из п. 5.5, привязка к видимой анимации шага/idle, расстояние и максимум голосов; массовому движению по WS не давать пачку шагов. | `tools/audio/recipes/monsters.json`, `frontend/src/game/renderer/`, `frontend/src/features/monster/MonsterSync.tsx` | ⏳ |
| 5.7 | `combat.player.attack` / `combat.player.hit` / `combat.loot.dropped` / `combat.loot.claimed`: резкий ручной удар, материал цели, падение трофея и мягкое получение; ручную атаку подтверждать ответом `attackMonster`, трофеи — `monster.loot.*`. Не дублировать звук попадания при последующем `monster.damaged`. | `tools/audio/recipes/combat.json`, `frontend/src/features/inspector/Inspector.tsx`, `shared/events/monster.ts` | ⏳ |
| 5.8 | `combat.threat.nearby` / `combat.raid.started` / `combat.victory` / `combat.retreat`: короткая тревога без непрерывной сирены, низкий удар рейда, умеренное завершение боя и спад при отступлении; тревоги адресовать владельцу и ограничивать, например одним повтором за 20–30 с на тип угрозы. | `tools/audio/recipes/alerts.json`, `frontend/src/features/threat/ThreatPanel.tsx`, `frontend/src/features/notifications/`, `shared/events/world.ts` | ⏳ |
| 5.9 | Настроить в бою правило плотности: одновременно не более 2–3 громких ударов, объединение однотипных попаданий за 80–150 мс, отдельный лимит шагов и защита высокоприоритетного сигнала от маскировки. При нескольких орудиях воспроизводить наиболее близкие и заметные события. | `frontend/src/audio/voiceManager.ts`, `frontend/src/audio/soundPolicy.ts` | ⏳ |

---

## Фаза 6 — Мир, социальные действия и атмосфера

| # | Что | Файлы | Статус |
|---|---|---|---|
| 6.1 | `world.forest.explore` / `world.forest.cut` / `world.ruin.discovered` / `world.ruin.captured`: листва и ветка, точный рубящий удар, сухая пыль с камнем и завершающий знак; воспроизводить по подтверждённым командам и видимому результату, без звука при простой загрузке тайла. | `tools/audio/recipes/world.json`, `frontend/src/features/world/forestActions.ts`, `shared/events/world.ts` | ⏳ |
| 6.2 | `world.territory.claimed` / `world.resource.discovered`: короткое закрепление флага и едва слышный блеск находки; локальный пространственный звук и персональный сигнал владельцу, если событие относится к нему. | `tools/audio/recipes/world.json`, `frontend/src/features/world/realtime.ts`, `shared/events/world.ts` | ⏳ |
| 6.3 | `social.chat.received` / `sent` / `mention`: тихий пузырёк/лист бумаги, приглушённая отправка, отдельный редкий акцент упоминания; не проигрывать свои сообщения дважды и дать выключить уведомления чата отдельно. | `tools/audio/recipes/social.json`, `frontend/src/features/chat/ChatPanel.tsx`, `shared/events/chat.ts` | ⏳ |
| 6.4 | `social.alliance.invite` / `accepted` / `declined` / `treasury`: бумажная печать приглашения, совместный двухнотный акцент, нейтральный отказ и монеты в общую казну; подтверждение через `alliance.*`, адресовать только участникам. | `tools/audio/recipes/social.json`, `frontend/src/features/alliance/AlliancePanel.tsx`, `shared/events/alliance.ts` | ⏳ |
| 6.5 | `ambience.grass` / `forest` / `river` / `mountain` / `ruins` / `town`: редкие короткие петли ветра, листвы, воды, горного воздуха, пыли и городской мастерской; плавное смешивание по видимому биому/масштабу камеры, без воспроизведения 6 петель сразу. Атмосферу оставить выключаемой отдельно от эффектов. | `tools/audio/recipes/ambience.json`, `frontend/src/audio/ambience.ts`, `frontend/src/game/state/useGameStore.ts` | ⏳ |
| 6.6 | `ambience.workshop` / `field` / `oil_well`: очень тихие локальные циклы работы механизмов, растений и насоса, только рядом с активной постройкой и в поле зрения; запуск/остановка с fade, максимум 1–2 петли каждого класса. | `tools/audio/recipes/ambience.json`, `frontend/src/audio/ambience.ts`, `shared/catalog/buildings.ts` | ⏳ |

---

## Фаза 7 — Клиентский аудиодвижок и подключение событий

| # | Что | Файлы | Статус |
|---|---|---|---|
| 7.1 | Создать типизированный manifest: `sound_id`, версии и пути файлов, варианты, шина, громкость, лимит одновременных голосов, cooldown, пространственность, приоритет, preload. Валидатор сверяет ссылки с собранными файлами и существующими `SoundEvent`. | `frontend/src/audio/soundManifest.ts`, `frontend/src/audio/soundEvents.ts`, `tools/audio/validate_audio.py` | ⏳ |
| 7.2 | Реализовать ленивый `AudioContext`, загрузку `fetch`/`decodeAudioData`, кеширование с ограничением памяти, `GainNode` шины `master/ui/world/alerts/ambience`, воспроизведение вариантов и безопасное завершение источников. Не создавать контекст при SSR/тестовом импорте. | `frontend/src/audio/AudioManager.ts`, `frontend/src/audio/audioGraph.ts` | ⏳ |
| 7.3 | Разблокировать звук первым пользовательским жестом через `resume`, сохранить намерение включения до разблокировки, показать ненавязчивый контроль звука, остановить/приглушить при скрытой вкладке и корректно восстановить после возврата. В браузерах проверять обещание `resume`, а не предполагать успех. | `frontend/src/audio/AudioProvider.tsx`, `frontend/src/app/`, `frontend/src/features/tools/ToolBar.tsx` | ⏳ |
| 7.4 | Добавить настройки `master`, `ui`, `world`, `alerts`, `ambience`, общий mute, отдельный чат, режим сниженной звуковой нагрузки; хранить локально по версии схемы, предусмотреть осмысленные значения по умолчанию и кнопку прослушивания каждой группы. | `frontend/src/audio/audioSettings.ts`, `frontend/src/features/settings/AudioSettings.tsx`, `frontend/src/game/state/useGameStore.ts` | ⏳ |
| 7.5 | Рассчитывать панораму и спад громкости по экранной/игровой дистанции от камеры, только для видимых мировых событий; учитывать масштаб, видимую область и циклическую карту при её появлении. Не панорамировать UI и персональные предупреждения. | `frontend/src/audio/spatialAudio.ts`, `frontend/src/game/coordinates/`, `frontend/src/game/state/useGameStore.ts` | ⏳ |
| 7.6 | Подписать один мост на `realtimeClient.onEvent`: фильтр `event_id` против повторов после reconnect, проверка получателя и видимости, преобразование типизированного payload в звуковое событие; звуковой мост не должен вызывать API и изменять authoritative state. | `frontend/src/audio/realtimeAudio.ts`, `frontend/src/shared/realtime/client.ts`, `frontend/src/features/world/WorldRealtime.tsx` | ⏳ |
| 7.7 | Привязать локальные UI-сигналы к общим компонентам и точечным действиям, а подтверждённые звуки к `onSuccess` mutations или WS. Для действия, видимого и через ответ, и через WS, выбрать ровно один источник либо дедуплицировать по action/event ID. | `frontend/src/shared/ui/`, `frontend/src/features/buildings/BuildMenu.tsx`, `frontend/src/features/inspector/Inspector.tsx`, `frontend/src/audio/actionAudio.ts` | ⏳ |
| 7.8 | При необходимости расширить `shared/events/world.ts`, `monster.ts` и серверный эмиттер причиной изменения, дельтой HP/ресурса, типом орудия, координатой и идентификатором действия; сохранять версию payload и совместимость клиента. Не передавать с клиента готовый урон или флаг «успех» как источник звука. | `shared/events/`, `backend/internal/service/events.go`, `backend/internal/service/combat.go`, `backend/internal/worker/simulation/` | ⏳ |
| 7.9 | Связать значимые звуки с анимациями: удар при контакте, выстрел в кадре запуска снаряда, сбор урожая при завершении жеста, смерть после подтверждения; при сетевой задержке допускается нейтральный звук нажатия до ответа, результат — после ответа. | `frontend/src/game/renderer/`, `frontend/src/features/fields/`, `frontend/src/audio/actionAudio.ts` | ⏳ |

---

## Фаза 8 — Проверка, наблюдаемость, выпуск и документация

| # | Что | Файлы | Статус |
|---|---|---|---|
| 8.1 | Автоматически проверять WAV/MP3: файл декодируется, частота/каналы ожидаемые, нет тишины вместо эффекта, клиппинга, обрезанного хвоста, слишком длинного короткого сигнала, повторяющихся имён и незарегистрированных файлов. Проверять суммарный и стартовый размер. | `tools/audio/validate_audio.py`, `frontend/scripts/check-asset-budget.mjs`, `frontend/package.json` | ⏳ |
| 8.2 | Unit-тесты маршрутизации: клик сразу, успех только после подтверждения, ошибка отдельно, WS replay не повторяет звук, изменение инвентаря при загрузке молчит, быстрые удары укладываются в лимит, дальние события не слышны, mute/громкость сохраняются. Мокать `AudioContext`, не сравнивать пиксели или форму волны с самим генератором. | `frontend/src/audio/*.test.ts`, `frontend/src/features/world/realtime.test.ts`, `frontend/src/features/buildings/BuildMenu.test.tsx` | ⏳ |
| 8.3 | Контрактные тесты для новых полей событий и причин результатов, если они понадобятся: backend публикует один значимый результат с координатой/типом и стабильным ID; клиент переносит старый payload без падения. | `backend/internal/service/*_test.go`, `shared/events/`, `frontend/src/audio/realtimeAudio.test.ts` | ⏳ |
| 8.4 | Ручной smoke на desktop и мобильном браузере: первый запуск до/после жеста, mute, скрытая вкладка, Safari/Chromium/Firefox, низкая скорость сети, повторное подключение WS, 20+ одновременных объектов, бой и сбор рядом с камерой. Отмечать слышимость и задержку, а не только факт загрузки файла. | `docs/audio/qa-checklist.md`, `frontend/src/audio/` | ⏳ |
| 8.5 | Прогнать `npm test`, `npm run lint`, `npm run build`, `npm run assets:budget` во frontend и нужные `go test` при изменении серверного контракта; добавить audio-валидацию в CI, не генерировать ассеты заново при обычном запуске браузера. | `frontend/package.json`, `.github/workflows/`, `Makefile` | ⏳ |
| 8.6 | Версионировать имена/manifest для долгого кеширования статики, проверить fallback при отсутствующем MP3 и корректное молчание при сбое, документировать процедуру отката пакета звуков вместе с версией клиента. | `frontend/public/assets/audio/`, `frontend/src/audio/soundManifest.ts`, `docs/operations/deploy.md` | ⏳ |
| 8.7 | Добавить в dev-панель состояние аудио, имя последнего эффекта, счётчик ограниченных голосов и ошибки декодирования; production-метрики вести агрегировано и без слежения за индивидуальными действиями. | `frontend/src/features/assets/AssetDebugPanel.tsx`, `frontend/src/audio/AudioManager.ts`, `docs/audio/production-guide.md` | ⏳ |
| 8.8 | Описать добавление нового звука от игрового события до рецепта, manifest, теста и проверки лицензии; приложить таблицу окончательных `sound_id`, путей, событий, приоритетов, настроек и известные ограничения браузеров. | `docs/audio/production-guide.md`, `docs/audio/event-matrix.md`, `docs/audio/asset-register.md` | ⏳ |

## Порядок зависимостей

```text
0. Матрица событий и правила звучания
   ├── 1. Инструменты и воспроизводимые ассеты
   │   ├── 2. Интерфейсные сигналы ───────────────┐
   │   ├── 3. Экономика и поля ────────────────────┤
   │   ├── 4. Строительство ───────────────────────┤
   │   ├── 5. Бой и монстры ───────────────────────┼── 7. Аудиодвижок и подключение событий ── 8. Приёмка, CI и выпуск
   │   └── 6. Мир, социальные действия, атмосфера ┘              ↑
   └── Уточнение серверных payload и причин событий (7.8) ───────┘

Первый слышимый релиз: 0 → 1 → 2 + 3.1–3.2 + 4.1–4.2 + 5.1/5.4 → 7.1–7.7 → 8.1–8.4.
Остальные эффекты подключаются пакетами по тем же правилам; окружающие петли — после устойчивой работы коротких сигналов.
```
