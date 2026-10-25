# Кандидаты на очистку проекта

Проверка выполнена 24 октября 2026 года. Размеры округлены; команды приведены для запуска из корня репозитория. **Ни одна команда из этого документа не выполнялась, файлы не удалялись.** Перед запуском выберите только те группы, которые больше не нужны для разработки или хранения истории моделей.

Под «отслеживается Git» ниже понимается наличие файла в текущем индексе. Удаление файла из рабочей директории само по себе не сокращает уже записанную историю Git. Команды `git rm` удаляют отслеживаемые файлы из рабочей директории и индекса; после коммита они перестанут входить в новые снимки репозитория. Переписывание истории здесь не предлагается.

## 1. Локальные сборки, зависимости и загрузки

| Путь | Размер | Git | Причина включения |
| --- | ---: | --- | --- |
| `frontend/dist/` | ~421 МБ | Игнорируется | Результат сборки Vite; пересоздаётся сборкой. |
| `frontend/node_modules/` | ~310 МБ | Игнорируется | Установленные зависимости; восстанавливаются менеджером пакетов. |
| `.cache/` | ~77 МБ | Игнорируется | Кеш инструментов, в основном загруженный FFmpeg для аудио. |
| `blender-5.2.2-linux-x64/` | ~1,2 ГБ | Не отслеживается | Локально распакованный Blender. В проекте не найдено ссылок на этот конкретный путь. Удалять, если Blender доступен другим способом или больше не нужен. |
| `blender-5.2.2-linux-x64.tar.xz` | ~366 МБ | Игнорируется | Скачанный архив Blender. |
| `index.html`, `index.html.1` | ~161 КБ | Не отслеживаются | Сохранённые страницы сайта Blender; это не `frontend/index.html`. |

```bash
rm -rf -- frontend/dist frontend/node_modules .cache
rm -rf -- blender-5.2.2-linux-x64
rm -- blender-5.2.2-linux-x64.tar.xz index.html index.html.1
```

## 2. Пробные сборки моделей

Эти каталоги не упоминаются в игровом реестре ассетов. Некоторые используются только скриптами генерации прототипов или упоминаются в документации как промежуточные варианты. Все перечисленные здесь файлы не отслеживаются Git.

| Путь | Размер | Примечание |
| --- | ---: | --- |
| `frontend/public/assets/buildings/housing/villa_test/` | ~4,4 МБ | Ранний прототип виллы. |
| `frontend/public/assets/buildings/housing/villa_v2_test/` | ~4,4 МБ | Второй ранний прототип виллы. |
| `frontend/public/assets/buildings/housing/villa_levels_test/` | ~18,9 МБ | Тест уровней виллы. Из него 16 файлов на ~16,6 МБ побайтно совпадают с файлами рабочей `villa/`; остальные содержат мастер-модели и отчёты прототипа. |

```bash
rm -rf -- \
  frontend/public/assets/buildings/housing/villa_test \
  frontend/public/assets/buildings/housing/villa_v2_test \
  frontend/public/assets/buildings/housing/villa_levels_test
```

## 3. Резервные копии Blender

Файлы `.blend1` и `.blend2` в каталогах ассетов занимают суммарно ~61 МБ, не отслеживаются Git и не являются игровыми файлами. Это резервные версии мастер-сцен. Их удаление лишит возможности вернуться к соответствующим версиям через файловую систему.

Сначала вывести список:

```bash
find frontend/public/assets frontend/src/assets -type f \
  \( -name '*.blend1' -o -name '*.blend2' \) -print
```

Если список подходит:

```bash
find frontend/public/assets frontend/src/assets -type f \
  \( -name '*.blend1' -o -name '*.blend2' \) -delete
```

Основные отдельные копии: `reed_bed_l01_l10.blend1` (~9,2 МБ), `mushroom_grove_l01_l10.blend1` (~7,3 МБ), `paper_workshop_levels.blend1` (~4,3 МБ), `dye_garden_levels.blend1` (~4,1 МБ), `concrete_plant_levels.blend1` (~3,9 МБ) и `cement_workshop_levels.blend1` (~3,8 МБ).

## 4. Старые каталоги и резервные варианты ассетов

