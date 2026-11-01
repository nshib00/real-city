# Браузерные материалы приёмки

Параметры, исправления и ограничения: [отчёт](../../../../frontend/interface-browser-review.md). [Манифест файлов](manifest.json) создаётся сборщиком после проверок. API изолирован; это снимки настоящего интерфейса с проектными ассетами, а не live-server E2E.

| Материал | Снимок |
|---|---|
| Игровой экран desktop | [1440 px, DPR 1](1440-dpr1/interface/world.png) |
| Игровой экран mobile | [390 px, DPR 2](390-dpr2/interface/world.png) |
| Landscape | [844×390](landscape/interface/world.png) |
| Своя и чужая постройка | [Своя](1440-dpr1/objects/own-building.png), [чужая](1440-dpr1/objects/foreign-building.png) |
| Предпросмотр | [Размещение](1440-dpr1/objects/placement.png), [недопустимый тайл](1440-dpr1/objects/placement-invalid.png) |
| Шрифт 200% | [Профиль](390-dpr2/interface/text-200-profile.png) |
| Сломанная иконка | [Fallback](390-dpr2/interface/resource-fallback.png) |
| Пилот знаков | [Без подписей](1440-dpr1/icons/pilot-without-labels.png), [с подписями](1440-dpr1/icons/pilot-with-labels.png) |
| Цветовое зрение | [Протанопия](1440-dpr1/vision/protanopia.png), [дейтеранопия](1440-dpr1/vision/deuteranopia.png), [тританопия](1440-dpr1/vision/tritanopia.png) |

В каталогах каждого размера находятся JSON измерений контраста и снимки панелей. Полные большие листы иконок для двух DPR и масштабов 100/200% остаются в локальном `frontend/review-results/`, чтобы не дублировать их в документации. Реальное устройство и независимая проверка экранным диктором не подменяются эмуляцией.
