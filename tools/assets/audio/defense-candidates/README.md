# Кандидаты звуков обороны

Звуки собраны для прослушивания и подбора эффектов к выстрелам оборонительных сооружений. Пока они не подключены к игровой аудиосистеме.

| Сооружение | Файл | Источник | Длительность |
| --- | --- | --- | ---: |
| Пушка (`combat.weapon.cannon`) | `defense-cannon-shot-shatter-explosion.wav` | [Shatter shot explosion, ID 1693](https://mixkit.co/free-sound-effects/shot/) | 2,95 с |
| Пушка (`combat.weapon.cannon`), короткий вариант | `defense-cannon-cannon-fire.wav` | [Battle at sea, cannon_fire.ogg](https://opengameart.org/content/battle-at-sea) — CC0 | 2,95 с |
| Болтомёт (`combat.weapon.bolt_thrower`) | `defense-bolt-thrower-arrow-shot.wav` | [Arrow shot through air, ID 2771](https://mixkit.co/free-sound-effects/shot/) | 1,04 с |
| Болтомёт (`combat.weapon.bolt_thrower`), арбалетный вариант | `defense-bolt-thrower-crossbow-shot.wav` | [Crossbow sounds](https://opengameart.org/content/crossbow-sounds), HolgiB — CC-BY 3.0 / GPL 2.0 | 0,58 с |
| Башня (`combat.weapon.tower`) | `tower-arrow-whizz.wav` | [Arrow whizz in battle, ID 2767](https://mixkit.co/free-sound-effects/medieval-battle/) | 1,26 с |
| Электрическая катушка (`combat.weapon.storm_coil`) | `defense-storm-coil-lightning-whip.wav` | [Lightning whip, ID 1508](https://mixkit.co/free-sound-effects/lightning/) | 0,82 с |

Кандидаты скачаны в WAV и оставлены вне `frontend/public`, поэтому они не попадают в сборку игры автоматически. Для арбалетного эффекта автор — HolgiB; страница OpenGameArt указывает лицензии CC-BY 3.0 и GPL 2.0. Пушечный `cannon_fire.ogg` опубликован под CC0. Эффект пушки сокращён до 2,95 с, чтобы он был сопоставим по длине с текущим тестовым вариантом.

Звуки Mixkit можно использовать в игровых и коммерческих проектах по [лицензии Mixkit Free Sound Effects](https://mixkit.co/license/modal/sfxFree/), но нельзя распространять оригинальные файлы отдельно или вместе с исходниками. Перед передачей их в игровой билд нужно включить в конечный продукт. Идентификаторы и страницы источников сохранены для сверки.