Это наиболее заметные кандидаты, **уже содержащие отслеживаемые Git файлы**. В общей сложности они занимают около 138 МБ на диске, из них около 34 МБ — отслеживаемые файлы. Некоторые содержат игнорируемые `.blend` и `.glb`, поэтому после `git rm` могут остаться файлы на диске.

| Путь | Всего | В Git | Примечание |
| --- | ---: | ---: | --- |
| `frontend/public/assets/resources/icons.backup-20260927-pre-midpoly-regen/` | ~9,5 МБ | ~3,4 МБ | Копия иконок до перегенерации; игра использует `resources/icons/`. |
| `frontend/public/assets/buildings/housing/wood_house_component_pilot/` | ~0,8 МБ | ~0,1 МБ | Пилот компонентной модели; игровая постройка использует `wood_house/`. |
| `frontend/public/assets/buildings/industry/oil_well/backup_2026-10-14_pre_remove_side_rods/` | ~6,5 МБ | 0 | Старый вариант нефтяной скважины. |
| `frontend/public/assets/buildings/industry/oil_well/backup_2026-10-14_pre_oil_pit_pumpjack_fence_rework/` | ~4,9 МБ | ~1,7 МБ | Старый вариант нефтяной скважины. |
| `frontend/public/assets/buildings/industry/oil_well/backup_2026-10-14_pre_straight_rods_rework/` | ~6,3 МБ | 0 | Старый вариант нефтяной скважины. |
| `frontend/public/assets/buildings/industry/oil_well/backup_2026-10-14_pre_style_regen/` | ~2,8 МБ | ~1,3 МБ | Старый вариант нефтяной скважины. |
| `frontend/public/assets/buildings/industry/mine/backup_2026-10-14_pre_l01_state_replacement/` | ~0,7 МБ | ~0,1 МБ | Копия старых состояний шахты. |
| `frontend/public/assets/buildings/industry/mine/backup_2026-10-14_pre_mountain_detail_runtime/` | ~52,3 МБ | ~4,1 МБ | Копия ассетов шахты до текущего варианта. |
| `frontend/public/assets/terrain/tiles/mountain_detail_staging/backup_2026-10-13_massive_blocked_entrance/` | ~15,7 МБ | ~7,0 МБ | Старый вариант гор и шахты. |
| `frontend/public/assets/terrain/tiles/mountain_detail_staging/backup_2026-10-13_massive_open_entrance_v1/` | ~17,6 МБ | ~7,1 МБ | Старый вариант гор и шахты. |
| `frontend/public/assets/terrain/tiles/mountain_detail_staging/backup_2026-10-13_thicker_v1/` | ~1,5 МБ | ~0,8 МБ | Старый вариант гор. |
| `frontend/public/assets/terrain/tiles/mountain_detail_staging/backup_2026-10-14_massive_sharper_v1/` | ~18,7 МБ | ~7,3 МБ | Старый вариант гор и шахты. |

Выберите нужные строки в массиве `candidates`, затем запустите команды. `git rm` обработает отслеживаемые файлы, а `rm -rf` — оставшиеся игнорируемые файлы в выбранных каталогах.

```bash
candidates=(
  frontend/public/assets/resources/icons.backup-20260927-pre-midpoly-regen
  frontend/public/assets/buildings/housing/wood_house_component_pilot
  frontend/public/assets/buildings/industry/oil_well/backup_2026-10-14_pre_remove_side_rods
  frontend/public/assets/buildings/industry/oil_well/backup_2026-10-14_pre_oil_pit_pumpjack_fence_rework
  frontend/public/assets/buildings/industry/oil_well/backup_2026-10-14_pre_straight_rods_rework
  frontend/public/assets/buildings/industry/oil_well/backup_2026-10-14_pre_style_regen
  frontend/public/assets/buildings/industry/mine/backup_2026-10-14_pre_l01_state_replacement
  frontend/public/assets/buildings/industry/mine/backup_2026-10-14_pre_mountain_detail_runtime
  frontend/public/assets/terrain/tiles/mountain_detail_staging/backup_2026-10-13_massive_blocked_entrance
  frontend/public/assets/terrain/tiles/mountain_detail_staging/backup_2026-10-13_massive_open_entrance_v1
  frontend/public/assets/terrain/tiles/mountain_detail_staging/backup_2026-10-13_thicker_v1
  frontend/public/assets/terrain/tiles/mountain_detail_staging/backup_2026-10-14_massive_sharper_v1
)
git rm -r --ignore-unmatch -- "${candidates[@]}"
rm -rf -- "${candidates[@]}"
```

