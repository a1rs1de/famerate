# Стиль текста (по референсу)
- Заголовок хука («ГОЛОС», «толисаммера», «20 СЕКУНД»): Unbounded Black, толстый тёмный контур, у цветных слов deep glow (голубой #27c7e6, жёлтый #ffd92e / glow #ffb800).
- Субтитры внизу: Montserrat ExtraBold, белый, трекинг -2%, лёгкое белое свечение.
- Шрифт референса: Druk Wide Bold (fonts/DrukWideBold.ttf). В присланном файле НЕТ кириллицы -> для русских слов запасной шрифт; нужен Druk Wide Cyr.
- Реализация: textfx.py (render(...) -> RGBA PNG, автоподгонка max_width). Превью: frames/style_preview.png, frames/style_fit.png.
- Шрифты: fonts/*.ttf (OFL, Google Fonts) — приближение к шрифту референса, оригинал точно не определён.
# Исходники
- gameplay1/2.mp4 — запись браузера с YouTube-плеером. Для хука кроп плеера (gameplay2: x294 y178 w1318 h740 из 1920x1080), в gameplay1 внутри плеера чёрные полосы по бокам.
