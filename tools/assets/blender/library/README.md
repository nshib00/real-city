# Real City Blender Source Library

Эта директория зарезервирована для сложных reusable collections, которые
нельзя разумно описать Python-фабриками.

На фазе 3 библиотека компонентов реализована кодом в
`tools/assets/blender/real_city/components/`, поэтому файл
`real_city_components.blend` пока не создается. Когда появится ручная `.blend`
библиотека, она должна:

- использовать версию component API из `components/__init__.py`;
- не менять уже опубликованные collection names без новой версии;
- иметь короткий manifest в этом каталоге;
- проходить roundtrip-импорт в Blender перед использованием генераторами.
