# Лесопильный двор

Внутренний id: `lumber_yard`.

Генератор:

```bash
blender --background --python tools/assets/blender/generate_lumber_yard_models.py
```

Ожидаемые артефакты:

- `frontend/public/assets/buildings/industry/lumber_yard/lumber_yard_levels.blend`;
- `frontend/public/assets/buildings/industry/lumber_yard/lumber_yard_levels.glb`;
- `frontend/public/assets/buildings/industry/lumber_yard/lumber_yard_l01_active.glb`;
- `frontend/public/assets/buildings/industry/lumber_yard/lumber_yard_l01_construction.glb`;
- `frontend/public/assets/buildings/industry/lumber_yard/lumber_yard_l01_damaged.glb`.

Каталог сейчас задает один уровень лесопилки (`level: 1`, `footprint: 1x1`, без `upgradeTo`), поэтому генератор создает уровень `l01` в трех состояниях.

Образ: светлый фентезийный лесопильный двор Эолии с открытым навесом, круглой пилой, краном, штабелями бревен и досок, инструментами и теплым фонарем. Состояние стройки добавляет леса, временный тент и балки; поврежденное состояние сохраняет силуэт, но показывает обугленную землю, пробитую крышу, дым и погнутую пилу.

Игра подключает эти модели по public URL. Пока `.glb` не сгенерированы, остается CSS fallback старой иконки здания.
