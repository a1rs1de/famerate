// After Effects ExtendScript: пересборка ролика "Голос Толи за 30 секунд" (1080x1920, 30 fps, 23.3 c)
// Запуск: File > Scripts > Run Script File... , затем выбрать этот файл.
// 1) Впиши пути к своим исходникам в SRC (оставь "" — будет placeholder-слой).
// 2) Скрипт создаст композицию, слои, субтитры, анимации и тайминги как в оригинале.

var SRC = {
    gameBg:      "",  // геймплей КС (фон интро, 0–3 c)
    person:      "",  // видео/фото автора (вылезает сверху, 2–8 c)
    tiktokProf:  "",  // скрин профиля TikTok
    siteBlur:    "",  // скрин сайта (будет размыт на 4–7 c)
    siteLib:     "",  // экран записи: библиотека голосов
    siteReg:     "",  // экран записи: регистрация
    siteText:    "",  // экран записи: поле ввода текста
    example:     "",  // пример реализации (геймплей + аватар)
    music:       ""   // звук/озвучка (опционально)
};

var W = 1080, H = 1920, FPS = 30, DUR = 23.3;
var FONT = "Montserrat-ExtraBold";
var HANDLE = "@vampnotvfx";

app.beginUndoGroup("Build Toly voice reel");
var comp = app.project.items.addComp("Toly_Voice_Reel", W, H, 1, DUR, FPS);
comp.bgColor = [0.04, 0.04, 0.07];

function footage(path, name, t0, t1, fill) {
    var layer;
    if (path && File(path).exists) {
        var item = app.project.importFile(new ImportOptions(File(path)));
        layer = comp.layers.add(item);
        var s = Math.max(W / layer.width, H / layer.height) * 100;
        if (!fill) s = Math.min(W / layer.width, H / layer.height) * 100;
        layer.property("Scale").setValue([s, s]);
    } else {
        layer = comp.layers.addSolid(fill ? [0.15, 0.1, 0.25] : [0.2, 0.2, 0.3], "PLACEHOLDER " + name, W, H, 1);
    }
    layer.name = name;
    layer.startTime = t0;
    layer.inPoint = t0;
    layer.outPoint = t1;
    return layer;
}

function popIn(layer, t) {            // быстрый "поп" появления
    var sc = layer.property("Scale");
    var v = sc.value[0];
    sc.setValuesAtTimes([t, t + 0.12, t + 0.22], [[v * 0.6, v * 0.6], [v * 1.08, v * 1.08], [v, v]]);
    layer.property("Opacity").setValuesAtTimes([t, t + 0.08], [0, 100]);
}

function caption(txt, t0, t1, yPos, color, size) {
    var l = comp.layers.addText(txt);
    var tp = l.property("Source Text");
    var d = tp.value;
    d.fontSize = size || 80; d.fillColor = color || [1, 1, 1];
    d.applyStroke = true; d.strokeColor = [0, 0, 0]; d.strokeWidth = 8; d.strokeOverFill = false;
    d.justification = ParagraphJustification.CENTER_JUSTIFY;
    try { d.font = FONT; } catch (e) {}
    tp.setValue(d);
    l.property("Position").setValue([W / 2, yPos || 1450]);
    l.inPoint = t0; l.outPoint = t1; l.name = "CAP: " + txt;
    popIn(l, t0);
    var sh = l.property("Effects").addProperty("ADBE Drop Shadow");
    sh.property("Opacity").setValue(180); sh.property("Distance").setValue(8); sh.property("Softness").setValue(20);
    return l;
}

// ===== СЦЕНЫ =====
// 0–3 c: интро, геймплей с красной виньеткой
var bg = footage(SRC.gameBg, "Intro gameplay", 0, 3, true);
var vig = comp.layers.addSolid([0.45, 0.02, 0.02], "Red vignette", W, H, 1);
vig.inPoint = 0; vig.outPoint = 3; vig.blendingMode = BlendingMode.MULTIPLY; vig.opacity.setValue(70);
var ar = bg.property("Scale"); var s0 = ar.value[0];
ar.setValuesAtTimes([0, 3], [[s0, s0], [s0 * 1.12, s0 * 1.12]]);  // медленный зум

