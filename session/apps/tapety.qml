// SPDX-License-Identifier: GPL-3.0-or-later
// LatteOS — Tapety: živé a statické tapety (integrácia projektu Aura, https://github.com/antwny/aura, GPL-3.0).
//   Knižnica   videá a obrázky z priečinkov knižnice s náhľadmi; klik = nastaviť, pravý klik = ponuka, ★ obľúbené
//   Objavovať  MotionBGS (živé 4K/HD), Wallhaven (4K/8K), Bing (denná fotka a archív), Minimalistické; hľadanie,
//              kategórie, stiahnutie s priebehom rovno do knižnice
//   Obrazovky  každá obrazovka vlastnú tapetu a mierku (vyplniť / prispôsobiť / roztiahnuť)
//   Nastavenia automatická pauza (zakryté / maximalizované / celá obrazovka = 0 % v hrách), batéria, zvuk,
//              striedanie tapiet, farby témy z tapety, priečinky knižnice
// Backend: latte-tapety (mpvpaper). Živé video iba s grafickou akceleráciou; obrázky vždy (tapeta Noctalie).
// Spúšťa sa: latte-app tapety [kniznica|objavovat|obrazovky|nastavenia]
import QtQuick
import Quickshell
import Quickshell.Io
import "common"

ShellRoot {
    id: app
    LatteTheme { id: theme }
    property string page: ["kniznica", "objavovat", "obrazovky", "nastavenia"].indexOf((Quickshell.env("LATTE_APP_ARGS") || "").trim()) >= 0 ? (Quickshell.env("LATTE_APP_ARGS") || "").trim() : "kniznica"
    property var lib: []
    property var st: ({ vystupy: {}, nastavenia: {}, gpu: false, engine: false })
    property var outs: []
    property string status: ""
    property string filter: ""

    component Q: Process {
        id: q
        signal done(string out, int code)
        property int parts: 0
        property string out: ""
        property int code: 0
        onRunningChanged: if (running) parts = 0
        stdout: StdioCollector { onStreamFinished: { q.out = this.text; if (++q.parts === 2) q.done(q.out, q.code); } }
        onExited: (c) => { q.code = c; if (++q.parts === 2) q.done(q.out, q.code); }
    }
    Q { id: libProc; command: ["latte-tapety", "kniznica"]; onDone: (o) => { try { app.lib = JSON.parse(o); } catch (e) {} app.nextThumb(); } }
    Q { id: stProc; command: ["latte-tapety", "stav"]; onDone: (o) => { try { app.st = JSON.parse(o); } catch (e) {} } }
    Q { id: outProc; command: ["latte-tapety", "vystupy"]; onDone: (o) => { try { app.outs = JSON.parse(o); } catch (e) {} } }
    Q { id: act; onDone: (o, c) => { app.status = o.trim().replace(/^OK$/, "Hotovo").replace(/^E /, "⚠ "); stProc.running = true; } }
    function run(args, msg) { status = msg || ""; act.command = ["latte-tapety"].concat(args); act.running = true; }
    // náhľady: po jednom (ffmpeg), aby knižnica ostala svižná
    Q { id: thumbProc; property string path: ""
        onDone: (o) => { const t = o.trim(); if (t) { const l = app.lib.slice(); const i = l.findIndex(x => x.path === thumbProc.path); if (i >= 0) { l[i] = Object.assign({}, l[i], { thumb: t }); app.lib = l; } } app.nextThumb(); } }
    function nextThumb() {
        if (thumbProc.running) return;
        const x = lib.find(i => !i.thumb && !i.noThumb);
        if (!x) return;
        const l = lib.slice(); l[l.indexOf(x)] = Object.assign({}, x, { noThumb: true }); lib = l;
        thumbProc.path = x.path; thumbProc.command = ["latte-tapety", "nahlad", x.path]; thumbProc.running = true;
    }
    Component.onCompleted: { libProc.running = true; stProc.running = true; outProc.running = true; }
    readonly property var cur: { const v = st.vystupy || {}; const k = Object.keys(v); return k.length ? v[k[0]] : null; }
    function isFav(p) { return ((st.nastavenia || {}).oblubene || []).indexOf(p) >= 0; }
    function human(b) { const u = ["B", "KB", "MB", "GB"]; let v = b || 0, i = 0; while (v >= 1024 && i < 3) { v /= 1024; i++; } return v.toFixed(i ? 1 : 0).replace(".", ",") + " " + u[i]; }
    function setWall(item, out) {
        if (item.video && !st.gpu) { status = "⚠ Živé video potrebuje grafickú akceleráciu (vo VM sa kreslí softvérovo). Na reálnom PC sa spustí samo."; return; }
        run(["nastav", item.path].concat(out ? ["--vystup", out] : []), "Nastavujem " + item.name + "…");
    }

    // ── Objavovať (online katalógy) ──
    property string src: "motionbgs"
    property string cat: "all"
    property string query: ""
    property string res: "hd"
    property string sort: "toplist"
    property int pageNo: 1
    property var online: []
    property string onlineErr: ""
    property var downloads: ({})          // url → percento (-1 = beží bez veľkosti)
    Q { id: onProc; onDone: (o) => { try { const d = JSON.parse(o); app.online = app.pageNo > 1 ? app.online.concat(d.items) : d.items; app.onlineErr = d.error; } catch (e) { app.onlineErr = "katalóg sa nedá načítať"; } } }
    function loadOnline(more) {
        pageNo = more ? pageNo + 1 : 1;
        if (!more) online = [];
        onProc.command = ["latte-tapety", "online", src, "--strana", String(pageNo), "--rozlisenie", res, "--triedenie", sort]
                         .concat(query ? ["--hladaj", query] : []).concat(cat !== "all" ? ["--kategoria", cat] : []);
        onProc.running = true;
    }
    onPageChanged: if (page === "objavovat" && online.length === 0 && !onProc.running) loadOnline(false)
    readonly property var cats: ({
        motionbgs: [["all", "Všetko"], ["anime", "Anime"], ["nature", "Príroda"], ["games", "Hry"], ["space", "Vesmír"], ["fantasy", "Fantasy"],
                    ["car", "Autá"], ["superhero", "Superhrdinovia"], ["technology", "Technológie"]],
        wallhaven: [["111", "Všetko"], ["100", "Všeobecné"], ["010", "Anime"], ["110", "Všeobecné + anime"]],
        bing: [], minimal: [] })
    Component {
        id: dlComp
        Q {
            id: dl
            property string url: ""
            stdout: SplitParser { onRead: (l) => {
                const m = l.match(/^P (-?\d+)/); if (m) { const d = Object.assign({}, app.downloads); d[dl.url] = parseInt(m[1]); app.downloads = d; }
                if (l.startsWith("OK ")) app.status = "Stiahnuté do knižnice: " + l.slice(3).split("/").pop();
                if (l.startsWith("E ")) app.status = "⚠ Sťahovanie zlyhalo: " + l.slice(2);
            } }
            onExited: { const d = Object.assign({}, app.downloads); delete d[dl.url]; app.downloads = d; libProc.running = true; destroy(); }
        }
    }
    function download(it) {
        if (downloads[it.url] !== undefined) return;
        const d = Object.assign({}, downloads); d[it.url] = 0; downloads = d;
        const p = dlComp.createObject(app, { url: it.url }); p.command = ["latte-tapety", "stiahni", it.url, it.title]; p.running = true;
        status = "Sťahujem " + it.title + "…";
    }

    FloatingWindow {
        onClosed: Qt.quit()
        title: "Tapety — LatteOS"
        implicitWidth: 1180; implicitHeight: 780
        color: theme.surface
        Item {
            id: root
            anchors.fill: parent

            SideBar {
                id: side
                theme: theme
                anchors { left: parent.left; top: parent.top; bottom: parent.bottom }
                heading: "Tapety"; headingGlyph: "wallpaper"
                model: [{ title: "Tapety", items: [
                    { key: "kniznica", path: "", glyph: "photo", label: "Knižnica", sub: app.lib.length + (app.lib.length === 1 ? " tapeta" : app.lib.length >= 2 && app.lib.length <= 4 ? " tapety" : " tapiet") },
                    { key: "objavovat", path: "", glyph: "world", label: "Objavovať", sub: "MotionBGS · Wallhaven · Bing" },
                    { key: "obrazovky", path: "", glyph: "device-desktop", label: "Obrazovky", sub: app.outs.length + (app.outs.length === 1 ? " obrazovka" : " obrazovky") },
                    { key: "nastavenia", path: "", glyph: "settings", label: "Nastavenia", sub: "pauza, batéria, striedanie" } ] }]
                current: app.page
                onActivated: (it) => app.page = it.key
            }
            HeaderBar {
                id: header
                theme: theme; appId: "latteos-tapety"
                anchors { left: side.right; right: parent.right; top: parent.top }
                title: ({ kniznica: "Knižnica", objavovat: "Objavovať", obrazovky: "Obrazovky", nastavenia: "Nastavenia" })[app.page]
                searchPlaceholder: app.page === "objavovat" ? "Hľadať v katalógu (Enter)" : "Filtrovať knižnicu"
                onSearchChanged: (t) => app.filter = t
                netUsed: app.page === "objavovat"
                onSearchSubmitted: (t) => { if (app.page === "objavovat") { app.query = t; app.loadOnline(false); } }
                onCloseRequested: Qt.quit()
            }
            // pruh prehrávača: čo hrá, pauza, ďalšia / predošlá
            Rectangle {
                id: player
                anchors { left: side.right; right: parent.right; top: header.bottom; margins: 12 }
                height: 52; radius: 12; color: theme.field
                Glyph { x: 14; anchors.verticalCenter: parent.verticalCenter; name: app.cur ? "movie" : "photo"; size: 20; color: theme.primary }
                Column {
                    x: 46; anchors.verticalCenter: parent.verticalCenter; width: parent.width - 420
                    Text { width: parent.width; elide: Text.ElideMiddle; color: theme.fg; font { family: theme.fontUi; pixelSize: 13; weight: Font.Bold }
                           text: app.cur ? app.cur.subor.split("/").pop() : "Živá tapeta nehrá (statická tapeta Noctalie)" }
                    Text { width: parent.width; elide: Text.ElideRight; color: app.status.startsWith("⚠") ? theme.error : theme.fgDim; font { family: theme.fontUi; pixelSize: 11 }
                           text: app.status || (!app.st.gpu ? "Bez GPU: obrázky áno, živé video až na počítači s grafickou akceleráciou"
                                               : app.cur ? (app.cur.pauza ? "pozastavené" : "hrá") + " · pauza pri okne: " + ((app.st.nastavenia || {}).auto_pauza || "") : "") }
                }
                Row {
                    anchors { right: parent.right; rightMargin: 10; verticalCenter: parent.verticalCenter }
                    spacing: 4
                    IconButton { theme: theme; glyph: "chevron-left"; tip: "Predošlá"; onClicked: app.run(["predosla"], "Predošlá tapeta") }
                    IconButton { theme: theme; glyph: app.cur && app.cur.pauza ? "player-play" : "player-pause"; tip: "Pauza / pokračovať (Super+Alt+P)"; enabledState: !!app.cur; onClicked: app.run(["pauza"], "") }
                    IconButton { theme: theme; glyph: "chevron-right"; tip: "Ďalšia (Super+Alt+W)"; onClicked: app.run(["dalsia"], "Ďalšia tapeta") }
                    IconButton { theme: theme; glyph: "x"; tip: "Vypnúť živú tapetu"; enabledState: !!app.cur; onClicked: app.run(["stop"], "Živá tapeta vypnutá") }
                }
            }

            component Chip: Rectangle {
                id: ch
                property string label; property bool on: false
                signal clicked()
                width: cl.implicitWidth + 22; height: 30; radius: 9
                color: on ? Qt.rgba(theme.primary.r, theme.primary.g, theme.primary.b, 0.2) : (cm.containsMouse ? theme.hover : theme.field)
                border { color: on ? theme.primary : "transparent"; width: 1.5 }
                Text { id: cl; anchors.centerIn: parent; text: ch.label; color: theme.fg; font { family: theme.fontUi; pixelSize: 12; weight: ch.on ? Font.Bold : Font.Medium } }
                MouseArea { id: cm; anchors.fill: parent; hoverEnabled: true; onClicked: ch.clicked() }
            }
            component Card: Rectangle {
                id: cd
                property string img; property string name; property string sub; property bool video: false
                property bool active: false; property bool fav: false; property real progress: -2
                signal clicked()
                signal menu(real x, real y)
                width: 250; height: 184; radius: 12; color: theme.field
                border { color: active ? theme.primary : (ca.containsMouse ? theme.outline : "transparent"); width: active ? 2 : 1 }
                Rectangle {
                    id: pic
                    x: 8; y: 8; width: parent.width - 16; height: 126; radius: 8; color: Qt.rgba(0, 0, 0, 0.25); clip: true
                    Image { anchors.fill: parent; source: cd.img ? (cd.img.startsWith("http") ? cd.img : "file://" + cd.img) : ""; fillMode: Image.PreserveAspectCrop; asynchronous: true; cache: true
                            sourceSize { width: 480; height: 270 } }
                    Glyph { anchors.centerIn: parent; visible: !cd.img; name: cd.video ? "movie" : "photo"; size: 30; color: theme.fgDim }
                    Rectangle { visible: cd.video; anchors { left: parent.left; bottom: parent.bottom; margins: 6 } width: vl.implicitWidth + 12; height: 20; radius: 6; color: Qt.rgba(0, 0, 0, 0.6)
                                Text { id: vl; anchors.centerIn: parent; text: "▶ živá"; color: "white"; font { family: theme.fontUi; pixelSize: 10; weight: Font.Bold } } }
                    Text { visible: cd.fav; anchors { right: parent.right; top: parent.top; margins: 6 } text: "★"; color: "#F2C14E"; style: Text.Outline; styleColor: Qt.rgba(0, 0, 0, 0.5)
                           font.pixelSize: 16 }
                    Rectangle { visible: cd.progress > -2; anchors { left: parent.left; right: parent.right; bottom: parent.bottom } height: 6; color: Qt.rgba(0, 0, 0, 0.4)
                                Rectangle { width: parent.width * Math.max(0.03, cd.progress / 100); height: parent.height; color: theme.primary } }
                }
                Text { x: 10; y: 140; width: parent.width - 20; elide: Text.ElideRight; text: cd.name; color: theme.fg; font { family: theme.fontUi; pixelSize: 13; weight: Font.DemiBold } }
                Text { x: 10; y: 160; width: parent.width - 20; elide: Text.ElideRight; text: cd.sub; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 11 } }
                MouseArea { id: ca; anchors.fill: parent; hoverEnabled: true; acceptedButtons: Qt.LeftButton | Qt.RightButton
                            onClicked: (m) => { if (m.button === Qt.RightButton) { const q = mapToItem(root, m.x, m.y); cd.menu(q.x, q.y); } else cd.clicked(); } }
            }

            // ── Knižnica ──
            GridView {
                id: libGrid
                visible: app.page === "kniznica"
                anchors { left: side.right; right: parent.right; top: player.bottom; bottom: parent.bottom; margins: 12 }
                cellWidth: 262; cellHeight: 196; clip: true
                model: app.lib.filter(x => !app.filter || x.name.toLowerCase().includes(app.filter.toLowerCase()))
                ScrollHint { flick: libGrid; colors: theme }
                delegate: Card {
                    required property var modelData
                    img: modelData.thumb || (modelData.video ? "" : modelData.path)
                    name: modelData.name; video: modelData.video; fav: app.isFav(modelData.path)
                    sub: (modelData.video ? "Video" : "Obrázok") + " · " + app.human(modelData.size) + (modelData.online ? " · stiahnuté" : "")
                    active: !!app.cur && app.cur.subor === modelData.path
                    onClicked: app.setWall(modelData, "")
                    onMenu: (x, y) => {
                        const it = modelData, items = [{ glyph: "photo", label: "Nastaviť na všetky obrazovky", action: () => app.setWall(it, "") }];
                        if (app.outs.length > 1) for (const o of app.outs) items.push({ glyph: "device-desktop", label: "Nastaviť na " + o.name, action: () => app.setWall(it, o.name) });
                        items.push({ separator: true });
                        items.push({ glyph: "star", label: app.isFav(it.path) ? "Odobrať z obľúbených" : "Pridať medzi obľúbené", action: () => app.run(["oblubena", it.path, app.isFav(it.path) ? "off" : "on"], "") });
                        items.push({ glyph: "palette", label: "Farby témy z tejto tapety", action: () => app.run(["farby", it.path], "Farby témy podľa " + it.name) });
                        items.push({ glyph: "folder", label: "Ukázať v Súboroch", action: () => { opener.command = ["latte-app", "subory", it.path.substring(0, it.path.lastIndexOf("/"))]; opener.startDetached(); } });
                        items.push({ glyph: "trash", label: "Do koša", danger: true, action: () => { opener.command = ["latte-kos", "vyhod", it.path]; opener.startDetached(); libRefresh.restart(); } });
                        ctx.open(x, y, items, it.name);
                    }
                }
                Column {
                    anchors.centerIn: parent; spacing: 10; visible: app.lib.length === 0 && !libProc.running
                    Text { anchors.horizontalCenter: parent.horizontalCenter; text: "Knižnica je prázdna"; color: theme.fg; font { family: theme.fontUi; pixelSize: 16; weight: Font.Bold } }
                    Text { anchors.horizontalCenter: parent.horizontalCenter; text: "Stiahni si tapety v Objavovať alebo vlož videá do ~/Videá/Tapety"; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 } }
                    Chip { anchors.horizontalCenter: parent.horizontalCenter; label: "Objavovať"; on: true; onClicked: app.page = "objavovat" }
                }
            }
            Timer { id: libRefresh; interval: 800; onTriggered: libProc.running = true }
            Process { id: opener }

            // ── Objavovať ──
            Item {
                visible: app.page === "objavovat"
                anchors { left: side.right; right: parent.right; top: player.bottom; bottom: parent.bottom; margins: 12 }
                Column {
                    id: onBar
                    width: parent.width; spacing: 8
                    Flow {
                        width: parent.width; spacing: 6
                        Repeater { model: [["motionbgs", "MotionBGS · živé"], ["wallhaven", "Wallhaven · 4K"], ["bing", "Bing · denná fotka"], ["minimal", "Minimalistické"]]
                            Chip { required property var modelData; label: modelData[1]; on: app.src === modelData[0]
                                   onClicked: { app.src = modelData[0]; app.cat = app.src === "wallhaven" ? "111" : "all"; app.loadOnline(false); } } }
                        Item { width: 16; height: 1 }
                        Repeater { model: app.src === "motionbgs" ? [["hd", "1080p"], ["4k", "4K"]] : (app.src === "wallhaven" ? [["all", "Všetky"], ["2k", "2K"], ["4k", "4K"], ["ultrawide", "Ultrawide"]] : [])
                            Chip { required property var modelData; label: modelData[1]; on: app.res === modelData[0]; onClicked: { app.res = modelData[0]; app.loadOnline(false); } } }
                        Repeater { model: app.src === "wallhaven" ? [["toplist", "Najlepšie"], ["hot", "Populárne"], ["random", "Náhodne"]] : []
                            Chip { required property var modelData; label: modelData[1]; on: app.sort === modelData[0]; onClicked: { app.sort = modelData[0]; app.loadOnline(false); } } }
                    }
                    Flow {
                        width: parent.width; spacing: 6; visible: (app.cats[app.src] || []).length > 0
                        Repeater { model: app.cats[app.src] || []
                            Chip { required property var modelData; label: modelData[1]; on: app.cat === modelData[0]; onClicked: { app.cat = modelData[0]; app.loadOnline(false); } } }
                    }
                    Text { visible: app.onlineErr !== ""; text: "⚠ " + app.onlineErr; color: theme.error; font { family: theme.fontUi; pixelSize: 12 } }
                    Text { visible: app.query !== ""; text: "Hľadám: „" + app.query + "“ · " + app.online.length + " výsledkov"; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 } }
                }
                GridView {
                    id: onGrid
                    anchors { left: parent.left; right: parent.right; top: onBar.bottom; topMargin: 10; bottom: parent.bottom }
                    cellWidth: 262; cellHeight: 196; clip: true
                    model: app.online
                    ScrollHint { flick: onGrid; colors: theme }
                    onAtYEndChanged: if (atYEnd && app.online.length && !onProc.running && app.src !== "bing") app.loadOnline(true)
                    delegate: Card {
                        required property var modelData
                        img: modelData.thumb; name: modelData.title; video: modelData.video
                        sub: modelData.res + " · " + (modelData.author || "") + (modelData.date ? " · " + modelData.date : "")
                        progress: app.downloads[modelData.url] !== undefined ? app.downloads[modelData.url] : -2
                        onClicked: app.download(modelData)
                        onMenu: (x, y) => ctx.open(x, y, [
                            { glyph: "download", label: "Stiahnuť do knižnice", action: () => app.download(modelData) },
                            { glyph: "external-link", label: "Otvoriť v prehliadači", action: () => { opener.command = ["xdg-open", modelData.url]; opener.startDetached(); } }
                        ], modelData.title)
                    }
                    Text { anchors.centerIn: parent; visible: onProc.running && app.online.length === 0; text: "Načítavam katalóg…"; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 14 } }
                }
            }

            // ── Obrazovky ──
            Column {
                visible: app.page === "obrazovky"
                anchors { left: side.right; right: parent.right; top: player.bottom; margins: 16 }
                spacing: 12
                Text { width: parent.width; wrapMode: Text.WordWrap; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 13 }
                       text: "Každá obrazovka môže mať vlastnú tapetu (pravý klik na tapetu v Knižnici › Nastaviť na …) a vlastnú mierku." }
                // náhľad rozloženia obrazoviek (ako Aura „Multi-Screen Studio“)
                Item {
                    id: layoutBox
                    width: parent.width; height: 180
                    readonly property real minX: Math.min.apply(null, app.outs.map(o => o.x).concat([0]))
                    readonly property real minY: Math.min.apply(null, app.outs.map(o => o.y).concat([0]))
                    readonly property real spanW: Math.max(1, Math.max.apply(null, app.outs.map(o => o.x + o.width).concat([1])) - minX)
                    readonly property real spanH: Math.max(1, Math.max.apply(null, app.outs.map(o => o.y + o.height).concat([1])) - minY)
                    readonly property real k: Math.min(width / spanW, height / spanH) * 0.9
                    Repeater {
                        model: app.outs
                        Rectangle {
                            required property var modelData
                            readonly property var v: (app.st.vystupy || {})[modelData.name] || (app.st.vystupy || {})["*"]
                            x: (modelData.x - layoutBox.minX) * layoutBox.k; y: (modelData.y - layoutBox.minY) * layoutBox.k
                            width: modelData.width * layoutBox.k - 6; height: modelData.height * layoutBox.k - 6; radius: 8
                            color: theme.field; border { color: theme.primary; width: 1.5 }
                            Column { anchors.centerIn: parent; spacing: 2
                                Text { anchors.horizontalCenter: parent.horizontalCenter; text: modelData.name; color: theme.fg; font { family: theme.fontUi; pixelSize: 14; weight: Font.Bold } }
                                Text { anchors.horizontalCenter: parent.horizontalCenter; text: modelData.width + " × " + modelData.height; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 11 } }
                                Text { anchors.horizontalCenter: parent.horizontalCenter; text: parent.parent.v ? parent.parent.v.subor.split("/").pop() : "statická tapeta"; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 11 } } }
                        }
                    }
                }
                Repeater {
                    model: app.outs
                    Row {
                        required property var modelData
                        spacing: 8
                        readonly property var v: (app.st.vystupy || {})[modelData.name] || (app.st.vystupy || {})["*"]
                        Text { width: 140; anchors.verticalCenter: parent.verticalCenter; text: modelData.name; color: theme.fg; font { family: theme.fontUi; pixelSize: 13; weight: Font.DemiBold } }
                        Repeater { model: [["fill", "Vyplniť"], ["fit", "Prispôsobiť"], ["stretch", "Roztiahnuť"]]
                            Chip { required property var modelData; label: modelData[1]; on: !!parent.v && parent.v.mierka === modelData[0]
                                   onClicked: app.run(["mierka", parent.parent.modelData.name, modelData[0]], "Mierka: " + modelData[1]) } }
                    }
                }
            }

            // ── Nastavenia ──
            Flickable {
                visible: app.page === "nastavenia"
                anchors { left: side.right; right: parent.right; top: player.bottom; bottom: parent.bottom; margins: 16 }
                contentHeight: setCol.implicitHeight; clip: true
                Column {
                    id: setCol
                    width: parent.width; spacing: 10
                    readonly property var n: app.st.nastavenia || {}
                    component Head: Text { topPadding: 8; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 11; weight: Font.Bold; letterSpacing: 0.8 } }
                    component Pick: Flow {
                        id: pk
                        property string key; property var options: []; property var value
                        width: parent.width; spacing: 6
                        Repeater { model: pk.options
                            Chip { required property var modelData; label: modelData[1]; on: String(pk.value) === String(modelData[0])
                                   onClicked: app.run(["nastavenie", pk.key, String(modelData[0])], "Uložené") } }
                    }
                    Head { text: "AUTOMATICKÁ PAUZA (0 % CPU A GPU)" }
                    Pick { key: "auto_pauza"; value: setCol.n.auto_pauza
                           options: [["max", "Pri maximalizovanom okne"], ["full", "Iba na celú obrazovku (hry)"], ["skryta", "Iba keď je tapeta zakrytá"], ["off", "Nikdy"]] }
                    Pick { key: "bateria"; value: setCol.n.bateria; options: [[true, "Na batérii pauza"], [false, "Hrať aj na batérii"]] }
                    Text { width: parent.width; wrapMode: Text.WordWrap; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 }
                           text: "V hernom režime sa živá tapeta vždy pozastaví. Bez grafickej akcelerácie (stupeň Softvér) sa video nespúšťa vôbec." }
                    Head { text: "ZVUK TAPETY" }
                    Pick { key: "zvuk"; value: setCol.n.ticho ? 0 : setCol.n.zvuk; options: [[0, "Bez zvuku"], [20, "Potichu"], [50, "Stredne"], [80, "Nahlas"]] }
                    Head { text: "STRIEDANIE TAPIET" }
                    Pick { key: "rotacia"; value: setCol.n.rotacia; options: [[0, "Vypnuté"], [5, "5 min"], [15, "15 min"], [30, "30 min"], [60, "1 hodina"], [240, "4 hodiny"]] }
                    Pick { key: "rotacia_poradie"; value: setCol.n.rotacia_poradie; options: [["postupne", "Postupne"], ["nahodne", "Náhodne"]] }
                    Pick { key: "len_oblubene"; value: setCol.n.len_oblubene; options: [[false, "Celá knižnica"], [true, "Iba obľúbené ★"]] }
                    Head { text: "FARBY TÉMY" }
                    Pick { key: "farby"; value: setCol.n.farby; options: [[true, "Farby podľa tapety"], [false, "Farby podľa témy LatteOS"]] }
                    Head { text: "DEKÓDOVANIE VIDEA" }
                    Pick { key: "hwdec"; value: setCol.n.hwdec; options: [["auto-safe", "Automaticky"], ["vaapi", "VA-API (Intel, AMD)"], ["nvdec", "NVDEC (NVIDIA)"], ["no", "Procesorom"]] }
                    Head { text: "PRIEČINKY KNIŽNICE" }
                    Repeater { model: setCol.n.adresare || []
                        Row { required property string modelData; spacing: 8
                              Glyph { anchors.verticalCenter: parent.verticalCenter; name: "folder"; size: 16; color: theme.primary }
                              Text { anchors.verticalCenter: parent.verticalCenter; text: modelData.replace(Quickshell.env("HOME") || "~", "~"); color: theme.fg; font { family: theme.fontUi; pixelSize: 13 } } } }
                }
            }
            ContextMenu { id: ctx; theme: theme }
        }
    }
}
