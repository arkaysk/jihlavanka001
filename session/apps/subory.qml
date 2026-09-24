// LatteOS — Súbory (Data Manager), prototyp v Quickshelli. Dva režimy (zadanie 24. 9., bod 7):
//   Forklift         jeden panel (alebo dva), panel náhľadu dá sa skryť, zobrazenie ako vo Win11 (ikony v 4
//                    veľkostiach, zoznam, podrobnosti), Nový priečinok/súbor, „Otvoriť v…“ s odporúčaniami
//                    App Managera (latte-otvor)
//   Total Commander  dva panely, lišta F-kláves (F3 zobraziť, F4 upraviť, F5 kopírovať, F6 presunúť,
//                    F7 nový priečinok, F8 kôš, F9 server), FTP/SFTP ako priečinky (latte-siet, rclone) Skutočná štruktúra Linuxu ostáva, pohľad „Tento počítač“ je iba zobrazenie
// diskov z lsblk (radar: „Súbory a inštalácie“). Spúšťa sa: qs -p /usr/share/latteos/apps/subory.qml
import QtQuick
import Quickshell
import Quickshell.Io
import "common"
import "data"

ShellRoot {
    id: app
    LatteTheme { id: theme }

    readonly property string home: Quickshell.env("HOME") || "/"
    property bool dual: false
    property int activeIndex: 0
    property string mode: "forklift"     // forklift | commander
    property bool showDetail: true       // panel náhľadu vpravo
    property string view: "detaily"      // detaily | zoznam | ikony (spoločné pre oba panely)
    property int iconSize: 72
    readonly property bool commander: mode === "commander"
    function setMode(m) {
        mode = m;
        if (m === "commander") { dual = true; showDetail = false; view = "detaily"; }
        else { showDetail = true; }
        saveState();
    }
    property var disks: []
    property string confirm: ""          // "trash" = čaká na potvrdenie koša
    property string status: ""
    readonly property var activePane: activeIndex === 0 ? paneA : paneB
    readonly property var otherPane: activeIndex === 0 ? paneB : paneA
    readonly property var sel: activePane ? activePane.current : null
    // Kôš podľa freedesktop (~/.local/share/Trash); v Súboroch je zložkou Obľúbených (old/docs/nastavenia.md)
    readonly property string trashDir: app.home + "/.local/share/Trash/files"
    property int trashCount: 0
    function inTrash(p) { return p === app.trashDir || p.startsWith(app.trashDir + "/"); }
    Process {
        id: trashProc; running: true
        command: ["sh", "-c", "mkdir -p \"$HOME/.local/share/Trash/files\" \"$HOME/.local/share/Trash/info\"; ls -A \"$HOME/.local/share/Trash/files\" | wc -l"]
        stdout: StdioCollector {
            onStreamFinished: {
                app.trashCount = parseInt(this.text) || 0;
                for (const p of [paneA, paneB]) if (p && app.inTrash(p.path)) p.refresh();
            }
        }
    }
    // kopírovanie s priebehom (rsync --info=progress2); presun v rámci disku je okamžitý (mv)
    property int copyPct: -1
    property string copyLabel: ""
    Process {
        id: copyProc
        stdout: SplitParser {
            onRead: (line) => { const m = line.match(/\s(\d+)%\s/); if (m) app.copyPct = parseInt(m[1]); }
        }
        onExited: (code) => { app.status = code === 0 ? "Hotovo: " + app.copyLabel : "Kopírovanie zlyhalo (kód " + code + ")"; app.copyPct = -1; trashProc.running = true; }
    }

    // ── farebné štítky a vlastné obľúbené (~/.config/latteos/tags.json) ─────────────
    // Štítok nemení priečinok, je to iba pohľad Súborov (IDEAS: „farba v kontextovom menu“).
    property var tags: ({})           // cesta → #rrggbb
    property var favorites: []        // ďalšie obľúbené priečinky (pravý klik › Pridať do Obľúbených)
    readonly property var tagColors: [
        { key: "", color: "", label: "bez" },
        { key: "#E5484D", color: "#E5484D", label: "červená" }, { key: "#F07F32", color: "#F07F32", label: "oranžová" },
        { key: "#E8C33B", color: "#E8C33B", label: "žltá" },    { key: "#46A758", color: "#46A758", label: "zelená" },
        { key: "#3E7BFA", color: "#3E7BFA", label: "modrá" },   { key: "#8E4EC6", color: "#8E4EC6", label: "fialová" },
        { key: "#8B8D98", color: "#8B8D98", label: "sivá" }
    ]
    FileView {
        id: tagsView
        path: (Quickshell.env("XDG_CONFIG_HOME") || (app.home + "/.config")) + "/latteos/tags.json"
        printErrors: false
        onLoaded: { try { const j = JSON.parse(text()); app.tags = j.tags || {}; app.favorites = j.favorites || []; } catch (e) {} }
    }
    function saveTags() { tagsView.setText(JSON.stringify({ tags: app.tags, favorites: app.favorites }, null, 1) + "\n"); }
    function setTag(path, color) {
        const t = Object.assign({}, app.tags);
        if (color) t[path] = color; else delete t[path];
        app.tags = t; saveTags();
        app.status = color ? "Štítok: " + path.split("/").pop() : "Štítok odstránený";
    }
    function toggleFavorite(path) {
        app.favorites = app.favorites.indexOf(path) >= 0 ? app.favorites.filter(f => f !== path) : app.favorites.concat([path]);
        saveTags();
    }
    function rename(e, name) {
        name = (name || "").trim();
        if (name === "" || name === e.name) return;
        if (name.includes("/")) { app.status = "Názov nesmie obsahovať /"; return; }
        const dst = e.path.substring(0, e.path.lastIndexOf("/") + 1) + name;
        run(["mv", "-n", "--", e.path, dst], "Premenované na " + name);
        if (app.tags[e.path]) { const c = app.tags[e.path]; setTag(e.path, ""); setTag(dst, c); }
        if (app.favorites.indexOf(e.path) >= 0) { app.favorites = app.favorites.map(f => f === e.path ? dst : f); saveTags(); }
    }
    function newFile(pane, base, ext) {
        run(["sh", "-c", "n=\"$2$3\"; i=2; while [ -e \"$1/$n\" ]; do n=\"$2 $i$3\"; i=$((i+1)); done; : > \"$1/$n\"", "sh", pane.path, base, ext], "Nový súbor: " + base + ext);
    }
    function newMenu(x, y, pane) {
        ctx.open(x, y, [
            { glyph: "folder-plus", label: "Nový priečinok", hint: app.commander ? "F7" : "", action: () => app.newFolder(pane) },
            { glyph: "file-text", label: "Textový súbor (.txt)", action: () => app.newFile(pane, "Nový textový súbor", ".txt") },
            { glyph: "pencil", label: "Dokument Heidelberg (.md)", action: () => app.newFile(pane, "Nový dokument", ".md") },
            { glyph: "file", label: "Prázdny súbor", action: () => app.newFile(pane, "Nový súbor", "") }
        ], "Nový v " + (pane.path.split("/").pop() || "/"));
    }
    // zobrazenie ako vo Windows 11
    function viewMenu(x, y) {
        const v = (key, size, label, glyph) => ({ glyph: glyph, label: label, hint: (app.view === key && (key !== "ikony" || app.iconSize === size)) ? "✓" : "",
                                                  action: () => { app.view = key; if (size) app.iconSize = size; } });
        ctx.open(x, y, [
            v("ikony", 176, "Extra veľké ikony", "photo"), v("ikony", 112, "Veľké ikony", "photo"),
            v("ikony", 72, "Stredné ikony", "layout-grid"), v("ikony", 48, "Malé ikony", "layout-grid"),
            { separator: true },
            v("zoznam", 0, "Zoznam", "layout-list"), v("detaily", 0, "Podrobnosti", "layout-list"),
            { separator: true },
            { glyph: "info-circle", label: app.showDetail ? "Skryť panel náhľadu" : "Ukázať panel náhľadu", hint: "Alt+P", action: () => app.showDetail = !app.showDetail }
        ], "Zobraziť");
    }
    // „Otvoriť v…“: aplikácie pre typ súboru, odporúčané z App Managera (latte-otvor)
    property var openWithEntry: null
    Process {
        id: openWith
        stdout: StdioCollector {
            onStreamFinished: {
                const lines = this.text.split("\n").filter(l => l !== "");
                const e = app.openWithEntry; if (!e || lines.length === 0) return;
                const kind = (lines[0].split("\t")[1] || "");
                const apps = lines.slice(1).map(l => l.split("\t"));
                const hints = { predvolena: "predvolená", odporucana: "odporúčaná", ina: "", nainstalovat: "nainštalovať" };
                const items = apps.filter(a => a[0] !== "nainstalovat").map(a => ({ glyph: a[0] === "predvolena" ? "check" : "external-link", label: a[2], hint: hints[a[0]],
                                                                                     action: () => app.run(["latte-otvor", "spusti", a[1], e.path], "Otváram v " + a[2]) }));
                const setDefault = apps.filter(a => a[0] === "odporucana" || a[0] === "ina");
                if (setDefault.length) {
                    items.push({ separator: true });
                    for (const a of setDefault.slice(0, 4))
                        items.push({ glyph: "star", label: "Vždy otvárať v " + a[2], action: () => app.run(["latte-otvor", "predvolena", a[1], e.path], a[2] + " je predvolená pre " + kind) });
                }
                const inst = apps.filter(a => a[0] === "nainstalovat");
                if (inst.length) {
                    items.push({ separator: true });
                    for (const a of inst) items.push({ glyph: "download", label: "Nainštalovať " + a[2] + "…", hint: "App Manager", action: () => app.run(["latte-app", "aplikacie", "hladat", a[1]]) });
                }
                if (items.length === 0) items.push({ glyph: "help", label: "Žiadna aplikácia pre " + kind, enabled: false, action: () => {} });
                ctx.replace(items, "Otvoriť v… · " + kind);
            }
        }
    }
    function openWithMenu(e) { app.openWithEntry = e; openWith.command = ["latte-otvor", "aplikacie", e.path]; openWith.running = true; }

    // ── sieť: FTP/SFTP servery ako priečinky (latte-siet → ~/Siet/…) ─────────────
    property var servers: []
    Process {
        id: serverScan; running: true
        command: ["latte-siet", "zoznam"]
        stdout: StdioCollector { onStreamFinished: app.servers = this.text.split("\n").filter(l => l !== "").map(l => { const f = l.split("\t"); return { path: f[0], url: f[1] || "" }; }) }
    }
    property bool connectOpen: false
    property string connectError: ""
    property bool connecting: false
    Process {
        id: connectProc
        stdinEnabled: true
        stdout: StdioCollector { id: connectOut }
        stderr: StdioCollector { id: connectErr }
        onExited: (code) => {
            app.connecting = false;
            if (code === 0) { app.connectOpen = false; serverScan.running = true; app.activePane.go(connectOut.text.trim()); app.status = "Pripojené: " + connectOut.text.trim().split("/").pop(); }
            else app.connectError = connectErr.text.trim().replace(/^latte-siet: /, "") || "Pripojenie zlyhalo";
        }
    }
    function connectServer(url, pw) {
        connectError = ""; connecting = true;
        connectProc.command = ["latte-siet", "pripoj", url.trim()].concat(pw !== "" ? ["--heslo-stdin"] : []);
        connectProc.running = true;
        if (pw !== "") connectProc.write(pw + "\n");
        connectProc.stdinEnabled = false;     // zatvoriť stdin (heslo nikam inam nejde)
        connectProc.stdinEnabled = true;
    }

    function newFolder(pane) {
        run(["sh", "-c", "n='Nový priečinok'; i=2; while [ -e \"$1/$n\" ]; do n=\"Nový priečinok $i\"; i=$((i+1)); done; mkdir -- \"$1/$n\"", "sh", pane.path], "Nový priečinok");
    }

    // kontextové menu položky v zozname (e = null → prázdne miesto v priečinku)
    function showMenu(e, x, y, pane) {
        const other = pane === paneA ? paneB : paneA;
        let items;
        if (!e) {
            items = [
                { glyph: "folder-plus", label: "Nový priečinok", action: () => app.newFolder(pane) },
                { glyph: "terminal-2", label: "Terminál tu", action: () => app.run(["foot", "--working-directory=" + pane.path]) },
                { glyph: pane.showHidden ? "eye-off" : "eye", label: pane.showHidden ? "Skryť skryté súbory" : "Ukázať skryté súbory", hint: "Ctrl+H", action: () => pane.showHidden = !pane.showHidden },
                { separator: true },
                { glyph: "clipboard", label: "Kopírovať cestu priečinka", action: () => app.run(["wl-copy", "--", pane.path], "Cesta skopírovaná") },
                { glyph: "star", label: app.favorites.indexOf(pane.path) >= 0 ? "Odobrať z Obľúbených" : "Pridať do Obľúbených", action: () => app.toggleFavorite(pane.path) }
            ];
            if (app.inTrash(pane.path)) items.unshift({ glyph: "trash", label: "Vysypať kôš (" + app.trashCount + ")", danger: true, enabled: app.trashCount > 0,
                                                        action: () => { app.run(["latte-kos", "vysypat"], "Kôš vysypaný"); trashRefresh.restart(); } });
            ctx.open(x, y, items, pane.path);
            return;
        }
        if (app.inTrash(e.path) && e.path.substring(0, e.path.lastIndexOf("/")) === app.trashDir) {
            ctx.open(x, y, [
                { glyph: "refresh", label: "Obnoviť na pôvodné miesto", action: () => { app.run(["latte-kos", "obnov", e.name], "Obnovené: " + e.name); trashRefresh.restart(); } },
                { glyph: "clipboard", label: "Kopírovať cestu", action: () => app.run(["wl-copy", "--", e.path], "Cesta skopírovaná") },
                { separator: true },
                { glyph: "trash", label: "Odstrániť natrvalo", danger: true, action: () => { app.run(["sh", "-c", "rm -rf -- \"$1\" \"$HOME/.local/share/Trash/info/$(basename \"$1\").trashinfo\"", "sh", e.path], "Odstránené natrvalo: " + e.name); trashRefresh.restart(); } }
            ], e.name + " · v koši");
            return;
        }
        items = [
            { glyph: "external-link", label: e.isDir ? "Otvoriť" : "Otvoriť v aplikácii", hint: "Enter", action: () => { if (e.isDir) pane.go(e.path); else app.openPath(e.path); } }
        ];
        if (!e.isDir) items.push({ glyph: "apps", label: "Otvoriť v…", keepOpen: true, action: () => app.openWithMenu(e) });
        if (!e.isDir && /\.(mp4|webm|mkv|mov|gif|webp)$/i.test(e.name))
            items.push({ glyph: "photo", label: "Nastaviť ako živú tapetu", action: () => app.run(["sh", "-c", "mkdir -p \"$HOME/.config/latteos\" && printf 'video:%s\\n' \"$1\" > \"$HOME/.config/latteos/live-wallpaper\" && (pgrep -f 'apps/[z]ivatapeta.qml' >/dev/null || setsid latte-app zivatapeta >/dev/null 2>&1 &)", "sh", e.path], "Živá tapeta: " + e.name) });
        if (e.isDir) items.push({ glyph: "columns-2", label: "Otvoriť v druhom paneli", action: () => { app.dual = true; other.go(e.path); } });
        items.push({ separator: true });
        items.push({ colors: app.tagColors, current: app.tags[e.path] || "", label: "Farba", action: (c) => app.setTag(e.path, c) });
        items.push({ separator: true });
        items.push({ glyph: "pencil", label: "Premenovať…", keepOpen: true, action: () => ctx.replace([{ input: e.name, action: (t) => app.rename(e, t) }], "Nový názov · Enter uloží, Esc zruší") });
        items.push({ glyph: "clipboard", label: "Kopírovať cestu", action: () => app.run(["wl-copy", "--", e.path], "Cesta skopírovaná") });
        if (!e.isDir && /\.(rpm|flatpakref|flatpak|appimage|exe|msi|apk|deb|run)$/i.test(e.name))
            items.push({ glyph: "help", label: "Bude to fungovať?", hint: "App Manager", action: () => app.run(["latte-app", "aplikacie", "check", e.path]) });
        if (app.dual) {
            items.push({ glyph: "copy", label: "Kopírovať do druhého", hint: "F5", action: () => app.copyToOther(false) });
            items.push({ glyph: "arrows-exchange", label: "Presunúť do druhého", hint: "F6", action: () => app.copyToOther(true) });
        }
        if (e.isDir) {
            items.push({ glyph: "star", label: app.favorites.indexOf(e.path) >= 0 ? "Odobrať z Obľúbených" : "Pridať do Obľúbených", action: () => app.toggleFavorite(e.path) });
            items.push({ glyph: "terminal-2", label: "Terminál tu", action: () => app.run(["foot", "--working-directory=" + e.path]) });
        }
        items.push({ separator: true });
        items.push({ glyph: "trash", label: "Do koša", hint: "Del", danger: true, action: () => { app.run(["latte-kos", "vyhod", e.path], "Do koša: " + e.name); trashRefresh.restart(); } });
        ctx.open(x, y, items, e.name);
    }
    // kontextové menu položky bočnej lišty (disky, obľúbené)
    function showSideMenu(it, x, y) {
        const items = [
            { glyph: "external-link", label: "Otvoriť", action: () => app.activePane.go(it.path) },
            { glyph: "columns-2", label: "Otvoriť v druhom paneli", action: () => { app.dual = true; app.otherPane.go(it.path); } },
            { glyph: "clipboard", label: "Kopírovať cestu", action: () => app.run(["wl-copy", "--", it.path], "Cesta skopírovaná") }
        ];
        if (!it.key.startsWith("disk:")) {
            items.push({ separator: true });
            items.push({ colors: app.tagColors, current: app.tags[it.path] || "", label: "Farba", action: (c) => app.setTag(it.path, c) });
        }
        if (it.key === "fav:trash") { items.push({ separator: true }); items.push({ glyph: "trash", label: "Vysypať kôš", danger: true, enabled: app.trashCount > 0, action: () => { app.run(["latte-kos", "vysypat"], "Kôš vysypaný"); trashRefresh.restart(); } }); }
        if (it.key.startsWith("net:") && it.path) { items.push({ separator: true }); items.push({ glyph: "x", label: "Odpojiť server", danger: true, action: () => { app.run(["latte-siet", "odpoj", it.path], "Odpojené: " + it.label); serverRefresh.restart(); if (app.activePane.path.startsWith(it.path)) app.activePane.go(app.home); } }); }
        if (it.custom) { items.push({ separator: true }); items.push({ glyph: "star", label: "Odobrať z Obľúbených", action: () => app.toggleFavorite(it.path) }); }
        ctx.open(x, y, items, it.label);
    }

    // hľadanie všade (Enter v hľadaní): find v aktívnom priečinku a podpriečinkoch, bez skrytých, najviac 300
    property var found: []
    property string foundQuery: ""
    property bool finding: false
    Process {
        id: findProc
        stdout: StdioCollector {
            onStreamFinished: {
                app.finding = false;
                app.found = this.text.split("\n").filter(l => l !== "").map(l => { const i = l.indexOf("|"); return { dir: l.slice(0, 1) === "d", path: l.slice(i + 1) }; });
                app.status = app.found.length + (app.found.length >= 300 ? "+" : "") + " nájdených pre „" + app.foundQuery + "“";
            }
        }
    }
    function findAll(q) {
        q = (q || "").trim();
        if (q.length < 2) { found = []; foundQuery = ""; return; }
        foundQuery = q; finding = true; status = "Hľadám „" + q + "“ v " + activePane.path + "…";
        findProc.command = ["sh", "-c", "find \"$1\" -mindepth 1 \\( -name '.*' -prune \\) -o -iname \"*$2*\" -printf '%y|%p\\n' 2>/dev/null | head -300", "sh", activePane.path, q];
        findProc.running = true;
    }

    // pripojené cloudové priečinky (~/Cloud/*, latte-cloud)
    property var cloudDirs: []
    Process {
        id: cloudScan; running: true
        command: ["sh", "-c", "for d in \"$HOME\"/Cloud/*/; do [ -d \"$d\" ] && mountpoint -q \"$d\" && basename \"$d\"; done"]
        stdout: StdioCollector { onStreamFinished: app.cloudDirs = this.text.split("\n").filter(l => l !== "") }
    }

    // test bez myši (setup/f1/headless.sh): LATTE_APP_TEST=menu otvorí kontextové menu prvej položky
    Timer {
        running: Quickshell.env("LATTE_APP_TEST") === "menu"; interval: 2500
        onTriggered: { if (paneA.count > 0) { paneA.moveSelection(1); app.showMenu(paneA.current, 420, 180, paneA); } }
    }

    // ── pamäť stavu: dva panely a ich cesty (~/.config/latteos/subory.json) ─────────
    readonly property string stateFile: (Quickshell.env("XDG_CONFIG_HOME") || (app.home + "/.config")) + "/latteos/subory.json"
    property bool stateLoaded: false
    FileView {
        id: stateView
        path: app.stateFile
        printErrors: false
        onLoaded: {
            try {
                const st = JSON.parse(text());
                app.dual = !!st.dual;
                if (st.mode) app.mode = st.mode;
                if (st.showDetail !== undefined) app.showDetail = !!st.showDetail;
                if (st.view) app.view = st.view;
                if (st.iconSize) app.iconSize = st.iconSize;
                if (st.left) paneA.go(st.left);
                if (st.right) paneB.go(st.right);
            } catch (e) {}
            app.openArg();
            app.stateLoaded = true;
        }
        onLoadFailed: { app.openArg(); app.stateLoaded = true; }
    }
    // latte-app subory <priečinok>: otvorí zadaný priečinok v ľavom paneli (file:// URL alebo cesta)
    function openArg() {
        let a = (Quickshell.env("LATTE_APP_ARGS") || "").trim();
        if (a.startsWith("file://")) a = decodeURIComponent(a.slice(7));
        if (a !== "") { paneA.go(a); app.activeIndex = 0; }
    }
    function saveState() {
        if (!app.stateLoaded) return;
        saver.command = ["sh", "-c", "mkdir -p \"$(dirname \"$1\")\" && printf '%s' \"$2\" > \"$1\"", "sh", app.stateFile,
                         JSON.stringify({ dual: app.dual, left: paneA.path, right: paneB.path, mode: app.mode,
                                         showDetail: app.showDetail, view: app.view, iconSize: app.iconSize })];
        saver.running = true;
    }
    Process { id: saver }
    onDualChanged: saveState()
    onShowDetailChanged: saveState()
    onViewChanged: saveState()
    onIconSizeChanged: saveState()

    // ── disky: lsblk (Systém, oddiely, USB) ───────────────────────────────────
    Process {
        id: lsblk
        running: true
        command: ["lsblk", "-J", "-b", "-o", "NAME,LABEL,SIZE,FSAVAIL,FSUSED,MOUNTPOINT,TYPE,RM,TRAN,MODEL"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const out = [];
                    const walk = (d, disk) => {
                        if (d.mountpoint && d.mountpoint !== "[SWAP]" && !d.mountpoint.startsWith("/boot")) {
                            const size = Number(d.size) || 0, used = Number(d.fsused) || 0, avail = Number(d.fsavail) || 0;
                            const usb = disk.rm || disk.tran === "usb";
                            out.push({
                                key: "disk:" + d.mountpoint, path: d.mountpoint,
                                glyph: usb ? "usb" : (d.mountpoint === "/" ? "device-desktop" : "database"),
                                label: d.mountpoint === "/" ? "Systém" : (d.label || d.mountpoint.split("/").pop() || d.name),
                                sub: app.human(avail) + " voľných z " + app.human(used + avail),
                                usage: (used + avail) > 0 ? used / (used + avail) : 0
                            });
                        }
                        for (const c of (d.children || [])) walk(c, disk);
                    };
                    for (const d of JSON.parse(this.text).blockdevices) walk(d, d);
                    app.disks = out;
                } catch (e) { console.warn("lsblk:", e); }
            }
        }
    }
    Timer { interval: 15000; running: true; repeat: true; onTriggered: { lsblk.running = true; cloudScan.running = true; serverScan.running = true; } }
    Timer { id: serverRefresh; interval: 700; onTriggered: serverScan.running = true }

    function human(b) {
        if (b < 1024) return b + " B";
        const u = ["kB", "MB", "GB", "TB"]; let v = b / 1024, i = 0;
        while (v >= 1024 && i < u.length - 1) { v /= 1024; i++; }
        return v.toFixed(v < 10 ? 1 : 0).replace(".", ",") + " " + u[i];
    }

    readonly property var sidebarModel: [
        { title: "Tento počítač", items: app.disks },
        { title: "Obľúbené", items: [
            { key: "fav:home", path: app.home, glyph: "home", label: "Domov" },
            { key: "fav:desk", path: app.home + "/Plocha", glyph: "device-desktop", label: "Plocha" },
            { key: "fav:docs", path: app.home + "/Dokumenty", glyph: "file-text", label: "Dokumenty" },
            { key: "fav:down", path: app.home + "/Stiahnuté", glyph: "download", label: "Stiahnuté" },
            { key: "fav:pics", path: app.home + "/Obrázky", glyph: "photo", label: "Obrázky" },
            { key: "fav:music", path: app.home + "/Hudba", glyph: "music", label: "Hudba" },
            { key: "fav:video", path: app.home + "/Videá", glyph: "movie", label: "Videá" },
            { key: "fav:trash", path: app.trashDir, glyph: "trash", label: "Kôš", sub: app.trashCount ? app.trashCount + " položiek · pravý klik: vysypať" : "prázdny" }
        ].concat(app.favorites.map(f => ({ key: "fav+:" + f, path: f, glyph: "folder", label: f.split("/").pop() || f, custom: true })))
         .map(it => Object.assign({}, it, { tag: app.tags[it.path] || "" })) },
        { title: "Cloud", items: app.cloudDirs.map(c => ({ key: "cloud:" + c, path: app.home + "/Cloud/" + c, glyph: "cloud", label: c, sub: "cloudový účet" }))
                                  .concat([{ key: "cloud:add", path: "", glyph: "plus", label: "Pridať cloudový účet", sub: "Nastavenia › Dáta", dim: app.cloudDirs.length > 0 }]) },
        { title: "Sieť", items: app.servers.map(sv => ({ key: "net:" + sv.path, path: sv.path, glyph: "server", label: sv.path.split("/").pop(), sub: sv.url || "server" }))
                                  .concat([{ key: "net:add", path: "", glyph: "plus", label: "Pripojiť server…", sub: "FTP, SFTP" + (app.commander ? " · F9" : ""), dim: app.servers.length > 0 }]) },
        { title: "Aplikácie", items: [
            { key: "apps:flatpak", path: "/var/lib/flatpak/app", glyph: "package", label: "Flatpak (systém)", sub: "každá appka vo vlastnom priečinku" },
            { key: "apps:flatpak-user", path: app.home + "/.local/share/flatpak/app", glyph: "package", label: "Flatpak (používateľ)" },
            { key: "apps:desktop", path: "/usr/share/applications", glyph: "apps", label: "Nainštalované (.desktop)" }
        ] },
        { title: "Systém Linux", items: [
            { key: "sys:root", path: "/", glyph: "server", label: "/ koreň", sub: "skutočná štruktúra, nič skryté" },
            { key: "sys:etc", path: "/etc", glyph: "settings", label: "/etc", sub: "nastavenia systému" },
            { key: "sys:mnt", path: "/run/media/" + (Quickshell.env("USER") || ""), glyph: "usb", label: "Pripojené médiá" }
        ] }
    ]

    // ── akcie ──────────────────────────────────────────────────────────────────
    Process { id: runner }
    function run(cmd, msg) { runner.command = cmd; runner.running = true; if (msg) app.status = msg; }
    function openPath(p) { run(["xdg-open", p]); }
    function copyToOther(move) {
        const e = app.sel; if (!e || !app.dual) { app.status = "F5/F6 potrebuje dva panely (F3)"; return; }
        const dst = app.otherPane.path;
        if (move) { run(["mv", "-n", "--", e.path, dst], "Presúvam " + e.name + " → " + dst); return; }
        if (copyProc.running) { app.status = "Ešte kopírujem " + app.copyLabel; return; }
        app.copyLabel = e.name + " → " + dst; app.copyPct = 0; app.status = "Kopírujem " + app.copyLabel;
        // --ignore-existing = neprepíše nič v cieli (ako cp -n); \r z priebehu rsync sa mení na nové riadky
        copyProc.command = ["sh", "-c", "rsync -a --ignore-existing --no-inc-recursive --info=progress2 -- \"$1\" \"$2/\" | stdbuf -o0 tr '\\r' '\\n'", "sh", e.path, dst];
        copyProc.running = true;
    }
    Timer { id: trashRefresh; interval: 600; onTriggered: trashProc.running = true }
    function trash() {
        const e = app.sel; if (!e) return;
        if (app.confirm !== "trash") { app.confirm = "trash"; app.status = "Stlač Delete znova (alebo tlačidlo) na presun do koša: " + e.name; return; }
        app.confirm = "";
        run(["latte-kos", "vyhod", e.path], "Do koša: " + e.name);
        trashRefresh.restart();
    }

    FloatingWindow {

        onClosed: Qt.quit()              // zavretie z kompozitora (✕ v titulku, Super+Q) ukončí aj proces
        id: win
        title: "Súbory — LatteOS"
        implicitWidth: 1280
        implicitHeight: 780
        color: theme.surface

        Item {
            id: root
            anchors.fill: parent
            focus: true
            Keys.onPressed: (ev) => {
                const p = app.activePane;
                if (app.connectOpen) return;
                if (ev.key === Qt.Key_Down) { p.moveRow(1); ev.accepted = true; }
                else if (ev.key === Qt.Key_Up) { p.moveRow(-1); ev.accepted = true; }
                else if (ev.key === Qt.Key_Right && p.icons) { p.moveSelection(1); ev.accepted = true; }
                else if (ev.key === Qt.Key_Left && p.icons) { p.moveSelection(-1); ev.accepted = true; }
                else if (ev.key === Qt.Key_P && (ev.modifiers & Qt.AltModifier)) { app.showDetail = !app.showDetail; ev.accepted = true; }
                else if (app.commander && ev.key === Qt.Key_F3) { if (app.sel) { if (app.sel.isDir) p.openCurrent(); else app.openPath(app.sel.path); } ev.accepted = true; }
                else if (app.commander && ev.key === Qt.Key_F4) { if (app.sel && !app.sel.isDir) app.run(["latte-otvor", "spusti", "latteos-heidelberg", app.sel.path], "Upraviť: " + app.sel.name); ev.accepted = true; }
                else if (app.commander && ev.key === Qt.Key_F7) { app.newFolder(p); ev.accepted = true; }
                else if (app.commander && ev.key === Qt.Key_F8) { app.trash(); ev.accepted = true; }
                else if (ev.key === Qt.Key_F9) { app.connectError = ""; app.connectOpen = true; ev.accepted = true; }
                else if (ev.key === Qt.Key_Return || ev.key === Qt.Key_Enter) { p.openCurrent(); ev.accepted = true; }
                else if (ev.key === Qt.Key_Backspace) { p.up(); ev.accepted = true; }
                else if (ev.key === Qt.Key_Tab && app.dual) { app.activeIndex = 1 - app.activeIndex; ev.accepted = true; }
                else if (ev.key === Qt.Key_F3) { app.dual = !app.dual; if (!app.dual) app.activeIndex = 0; ev.accepted = true; }
                else if (ev.key === Qt.Key_F5) { app.copyToOther(false); ev.accepted = true; }
                else if (ev.key === Qt.Key_F6) { app.copyToOther(true); ev.accepted = true; }
                else if (ev.key === Qt.Key_Delete) { app.trash(); ev.accepted = true; }
                else if (ev.key === Qt.Key_H && (ev.modifiers & Qt.ControlModifier)) { p.showHidden = !p.showHidden; ev.accepted = true; }
                else if (ev.key === Qt.Key_Escape) { app.confirm = ""; app.status = ""; }
            }

            SideBar {
                id: side
                theme: theme
                anchors { left: parent.left; top: parent.top; bottom: parent.bottom }
                heading: "Súbory"; headingGlyph: "folder"
                model: app.sidebarModel
                current: {
                    const p = app.activePane ? app.activePane.path : "";
                    for (const s of app.sidebarModel) for (const it of s.items) if (it.path === p) return it.key;
                    return "";
                }
                onActivated: (it) => { if (it.key === "cloud:add") { app.run(["latte-app", "nastavenia", "synchronizacia"]); return; }
                                       if (it.key === "net:add") { app.connectError = ""; app.connectOpen = true; return; }
                                       app.activePane.go(it.path); root.forceActiveFocus(); }
                onContextRequested: (it, x, y) => app.showSideMenu(it, x, y)
            }

            HeaderBar {
                id: header
                theme: theme
                appId: "latteos-subory"
                anchors { left: side.right; right: parent.right; top: parent.top }
                title: app.activePane ? (app.activePane.path === app.trashDir ? "Kôš" : app.activePane.path) : ""
                canBack: app.activePane && app.activePane.historyIndex > 0
                canForward: app.activePane && app.activePane.historyIndex < app.activePane.history.length - 1
                searchPlaceholder: "Hľadať (Enter = všade)"
                onBack: app.activePane.back()
                onForward: app.activePane.forward()
                onSearchChanged: (t) => { app.activePane.filter = t; if (t === "") app.found = []; }
                onSearchSubmitted: (t) => app.findAll(t)
                onCloseRequested: Qt.quit()

                IconButton { theme: theme; glyph: "arrow-up"; tip: "O úroveň vyššie (Backspace)"; onClicked: app.activePane.up() }
                IconButton { id: newBtn; theme: theme; glyph: "plus"; tip: "Nový priečinok alebo súbor"
                             onClicked: { const q = newBtn.mapToItem(null, 0, newBtn.height + 4); app.newMenu(q.x, q.y, app.activePane); } }
                IconButton { id: viewBtn; theme: theme; glyph: app.view === "ikony" ? "layout-grid" : "layout-list"; tip: "Zobrazenie (ikony, zoznam, podrobnosti)"
                             onClicked: { const q = viewBtn.mapToItem(null, 0, viewBtn.height + 4); app.viewMenu(q.x, q.y); } }
                IconButton { theme: theme; glyph: "info-circle"; checked: app.showDetail; tip: "Panel náhľadu (Alt+P)"; onClicked: app.showDetail = !app.showDetail }
                IconButton { visible: !app.commander; theme: theme; glyph: "columns-2"; checked: app.dual; tip: "Dva panely (F3)"; onClicked: { app.dual = !app.dual; if (!app.dual) app.activeIndex = 0; } }
                IconButton { theme: theme; glyph: "layout-columns"; checked: app.commander; tip: app.commander ? "Režim Total Commander · klik: Forklift" : "Režim Forklift · klik: Total Commander"
                             onClicked: app.setMode(app.commander ? "forklift" : "commander") }
                IconButton { theme: theme; glyph: app.activePane && app.activePane.showHidden ? "eye" : "eye-off"; tip: "Skryté súbory (Ctrl+H)"; onClicked: app.activePane.showHidden = !app.activePane.showHidden }
                IconButton { theme: theme; glyph: "terminal-2"; tip: "Terminál tu"; onClicked: app.run(["foot", "--working-directory=" + app.activePane.path]) }
            }

            // panely + detail
            Row {
                id: body
                anchors { left: side.right; right: parent.right; top: header.bottom; bottom: statusBar.top; margins: 10 }
                spacing: 10
                readonly property real detailW: 280
                readonly property real paneW: (width - (app.showDetail ? detailW + spacing : 0) - (app.dual ? spacing : 0)) / (app.dual ? 2 : 1)

                FilePane {
                    id: paneA
                    theme: theme
                    tags: app.tags
                    view: app.view; iconSize: app.iconSize
                    onContextRequested: (e, x, y) => app.showMenu(e, x, y, paneA)
                    width: body.paneW; height: body.height
                    active: app.dual && app.activeIndex === 0
                    Component.onCompleted: go(app.home)
                    onPathChanged: app.saveState()
                    onFocusRequested: { app.activeIndex = 0; app.confirm = ""; root.forceActiveFocus(); }
                    onOpenFile: (p) => app.openPath(p)
                }
                FilePane {
                    id: paneB
                    theme: theme
                    tags: app.tags
                    view: app.view; iconSize: app.iconSize
                    onContextRequested: (e, x, y) => app.showMenu(e, x, y, paneB)
                    visible: app.dual
                    width: app.dual ? body.paneW : 0; height: body.height
                    active: app.dual && app.activeIndex === 1
                    Component.onCompleted: go("/")
                    onPathChanged: app.saveState()
                    onFocusRequested: { app.activeIndex = 1; app.confirm = ""; root.forceActiveFocus(); }
                    onOpenFile: (p) => app.openPath(p)
                }

                // detail vybranej položky (návrh V2: pravý panel)
                Rectangle {
                    visible: app.showDetail
                    width: body.detailW; height: body.height; radius: theme.radius
                    color: Qt.rgba(0, 0, 0, theme.mode === "dark" ? 0.16 : 0.04)
                    border { color: theme.line; width: 1 }
                    Column {
                        anchors { fill: parent; margins: 16 }
                        spacing: 10
                        readonly property var e: app.sel
                        readonly property var k: e ? app.activePane.kind(e) : ["", "folder"]

                        Rectangle {
                            width: parent.width; height: 150; radius: 12; color: theme.field; clip: true
                            Glyph { anchors.centerIn: parent; visible: !preview.visible; name: parent.parent.k[1]; size: 64; color: theme.primary }
                            Image {
                                id: preview
                                anchors.fill: parent; fillMode: Image.PreserveAspectCrop; asynchronous: true
                                sourceSize { width: 520; height: 300 }
                                visible: status === Image.Ready && parent.parent.k[0] === "Obrázok"
                                source: parent.parent.e && parent.parent.k[0] === "Obrázok" ? "file://" + parent.parent.e.path : ""
                            }
                        }
                        Text {
                            width: parent.width; wrapMode: Text.WrapAnywhere; maximumLineCount: 3; elide: Text.ElideRight
                            text: parent.e ? parent.e.name : (app.activePane ? (app.activePane.path === app.trashDir ? "Kôš" : (app.activePane.path.split("/").pop() || "/")) : "")
                            color: theme.fg; font { family: theme.fontDisplay; pixelSize: 18; weight: Font.DemiBold }
                        }
                        Text {
                            text: parent.e ? parent.k[0] : (app.activePane ? app.activePane.count + " položiek" : "")
                            color: theme.primary; font { family: theme.fontUi; pixelSize: 12; weight: Font.Bold }
                        }
                        Repeater {
                            model: parent.e ? [
                                ["Veľkosť", parent.e.isDir ? "—" : app.human(parent.e.size)],
                                ["Upravené", Qt.formatDateTime(parent.e.modified, "d. M. yyyy HH:mm")],
                                ["Cesta", parent.e.path]
                            ] : []
                            Column {
                                required property var modelData
                                width: parent.width; spacing: 1
                                Text { text: modelData[0].toUpperCase(); color: theme.fgDim; font { family: theme.fontUi; pixelSize: 10; weight: Font.Bold; letterSpacing: 0.6 } }
                                Text { width: parent.width; wrapMode: Text.WrapAnywhere; text: modelData[1]; color: theme.fg; font { family: theme.fontUi; pixelSize: 12 } }
                            }
                        }
                        Item { width: 1; height: 6 }
                        component Action: Rectangle {
                            id: act
                            property string glyph; property string label; property bool danger: false
                            signal clicked()
                            width: parent.width; height: 36; radius: 10
                            color: am.containsMouse ? (danger ? Qt.rgba(theme.error.r, theme.error.g, theme.error.b, 0.2) : theme.hover) : theme.field
                            Row {
                                x: 12; anchors.verticalCenter: parent.verticalCenter; spacing: 10
                                Glyph { name: act.glyph; size: 16; color: act.danger ? theme.error : theme.fg }
                                Text { text: act.label; color: act.danger ? theme.error : theme.fg; font { family: theme.fontUi; pixelSize: 13; weight: Font.DemiBold } }
                            }
                            MouseArea { id: am; anchors.fill: parent; hoverEnabled: true; onClicked: act.clicked() }
                        }
                        Action { visible: !!parent.e; glyph: "external-link"; label: parent.e && parent.e.isDir ? "Otvoriť priečinok" : "Otvoriť"; onClicked: app.activePane.openCurrent() }
                        Action { visible: !!parent.e; glyph: "clipboard"; label: "Kopírovať cestu"; onClicked: app.run(["wl-copy", "--", app.sel.path], "Cesta skopírovaná") }
                        Action { visible: !!parent.e && app.dual; glyph: "copy"; label: "Kopírovať do druhého (F5)"; onClicked: app.copyToOther(false) }
                        Action { visible: !!parent.e && app.dual; glyph: "arrows-exchange"; label: "Presunúť do druhého (F6)"; onClicked: app.copyToOther(true) }
                        Action {
                            visible: !!parent.e; danger: true; glyph: "trash"
                            label: app.confirm === "trash" ? "Naozaj do koša?" : "Do koša (Delete)"
                            onClicked: app.trash()
                        }
                    }
                }
            }

            Rectangle {
                id: statusBar
                anchors { left: side.right; right: parent.right; bottom: parent.bottom }
                height: 30; color: "transparent"
                Rectangle { width: parent.width; height: 1; color: theme.line }
                Rectangle {   // priebeh kopírovania
                    visible: app.copyPct >= 0
                    anchors { left: parent.left; bottom: parent.bottom }
                    width: parent.width * Math.max(0, app.copyPct) / 100; height: 3; color: theme.primary
                }
                Text {
                    x: 14; anchors.verticalCenter: parent.verticalCenter
                    text: (app.activePane ? app.activePane.count + " položiek" : "") + (app.copyPct >= 0 ? "   ·   " + app.copyPct + " % · " + app.copyLabel : (app.status !== "" ? "   ·   " + app.status : ""))
                    color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 }
                }
                Text {
                    visible: !app.commander
                    anchors { right: parent.right; rightMargin: 14; verticalCenter: parent.verticalCenter }
                    text: "Pravý klik: menu a farba · F3 dva panely · F5 kopírovať · F6 presunúť · Del kôš · Alt+P náhľad"
                    color: theme.fgDim; opacity: 0.8; font { family: theme.fontUi; pixelSize: 11 }
                }
                // Total Commander: lišta F-kláves (klik = to isté ako kláves)
                Row {
                    visible: app.commander
                    anchors { right: parent.right; rightMargin: 8; verticalCenter: parent.verticalCenter }
                    spacing: 4
                    Repeater {
                        model: [["F3", "Zobraziť"], ["F4", "Upraviť"], ["F5", "Kopírovať"], ["F6", "Presunúť"], ["F7", "Nový priečinok"], ["F8", "Do koša"], ["F9", "Server"]]
                        Rectangle {
                            required property var modelData
                            width: fkt.implicitWidth + 16; height: 24; radius: 6; color: fkm.containsMouse ? theme.hover : theme.field
                            Text { id: fkt; anchors.centerIn: parent; text: modelData[0] + " " + modelData[1]; color: theme.fg; font { family: theme.fontUi; pixelSize: 11; weight: Font.DemiBold } }
                            MouseArea {
                                id: fkm; anchors.fill: parent; hoverEnabled: true
                                onClicked: {
                                    const k = modelData[0], p = app.activePane;
                                    if (k === "F3") { if (app.sel) { if (app.sel.isDir) p.openCurrent(); else app.openPath(app.sel.path); } }
                                    else if (k === "F4") { if (app.sel && !app.sel.isDir) app.run(["latte-otvor", "spusti", "latteos-heidelberg", app.sel.path], "Upraviť: " + app.sel.name); }
                                    else if (k === "F5") app.copyToOther(false);
                                    else if (k === "F6") app.copyToOther(true);
                                    else if (k === "F7") app.newFolder(p);
                                    else if (k === "F8") app.trash();
                                    else if (k === "F9") { app.connectError = ""; app.connectOpen = true; }
                                    root.forceActiveFocus();
                                }
                            }
                        }
                    }
                }
            }

            // výsledky hľadania všade — prekryjú panely, klik otvorí priečinok s nájdenou položkou
            Rectangle {
                visible: app.found.length > 0 || app.finding
                anchors { left: side.right; top: header.bottom; bottom: statusBar.top; right: parent.right; margins: 10; rightMargin: 300 }
                radius: 10; color: theme.surface; border { color: theme.primary; width: 1 }
                Row {
                    id: fhead; x: 14; y: 10; spacing: 10
                    Glyph { name: "search"; size: 16; color: theme.primary; anchors.verticalCenter: parent.verticalCenter }
                    Text { anchors.verticalCenter: parent.verticalCenter; text: app.finding ? "Hľadám…" : "Nájdené „" + app.foundQuery + "“ · " + app.found.length; color: theme.fg; font { family: theme.fontUi; pixelSize: 14; weight: Font.Bold } }
                }
                IconButton { anchors { right: parent.right; rightMargin: 8; top: parent.top; topMargin: 6 } theme: theme; glyph: "x"; tip: "Zavrieť výsledky"; onClicked: app.found = [] }
                ListView {
                    anchors { left: parent.left; right: parent.right; top: fhead.bottom; bottom: parent.bottom; margins: 8; topMargin: 10 }
                    clip: true; model: app.found; boundsBehavior: Flickable.StopAtBounds
                    delegate: Rectangle {
                        id: fr
                        required property var modelData
                        width: ListView.view.width; height: 40; radius: 8; color: frm.containsMouse ? theme.hover : "transparent"
                        readonly property string name: modelData.path.split("/").pop()
                        readonly property string dir: modelData.path.substring(0, modelData.path.lastIndexOf("/"))
                        Glyph { x: 10; anchors.verticalCenter: parent.verticalCenter; name: fr.modelData.dir ? "folder" : "file"; size: 17; color: fr.modelData.dir ? theme.primary : theme.fgDim }
                        Column {
                            x: 36; width: parent.width - 46; anchors.verticalCenter: parent.verticalCenter
                            Text { width: parent.width; elide: Text.ElideRight; text: fr.name; color: theme.fg; font { family: theme.fontUi; pixelSize: 13; weight: Font.DemiBold } }
                            Text { width: parent.width; elide: Text.ElideMiddle; text: fr.dir.replace(app.home, "~"); color: theme.fgDim; font { family: theme.fontUi; pixelSize: 11 } }
                        }
                        MouseArea {
                            id: frm; anchors.fill: parent; hoverEnabled: true
                            onClicked: { app.activePane.filter = ""; header.searchText = ""; app.activePane.go(fr.modelData.dir ? fr.modelData.path : fr.dir); app.found = []; }
                            onDoubleClicked: if (!fr.modelData.dir) app.openPath(fr.modelData.path)
                        }
                    }
                }
            }

            // pripojenie servera (FTP/SFTP): adresa + voliteľné heslo (ide iba do latte-siet cez stdin)
            Rectangle {
                visible: app.connectOpen
                anchors.fill: parent; color: Qt.rgba(0, 0, 0, 0.35)
                MouseArea { anchors.fill: parent; onClicked: app.connectOpen = false }
                Rectangle {
                    anchors.centerIn: parent; width: 520; height: dlg.implicitHeight + 40; radius: 16
                    color: theme.surface; border { color: theme.outline; width: 1 }
                    MouseArea { anchors.fill: parent }
                    Column {
                        id: dlg; x: 20; y: 20; width: parent.width - 40; spacing: 12
                        Text { text: "Pripojiť server"; color: theme.fg; font { family: theme.fontDisplay; pixelSize: 20; weight: Font.DemiBold } }
                        Text { width: parent.width; wrapMode: Text.WordWrap; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 }
                               text: "Server sa otvorí ako priečinok v ~/Siet (v bočnej lište pod Sieť). SFTP bez hesla použije tvoje SSH kľúče. Heslo sa nikam neukladá." }
                        Rectangle {
                            width: parent.width; height: 40; radius: 10; color: theme.field; border { color: urlIn.activeFocus ? theme.primary : "transparent"; width: 1 }
                            TextInput { id: urlIn; anchors { fill: parent; leftMargin: 12; rightMargin: 12 } verticalAlignment: TextInput.AlignVCenter
                                        color: theme.fg; font { family: theme.fontMono; pixelSize: 13 }
                                        KeyNavigation.tab: pwIn
                                        onAccepted: app.connectServer(urlIn.text, pwIn.text) }
                            Text { x: 12; anchors.verticalCenter: parent.verticalCenter; visible: urlIn.text === ""; text: "sftp://meno@server  ·  ftp://server/priečinok"; color: theme.fgDim; font { family: theme.fontMono; pixelSize: 13 } }
                        }
                        Rectangle {
                            width: parent.width; height: 40; radius: 10; color: theme.field; border { color: pwIn.activeFocus ? theme.primary : "transparent"; width: 1 }
                            TextInput { id: pwIn; anchors { fill: parent; leftMargin: 12; rightMargin: 12 } verticalAlignment: TextInput.AlignVCenter
                                        echoMode: TextInput.Password; passwordCharacter: "•"; color: theme.fg; font { family: theme.fontUi; pixelSize: 13 }
                                        onAccepted: app.connectServer(urlIn.text, pwIn.text) }
                            Text { x: 12; anchors.verticalCenter: parent.verticalCenter; visible: pwIn.text === ""; text: "Heslo (ak treba)"; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 13 } }
                        }
                        Text { visible: app.connectError !== ""; width: parent.width; wrapMode: Text.WordWrap; text: app.connectError; color: theme.error; font { family: theme.fontUi; pixelSize: 12 } }
                        Row {
                            spacing: 10
                            Rectangle {
                                width: cbt.implicitWidth + 28; height: 38; radius: 10; color: app.connecting ? theme.field : theme.primary
                                Text { id: cbt; anchors.centerIn: parent; text: app.connecting ? "Pripájam…" : "Pripojiť"; color: app.connecting ? theme.fg : theme.fgOnPrimary; font { family: theme.fontUi; pixelSize: 13; weight: Font.Bold } }
                                MouseArea { anchors.fill: parent; enabled: !app.connecting; onClicked: app.connectServer(urlIn.text, pwIn.text) }
                            }
                            Rectangle {
                                width: zbt.implicitWidth + 28; height: 38; radius: 10; color: zm.containsMouse ? theme.hover : theme.field
                                Text { id: zbt; anchors.centerIn: parent; text: "Zrušiť"; color: theme.fg; font { family: theme.fontUi; pixelSize: 13; weight: Font.Bold } }
                                MouseArea { id: zm; anchors.fill: parent; hoverEnabled: true; onClicked: app.connectOpen = false }
                            }
                        }
                    }
                }
                onVisibleChanged: if (visible) { pwIn.text = ""; urlIn.forceActiveFocus(); } else root.forceActiveFocus()
            }

            ContextMenu { id: ctx; theme: theme }
        }
    }
}
