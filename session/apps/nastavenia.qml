// LatteOS — Nastavenia. Navigácia vrstvenými kartami (old/main_setting_v2.md: päť oblastí + Systém,
// vždy otvorená jedna karta), obsah v strede, detail vpravo (návrh V2: Stav · Oblasť · Uložené v).
// Radar: „Všetko prepínačmi, žiadne editovanie súborov“. Spúšťa sa: latte-app nastavenia [stránka]
import QtQuick
import Quickshell
import Quickshell.Io
import "common"

ShellRoot {
    id: app
    LatteTheme { id: theme }

    readonly property string home: Quickshell.env("HOME") || "/"
    readonly property string user: Quickshell.env("USER") || ""
    readonly property string cfgHome: Quickshell.env("XDG_CONFIG_HOME") || (home + "/.config")
    readonly property string stateHome: Quickshell.env("XDG_STATE_HOME") || (home + "/.local/state")
    property string section: (Quickshell.env("LATTE_APP_ARGS") || "").trim() || "domov"
    property var history: []
    property int historyIndex: -1
    property string search: ""
    property string status: ""

    // ── stav LatteOS ─────────────────────────────────────────────────────────────
    property var mode: ({})
    property string tierChoice: "auto"
    property string windowMode: "paska"
    property bool forceSafe: false
    property int crashCount: 0
    property var themes: []
    property var wallpapers: []
    property string greeter: "latte"
    property string modePref: "tema"
    property var bar: ({})            // prepisy [bar.main] z ~/.local/state/noctalia/settings.toml
    property var location: ({})       // prepisy [location]
    property var greeterConf: ({ background: "/usr/share/backgrounds/latteos/latteos-wallpaper1.jpg", color: "#1B1410", dim: "0.55", panel: "log", panel_title: "", panel_text: "" })
    property string crashLog: ""
    property var ai: ({})             // latte-ai status
    property var aiModels: []
    property string aiAnswer: ""
    property var clockZones: []
    property string about: ""
    property string storage: ""
    property string mascot: "macka"
    property string barAnim: ""        // prázdne = podľa stupňa (VM: pod kurzorom)
    property string barScene: "para"
    property bool wsWallpaper: false

    // ── strom Nastavení (kanonický, main_setting_v2.md §58) ──────────────────────
    // status: ready = funguje · partial = časť · planned = zatiaľ len plán
    readonly property var areas: [
        { key: "softver", title: "Softvér", glyph: "apps", summary: "AI: " + (ai.ok === "1" ? (ai.model || "pripravené") : "nenastavené"), owner: "App Manager",
          pages: [
            { key: "aplikacie", label: "Aplikácie", glyph: "apps", status: "partial" },
            { key: "instalacia", label: "Inštalácia aplikácií", glyph: "download", status: "partial" },
            { key: "aktualizacie", label: "Aktualizácie", glyph: "refresh", status: "partial" },
            { key: "ai", label: "AI", glyph: "sparkles", status: "ready" },
            { key: "spustanie", label: "Spúšťanie a na pozadí", glyph: "player-play", status: "partial" },
            { key: "sukromie", label: "Súkromie a NET", glyph: "world", status: "partial" } ] },
        { key: "data", title: "Dáta", glyph: "folder", summary: "Súbory · farebné štítky", owner: "Data Manager",
          pages: [
            { key: "subory", label: "Súbory a priečinky", glyph: "folder", status: "ready" },
            { key: "ulozisko", label: "Úložisko", glyph: "database", status: "partial" },
            { key: "zalohy", label: "Zálohovanie a obnova", glyph: "history", status: "planned" },
            { key: "synchronizacia", label: "Synchronizácia", glyph: "cloud", status: "planned" } ] },
        { key: "hardver", title: "Hardvér", glyph: "cpu", summary: (mode.renderer || "?") + " · stupeň " + (mode.tier || "?"), owner: "Device Manager",
          pages: [
            { key: "vykon", label: "Výkon a grafika", glyph: "bolt", status: "ready" },
            { key: "obrazovky", label: "Obrazovky", glyph: "device-desktop", status: "partial" },
            { key: "zvuk", label: "Zvuk", glyph: "volume", status: "partial" },
            { key: "siet", label: "Sieť", glyph: "wifi", status: "partial" },
            { key: "bluetooth", label: "Bluetooth a periférie", glyph: "bluetooth", status: "partial" },
            { key: "napajanie", label: "Napájanie", glyph: "battery", status: "partial" },
            { key: "diagnostika", label: "Diagnostika a pády", glyph: "stethoscope", status: "partial" } ] },
        { key: "ucet", title: "Účet", glyph: "user", summary: user, owner: "Session Manager",
          pages: [
            { key: "mojucet", label: "Môj účet", glyph: "user", status: "planned" },
            { key: "pouzivatelia", label: "Používatelia", glyph: "users", status: "planned" },
            { key: "prihlasovanie", label: "Prihlasovanie", glyph: "login", status: "ready" },
            { key: "uzamknutie", label: "Uzamknutie", glyph: "lock", status: "planned" } ] },
        { key: "prostredie", title: "Prostredie", glyph: "palette", summary: theme.themeName + " · " + modeName(modePref), owner: "Prispôsobenie",
          pages: [
            { key: "motiv", label: "Motív a farby", glyph: "palette", status: "ready" },
            { key: "pozadie", label: "Pozadie", glyph: "photo", status: "ready" },
            { key: "okna", label: "Okná", glyph: "layout-columns", status: "ready" },
            { key: "lista", label: "Lišta a systémové menu", glyph: "layout-bottombar", status: "ready" },
            { key: "oznamenia", label: "Oznámenia", glyph: "bell", status: "planned" },
            { key: "efekty", label: "Animácie a efekty", glyph: "sparkles", status: "partial" },
            { key: "pristupnost", label: "Prístupnosť", glyph: "accessible", status: "planned" } ] },
        { key: "system", title: "Systém", glyph: "shield", summary: (mode.mode || "?").toUpperCase() + " · pády " + crashCount, owner: "LatteOS",
          pages: [
            { key: "start", label: "Štart a režim", glyph: "shield", status: "ready" },
            { key: "cas", label: "Dátum, čas a poloha", glyph: "clock", status: "ready" },
            { key: "jazyk", label: "Jazyk a región", glyph: "language", status: "planned" },
            { key: "klavesnica", label: "Klávesnica a vstup", glyph: "keyboard", status: "planned" },
            { key: "o", label: "O LatteOS", glyph: "info-circle", status: "ready" } ] }
    ]
    readonly property var allPages: {
        const out = [{ key: "domov", label: "Domov", glyph: "home", status: "ready", area: "", areaTitle: "Prehľad", owner: "LatteOS" }];
        for (const a of areas) for (const p of a.pages) out.push(Object.assign({ area: a.key, areaTitle: a.title, owner: a.owner }, p));
        return out;
    }
    readonly property var current: allPages.find(p => p.key === section) || allPages[0]

    function go(key, push) {
        if (key === "zariadenia") key = "vykon";        // staré odkazy
        if (key === "vzhlad") key = "motiv";
        section = key;
        const p = allPages.find(x => x.key === key);
        if (p && p.area) side.openArea = p.area;
        if (push !== false) { history = history.slice(0, historyIndex + 1).concat([key]); historyIndex = history.length - 1; }
        if (key === "ai") { aiStatus.running = true; aiList.running = true; }
        if (key === "o") aboutProc.running = true;
        if (key === "ulozisko" || key === "domov") storageProc.running = true;
    }
    Component.onCompleted: { go(section); aiStatus.running = true; }

    function modeName(m) { return ({ tema: "podľa témy", dark: "tmavý", light: "svetlý", auto: "automaticky" })[m] || m; }

    // ── načítanie stavu ─────────────────────────────────────────────────────────
    FileView {
        path: "/run/latteos/mode.toml"; printErrors: false; watchChanges: true; onFileChanged: reload()
        onLoaded: {
            const m = {};
            for (const l of text().split("\n")) { const r = l.match(/^(\w+) = "?([^"]*)"?$/); if (r && !(r[1] in m)) m[r[1]] = r[2]; }
            app.mode = m;
        }
    }
    FileView { path: app.cfgHome + "/latteos/tier"; printErrors: false; watchChanges: true; onFileChanged: reload()
               onLoaded: app.tierChoice = text().trim() || "auto"; onLoadFailed: app.tierChoice = "auto" }
    FileView { path: app.cfgHome + "/latteos/theme-mode"; printErrors: false; watchChanges: true; onFileChanged: reload()
               onLoaded: app.modePref = text().trim() || "tema"; onLoadFailed: app.modePref = "tema" }
    FileView { path: app.stateHome + "/latteos/window-mode"; printErrors: false; watchChanges: true; onFileChanged: reload()
               onLoaded: app.windowMode = text().trim() || "paska" }
    FileView { path: "/var/lib/latteos/crash-count"; printErrors: false; watchChanges: true; onFileChanged: reload()
               onLoaded: app.crashCount = parseInt(text()) || 0 }
    FileView { path: "/etc/latteos/boot.toml"; printErrors: false
               onLoaded: { const r = text().match(/^greeter = "(\w+)"/m); app.greeter = r ? r[1] : "latte"; } }
    FileView { path: "/var/lib/latteos/greeter/last-crash.log"; printErrors: false; watchChanges: true; onFileChanged: reload()
               onLoaded: app.crashLog = text().trim(); onLoadFailed: app.crashLog = "" }
    FileView {
        id: greeterFile
        path: "/var/lib/latteos/greeter/greeter.conf"; printErrors: false
        onLoaded: {
            const c = Object.assign({}, app.greeterConf);
            for (const l of text().split("\n")) { const r = l.match(/^\s*(\w+)\s*=\s*"(.*)"\s*$/); if (r) c[r[1]] = r[2].replace(/\\n/g, "\n"); }
            app.greeterConf = c;
        }
    }
    function setGreeter(k, v) {
        const c = Object.assign({}, greeterConf); c[k] = v; greeterConf = c;
        let out = "# LatteOS — vzhľad obrazovky prihlásenia (zapísali Nastavenia › Účet › Prihlasovanie)\n";
        for (const key of ["background", "color", "dim", "panel", "panel_title", "panel_text"])
            out += key + " = \"" + String(c[key] || "").replace(/"/g, "'").replace(/\n/g, "\\n") + "\"\n";
        greeterFile.setText(out);
        status = "Obrazovka prihlásenia uložená (prejaví sa pri ďalšom prihlásení)";
    }
    FileView {
        path: app.stateHome + "/noctalia/settings.toml"; printErrors: false; watchChanges: true; onFileChanged: reload()
        onLoaded: {
            const t = {}; let sec = "";
            for (const l of text().split("\n")) {
                const h = l.match(/^\s*\[([^\]]+)\]\s*$/); if (h) { sec = h[1]; continue; }
                const r = l.match(/^\s*(\w+)\s*=\s*"?([^"]*)"?\s*$/); if (r) { (t[sec] = t[sec] || {})[r[1]] = r[2]; }
            }
            app.bar = t["bar.main"] || {}; app.location = t["location"] || {};
        }
    }
    FileView {
        id: clockFile
        path: app.cfgHome + "/latteos/clock.conf"; printErrors: false
        onLoaded: { const r = text().match(/^zones = "(.*)"/m); app.clockZones = r && r[1] ? r[1].split(",") : []; }
    }
    FileView { path: app.cfgHome + "/latteos/mascot"; printErrors: false; watchChanges: true; onFileChanged: reload()
               onLoaded: app.mascot = text().trim() || "macka"; onLoadFailed: app.mascot = "macka" }
    FileView { path: app.cfgHome + "/latteos/bar-anim"; printErrors: false; watchChanges: true; onFileChanged: reload()
               onLoaded: app.barAnim = text().trim(); onLoadFailed: app.barAnim = "" }
    FileView { path: app.cfgHome + "/latteos/bar-scene"; printErrors: false; watchChanges: true; onFileChanged: reload()
               onLoaded: app.barScene = text().trim() || "para"; onLoadFailed: app.barScene = "para" }
    FileView { path: app.cfgHome + "/latteos/wallpaper-per-workspace"; printErrors: false; watchChanges: true; onFileChanged: reload()
               onLoaded: app.wsWallpaper = true; onLoadFailed: app.wsWallpaper = false }
    function writePref(name, value, msg) {
        if (value === "") run(["rm", "-f", app.cfgHome + "/latteos/" + name], msg);
        else run(["sh", "-c", "mkdir -p \"$(dirname \"$1\")\" && printf '%s\\n' \"$2\" > \"$1\"", "sh", app.cfgHome + "/latteos/" + name, value], msg);
    }
    function toggleZone(z) {
        const zs = clockZones.indexOf(z) >= 0 ? clockZones.filter(x => x !== z) : clockZones.concat([z]);
        clockZones = zs;
        clockFile.setText("# LatteOS — ďalšie časové pásma v paneli Čas (Nastavenia › Systém › Dátum a čas)\nzones = \"" + zs.join(",") + "\"\n");
    }

    component Cmd: Process {
        id: c
        signal done(string out)
        stdout: StdioCollector { onStreamFinished: c.done(this.text) }
    }
    Cmd {
        id: scan; running: true
        command: ["sh", "-c", "test -e /var/lib/latteos/force-safe && echo FORCE; for f in /usr/share/latteos/themes/*.theme; do printf 'T %s|%s|%s\\n' \"$(basename $f .theme)\" \"$(sed -n 's/^name = //p' $f)\" \"$(sed -n 's/^desc = //p' $f)\"; done; for f in /usr/share/backgrounds/latteos/*; do echo \"W $f\"; done"]
        onDone: (out) => {
            const th = [], wp = []; let fs = false;
            for (const l of out.split("\n")) {
                if (l === "FORCE") fs = true;
                else if (l.startsWith("T ")) { const p = l.slice(2).split("|"); th.push({ id: p[0], name: p[1], desc: p[2] }); }
                else if (l.startsWith("W ")) wp.push(l.slice(2));
            }
            app.forceSafe = fs; app.themes = th; app.wallpapers = wp;
        }
    }
    Timer { interval: 4000; repeat: true; running: true; onTriggered: scan.running = true }
    Cmd {
        id: aiStatus; command: ["latte-ai", "status"]
        onDone: (out) => { const s = {}; for (const l of out.split("\n")) { const i = l.indexOf("="); if (i > 0) s[l.slice(0, i)] = l.slice(i + 1); } app.ai = s; }
    }
    Cmd {
        id: aiList; command: ["latte-ai", "models"]
        onDone: (out) => app.aiModels = out.split("\n").filter(l => l !== "").map(l => { const p = l.split("\t"); return { id: p[0], state: p[1] || "" }; })
    }
    Cmd {
        id: aiAsk; command: ["latte-ai", "ask", "Predstav sa jednou krátkou vetou po slovensky."]
        onDone: (out) => app.aiAnswer = out.trim() || "(bez odpovede — pozri stav vpravo)"
    }
    Cmd {
        id: aboutProc
        command: ["sh", "-c", ". /etc/os-release; echo \"Systém|$PRETTY_NAME\"; echo \"Jadro|$(uname -r)\"; echo \"Hyprland|$(rpm -q --qf '%{VERSION}-%{RELEASE}' hyprland 2>/dev/null)\"; echo \"Noctalia|$(noctalia --version 2>/dev/null | head -1)\"; echo \"Quickshell|$(qs --version 2>/dev/null | head -1)\"; echo \"Procesor|$(sed -n 's/^model name[^:]*: //p' /proc/cpuinfo | head -1)\"; echo \"Pamäť|$(free -h | awk '/^Mem/{print $2}')\""]
        onDone: (out) => app.about = out
    }
    Cmd {
        id: storageProc
        command: ["sh", "-c", "df -h --output=target,size,used,avail,pcent -x tmpfs -x devtmpfs -x efivarfs -x squashfs | tail -n +2"]
        onDone: (out) => app.storage = out
    }

    Process { id: runner }
    function run(cmd, msg) { runner.command = cmd; runner.running = true; if (msg) app.status = msg; }
    function setTier(t) {
        if (t === "auto") run(["sh", "-c", "rm -f \"$1\" && hyprctl reload", "sh", app.cfgHome + "/latteos/tier"], "Stupeň: automaticky");
        else run(["sh", "-c", "mkdir -p \"$(dirname \"$1\")\" && printf '%s\\n' \"$2\" > \"$1\" && hyprctl reload", "sh", app.cfgHome + "/latteos/tier", t], "Stupeň: " + t);
        app.tierChoice = t;
    }
    function shellSet(key, value, msg) {
        if (value === null) run(["latte-shellset", "unset", key], msg);
        else run(["latte-shellset", "set", key, String(value)], msg);
    }
    function aiSet(key, value) { run(["sh", "-c", "latte-ai set \"$1\" \"$2\"", "sh", key, value], "AI: " + key + " = " + (value || "automaticky")); aiRefresh.restart(); }
    Timer { id: aiRefresh; interval: 400; onTriggered: { aiStatus.running = true; aiList.running = true; } }

    // ── okno ─────────────────────────────────────────────────────────────────────
    FloatingWindow {
        title: "Nastavenia — LatteOS"
        implicitWidth: 1220; implicitHeight: 780
        color: theme.surface

        CardStack {
            id: side
            theme: theme
            anchors { left: parent.left; top: parent.top; bottom: parent.bottom }
            areas: app.search === "" ? app.areas
                 : app.areas.map(a => Object.assign({}, a, { pages: a.pages.filter(p => (p.label + " " + a.title).toLowerCase().includes(app.search.toLowerCase())) }))
                            .filter(a => a.pages.length > 0)
            current: app.section
            onActivated: (area, page) => app.go(page)
            onHomeRequested: app.go("domov")
        }

        HeaderBar {
            id: header
            theme: theme
            anchors { left: side.right; right: parent.right; top: parent.top }
            title: (app.current.areaTitle ? app.current.areaTitle + " › " : "") + app.current.label
            canBack: app.historyIndex > 0
            canForward: app.historyIndex < app.history.length - 1
            searchPlaceholder: "Hľadať nastavenie"
            onBack: { app.historyIndex--; app.go(app.history[app.historyIndex], false); }
            onForward: { app.historyIndex++; app.go(app.history[app.historyIndex], false); }
            onSearchChanged: (t) => {
                app.search = t;
                const hit = app.allPages.find(p => t !== "" && p.label.toLowerCase().includes(t.toLowerCase()));
                if (hit && hit.area) side.openArea = hit.area;
            }
            onCloseRequested: Qt.quit()
        }

        Flickable {
            id: content
            anchors { left: side.right; top: header.bottom; bottom: parent.bottom; right: detail.left; margins: 24 }
            contentHeight: body.implicitHeight + 24; clip: true
            Column {
                id: body
                width: content.width
                spacing: 16
                Text { text: app.current.label; color: theme.fg; font { family: theme.fontDisplay; pixelSize: 28; weight: Font.DemiBold } }
                Text { width: parent.width; wrapMode: Text.WordWrap; text: app.intro(app.section); color: theme.fgDim; font { family: theme.fontUi; pixelSize: 14 } }
                Loader { width: parent.width; sourceComponent: app.page(app.section) }
            }
        }

        // detail (návrh V2: stav stránky, oblasť, kde je uložená)
        Rectangle {
            id: detail
            anchors { right: parent.right; top: header.bottom; bottom: parent.bottom; margins: 14 }
            width: 260; radius: theme.radius
            color: Qt.rgba(0, 0, 0, theme.mode === "dark" ? 0.16 : 0.04); border { color: theme.line; width: 1 }
            Column {
                anchors { fill: parent; margins: 18 }
                spacing: 12
                Text { width: parent.width; wrapMode: Text.WordWrap; text: app.current.label; color: theme.fg; font { family: theme.fontUi; pixelSize: 17; weight: Font.Bold } }
                Text {
                    text: ({ ready: "● Funguje", partial: "◐ Čiastočne", planned: "○ Zatiaľ len plán" })[app.current.status]
                    color: app.current.status === "planned" ? theme.fgDim : theme.primary; font { family: theme.fontUi; pixelSize: 13; weight: Font.Bold }
                }
                Text { text: "STAV"; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 10; weight: Font.Bold; letterSpacing: 0.8 } }
                Text { width: parent.width; wrapMode: Text.WordWrap; text: app.stateText(app.section); color: theme.fg; font { family: theme.fontUi; pixelSize: 12 } }
                Text { text: "OBLASŤ"; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 10; weight: Font.Bold; letterSpacing: 0.8 } }
                Text { width: parent.width; wrapMode: Text.WordWrap; text: (app.current.areaTitle || "Prehľad") + " · " + app.current.owner; color: theme.fg; font { family: theme.fontUi; pixelSize: 13 } }
                Text { text: "ULOŽENÉ V"; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 10; weight: Font.Bold; letterSpacing: 0.8 } }
                Text { width: parent.width; wrapMode: Text.WrapAnywhere; text: app.storedIn(app.section); color: theme.fgDim; font { family: theme.fontMono; pixelSize: 11 } }
            }
            Text {
                anchors { left: parent.left; right: parent.right; bottom: parent.bottom; margins: 18 }
                wrapMode: Text.WordWrap; text: app.status; color: theme.primary; font { family: theme.fontUi; pixelSize: 12 }
            }
        }
    }

    // ── texty stránok ─────────────────────────────────────────────────────────────
    function intro(k) {
        return ({
            domov: "Stav systému na jednom mieste. Klik na kartu otvorí jej nastavenia.",
            aplikacie: "App Manager spravuje aplikácie; tu je rýchly vstup.",
            obrazovky: "Obrazovky spravuje Správca zariadení.", zvuk: "Zvuk spravuje Správca zariadení.", siet: "Sieť spravuje Správca zariadení.",
            bluetooth: "Bluetooth spravuje Správca zariadení.", napajanie: "Napájanie spravuje Správca zariadení.",
            instalacia: "Inštalácia jedným klikom a kontrola stiahnutých súborov.",
            aktualizacie: "Aktualizácie systému a aplikácií.",
            sukromie: "Kto smie na internet (NET) a k súborom.",
            spustanie: "Aplikácie a služby, ktoré sa spúšťajú samé.",
            ai: "Kam sa pýta režim AI v Text Bare: malý model na tomto PC, tvoj domáci server (napr. LM Studio), alebo veľké AI v cloude.",
            subory: "Súbory (Data Manager) otvoríš tlačidlom nižšie alebo Super+E. Priečinky sa dajú farebne označiť pravým klikom.",
            ulozisko: "Pripojené disky a voľné miesto. Upratovanie a veľké súbory pribudnú v Data Manageri.",
            vykon: "Stupeň určuje efekty (sklo, tiene, žiara, animácie). Automaticky ho volí štart systému podľa hardvéru.",
            diagnostika: "Počítadlo pádov a prvý log z posledného pádu relácie. Ten istý záznam ukazuje vývojárska obrazovka prihlásenia.",
            prihlasovanie: "Vzhľad obrazovky prihlásenia: obrázok alebo farba a ľavý panel. Posledné dva účty sa ukazujú samé.",
            motiv: "Téma prefarbí lištu, panely, okná aj aplikácie naraz. Každá téma má tmavú aj svetlú verziu.",
            pozadie: "Tapeta plochy. Témy si pri zmene vyberú svoju, tu ju môžeš zmeniť.",
            okna: "Ako sa ukladajú okná. Super+W prepína režimy aj bez otvárania nastavení.",
            lista: "Spodná lišta z ostrovov. Šírku určuje odsadenie od okrajov obrazovky. Vľavo dlaždica aplikácií, vpravo maskot.",
            efekty: "Efekty kompozitora riadi stupeň výkonu; pohyblivé materiály tém prídu na silnejšom HW.",
            start: "Režim NORMAL (Hyprland) alebo SAFE (labwc bez GPU). SAFE naskočí sám po dvoch pádoch za sebou.",
            cas: "Poloha určuje východ a západ slnka pre automatický svetlý/tmavý režim a nočné svetlo. Ďalšie časové pásma ukáže panel Čas.",
            o: "Verzie častí systému, z ktorých sa LatteOS skladá."
        })[k] || (plans[k] ? "Pripravujeme. Čo tu bude:" : "");
    }
    readonly property var plans: ({
        aplikacie: ["zoznam aplikácií (Flatpak, RPM, AppImage, Windows cez Proton, Android cez Waydroid)", "predvolené aplikácie", "App Manager: „Bude to fungovať?“ pred inštaláciou"],
        instalacia: ["inštalácia jedným klikom", "zdroje: Flathub, Fedora, LatteOS", "náhľad oprávnení pred inštaláciou"],
        aktualizacie: ["systém (Atomic: celý obraz naraz s návratom)", "aplikácie", "firmware (fwupd)", "„Aktualizovať všetko“"],
        spustanie: ["aplikácie pri prihlásení", "služby na pozadí", "Latte System Monitor: autorun položky s pôvodom"],
        sukromie: ["tlačidlo NET pre každú aplikáciu", "dôveryhodné / nedôveryhodné aplikácie", "kamera, mikrofón, poloha"],
        zalohy: ["zálohy domovského priečinka (restic/btrfs snapshoty)", "obnova súboru z minulosti"],
        synchronizacia: ["priečinky v cloude", "dáta aplikácií medzi PC", "prenos profilu cez USB"],
        obrazovky: ["rozlíšenie, frekvencia, mierka, otočenie", "potvrdenie do 15 s, inak návrat", "HDR a VRR na reálnom HW"],
        zvuk: ["výstup a vstup", "hlasitosť aplikácií", "Bluetooth slúchadlá"],
        siet: ["Wi-Fi a káblové pripojenia", "VPN", "zdieľanie pripojenia"],
        bluetooth: ["párovanie", "ovládače a periférie"],
        napajanie: ["profil výkonu", "uspávanie a vypnutie obrazovky", "batéria"],
        mojucet: ["meno, obrázok", "prihlásenie mobilom"],
        pouzivatelia: ["pridať a odstrániť účet", "rodičovská kontrola"],
        uzamknutie: ["automatické zamknutie", "obrazovka zámku (Noctalia)"],
        oznamenia: ["nerušiť a plán", "oznámenia z mobilu (KDE Connect)", "pravidlá podľa aplikácie"],
        pristupnost: ["veľké písmo a kontrast", "čítačka obrazovky", "bez animácií"],
        jazyk: ["jazyk systému", "formáty dátumu a čísel"],
        klavesnica: ["rozloženia (teraz sk, us; Alt+Shift)", "skratky LatteOS"]
    })
    function stateText(k) {
        const m = app.mode;
        if (k === "domov" || k === "start") return (m.mode || "?").toUpperCase() + " · " + (m.renderer || "?") + " · stupeň " + (m.tier || "?") + (m.reason ? "\n" + m.reason : "");
        if (k === "motiv") return "Téma " + theme.themeName + " · režim " + modeName(modePref) + " (teraz " + theme.mode + ")";
        if (k === "okna") return ({ paska: "Nekonečná páska", dlazdice: "Dlaždice", plavajuce: "Plávajúce okná" })[app.windowMode] || app.windowMode;
        if (k === "vykon" || k === "efekty") return app.tierChoice === "auto" ? "Automaticky (" + (m.tier || "?") + ")" : "Vynútený: " + app.tierChoice;
        if (k === "ai") return (ai.ok === "1" ? "● Dostupné" : "× Nedostupné") + "\n" + (ai.target || "") + (ai.model ? "\nmodel " + ai.model : "") + (ai.error ? "\n" + ai.error : "");
        if (k === "diagnostika") return "Pády NORMAL: " + crashCount + " / 2" + (crashLog ? "\n" + crashLog.split("\n")[0] : "\nbez záznamu pádu");
        if (k === "prihlasovanie") return "Greeter: " + greeter + " · panel " + greeterConf.panel;
        if (k === "lista") return "Hrúbka " + (bar.thickness || 56) + " · okraje " + (bar.margin_ends || 12) + " · spodok " + (bar.margin_edge || 10);
        if (k === "cas") return "Poloha " + (location.latitude || "48.74") + ", " + (location.longitude || "19.15") + (clockZones.length ? "\nPásma: " + clockZones.join(", ") : "");
        if (plans[k]) return "Zatiaľ len plán";
        return "—";
    }
    function storedIn(k) {
        return ({
            domov: "/run/latteos/mode.toml", motiv: "~/.config/latteos/theme\n~/.config/latteos/theme-mode", pozadie: "~/.local/state/noctalia/settings.toml",
            okna: "~/.local/state/latteos/window-mode", vykon: "~/.config/latteos/tier", efekty: "~/.config/latteos/tier",
            start: "/etc/latteos/boot.toml\n/var/lib/latteos/", ai: "~/.config/latteos/ai.toml\n~/.config/latteos/ai-keys (0600)",
            lista: "~/.local/state/noctalia/settings.toml [bar.main]\n~/.config/latteos/bar-anim, bar-scene, mascot", cas: "~/.local/state/noctalia/settings.toml [location]\n~/.config/latteos/clock.conf",
            prihlasovanie: "/var/lib/latteos/greeter/greeter.conf", diagnostika: "/var/lib/latteos/greeter/last-crash.log\n/var/lib/latteos/crash-count",
            subory: "~/.config/latteos/subory.json\n~/.config/latteos/tags.json"
        })[k] || "—";
    }

    // ── ovládacie prvky ──────────────────────────────────────────────────────────
    component Card: Rectangle {
        id: card
        property string title; property string sub; property bool selected: false; property string glyph: ""
        signal clicked()
        width: 200; height: 76; radius: 12
        color: selected ? Qt.rgba(theme.primary.r, theme.primary.g, theme.primary.b, 0.16) : (cm.containsMouse ? theme.hover : theme.field)
        border { color: selected ? theme.primary : "transparent"; width: 1.5 }
        Glyph { visible: card.glyph !== ""; x: 14; anchors.verticalCenter: parent.verticalCenter; name: card.glyph || "point"; size: 22; color: card.selected ? theme.primary : theme.fg }
        Column {
            anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter; margins: 14; leftMargin: card.glyph !== "" ? 48 : 14 }
            spacing: 3
            Text { width: parent.width; elide: Text.ElideRight; text: card.title; color: theme.fg; font { family: theme.fontUi; pixelSize: 14; weight: Font.Bold } }
            Text { width: parent.width; wrapMode: Text.WordWrap; maximumLineCount: 2; elide: Text.ElideRight; text: card.sub; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 11 } }
        }
        MouseArea { id: cm; anchors.fill: parent; hoverEnabled: true; onClicked: card.clicked() }
    }
    component Heading: Text { color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12; weight: Font.Bold; letterSpacing: 0.8 } }
    component Button: Rectangle {
        id: btn
        property string label; property string glyph: ""; property bool danger: false; property bool primaryStyle: false
        signal clicked()
        width: row.implicitWidth + 28; height: 38; radius: 10
        color: primaryStyle ? theme.primary : (bm.containsMouse ? theme.hover : theme.field)
        Row { id: row; anchors.centerIn: parent; spacing: 8
            Glyph { visible: btn.glyph !== ""; name: btn.glyph || "x"; size: 16; color: btn.primaryStyle ? theme.fgOnPrimary : (btn.danger ? theme.error : theme.fg) }
            Text { text: btn.label; color: btn.primaryStyle ? theme.fgOnPrimary : (btn.danger ? theme.error : theme.fg); font { family: theme.fontUi; pixelSize: 13; weight: Font.Bold } } }
        MouseArea { id: bm; anchors.fill: parent; hoverEnabled: true; onClicked: btn.clicked() }
    }
    // voľby vedľa seba (segmenty)
    component Segments: Row {
        id: seg
        property var options: []      // [[hodnota, text]]
        property string value
        signal picked(string v)
        spacing: 6
        Repeater {
            model: seg.options
            Rectangle {
                required property var modelData
                readonly property bool on: seg.value === modelData[0]
                width: st.implicitWidth + 28; height: 36; radius: 10
                color: on ? Qt.rgba(theme.primary.r, theme.primary.g, theme.primary.b, 0.18) : (sm.containsMouse ? theme.hover : theme.field)
                border { color: on ? theme.primary : "transparent"; width: 1.5 }
                Text { id: st; anchors.centerIn: parent; text: modelData[1]; color: theme.fg; font { family: theme.fontUi; pixelSize: 13; weight: on ? Font.Bold : Font.Medium } }
                MouseArea { id: sm; anchors.fill: parent; hoverEnabled: true; onClicked: seg.picked(modelData[0]) }
            }
        }
    }
    // číslo so šípkami (– hodnota +)
    component Stepper: Row {
        id: sp
        property string label; property real value; property real step: 1; property real min: 0; property real max: 100; property string unit: " px"
        signal stepped(real v)
        spacing: 10
        Text { width: 230; anchors.verticalCenter: parent.verticalCenter; text: sp.label; color: theme.fg; font { family: theme.fontUi; pixelSize: 13 } }
        Rectangle {
            width: 150; height: 36; radius: 10; color: theme.field
            IconButton { anchors { left: parent.left; verticalCenter: parent.verticalCenter } theme: theme; glyph: "minus"; enabledState: sp.value > sp.min; onClicked: sp.stepped(Math.max(sp.min, sp.value - sp.step)) }
            Text { anchors.centerIn: parent; text: (sp.step < 1 ? sp.value.toFixed(2) : Math.round(sp.value)) + sp.unit; color: theme.fg; font { family: theme.fontUi; pixelSize: 13; weight: Font.Bold } }
            IconButton { anchors { right: parent.right; verticalCenter: parent.verticalCenter } theme: theme; glyph: "plus"; enabledState: sp.value < sp.max; onClicked: sp.stepped(Math.min(sp.max, sp.value + sp.step)) }
        }
    }
    // textové pole; Enter alebo strata fokusu = uložiť
    component Field: Rectangle {
        id: fld
        property string text; property string placeholder; property bool secret: false; property bool multiline: false
        signal committed(string t)
        width: 420; height: multiline ? 110 : 38; radius: 10; color: theme.field
        border { color: inp.activeFocus ? theme.primary : "transparent"; width: 1 }
        TextEdit {
            id: inp
            visible: fld.multiline
            anchors { fill: parent; margins: 10 }
            wrapMode: TextEdit.Wrap; text: fld.text; color: theme.fg; selectionColor: theme.primary
            font { family: theme.fontUi; pixelSize: 13 }
            onActiveFocusChanged: if (!activeFocus && fld.multiline) fld.committed(text)
        }
        TextInput {
            id: one
            visible: !fld.multiline
            anchors { fill: parent; leftMargin: 12; rightMargin: 12 }
            verticalAlignment: TextInput.AlignVCenter; clip: true
            text: fld.text; color: theme.fg; selectionColor: theme.primary
            echoMode: fld.secret ? TextInput.Password : TextInput.Normal
            font { family: theme.fontUi; pixelSize: 13 }
            onAccepted: { fld.committed(text); focus = false; }
            onActiveFocusChanged: if (!activeFocus) fld.committed(text)
        }
        Text {
            x: 12; y: fld.multiline ? 10 : (parent.height - height) / 2
            visible: (fld.multiline ? inp.text : one.text) === ""; text: fld.placeholder; color: theme.fgDim
            font { family: theme.fontUi; pixelSize: 13 }
        }
    }

    // stránky, ktoré vlastní iný manažér (main_setting_v2 §57: stav + odkaz, nie druhá implementácia)
    readonly property var managed: ({
        aplikacie: ["Aplikácie", "Nainštalované aplikácie, zdroj, veľkosť, odinštalovanie.", ["latte-app", "aplikacie", "nainstalovane"]],
        instalacia: ["Aplikácie", "Objavovať: Flathub (bez hesla, v izolácii) a Fedora. „Bude to fungovať?“ pre stiahnuté súbory.", ["latte-app", "aplikacie", "objavovat"]],
        aktualizacie: ["Aplikácie", "Systém (dnf) aj Flatpak aplikácie na jednom mieste, „Aktualizovať všetko“.", ["latte-app", "aplikacie", "aktualizacie"]],
        sukromie: ["Aplikácie", "NET pre Flatpak aplikácie už funguje (internet áno/nie). Natívne aplikácie a Windows hry príde s F6.", ["latte-app", "aplikacie", "opravnenia"]],
        obrazovky: ["Správca zariadení", "Rozlíšenie a mierka obrazovky s potvrdením do 15 s (inak sa zmena vráti). Uloží sa do ~/.config/latteos/monitors.lua.", ["latte-app", "zariadenia", "obrazovky"]],
        zvuk: ["Správca zariadení", "Zvukové karty a predvolený výstup; hlasitosť je v Zariadeniach na lište.", ["latte-app", "zariadenia", "zvuk"]],
        siet: ["Správca zariadení", "Sieťové karty a pripojenia (NetworkManager). Wi-Fi a VPN cez nmtui, neskôr priamo.", ["latte-app", "zariadenia", "siet"]],
        bluetooth: ["Správca zariadení", "Bluetooth adaptéry; párovanie v riadiacom centre.", ["latte-app", "zariadenia", "bluetooth"]],
        napajanie: ["Správca zariadení", "Batéria, adaptér a profil výkonu.", ["latte-app", "zariadenia", "napajanie"]],
        spustanie: ["Monitor", "Čo sa spúšťa po prihlásení: autostart, služby tvojho účtu, časovače. Vypnutie jedným klikom.", ["latte-app", "monitor", "autorun"]]
    })
    function page(k) {
        if (managed[k]) return pManaged;
        return ({ domov: pDomov, ai: pAi, subory: pSubory, ulozisko: pUlozisko, vykon: pVykon, diagnostika: pDiag,
                  prihlasovanie: pGreeter, motiv: pMotiv, pozadie: pPozadie, okna: pOkna, lista: pLista, efekty: pEfekty,
                  start: pStart, cas: pCas, o: pO })[k] || pPlan;
    }

    // ── stránky ──────────────────────────────────────────────────────────────────
    Component {
        id: pDomov
        Column {
            spacing: 18
            Flow {
                width: parent.width; spacing: 12
                Repeater {
                    model: [
                        ["system", "start", "LatteOS", (app.mode.mode || "?").toUpperCase() + " · pády " + app.crashCount + " / 2", "shield"],
                        ["hardver", "vykon", "Hardvér", (app.mode.renderer || "?") + " · stupeň " + (app.mode.tier || "?"), "cpu"],
                        ["data", "ulozisko", "Dáta", (app.storage.split("\n").find(l => l.startsWith("/ ")) || "/ ?").trim().split(/\s+/).slice(3, 5).join(" voľné · ") + " obsadené", "database"],
                        ["softver", "ai", "AI", app.ai.ok === "1" ? (app.ai.model || "pripravené") : "nenastavené", "sparkles"],
                        ["prostredie", "motiv", "Prostredie", theme.themeName + " · " + app.modeName(app.modePref), "palette"],
                        ["ucet", "prihlasovanie", "Účet", app.user + " · prihlásenie " + app.greeter, "user"]
                    ]
                    Card {
                        required property var modelData
                        width: 250; glyph: modelData[4]; title: modelData[2]; sub: modelData[3]
                        onClicked: app.go(modelData[1])
                    }
                }
            }
            Heading { text: "NEDÁVNO POUŽITÉ" }
            Flow {
                width: parent.width; spacing: 8
                Repeater {
                    model: app.history.filter((k, i, a) => k !== "domov" && a.lastIndexOf(k) === i).slice(-5).reverse()
                    Button { required property string modelData; label: (app.allPages.find(p => p.key === modelData) || {}).label || modelData; onClicked: app.go(modelData) }
                }
            }
        }
    }
    Component {
        id: pAi
        Column {
            spacing: 14
            Heading { text: "KDE BEŽÍ AI" }
            Flow {
                width: parent.width; spacing: 10
                Repeater {
                    model: [["lokalne", "Tento počítač", "Ollama, malý model; bez internetu", "device-desktop"],
                            ["domaci", "Domáci server", "LM Studio, llama.cpp, Ollama v sieti alebo cez SSH", "server"],
                            ["cloud", "Veľké AI (cloud)", "Claude, ChatGPT, Gemini, Mistral — s API kľúčom", "cloud"]]
                    Card {
                        required property var modelData
                        width: 250; glyph: modelData[3]; title: modelData[1]; sub: modelData[2]; selected: app.ai.provider === modelData[0]
                        onClicked: app.aiSet("provider", modelData[0])
                    }
                }
            }
            // domáci server
            Column {
                visible: app.ai.provider === "domaci"; spacing: 10; width: parent.width
                Heading { text: "ADRESA SERVERA (OpenAI API)" }
                Field { text: (app.ai.target || "").split(" cez ssh ")[0]; placeholder: "http://192.168.56.1:1234/v1"; onCommitted: (t) => { if (t !== "" && t !== (app.ai.target || "").split(" cez ssh ")[0]) app.aiSet("url", t); } }
                Heading { text: "SSH PRÍSTUP (voliteľné)" }
                Text { width: parent.width; wrapMode: Text.WordWrap; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 }
                       text: "Ak server nie je otvorený do siete: zadaj pouzivatel@server. LatteOS otvorí SSH tunel na port z adresy (prihlásenie kľúčom, ssh-copy-id)." }
                Field { text: (app.ai.target || "").split(" cez ssh ")[1] || ""; placeholder: "pouzivatel@domaci-server"; onCommitted: (t) => { if (t !== ((app.ai.target || "").split(" cez ssh ")[1] || "")) app.aiSet("ssh", t); } }
            }
            // cloud
            Column {
                visible: app.ai.provider === "cloud"; spacing: 10; width: parent.width
                Heading { text: "SLUŽBA" }
                Segments {
                    options: [["anthropic", "Claude"], ["openai", "ChatGPT"], ["gemini", "Gemini"], ["mistral", "Mistral"]]
                    value: app.ai.target || ""
                    onPicked: (v) => app.aiSet("cloud", v)
                }
                Heading { text: "API KĽÚČ" }
                Field {
                    secret: true; placeholder: "vlož kľúč a stlač Enter (uloží sa s právami 0600)"
                    onCommitted: (t) => { if (t !== "") { app.run(["latte-ai", "key", app.ai.target || "anthropic", t], "Kľúč uložený"); text = ""; aiRefresh.restart(); } }
                }
            }
            Heading { text: "MODEL"; visible: app.ai.provider !== "cloud" }
            Flow {
                visible: app.ai.provider !== "cloud"
                width: parent.width; spacing: 8
                Card { width: 220; height: 58; title: "Automaticky"; sub: "načítaný na serveri"; selected: false; onClicked: app.aiSet("model", "") }
                Repeater {
                    model: app.aiModels
                    Card {
                        required property var modelData
                        width: 220; height: 58; title: modelData.id.split("/").pop(); sub: modelData.state === "loaded" ? "● načítaný" : (modelData.state === "not-loaded" ? "načíta sa pri otázke" : modelData.state)
                        selected: app.ai.model === modelData.id
                        onClicked: app.aiSet("model", modelData.id)
                    }
                }
            }
            Row {
                spacing: 10
                Button { label: "Vyskúšať"; glyph: "sparkles"; primaryStyle: true; onClicked: { app.aiAnswer = "Pýtam sa…"; aiAsk.running = true; } }
                Button { label: "Obnoviť"; glyph: "refresh"; onClicked: aiRefresh.restart() }
            }
            Text { width: parent.width; wrapMode: Text.WordWrap; visible: app.aiAnswer !== ""; text: app.aiAnswer; color: theme.fg; font { family: theme.fontUi; pixelSize: 14 } }
        }
    }
    Component {
        id: pSubory
        Column {
            spacing: 12
            Button { label: "Otvoriť Súbory"; glyph: "folder"; primaryStyle: true; onClicked: app.run(["latte-app", "subory"]) }
            Text {
                width: parent.width; wrapMode: Text.WordWrap; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 13 }
                text: "Farebné štítky: pravý klik na priečinok (v zozname aj v Obľúbených) › Farba. Štítok je viditeľný všade v Súboroch a nemení samotný priečinok."
            }
        }
    }
    Component {
        id: pUlozisko
        Column {
            spacing: 8
            Repeater {
                model: app.storage.split("\n").filter(l => l.trim() !== "")
                Rectangle {
                    required property string modelData
                    readonly property var f: modelData.trim().split(/\s+/)
                    width: Math.min(parent.width, 560); height: 54; radius: 12; color: theme.field
                    Column {
                        anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter; margins: 14 }
                        spacing: 6
                        Text { text: f[0] + "   ·   " + f[3] + " voľné z " + f[1]; color: theme.fg; font { family: theme.fontUi; pixelSize: 13; weight: Font.Bold } }
                        Rectangle {
                            width: parent.width; height: 4; radius: 2; color: theme.line
                            Rectangle { width: parent.width * (parseInt(f[4]) || 0) / 100; height: 4; radius: 2; color: (parseInt(f[4]) || 0) > 90 ? theme.error : theme.primary }
                        }
                    }
                }
            }
        }
    }
    Component {
        id: pVykon
        Flow {
            spacing: 10
            Repeater {
                model: [["auto", "Automaticky", "Podľa hardvéru pri štarte"], ["plny", "Plný", "Sklo, blur, žiara, animácie 120 Hz"],
                        ["standard", "Štandard", "Menší blur, plné animácie"], ["usporny", "Úsporný", "Bez blur a tieňov, krátke animácie"],
                        ["minimalny", "Minimálny", "Bez priehľadnosti a animácií"], ["softver", "Softvér", "VM a slabé PC, bez efektov"]]
                Card {
                    required property var modelData
                    title: modelData[1]; sub: modelData[2]; selected: app.tierChoice === modelData[0]
                    onClicked: app.setTier(modelData[0])
                }
            }
        }
    }
    Component {
        id: pDiag
        Column {
            spacing: 14
            Row {
                spacing: 12
                Text { anchors.verticalCenter: parent.verticalCenter; text: app.crashCount + " z 2 pádov (pri 2 naštartuje SAFE)"; color: theme.fg; font { family: theme.fontUi; pixelSize: 13 } }
                Button { label: "Vynulovať"; glyph: "refresh"; onClicked: app.run(["latte-boot", "reset"], "Počítadlo vynulované") }
            }
            Heading { text: "POSLEDNÝ PÁD" }
            Rectangle {
                width: parent.width; height: Math.max(80, log.implicitHeight + 28); radius: 12; color: theme.field
                Text {
                    id: log
                    anchors { left: parent.left; right: parent.right; top: parent.top; margins: 14 }
                    wrapMode: Text.WrapAnywhere; textFormat: Text.PlainText
                    text: app.crashLog || "Žiadny zaznamenaný pád. ☕"; color: theme.fgDim
                    font { family: theme.fontMono; pixelSize: 11 }
                }
            }
            Button { visible: app.crashLog !== ""; label: "Vymazať záznam"; glyph: "trash"; onClicked: app.run(["rm", "-f", "/var/lib/latteos/greeter/last-crash.log"], "Záznam pádu vymazaný") }
        }
    }
    Component {
        id: pGreeter
        Column {
            spacing: 14
            Heading { text: "POZADIE" }
            Flow {
                width: parent.width; spacing: 10
                Rectangle {
                    width: 180; height: 102; radius: 12; color: app.greeterConf.color
                    border { color: app.greeterConf.background === "" ? theme.primary : "transparent"; width: 2 }
                    Text { anchors.centerIn: parent; text: "Iba farba"; color: "#F3EBDD"; font { family: theme.fontUi; pixelSize: 13; weight: Font.Bold } }
                    MouseArea { anchors.fill: parent; onClicked: app.setGreeter("background", "") }
                }
                Repeater {
                    model: app.wallpapers
                    Rectangle {
                        required property string modelData
                        width: 180; height: 102; radius: 12; clip: true; color: theme.field
                        border { color: app.greeterConf.background === modelData ? theme.primary : "transparent"; width: 2 }
                        Image { anchors { fill: parent; margins: 2 } source: "file://" + parent.modelData; fillMode: Image.PreserveAspectCrop; asynchronous: true; sourceSize { width: 360; height: 204 } }
                        MouseArea { anchors.fill: parent; onClicked: app.setGreeter("background", parent.modelData) }
                    }
                }
            }
            Heading { text: "FARBA" }
            Row {
                spacing: 10
                Repeater {
                    model: ["#1B1410", "#101418", "#141A12", "#1A1020", "#2A2A2E", "#0E0E0E"]
                    Rectangle {
                        required property string modelData
                        width: 38; height: 38; radius: 19; color: modelData
                        border { color: app.greeterConf.color.toLowerCase() === modelData.toLowerCase() ? theme.primary : theme.line; width: 2 }
                        MouseArea { anchors.fill: parent; onClicked: app.setGreeter("color", parent.modelData) }
                    }
                }
            }
            Stepper { label: "Stmavenie obrázka"; value: parseFloat(app.greeterConf.dim) || 0; step: 0.05; min: 0; max: 0.85; unit: ""
                      onStepped: (v) => app.setGreeter("dim", v.toFixed(2)) }
            Heading { text: "ĽAVÝ PANEL" }
            Segments {
                options: [["log", "Log posledného pádu"], ["text", "Vlastný text"], ["none", "Nič"]]
                value: app.greeterConf.panel
                onPicked: (v) => app.setGreeter("panel", v)
            }
            Text { width: parent.width; wrapMode: Text.WordWrap; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 }
                   text: "Vývojárska verzia: log. Vo vydanej verzii tu bude miesto pre RSS, novinky alebo počasie; zatiaľ vlastný text." }
            Column {
                visible: app.greeterConf.panel === "text"; spacing: 8
                Field { text: app.greeterConf.panel_title; placeholder: "Nadpis (napr. Dnes)"; onCommitted: (t) => { if (t !== app.greeterConf.panel_title) app.setGreeter("panel_title", t); } }
                Field { multiline: true; text: app.greeterConf.panel_text; placeholder: "Text na obrazovke prihlásenia"; onCommitted: (t) => { if (t !== app.greeterConf.panel_text) app.setGreeter("panel_text", t); } }
            }
            Heading { text: "TYP" }
            Text {
                width: parent.width; wrapMode: Text.WordWrap
                text: "Aktuálne: " + ({ latte: "LatteOS (grafická)", tui: "textová (tuigreet)", noctalia: "Noctalia Greeter" })[app.greeter]
                      + ". Zmena vyžaduje administrátora: v /etc/latteos/boot.toml riadok greeter = \"latte\" alebo \"tui\"."
                color: theme.fgDim; font { family: theme.fontUi; pixelSize: 13 }
            }
        }
    }
    Component {
        id: pMotiv
        Column {
            spacing: 14
            Heading { text: "SVETLÁ / TMAVÁ VERZIA" }
            Segments {
                options: [["tema", "Podľa témy"], ["dark", "Tmavá"], ["light", "Svetlá"], ["auto", "Automaticky (slnko)"]]
                value: app.modePref
                onPicked: (v) => { app.run(["latte-theme", "mode", v], "Režim: " + app.modeName(v)); app.modePref = v; }
            }
            Text { visible: app.modePref === "auto"; width: parent.width; wrapMode: Text.WordWrap; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 }
                   text: "Cez deň svetlá, po západe slnka tmavá. Poloha: Systém › Dátum, čas a poloha." }
            Heading { text: "TÉMA" }
            Flow {
                width: parent.width; spacing: 10
                Repeater {
                    model: app.themes
                    Card {
                        required property var modelData
                        title: modelData.name; sub: modelData.desc; selected: theme.themeId === modelData.id
                        onClicked: app.run(["latte-theme", "set", modelData.id], "Téma: " + modelData.name)
                    }
                }
            }
        }
    }
    Component {
        id: pPozadie
        Column {
          spacing: 14
          Row {
            spacing: 10
            Rectangle {
                width: 46; height: 26; radius: 13; anchors.verticalCenter: parent.verticalCenter
                color: app.wsWallpaper ? theme.primary : theme.field; border { color: theme.line; width: 1 }
                Rectangle { width: 20; height: 20; radius: 10; y: 3; x: app.wsWallpaper ? 23 : 3; color: app.wsWallpaper ? theme.fgOnPrimary : theme.fgDim }
                MouseArea { anchors.fill: parent; onClicked: { app.wsWallpaper = !app.wsWallpaper; app.writePref("wallpaper-per-workspace", app.wsWallpaper ? "1" : "", app.wsWallpaper ? "Tapeta podľa plochy: zapnuté" : "Tapeta podľa plochy: vypnuté"); } }
            }
            Text { anchors.verticalCenter: parent.verticalCenter; text: "Každá plocha má inú tapetu (poradie tapiet LatteOS)"; color: theme.fg; font { family: theme.fontUi; pixelSize: 13 } }
          }
          Flow {
            width: parent.width
            spacing: 10
            Repeater {
                model: app.wallpapers
                Rectangle {
                    required property string modelData
                    width: 200; height: 112; radius: 12; clip: true; color: theme.field
                    Image { anchors.fill: parent; source: "file://" + parent.modelData; fillMode: Image.PreserveAspectCrop; asynchronous: true; sourceSize { width: 400; height: 224 } }
                    MouseArea { anchors.fill: parent; onClicked: app.run(["noctalia", "msg", "wallpaper-set", parent.modelData], "Tapeta zmenená") }
                }
            }
          }
        }
    }
    Component {
        id: pOkna
        Flow {
            spacing: 10
            Repeater {
                model: [["paska", "Nekonečná páska", "Okná v stĺpcoch vedľa seba, páska sa posúva"],
                        ["dlazdice", "Dlaždice", "Okná sa delia o obrazovku"],
                        ["plavajuce", "Plávajúce okná", "Voľné okná ako vo Windows"]]
                Card {
                    required property var modelData
                    width: 240; title: modelData[1]; sub: modelData[2]; selected: app.windowMode === modelData[0]
                    onClicked: { app.run(["hyprctl", "eval", "require(\"latte.windows\").apply(\"" + modelData[0] + "\", true)"], modelData[1]); app.windowMode = modelData[0]; }
                }
            }
        }
    }
    Component {
        id: pLista
        Column {
            spacing: 12
            Stepper { label: "Hrúbka lišty"; value: parseInt(app.bar.thickness) || 56; step: 4; min: 40; max: 72
                      onStepped: (v) => app.shellSet("bar.main.thickness", v, "Hrúbka lišty " + v) }
            Stepper { label: "Odsadenie od okrajov (šírka)"; value: parseInt(app.bar.margin_ends) || 12; step: 24; min: 0; max: 480
                      onStepped: (v) => app.shellSet("bar.main.margin_ends", v, "Odsadenie od okrajov " + v) }
            Stepper { label: "Odsadenie od spodku"; value: parseInt(app.bar.margin_edge) || 10; step: 2; min: 0; max: 40
                      onStepped: (v) => app.shellSet("bar.main.margin_edge", v, "Odsadenie od spodku " + v) }
            Stepper { label: "Medzera medzi ostrovmi"; value: parseInt(app.bar.widget_spacing) || 12; step: 2; min: 4; max: 32
                      onStepped: (v) => app.shellSet("bar.main.widget_spacing", v, "Medzera " + v) }
            Heading { text: "DLAŽDICA APLIKÁCIÍ (vľavo)" }
            Segments {
                options: [["", "Podľa výkonu"], ["vzdy", "Vždy v pohybe"], ["kurzor", "Pod kurzorom"], ["vypnuty", "Bez pohybu"]]
                value: app.barAnim
                onPicked: (v) => { app.barAnim = v; app.writePref("bar-anim", v, "Pohyb dlaždice: " + (v || "podľa výkonu")); }
            }
            Segments {
                options: [["para", "Para"], ["matrix", "Matrix"]]
                value: app.barScene
                onPicked: (v) => { app.barScene = v; app.writePref("bar-scene", v, "Textúra: " + v); }
            }
            Heading { text: "MASKOT" }
            Segments {
                options: [["macka", "Latte mačka"], ["mokka", "Mokka"], ["zrnko", "Zrnko"], ["ziadny", "Žiadny"]]
                value: app.mascot
                onPicked: (v) => { app.mascot = v; app.writePref("mascot", v, "Maskot: " + v); }
            }
            Text { width: parent.width; wrapMode: Text.WordWrap; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 }
                   text: "Maskot ťuká labkami do rytmu hudby, žmurká a v noci či pri Nerušiť spí. Pohyb stojí trochu CPU, preto je vo VM iba pri hudbe." }
            Row {
                spacing: 10
                Button { label: "Predvolené LatteOS"; glyph: "refresh"
                         onClicked: app.run(["sh", "-c", "for k in thickness margin_ends margin_edge widget_spacing; do latte-shellset unset bar.main.$k; done"], "Lišta: predvolené") }
                Button { label: "Ďalšie voľby lišty (Noctalia)"; glyph: "settings"; onClicked: app.run(["noctalia", "msg", "settings-open"]) }
            }
        }
    }
    Component {
        id: pEfekty
        Column {
            spacing: 12
            Button { label: "Stupeň výkonu"; glyph: "bolt"; primaryStyle: true; onClicked: app.go("vykon") }
            Text { width: parent.width; wrapMode: Text.WordWrap; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 13 }
                   text: "Herný režim (Zariadenia na lište) vypne efekty dočasne. Pohyblivé textúry tém (mráz, kov, jantár) potrebujú GPU — prídu s reálnym HW." }
        }
    }
    Component {
        id: pStart
        Column {
            spacing: 14
            Heading { text: "ĎALŠÍ ŠTART" }
            Row {
                spacing: 10
                Card { title: "NORMAL"; sub: "Hyprland + Noctalia (odporúčané)"; selected: !app.forceSafe
                       onClicked: app.run(["latte-boot", "reset"], "Ďalší štart: NORMAL") }
                Card { title: "SAFE"; sub: "labwc bez GPU, iba nabudúce"; selected: app.forceSafe
                       onClicked: app.run(["latte-boot", "force-safe"], "Ďalší štart: SAFE") }
            }
            Heading { text: "POČÍTADLO PÁDOV" }
            Row {
                spacing: 12
                Text { anchors.verticalCenter: parent.verticalCenter; text: app.crashCount + " z 2 pádov (pri 2 naštartuje SAFE)"; color: theme.fg; font { family: theme.fontUi; pixelSize: 13 } }
                Button { label: "Diagnostika"; glyph: "stethoscope"; onClicked: app.go("diagnostika") }
            }
        }
    }
    Component {
        id: pCas
        Column {
            spacing: 14
            Heading { text: "POLOHA (VÝCHOD A ZÁPAD SLNKA)" }
            Flow {
                width: parent.width; spacing: 8
                Repeater {
                    model: [["Bratislava", 48.15, 17.11], ["Banská Bystrica", 48.74, 19.15], ["Košice", 48.72, 21.26], ["Žilina", 49.22, 18.74],
                            ["Praha", 50.08, 14.43], ["Brno", 49.20, 16.61], ["Viedeň", 48.21, 16.37], ["Budapešť", 47.50, 19.04], ["Londýn", 51.51, -0.13]]
                    Card {
                        required property var modelData
                        width: 150; height: 52; title: modelData[0]; sub: modelData[1] + ", " + modelData[2]
                        selected: Math.abs((parseFloat(app.location.latitude) || 48.74) - modelData[1]) < 0.01 && Math.abs((parseFloat(app.location.longitude) || 19.15) - modelData[2]) < 0.01
                        onClicked: app.run(["sh", "-c", "latte-shellset set location.latitude \"$1\" && latte-shellset set location.longitude \"$2\"", "sh", String(modelData[1]), String(modelData[2])], "Poloha: " + modelData[0])
                    }
                }
            }
            Heading { text: "ĎALŠIE ČASOVÉ PÁSMA V PANELI ČAS" }
            Flow {
                width: parent.width; spacing: 8
                Repeater {
                    model: [["Europe/London", "Londýn"], ["America/New_York", "New York"], ["America/Los_Angeles", "Los Angeles"], ["Asia/Tokyo", "Tokio"],
                            ["Asia/Shanghai", "Peking"], ["Asia/Kolkata", "Dillí"], ["Australia/Sydney", "Sydney"], ["Europe/Moscow", "Moskva"], ["UTC", "UTC"]]
                    Card {
                        required property var modelData
                        width: 150; height: 52; title: modelData[1]; sub: modelData[0]; selected: app.clockZones.indexOf(modelData[0]) >= 0
                        onClicked: app.toggleZone(modelData[0])
                    }
                }
            }
        }
    }
    Component {
        id: pO
        Column {
            spacing: 6
            Row {
                spacing: 14; bottomPadding: 10
                Image { source: "file:///usr/share/latteos/noctalia/icons/latte-cup.png"; width: 56; height: 56 }
                Column {
                    anchors.verticalCenter: parent.verticalCenter
                    Text { text: "LatteOS"; color: theme.fg; font { family: theme.fontDisplay; pixelSize: 26; weight: Font.DemiBold } }
                    Text { text: "vývojárska verzia · gamerdistro"; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 13 } }
                }
            }
            Repeater {
                model: app.about.split("\n").filter(l => l.includes("|"))
                Row {
                    required property string modelData
                    spacing: 12
                    Text { width: 130; text: modelData.split("|")[0]; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 13 } }
                    Text { text: modelData.split("|")[1] || "—"; color: theme.fg; font { family: theme.fontUi; pixelSize: 13; weight: Font.DemiBold } }
                }
            }
        }
    }
    Component {
        id: pManaged
        Column {
            spacing: 12
            readonly property var m: app.managed[app.section] || ["", "", []]
            Text { width: parent.width; wrapMode: Text.WordWrap; text: parent.m[1]; color: theme.fg; font { family: theme.fontUi; pixelSize: 14 } }
            Button { label: "Otvoriť " + parent.m[0]; glyph: parent.m[0] === "Monitor" ? "activity" : (parent.m[0] === "Aplikácie" ? "apps" : "cpu"); primaryStyle: true; onClicked: app.run(parent.m[2]) }
            Text { text: "Nastavenia ukazujú stav a odkaz; operácie vlastní " + parent.m[0] + " (jedna implementácia)."; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 } }
        }
    }
    Component {
        id: pPlan
        Column {
            spacing: 10
            Repeater {
                model: app.plans[app.section] || []
                Row {
                    required property string modelData
                    spacing: 10
                    Text { text: "○"; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 13 } }
                    Text { text: modelData; color: theme.fg; font { family: theme.fontUi; pixelSize: 14 } }
                }
            }
            Text { topPadding: 8; text: "Spravuje: " + app.current.owner + " · ROADMAP.md"; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 } }
        }
    }
}