caption("ГОЛОС ТОЛИ", 0, 1, 1450, [1, 1, 1], 130);
caption("ЗА", 1, 2, 1450, [1, 1, 1], 130);
caption("30 СЕКУНД", 2, 3, 1450, [1, 0.85, 0.1], 130);

// 3–4 c: профиль TikTok
footage(SRC.tiktokProf, "TikTok profile", 3, 4.2, false);
caption("в шапке профиля", 3, 4.2, 1500, [1, 1, 1], 70);

// 4–7 c: сайт под блюром + автор сверху (ч/б)
var blur = footage(SRC.siteBlur, "Site blurred", 4.2, 7, true);
var gb = blur.property("Effects").addProperty("ADBE Gaussian Blur 2"); gb.property("Blurriness").setValue(40);
var per = footage(SRC.person, "Author (B/W)", 2, 8, false);
per.property("Position").setValue([W / 2, 380]);
per.property("Effects").addProperty("ADBE Black&White");
per.inPoint = 2; per.outPoint = 8;
per.property("Position").setValuesAtTimes([2, 2.4, 2.6], [[W / 2, -200], [W / 2, 420], [W / 2, 380]]);
caption("заходим в мой", 4.2, 5.2, 1500, [1, 1, 1], 70);
caption("телеграм канал", 5.2, 7.2, 1500, [1, 1, 1], 70);

// 7–11 c: запись экрана сервиса
footage(SRC.siteLib, "Screen: library", 7.2, 8.4, true);
caption("и переходим уже", 7.2, 8.4, 1500, [1, 1, 1], 70);
footage(SRC.siteReg, "Screen: registration", 8.4, 11.2, true);
caption("на готовую ссылку", 8.4, 9.4, 1500, [1, 1, 1], 70);
caption("регистрируйся", 9.4, 10.4, 1500, [1, 1, 1], 70);
caption("и в пустом поле", 10.4, 11.2, 1500, [1, 1, 1], 70);

// 11–15.3 c: ввод текста
var txt = footage(SRC.siteText, "Screen: text input", 11.2, 15.3, true);
caption("снизу убедившись", 11.2, 12.5, 1500, [1, 1, 1], 70);
caption("что модель выбрана", 12.5, 13.8, 1500, [1, 1, 1], 70);
caption("вводи че захочешь", 13.8, 15.3, 1500, [1, 1, 1], 70);

// 15.3–19 c: пример реализации
footage(SRC.example, "Example", 15.3, 19, false);
var box = caption("ТОЛИ САМЕР ВТОРОЙ РАЗ\nИГРАЕТ В КС", 15.3, 19, 300, [0, 0, 0], 60);
var plate = comp.layers.addSolid([1, 1, 1], "Title plate", 900, 190, 1);
plate.property("Position").setValue([W / 2, 300]); plate.inPoint = 15.3; plate.outPoint = 19;
plate.moveAfter(box);
caption("пример реализации", 15.3, 19, 1650, [1, 1, 1], 70);

// 19–23.3 c: аутро TikTok
var out = comp.layers.addSolid([0.05, 0.05, 0.1], "Outro BG", W, H, 1);
out.inPoint = 19; out.outPoint = DUR;
caption("TikTok", 19, DUR, 800, [1, 1, 1], 120);
var bar = comp.layers.addSolid([1, 1, 1], "Search bar", 640, 90, 1);
bar.property("Position").setValue([W / 2, 1000]); bar.inPoint = 19.5; bar.outPoint = DUR;
popIn(bar, 19.5);
caption(HANDLE, 19.8, DUR, 1000, [0, 0, 0], 44);

// звук
if (SRC.music && File(SRC.music).exists) {
    var m = comp.layers.add(app.project.importFile(new ImportOptions(File(SRC.music))));
    m.name = "Audio";
}

// водяной знак TikTok на всём ролике (кроме аутро)
var wm = comp.layers.addText("TikTok  " + HANDLE);
wm.inPoint = 0; wm.outPoint = 19; wm.property("Position").setValue([140, 1100]); wm.opacity.setValue(70);
wm.name = "Watermark";

comp.openInViewer();
app.endUndoGroup();
alert("Готово. Композиция Toly_Voice_Reel создана. Подставь пути в SRC и перезапусти для реальных исходников.");