Каталог `stone_house_component_pilot/` уже отсутствует в рабочей директории: его файлы помечены к удалению в текущем состоянии Git. Дополнительная команда для удаления с диска не требуется.

## 5. Проверочные изображения

Проверочные листы и изображения с `review` или `contact_sheet` в названии не загружаются игровым интерфейсом. Они нужны для визуальной проверки моделей и могут создаваться валидаторами. В Git отслеживается примерно **31 файл / 39,6 МБ** в `frontend/public/assets/buildings/`, **8 файлов / 4,1 МБ** в `terrain/` и **8 файлов / 3,0 МБ** в `resources/`. Среди самых крупных — обзоры `flax_field`, `mushroom_grove`, `seed_garden`, `reed_bed`, `herb_bed` и `oilseed_field` размером около 3–5,6 МБ каждый. Удалять эту группу имеет смысл только после решения, что визуальная история не нужна в репозитории.

Предварительный просмотр **отслеживаемых** кандидатов:

```bash
git ls-files -z -- \
  frontend/public/assets/buildings \
  frontend/public/assets/terrain \
  frontend/public/assets/resources |
  python3 -c 'import sys; paths=sys.stdin.buffer.read().split(b"\0"); selected=[p for p in paths if p.lower().endswith(b".png") and (b"review" in p.lower() or b"contact_sheet" in p.lower())]; sys.stdout.buffer.write(b"\0".join(selected)+(b"\0" if selected else b""))' |
  xargs -0 -r -n1 printf '%s\n'
```

Команда удаления такого же набора:

```bash
git ls-files -z -- \
  frontend/public/assets/buildings \
  frontend/public/assets/terrain \
  frontend/public/assets/resources |
  python3 -c 'import sys; paths=sys.stdin.buffer.read().split(b"\0"); selected=[p for p in paths if p.lower().endswith(b".png") and (b"review" in p.lower() or b"contact_sheet" in p.lower())]; sys.stdout.buffer.write(b"\0".join(selected)+(b"\0" if selected else b""))' |
  xargs -0 -r git rm --
```

Отдельный крупный документальный результат — `docs/assets/component-library-showcase.png` (~5,6 МБ). Это проверочное изображение, а не игровой ассет; оно упоминается в `docs/assets/component-library-showcase-report.json`. Если иллюстрация больше не нужна: `git rm -- docs/assets/component-library-showcase.png`.

## 6. Справочные анимации оригинальной игры

`reference/buildings/original-assets/animations/` занимает ~513 МБ и игнорируется Git. Ссылок на файлы анимации в коде, инструментах и Markdown не найдено. Это кандидат **только если исходный исследовательский материал больше не нужен**. Другие части `reference/` используются в проектной документации как визуальные ориентиры.

```bash
rm -rf -- reference/buildings/original-assets/animations
```

## Не включено в команды удаления

- Весь каталог `frontend/public/assets/terrain/tiles/mountain_detail_staging/`: `mountain_detail_ridge.png`, `mountain_detail_spire.png` и `mountain_detail_snowcap.png` загружаются картой. Удалять можно только явно выбранные старые подпапки.
- Все `.glb` или все `.blend` сразу: `.glb` используются для просмотра 3D-моделей в разработке, а модели каменного дома и виллы подключены к игровой сборке; `.blend` служат редактируемыми мастер-сценами и проверяются валидаторами.
- `frontend/public/assets/buildings/housing/villa/`, `stone_house/`, действующие PNG построек, атласы монстров, иконки ресурсов и текущие аудиофайлы: на них есть ссылки из игрового кода.
- `.git/`: его текущий размер около 573 МБ связан с историей Git. Обычные команды удаления файлов не удалят старые объекты из истории.
