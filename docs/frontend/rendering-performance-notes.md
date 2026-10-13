# Performance Notes Для Карты

Документ фиксирует базовую методику проверки Pixi object layer после переноса построек, ресурсов и монстров из массового DOM-рендера.

## Dev-Сценарии

Нагрузочные сценарии включаются только в dev-сборке через query-параметр `perf`.

| URL | Назначение |
| --- | --- |
| `/?perf=buildings` | Много fake-построек, небольшой фон монстров и ресурсов |
| `/?perf=monsters` | Много анимированных монстров, умеренное число построек |
| `/?perf=mixed` | Смешанная карта: постройки, ресурсы, монстры и fake-тайлы |

Количество объектов можно переопределить параметрами:

- `perfBuildings=2600` - число построек;
- `perfMonsters=720` - число монстров;
- `perfResources=260` - число ресурсных узлов;
- `perfTileRadius=34` - радиус fake-тайлов вокруг центра.

Пример для desktop-проверки:

```text
http://localhost:5173/?perf=mixed&perfBuildings=2600&perfMonsters=720&perfResources=260&perfTileRadius=34
```

## Что Показывает HUD

В правом нижнем углу карты появляется `Performance HUD`.

Поля:

- `fps` - rolling FPS Pixi ticker за короткое окно;
- `obj` - видимые постройки, ресурсы и монстры;
- `heap` - `usedJSHeapSize`, если браузер поддерживает `performance.memory`;
- `gl` - активные Pixi-контексты плюс активные Three preview.

Ожидаемая базовая проверка:

1. Открыть desktop viewport около `1440x900`.
2. Проверить `/?perf=mixed&perfBuildings=2600&perfMonsters=720&perfResources=260`.
3. Несколько раз выполнить pan/zoom карты.
4. Переключиться между `perf=buildings`, `perf=monsters`, `perf=mixed`.
5. Убедиться, что `gl` остается стабильным: обычно `1+0`, если не открыт 3D preview.
6. Убедиться, что heap после pan/zoom и смены сценариев не растет монотонно без стабилизации.
7. Зафиксировать FPS и память в заметках к PR или задаче.

## Автоматические Проверки

Unit/integration:

```bash
npm --prefix frontend run test -- --run src/game/dev/performanceScenarios.test.ts src/game/renderer/renderPerformanceMetrics.test.ts src/game/IsoMap.interaction.test.tsx
```

E2E smoke для nonblank Pixi canvas лежит в `frontend/tests/e2e/pixi-canvas.spec.ts`. Сейчас `@playwright/test` не подключен в `frontend/package.json`, поэтому файл является готовым контрактом для будущего e2e-раннера и не входит в Vitest.

## Текущий Baseline

- Массовые постройки, ресурсы и монстры передаются в Pixi object layer, а DOM остается только для интерактивных оверлеев и неподдержанных объектов.
- GLB/Three не используется на карте и включается только в ограниченных preview-слотах.
- Pixi stage регистрирует активный контекст и rolling FPS; это позволяет ловить рост контекстов после mount/unmount и смены сценариев.
- Нагрузочные fake-объекты генерируются детерминированно и не пишутся в Zustand-store, серверные данные или пользовательское состояние.
