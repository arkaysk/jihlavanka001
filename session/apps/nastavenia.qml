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
    readonly property var latteTheme: theme      // pre vnorené prvky s vlastnou vlastnosťou „theme“ (IconButton)

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
    property var notif: ({})          // prepisy [notification]
    property var access: ({})         // prepisy [accessibility]
    property string fullName: ""
    property var clouds: []           // latte-cloud list
    property var accounts: []         // [{ name, full, admin, me }]
    property string newUser: ""
    property var backup: ({})        // latte-backup status
    property var backupDrives: []
    property var backupList: []
    property int backupPct: -1
    property var locales: []          // nainštalované (locale -a)
    property var localeConf: ({})     // ~/.config/latteos/locale
    property var avatarChoices: []
    property int avatarRev: 0          // obnovenie náhľadu po zmene
    property var idle: ({})           // [idle.behavior.*] → { lock: {enabled, timeout}, … }
    property var shellAnim: ({})      // prepisy [shell.animation]
    property bool noAnim: false
    property string cursorSize: "24"
    property bool dnd: false
    property var greeterConf: ({ background: "/usr/share/backgrounds/latteos/latteos-wallpaper1.jpg", color: "#1B1410", dim: "0.55", panel: "log", panel_title: "", panel_text: "",
                                 rss_url: "https://www.aktuality.sk/rss/", lat: "48.74", lon: "19.15", place: "Banská Bystrica" })
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
    property string liveWp: ""

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
            { key: "zalohy", label: "Zálohovanie a obnova", glyph: "history", status: "ready" },
            { key: "synchronizacia", label: "Cloud a synchronizácia", glyph: "cloud", status: "ready" } ] },
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
            { key: "mojucet", label: "Môj účet", glyph: "user", status: "ready" },
            { key: "pouzivatelia", label: "Používatelia", glyph: "users", status: "ready" },
            { key: "prihlasovanie", label: "Prihlasovanie", glyph: "login", status: "ready" },
            { key: "uzamknutie", label: "Uzamknutie a nečinnosť", glyph: "lock", status: "ready" } ] },
        { key: "prostredie", title: "Prostredie", glyph: "palette", summary: theme.themeName + " · " + modeName(modePref), owner: "Prispôsobenie",
          pages: [
            { key: "motiv", label: "Motív a farby", glyph: "palette", status: "ready" },
            { key: "pozadie", label: "Pozadie", glyph: "photo", status: "ready" },
            { key: "okna", label: "Okná", glyph: "layout-columns", status: "ready" },
            { key: "lista", label: "Lišta a systémové menu", glyph: "layout-bottombar", status: "ready" },
            { key: "oznamenia", label: "Oznámenia", glyph: "bell", status: "ready" },
            { key: "efekty", label: "Animácie a efekty", glyph: "sparkles", status: "ready" },
            { key: "pristupnost", label: "Prístupnosť", glyph: "accessible", status: "ready" } ] },
        { key: "system", title: "Systém", glyph: "shield", summary: (mode.mode || "?").toUpperCase() + " · pády " + crashCount, owner: "LatteOS",
          pages: [
            { key: "start", label: "Štart a režim", glyph: "shield", status: "ready" },
            { key: "cas", label: "Dátum, čas a poloha", glyph: "clock", status: "ready" },
            { key: "jazyk", label: "Jazyk a región", glyph: "language", status: "ready" },
            { key: "klavesnica", label: "Klávesnica a skratky", glyph: "keyboard", status: "partial" },
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
        if (key === "oznamenia") dndProc.running = true;
        if (key === "mojucet") accountProc.running = true;
        if (key === "jazyk") localeProc.running = true;
        if (key === "pouzivatelia") usersProc.running = true;
        if (key === "synchronizacia") cloudProc.running = true;
        if (key === "zalohy" || key === "domov") backupProc.running = true;
        if (key === "domov") { netProc.running = true; cloudProc.running = true; }
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
        for (const key of ["background", "color", "dim", "panel", "panel_title", "panel_text", "rss_url", "lat", "lon", "place"])
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
            app.bar = t["bar.main"] || {}; app.location = t["location"] || {}; app.notif = t["notification"] || {}; app.access = t["accessibility"] || {};
            app.idle = { lock: t["idle.behavior.lock"] || {}, screen: t["idle.behavior.screen-off"] || {}, suspend: t["idle.behavior.lock-and-suspend"] || {} }; app.shellAnim = t["shell.animation"] || {};
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
    FileView { path: app.cfgHome + "/latteos/no-animations"; printErrors: false; watchChanges: true; onFileChanged: reload()
               onLoaded: app.noAnim = true; onLoadFailed: app.noAnim = false }
    FileView { path: app.cfgHome + "/latteos/cursor-size"; printErrors: false; watchChanges: true; onFileChanged: reload()
               onLoaded: app.cursorSize = text().trim() || "24"; onLoadFailed: app.cursorSize = "24" }
    // nečinnosť: Noctalia prepíše celé správanie, preto sa vždy zapíše enabled + timeout + action
    function setIdle(name, action, minutes, msg) {
        const k = "idle.behavior." + name + ".";
        run(["sh", "-c", "latte-shellset set \"$1enabled\" \"$2\" && latte-shellset set \"$1timeout\" \"$3\" && latte-shellset set \"$1action\" \"$4\"",
             "sh", k, minutes > 0 ? "true" : "false", String(Math.max(60, minutes * 60)), action], msg);
    }
    function idleMin(b) { return b && b.enabled === "true" ? Math.round((parseFloat(b.timeout) || 0) / 60) : 0; }
    function setNoAnim(on) {
        app.noAnim = on;
        app.writePref("no-animations", on ? "1" : "", on ? "Animácie vypnuté" : "Animácie podľa stupňa výkonu");
        shellSet("shell.animation.enabled", on ? false : null);
        run(["sh", "-c", "sleep 0.3; hyprctl reload"]);
    }
    FileView { path: app.cfgHome + "/latteos/live-wallpaper"; printErrors: false; watchChanges: true; onFileChanged: reload()
               onLoaded: app.liveWp = text().trim() || "tema"; onLoadFailed: app.liveWp = "" }
    function setLive(v) {
        liveWp = v;
        writePref("live-wallpaper", v, v === "" ? "Živá tapeta vypnutá" : "Živá tapeta: " + v);
        if (v === "") run(["pkill", "-f", "latteos/apps/[z]ivatapeta.qml"]);   // [z]: vzor nenájde sám seba
        else run(["sh", "-c", "pgrep -f latteos/apps/[z]ivatapeta.qml >/dev/null || setsid latte-app zivatapeta >/dev/null 2>&1 &"]);
    }
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
        id: accountProc
        command: ["sh", "-c", "getent passwd \"$USER\" | cut -d: -f5 | cut -d, -f1; ls /usr/share/latteos/noctalia/plugins/cat/mascots/*-sedi.png 2>/dev/null; ls -t \"$HOME\"/Obrázky/*.png \"$HOME\"/Obrázky/*.jpg \"$HOME\"/Pictures/*.png \"$HOME\"/Pictures/*.jpg 2>/dev/null | head -8"]
        onDone: (out) => { const l = out.split("\n"); app.fullName = l[0] || ""; app.avatarChoices = l.slice(1).filter(x => x !== ""); }
    }
    function setAvatar(src) {
        const dst = "/var/lib/latteos/greeter/avatars/" + app.user + ".png";
        if (src === "") run(["sh", "-c", "rm -f \"$1\" \"$HOME/.face\"", "sh", dst], "Obrázok účtu odstránený");
        else run(["sh", "-c", "cp -f \"$1\" \"$2\" && chmod 664 \"$2\" && cp -f \"$1\" \"$HOME/.face\"", "sh", src, dst], "Obrázok účtu nastavený");
        avatarTick.restart();
    }
    Timer { id: avatarTick; interval: 500; onTriggered: app.avatarRev++ }
    Cmd {
        id: backupProc; command: ["latte-backup", "status"]
        onDone: (out) => {
            const b = {}, dr = [];
            for (const l of out.split("\n")) { const i = l.indexOf("="); if (i < 0) continue; const k = l.slice(0, i), v = l.slice(i + 1); if (k === "drive") dr.push(v.split("|")); else b[k] = v; }
            app.backup = b; app.backupDrives = dr;
            if (b.target) backupListProc.running = true;
        }
    }
    Cmd { id: backupListProc; command: ["latte-backup", "list"]; onDone: (out) => app.backupList = out.split("\n").filter(l => l !== "") }
    Process {
        id: backupRun
        command: ["latte-backup", "run"]
        stdout: SplitParser { onRead: (line) => { const m = line.match(/^pct=(\d+)/); if (m) app.backupPct = parseInt(m[1]); const e = line.match(/^error=(.*)/); if (e) app.status = e[1]; } }
        onExited: (code) => { app.backupPct = -1; if (code === 0) app.status = "Záloha hotová"; backupProc.running = true; }
    }
    Cmd {
        id: usersProc
        command: ["sh", "-c", "getent passwd | awk -F: '$3>=1000 && $3<60000 && $7 !~ /nologin|false/ {print $1\"|\"$5}'; echo '#wheel'; getent group wheel | cut -d: -f4"]
        onDone: (out) => {
            const [list, wheel] = out.split("#wheel");
            const admins = (wheel || "").trim().split(",");
            app.accounts = list.split("\n").filter(l => l).map(l => { const p = l.split("|"); return { name: p[0], full: (p[1] || "").split(",")[0], admin: admins.indexOf(p[0]) >= 0, me: p[0] === app.user }; });
        }
    }
    function term(cmd, msg) { run(["foot", "-e", "sh", "-c", cmd + "; echo; read -p 'Enter zavrie okno…' x"], msg); usersRefresh.restart(); }
    Timer { id: usersRefresh; interval: 15000; onTriggered: usersProc.running = true }
    Cmd { id: cloudProc; command: ["latte-cloud", "list"]
          onDone: (out) => app.clouds = out.split("\n").filter(l => l.includes("|")).map(l => { const p = l.split("|"); return { name: p[0], type: p[1], mounted: p[2] === "1", auto: p[3] === "1" }; }) }
    Timer { id: cloudRefresh; interval: 1500; onTriggered: cloudProc.running = true }
    property string netState: ""
    Cmd { id: netProc; command: ["sh", "-c", "nmcli -t -f TYPE,STATE,CONNECTION device 2>/dev/null | grep ':connected:\\|:pripojené:' | head -1"]
          onDone: (out) => { const p = out.trim().split(":"); app.netState = p.length >= 3 ? ({ ethernet: "Kábel", wifi: "Wi-Fi" })[p[0]] + " · " + p.slice(2).join(":") : "Bez pripojenia"; } }
    // upozornenia pre Domov (old/main_setting_v2.md §5: dôležité upozornenia na jednom mieste)
    readonly property var warnings: {
        const w = [];
        if ((mode.mode || "") === "safe") w.push(["shield", "Beží režim SAFE", mode.reason || "grafika bez GPU", "start"]);
        if (crashCount > 0) w.push(["alert-triangle", "Relácia NORMAL spadla " + crashCount + "×", "pri 2 pádoch naštartuje SAFE", "diagnostika"]);
        const root = (storage.split("\n").find(l => l.trim().startsWith("/ ")) || "").trim().split(/\s+/);
        if (root.length >= 5 && parseInt(root[4]) >= 90) w.push(["database", "Systémový disk je plný na " + root[4], "uprac v Súboroch alebo Monitore", "ulozisko"]);
        if (!backup.target) w.push(["history", "Zálohy nie sú nastavené", "pripoj USB disk a zapni zálohu", "zalohy"]);
        else if (!backup.last) w.push(["history", "Ešte žiadna záloha", "Zálohovať teraz", "zalohy"]);
        if (ai.ok === "0") w.push(["robot-off", "AI teraz neodpovedá", ai.target || "", "ai"]);
        return w;
    }
    Cmd { id: localeProc; command: ["sh", "-c", "locale -a"]; onDone: (out) => app.locales = out.split("\n").map(l => l.toLowerCase()) }
    FileView {
        id: localeFile
        path: app.cfgHome + "/latteos/locale"; printErrors: false; watchChanges: true; onFileChanged: reload()
        onLoaded: { const c = {}; for (const l of text().split("\n")) { const r = l.match(/^(\w+)=(.*)$/); if (r) c[r[1]] = r[2]; } app.localeConf = c; }
        onLoadFailed: app.localeConf = ({})
    }
    function hasLocale(code) { return locales.indexOf(code.toLowerCase().replace("utf-8", "utf8")) >= 0; }
    function setLocale(key, code) {
        const c = Object.assign({}, localeConf); if (code) c[key] = code; else delete c[key]; localeConf = c;
        let out = "# LatteOS — jazyk a formáty (Nastavenia › Systém › Jazyk a región); platí po novom prihlásení\n";
        for (const k of Object.keys(c)) out += k + "=" + c[k] + "\n";
        localeFile.setText(out);
        status = "Uložené — platí po odhlásení a prihlásení";
    }
    Cmd { id: dndProc; command: ["noctalia", "msg", "notification-dnd-status"]; onDone: (out) => app.dnd = out.trim() === "on" }
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
            appId: "latteos-nastavenia"
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
            efekty: "Pohyblivé textúry tém (živá tapeta) a efekty okien.",
            start: "Režim NORMAL (Hyprland) alebo SAFE (labwc bez GPU). SAFE naskočí sám po dvoch pádoch za sebou.",
            cas: "Poloha určuje východ a západ slnka pre automatický svetlý/tmavý režim a nočné svetlo. Ďalšie časové pásma ukáže panel Čas.",
            o: "Verzie častí systému, z ktorých sa LatteOS skladá.",
            synchronizacia: "Cloudové účty (Google Drive, OneDrive, Dropbox, Nextcloud…) ako priečinky v ~/Cloud. Súbory sa stiahnu pri otvorení, zmeny sa odošlú na pozadí.",
            pouzivatelia: "Účty na tomto počítači. Každý má vlastný domov, nastavenia a kôš; obrazovka prihlásenia ukáže posledné dva.",
            zalohy: "Záloha domovského priečinka na USB disk alebo do priečinka. Každá záloha vyzerá ako celá kópia, nezmenené súbory zaberajú miesto iba raz.",
            jazyk: "Jazyk aplikácií a formáty dátumu, času, čísel a mien. Aplikácie LatteOS sú po slovensky; shell Noctalia zatiaľ nemá slovenský preklad (anglicky).",
            mojucet: "Meno, heslo a obrázok, ktorý ukáže obrazovka prihlásenia.",
            uzamknutie: "Čo sa stane, keď počítač chvíľu nepoužívaš. Pred akciou obrazovka 2 s pomaly stmavne — pohyb myšou to zruší.",
            pristupnost: "Väčšie rozhranie, vyšší kontrast, žiadny pohyb, väčší kurzor.",
            oznamenia: "Kde a ako sa ukazujú oznámenia. História a Nerušiť sú aj v paneli Čas na lište.",
            klavesnica: "Rozloženia klávesnice sk a us, prepínanie Alt+Shift. Skratky LatteOS:"
        })[k] || (plans[k] ? "Pripravujeme. Čo tu bude:" : "");
    }
    readonly property var plans: ({
        aplikacie: ["zoznam aplikácií (Flatpak, RPM, AppImage, Windows cez Proton, Android cez Waydroid)", "predvolené aplikácie", "App Manager: „Bude to fungovať?“ pred inštaláciou"],
        instalacia: ["inštalácia jedným klikom", "zdroje: Flathub, Fedora, LatteOS", "náhľad oprávnení pred inštaláciou"],
        aktualizacie: ["systém (Atomic: celý obraz naraz s návratom)", "aplikácie", "firmware (fwupd)", "„Aktualizovať všetko“"],
        spustanie: ["aplikácie pri prihlásení", "služby na pozadí", "Latte System Monitor: autorun položky s pôvodom"],
        sukromie: ["tlačidlo NET pre každú aplikáciu", "dôveryhodné / nedôveryhodné aplikácie", "kamera, mikrofón, poloha"],
        obrazovky: ["rozlíšenie, frekvencia, mierka, otočenie", "potvrdenie do 15 s, inak návrat", "HDR a VRR na reálnom HW"],
        zvuk: ["výstup a vstup", "hlasitosť aplikácií", "Bluetooth slúchadlá"],
        siet: ["Wi-Fi a káblové pripojenia", "VPN", "zdieľanie pripojenia"],
        bluetooth: ["párovanie", "ovládače a periférie"],
        napajanie: ["profil výkonu", "uspávanie a vypnutie obrazovky", "batéria"],
    })
    function stateText(k) {
        const m = app.mode;
        if (k === "domov" || k === "start") return (m.mode || "?").toUpperCase() + " · " + (m.renderer || "?") + " · stupeň " + (m.tier || "?") + (m.reason ? "\n" + m.reason : "");
        if (k === "motiv") return "Téma " + theme.themeName + " · režim " + modeName(modePref) + " (teraz " + theme.mode + ")";
        if (k === "okna") return ({ paska: "Nekonečná páska", dlazdice: "Dlaždice", plavajuce: "Plávajúce okná" })[app.windowMode] || app.windowMode;
        if (k === "efekty") return "Živá tapeta: " + (liveWp === "" ? "vypnutá" : liveWp) + "\nStupeň: " + (app.tierChoice === "auto" ? "automaticky (" + (m.tier || "?") + ")" : app.tierChoice);
        if (k === "vykon") return app.tierChoice === "auto" ? "Automaticky (" + (m.tier || "?") + ")" : "Vynútený: " + app.tierChoice;
        if (k === "ai") return (ai.ok === "1" ? "● Dostupné" : "× Nedostupné") + "\n" + (ai.target || "") + (ai.model ? "\nmodel " + ai.model : "") + (ai.error ? "\n" + ai.error : "");
        if (k === "diagnostika") return "Pády NORMAL: " + crashCount + " / 2" + (crashLog ? "\n" + crashLog.split("\n")[0] : "\nbez záznamu pádu");
        if (k === "prihlasovanie") return "Greeter: " + greeter + " · panel " + greeterConf.panel;
        if (k === "lista") return "Hrúbka " + (bar.thickness || 56) + " · okraje " + (bar.margin_ends || 12) + " · spodok " + (bar.margin_edge || 10);
        if (k === "cas") return "Poloha " + (location.latitude || "48.74") + ", " + (location.longitude || "19.15") + (clockZones.length ? "\nPásma: " + clockZones.join(", ") : "");
        if (k === "synchronizacia") return clouds.length ? clouds.length + (clouds.length === 1 ? " účet" : (clouds.length <= 4 ? " účty" : " účtov")) + " · pripojené: " + clouds.filter(c => c.mounted).length : "Žiadny cloudový účet";
        if (k === "pouzivatelia") return accounts.length + (accounts.length === 1 ? " účet" : " účty") + " · správcovia: " + accounts.filter(a => a.admin).map(a => a.name).join(", ");
        if (k === "zalohy") return backup.target ? ("Cieľ: " + backup.target + "\nPosledná: " + (backup.last || "zatiaľ žiadna") + "\nSnímok: " + (backup.count || 0) + (backup.free ? " · voľné " + backup.free : "") + (backup.schedule === "on" ? "\nDenne automaticky" : "")) : "Cieľ zálohy nie je nastavený";
        if (k === "jazyk") return "Jazyk: " + (localeConf.LANG || "systémový (sk_SK.UTF-8)") + (localeConf.LC_TIME ? "\nFormáty: " + localeConf.LC_TIME : "");
        if (k === "mojucet") return (fullName || user) + " (" + user + ")";
        if (k === "uzamknutie") return "Zamknúť: " + (idleMin(idle.lock) ? idleMin(idle.lock) + " min" : "nikdy") + "\nObrazovka: " + (idleMin(idle.screen) ? idleMin(idle.screen) + " min" : "nikdy") + "\nUspať: " + (idleMin(idle.suspend) ? idleMin(idle.suspend) + " min" : "nikdy");
        if (k === "pristupnost") return "Mierka rozhrania " + Math.round((parseFloat(access.ui_scale) || 1) * 100) + " %" + (access.high_contrast === "true" ? " · vysoký kontrast" : "") + (noAnim ? " · bez animácií" : "") + "\nKurzor " + cursorSize + " px";
        if (k === "oznamenia") return (dnd ? "Nerušiť: zapnuté" : "Nerušiť: vypnuté") + "\nPoloha: " + ({ top_right: "vpravo hore", top_center: "hore v strede", top_left: "vľavo hore", bottom_right: "vpravo dole", bottom_left: "vľavo dole" })[notif.position || "top_right"];
        if (k === "klavesnica") return "Rozloženia sk, us (Alt+Shift)\nEditor skratiek: plán";
        if (plans[k]) return "Zatiaľ len plán";
        return "—";
    }
    function storedIn(k) {
        return ({
            domov: "/run/latteos/mode.toml", motiv: "~/.config/latteos/theme\n~/.config/latteos/theme-mode", pozadie: "~/.local/state/noctalia/settings.toml",
            okna: "~/.local/state/latteos/window-mode", vykon: "~/.config/latteos/tier", efekty: "~/.config/latteos/live-wallpaper\n~/.config/latteos/tier",
            start: "/etc/latteos/boot.toml\n/var/lib/latteos/", ai: "~/.config/latteos/ai.toml\n~/.config/latteos/ai-keys (0600)",
            lista: "~/.local/state/noctalia/settings.toml [bar.main]\n~/.config/latteos/bar-anim, bar-scene, mascot", cas: "~/.local/state/noctalia/settings.toml [location]\n~/.config/latteos/clock.conf",
            prihlasovanie: "/var/lib/latteos/greeter/greeter.conf", diagnostika: "/var/lib/latteos/greeter/last-crash.log\n/var/lib/latteos/crash-count",
            subory: "~/.config/latteos/subory.json\n~/.config/latteos/tags.json",
            oznamenia: "~/.local/state/noctalia/settings.toml [notification]",
            uzamknutie: "~/.local/state/noctalia/settings.toml [idle.behavior.*]",
            mojucet: "/var/lib/latteos/greeter/avatars/<meno>.png\n~/.face",
            synchronizacia: "~/.config/rclone/rclone.conf\n~/Cloud/<účet>\nsystemd --user latte-cloud@<účet>",
            zalohy: "~/.config/latteos/backup.conf\n<cieľ>/LatteOS-zaloha-<meno>/<dátum>\n~/.config/systemd/user/latte-backup.timer",
            jazyk: "~/.config/latteos/locale (načíta latte-session)\n/etc/locale.conf (systém)",
            pristupnost: "~/.local/state/noctalia/settings.toml [accessibility]\n~/.config/latteos/no-animations, cursor-size",
            klavesnica: "/usr/share/latteos/hypr/hyprland.lua\n~/.config/latteos/hyprland.lua"
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
            IconButton { anchors { left: parent.left; verticalCenter: parent.verticalCenter } theme: app.latteTheme; glyph: "minus"; enabledState: sp.value > sp.min; onClicked: sp.stepped(Math.max(sp.min, sp.value - sp.step)) }
            Text { anchors.centerIn: parent; text: (sp.step < 1 ? sp.value.toFixed(2) : Math.round(sp.value)) + sp.unit; color: theme.fg; font { family: theme.fontUi; pixelSize: 13; weight: Font.Bold } }
            IconButton { anchors { right: parent.right; verticalCenter: parent.verticalCenter } theme: app.latteTheme; glyph: "plus"; enabledState: sp.value < sp.max; onClicked: sp.stepped(Math.min(sp.max, sp.value + sp.step)) }
        }
    }
    // textové pole; Enter alebo strata fokusu = uložiť
    component Field: Rectangle {
        id: fld
        property string text; property string placeholder; property bool secret: false; property bool multiline: false
        signal committed(string t)
        signal edited(string t)          // každá zmena (pre tlačidlá vedľa poľa)
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
            onTextChanged: fld.edited(text)
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
        sukromie: ["Aplikácie", "NET pre každú aplikáciu: internet áno/nie. Flatpak cez jeho izoláciu, ostatné aplikácie bežia bez siete (bubblewrap). Windows hry cez Proton prídu s hernou vrstvou.", ["latte-app", "aplikacie", "opravnenia"]],
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
                  start: pStart, cas: pCas, o: pO, klavesnica: pKlavesy, oznamenia: pOznamenia, pristupnost: pPristupnost,
                  uzamknutie: pUzamknutie, mojucet: pUcet, jazyk: pJazyk, zalohy: pZalohy, pouzivatelia: pPouzivatelia, synchronizacia: pCloud })[k] || pPlan;
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
                        ["ucet", "prihlasovanie", "Účet", app.user + " · prihlásenie " + app.greeter, "user"],
                        ["hardver", "siet", "Sieť", app.netState || "…", "wifi"],
                        ["data", "zalohy", "Zálohy", app.backup.last ? "posledná " + app.backup.last.slice(0, 10) : (app.backup.target ? "zatiaľ žiadna" : "nenastavené"), "history"],
                        ["data", "synchronizacia", "Cloud", app.clouds.length ? app.clouds.filter(c => c.mounted).length + " z " + app.clouds.length + " pripojených" : "žiadny účet", "cloud"]
                    ]
                    Card {
                        required property var modelData
                        width: 250; glyph: modelData[4]; title: modelData[2]; sub: modelData[3]
                        onClicked: app.go(modelData[1])
                    }
                }
            }
            Heading { text: app.warnings.length ? "UPOZORNENIA · " + app.warnings.length : "UPOZORNENIA"; visible: true }
            Text { visible: app.warnings.length === 0; text: "● Všetko v poriadku"; color: theme.primary; font { family: theme.fontUi; pixelSize: 13; weight: Font.Bold } }
            Repeater {
                model: app.warnings
                Rectangle {
                    required property var modelData
                    width: Math.min(parent.width, 640); height: 52; radius: 12
                    color: wm.containsMouse ? theme.hover : Qt.rgba(theme.error.r, theme.error.g, theme.error.b, 0.10)
                    border { color: Qt.rgba(theme.error.r, theme.error.g, theme.error.b, 0.45); width: 1 }
                    Glyph { x: 14; anchors.verticalCenter: parent.verticalCenter; name: parent.modelData[0]; size: 20; color: theme.error }
                    Column {
                        x: 46; anchors.verticalCenter: parent.verticalCenter
                        Text { text: "! " + parent.parent.modelData[1]; color: theme.fg; font { family: theme.fontUi; pixelSize: 13; weight: Font.Bold } }
                        Text { text: parent.parent.modelData[2]; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 11 } }
                    }
                    Glyph { anchors { right: parent.right; rightMargin: 14; verticalCenter: parent.verticalCenter } name: "chevron-right"; size: 16; color: theme.fgDim }
                    MouseArea { id: wm; anchors.fill: parent; hoverEnabled: true; onClicked: app.go(parent.modelData[3]) }
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
                options: [["log", "Log pádu"], ["pocasie", "Počasie"], ["rss", "Novinky (RSS)"], ["text", "Vlastný text"], ["none", "Nič"]]
                value: app.greeterConf.panel
                onPicked: (v) => {
                    app.setGreeter("panel", v);
                    if (v === "pocasie") {   // poloha z Nastavení › Dátum, čas a poloha
                        const lat = app.location.latitude || "48.74", lon = app.location.longitude || "19.15";
                        app.setGreeter("lat", lat); app.setGreeter("lon", lon);
                    }
                }
            }
            Text { width: parent.width; wrapMode: Text.WordWrap; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 }
                   text: "Vývojárska verzia: log posledného pádu. Počasie berie polohu z Dátum, čas a poloha (Open-Meteo, bez účtu)." }
            Column {
                visible: app.greeterConf.panel === "rss"; spacing: 8; width: parent.width
                Flow {
                    width: parent.width; spacing: 8
                    Repeater {
                        model: [["https://www.aktuality.sk/rss/", "Aktuality.sk"], ["https://spravy.stvr.sk/feed/", "Správy STVR"], ["https://www.root.cz/rss/clanky/", "Root.cz"], ["https://www.phoronix.com/rss.php", "Phoronix"]]
                        Card { required property var modelData; width: 170; height: 48; title: modelData[1]; sub: ""; selected: app.greeterConf.rss_url === modelData[0]
                               onClicked: { app.setGreeter("rss_url", modelData[0]); app.setGreeter("panel_title", modelData[1]); } }
                    }
                }
                Field { text: app.greeterConf.rss_url; placeholder: "vlastný RSS odkaz"; onCommitted: (t) => { if (t !== "" && t !== app.greeterConf.rss_url) app.setGreeter("rss_url", t); } }
            }
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
            spacing: 14
            Heading { text: "ŽIVÁ TAPETA (pohyblivá textúra nad tapetou, pod oknami)" }
            Segments {
                options: [["", "Vypnutá"], ["tema", "Podľa témy"], ["para", "Para"], ["bublinky", "Bublinky"], ["sneh", "Sneh"], ["iskry", "Iskry"], ["trblietky", "Trblietky"], ["prach", "Prach"]]
                value: app.liveWp
                onPicked: (v) => app.setLive(v)
            }
            Text { width: parent.width; wrapMode: Text.WordWrap; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 }
                   text: "Podľa témy: Latte = para nad šálkou, Jantár = bublinky, Mráz = sneh, kovy = iskry, drahokamy = trblietky, kameň = prach. "
                         + "V hernom režime stojí. Stojí asi 2 % jedného jadra" + ((app.mode.tier === "softver" || app.mode.tier === "minimalny") ? " — vo VM so softvérovým kreslením ju odporúčame nechať vypnutú." : ".") }
            Heading { text: "EFEKTY OKIEN" }
            Button { label: "Stupeň výkonu"; glyph: "bolt"; primaryStyle: true; onClicked: app.go("vykon") }
            Text { width: parent.width; wrapMode: Text.WordWrap; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 13 }
                   text: "Sklo, tiene a žiaru okien riadi stupeň výkonu. Herný režim (Zariadenia na lište) ich vypne dočasne. Materiály tém ako shadery (mráz na skle, kovový lesk) prídu s GPU na reálnom HW." }
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
                        onClicked: {
                            app.run(["sh", "-c", "latte-shellset set location.latitude \"$1\" && latte-shellset set location.longitude \"$2\"", "sh", String(modelData[1]), String(modelData[2])], "Poloha: " + modelData[0]);
                            // počasie na obrazovke prihlásenia pre to isté mesto
                            app.setGreeter("place", modelData[0]); app.setGreeter("lat", String(modelData[1])); app.setGreeter("lon", String(modelData[2]));
                            app.status = "Poloha: " + modelData[0];
                        }
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
        id: pCloud
        Column {
            id: cloudPage
            spacing: 12
            readonly property var types: ({ drive: "Google Drive", onedrive: "OneDrive", dropbox: "Dropbox", webdav: "Nextcloud / WebDAV", s3: "S3", sftp: "SFTP (domáci server)", pcloud: "pCloud", mega: "MEGA", box: "Box", protondrive: "Proton Drive", alias: "priečinok" })
            Text { visible: app.clouds.length === 0; width: parent.width; wrapMode: Text.WordWrap; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 13 }
                   text: "Zatiaľ žiadny účet. Klikni Pridať účet — otvorí sa sprievodca rclone (n = nový, potom vyber službu a prihlás sa v prehliadači)." }
            Repeater {
                model: app.clouds
                Rectangle {
                    required property var modelData
                    width: Math.min(parent.width, 680); height: 64; radius: 12; color: theme.field
                    Glyph { x: 14; anchors.verticalCenter: parent.verticalCenter; name: "cloud"; size: 24; color: modelData.mounted ? theme.primary : theme.fgDim }
                    Column {
                        x: 50; anchors.verticalCenter: parent.verticalCenter
                        Text { text: parent.parent.modelData.name; color: theme.fg; font { family: theme.fontUi; pixelSize: 14; weight: Font.Bold } }
                        Text { text: (cloudPage.types[parent.parent.modelData.type] || parent.parent.modelData.type) + " · " + (parent.parent.modelData.mounted ? "● pripojené v ~/Cloud/" + parent.parent.modelData.name : "○ odpojené")
                               color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 } }
                    }
                    Row {
                        anchors { right: parent.right; rightMargin: 10; verticalCenter: parent.verticalCenter }
                        spacing: 6
                        Button { visible: parent.parent.modelData.mounted; label: "Otvoriť"; glyph: "folder"; onClicked: app.run(["latte-app", "subory", app.home + "/Cloud/" + parent.parent.modelData.name]) }
                        Button { label: parent.parent.modelData.mounted ? "Odpojiť" : "Pripojiť"; glyph: "cloud"; primaryStyle: !parent.parent.modelData.mounted
                                 onClicked: { app.run(["latte-cloud", parent.parent.modelData.mounted ? "unmount" : "mount", parent.parent.modelData.name]); cloudRefresh.restart(); } }
                        Button { label: parent.parent.modelData.auto ? "Po prihlásení: áno" : "Po prihlásení: nie"
                                 onClicked: { app.run(["latte-cloud", "auto", parent.parent.modelData.name, parent.parent.modelData.auto ? "off" : "on"]); cloudRefresh.restart(); } }
                    }
                }
            }
            Row {
                spacing: 10
                Button { label: "Pridať účet"; glyph: "plus"; primaryStyle: true; onClicked: { app.run(["latte-cloud", "add"]); cloudRefresh.interval = 20000; cloudRefresh.restart(); } }
                Button { label: "Obnoviť"; glyph: "refresh"; onClicked: cloudProc.running = true }
            }
            Text { width: parent.width; wrapMode: Text.WordWrap; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 }
                   text: "Tip: domáci server cez SSH pridáš ako typ sftp. Pripojené účty sú aj v Súboroch v sekcii Cloud." }
        }
    }
    Component {
        id: pPouzivatelia
        Column {
            spacing: 12
            Repeater {
                model: app.accounts
                Rectangle {
                    required property var modelData
                    width: Math.min(parent.width, 620); height: 64; radius: 12; color: theme.field
                    Rectangle {
                        id: av; x: 12; anchors.verticalCenter: parent.verticalCenter; width: 42; height: 42; radius: 11; color: theme.primary; clip: true
                        Text { anchors.centerIn: parent; visible: ai.status !== Image.Ready; text: parent.parent.modelData.name.charAt(0).toUpperCase(); color: theme.fgOnPrimary; font { family: theme.fontUi; pixelSize: 18; weight: Font.Bold } }
                        Image { id: ai; anchors.fill: parent; smooth: false; fillMode: Image.PreserveAspectCrop; source: "file:///var/lib/latteos/greeter/avatars/" + parent.parent.modelData.name + ".png" }
                    }
                    Column {
                        anchors { left: av.right; leftMargin: 12; verticalCenter: parent.verticalCenter }
                        Text { text: (parent.parent.modelData.full || parent.parent.modelData.name) + (parent.parent.modelData.me ? "  (ty)" : ""); color: theme.fg; font { family: theme.fontUi; pixelSize: 14; weight: Font.Bold } }
                        Text { text: parent.parent.modelData.name + " · " + (parent.parent.modelData.admin ? "správca" : "bežný účet"); color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 } }
                    }
                    Button {
                        visible: !parent.modelData.me
                        anchors { right: parent.right; rightMargin: 10; verticalCenter: parent.verticalCenter }
                        label: "Odstrániť"; glyph: "trash"; danger: true
                        onClicked: app.term("echo 'Odstrániť účet " + parent.modelData.name + " aj s domovom? (Ctrl+C = nie)'; read x; sudo userdel -r " + parent.modelData.name, "Odstránenie účtu v termináli")
                    }
                }
            }
            Heading { text: "PRIDAŤ ÚČET" }
            Row {
                spacing: 10
                Field { width: 260; placeholder: "prihlasovacie meno (malé písmená)"; onEdited: (t) => app.newUser = t.trim().toLowerCase() }
                Button {
                    label: "Pridať"; glyph: "plus"; primaryStyle: true
                    onClicked: {
                        if (!/^[a-z_][a-z0-9_-]{0,30}$/.test(app.newUser)) { app.status = "Meno: malé písmená, číslice, - a _ (napr. anna)"; return; }
                        app.term("sudo useradd -m '" + app.newUser + "' && sudo passwd '" + app.newUser + "'", "Nový účet " + app.newUser + " v termináli");
                    }
                }
            }
            Text { width: parent.width; wrapMode: Text.WordWrap; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 }
                   text: "Nový účet je bežný (bez práv správcu), domov má súkromný. Pridanie a odstránenie vyžaduje heslo správcu. Rodičovskú kontrolu pripravujeme." }
        }
    }
    Component {
        id: pZalohy
        Column {
            spacing: 14
            Heading { text: "KAM ZÁLOHOVAŤ" }
            Text { visible: app.backupDrives.length === 0; width: parent.width; wrapMode: Text.WordWrap; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 13 }
                   text: "Pripoj USB disk (objaví sa tu), alebo zadaj priečinok nižšie." }
            Flow {
                width: parent.width; spacing: 10
                Repeater {
                    model: app.backupDrives
                    Card {
                        required property var modelData
                        width: 240; glyph: "usb"; title: modelData[0].split("/").pop(); sub: modelData[1] + " voľné"; selected: app.backup.target === modelData[0]
                        onClicked: { app.run(["latte-backup", "set-target", modelData[0]], "Cieľ zálohy: " + modelData[0]); backupRefresh.restart(); }
                    }
                }
            }
            Field { placeholder: "alebo priečinok, napr. /run/media/" + app.user + "/Zaloha"; text: app.backup.target || ""
                    onCommitted: (t) => { if (t !== "" && t !== app.backup.target) { app.run(["latte-backup", "set-target", t], "Cieľ zálohy: " + t); backupRefresh.restart(); } } }
            Timer { id: backupRefresh; interval: 500; onTriggered: backupProc.running = true }
            Row {
                spacing: 10
                Button { label: app.backupPct >= 0 ? "Zálohujem… " + app.backupPct + " %" : "Zálohovať teraz"; glyph: "history"; primaryStyle: true
                         onClicked: if (app.backupPct < 0 && app.backup.target) { app.backupPct = 0; backupRun.running = true; } }
                Button { label: app.backup.schedule === "on" ? "Denne: zapnuté" : "Denne: vypnuté"; glyph: "clock"
                         onClicked: { app.run(["latte-backup", "schedule", app.backup.schedule === "on" ? "off" : "on"], "Denná záloha " + (app.backup.schedule === "on" ? "vypnutá" : "zapnutá")); backupRefresh.restart(); } }
            }
            Rectangle { visible: app.backupPct >= 0; width: parent.width; height: 6; radius: 3; color: theme.field
                        Rectangle { width: parent.width * app.backupPct / 100; height: 6; radius: 3; color: theme.primary } }
            Heading { text: "ZÁLOHY (obnova: otvor zálohu v Súboroch a skopíruj súbor späť, F5)" }
            Text { visible: app.backupList.length === 0; text: "Zatiaľ žiadne."; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 13 } }
            Repeater {
                model: app.backupList.slice(0, 10)
                Rectangle {
                    required property string modelData
                    width: Math.min(parent.width, 560); height: 44; radius: 10; color: theme.field
                    Text { x: 14; anchors.verticalCenter: parent.verticalCenter
                           text: modelData.replace(/^(\d{4})-(\d\d)-(\d\d)_(\d\d)(\d\d)(\d\d)?$/, (m, y, mo, d, h, mi) => parseInt(d) + ". " + parseInt(mo) + ". " + y + "  " + h + ":" + mi)
                           color: theme.fg; font { family: theme.fontUi; pixelSize: 13; weight: Font.DemiBold } }
                    Button { anchors { right: parent.right; rightMargin: 6; verticalCenter: parent.verticalCenter } label: "Otvoriť"; glyph: "folder"
                             onClicked: app.run(["latte-app", "subory", app.backup.target + "/LatteOS-zaloha-" + app.user + "/" + parent.modelData]) }
                }
            }
            Text { width: parent.width; wrapMode: Text.WordWrap; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 }
                   text: "Nezálohuje sa: vyrovnávacia pamäť, kôš, Steam a Flatpak aplikácie (dajú sa stiahnuť znova). Ponecháva sa 14 najnovších záloh." }
        }
    }
    Component {
        id: pJazyk
        Column {
            spacing: 14
            readonly property var langs: [["sk_SK.UTF-8", "Slovenčina", "sk"], ["cs_CZ.UTF-8", "Čeština", "cs"], ["en_US.UTF-8", "English (US)", "en"],
                                          ["en_GB.UTF-8", "English (UK)", "en"], ["de_DE.UTF-8", "Deutsch", "de"], ["hu_HU.UTF-8", "Magyar", "hu"], ["pl_PL.UTF-8", "Polski", "pl"]]
            Heading { text: "JAZYK" }
            Flow {
                width: parent.width; spacing: 10
                Repeater {
                    model: parent.parent.langs
                    Card {
                        required property var modelData
                        readonly property bool installed: app.hasLocale(modelData[0])
                        width: 190; height: 62; title: modelData[1]; sub: installed ? modelData[0] : "treba doinštalovať (klikni)"
                        selected: (app.localeConf.LANG || "sk_SK.UTF-8") === modelData[0]
                        onClicked: {
                            if (!installed) { app.run(["latte-app", "instalator", "--nazov=Jazyk_" + modelData[1].replace(/ /g, "_"), "install", "glibc-langpack-" + modelData[2]], "Inštalácia jazyka"); return; }
                            app.setLocale("LANG", modelData[0] === "sk_SK.UTF-8" ? "" : modelData[0]);
                        }
                    }
                }
            }
            Heading { text: "FORMÁTY (dátum, čas, čísla, meny)" }
            Flow {
                width: parent.width; spacing: 10
                Repeater {
                    model: [["", "Podľa jazyka"], ["sk_SK.UTF-8", "Slovensko · 24. 9. 2026 · 1 234,50 €"], ["cs_CZ.UTF-8", "Česko · 24. 09. 2026 · 1 234,50 Kč"],
                            ["en_GB.UTF-8", "UK · 24/09/2026 · £1,234.50"], ["en_US.UTF-8", "USA · 9/24/2026 · $1,234.50"]]
                    Card {
                        required property var modelData
                        width: 290; height: 56; title: modelData[1]; sub: modelData[0] && !app.hasLocale(modelData[0]) ? "treba doinštalovať jazyk" : ""
                        selected: (app.localeConf.LC_TIME || "") === modelData[0]
                        onClicked: { for (const k of ["LC_TIME", "LC_NUMERIC", "LC_MONETARY", "LC_PAPER", "LC_MEASUREMENT"]) app.setLocale(k, modelData[0]); }
                    }
                }
            }
            Text { width: parent.width; wrapMode: Text.WordWrap; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 }
                   text: "Zmena platí po odhlásení a prihlásení. Jazyk celého systému (aj obrazovky prihlásenia) mení správca: localectl set-locale." }
        }
    }
    Component {
        id: pUcet
        Column {
            spacing: 14
            Row {
                spacing: 16
                Rectangle {
                    width: 84; height: 84; radius: 20; color: theme.primary; clip: true
                    Text { anchors.centerIn: parent; visible: face.status !== Image.Ready; text: app.user.charAt(0).toUpperCase(); color: theme.fgOnPrimary; font { family: theme.fontDisplay; pixelSize: 40; weight: Font.Bold } }
                    Image { id: face; anchors.fill: parent; fillMode: Image.PreserveAspectCrop; cache: false; smooth: false
                            source: "file:///var/lib/latteos/greeter/avatars/" + app.user + ".png?" + app.avatarRev }
                }
                Column {
                    anchors.verticalCenter: parent.verticalCenter; spacing: 4
                    Text { text: app.fullName || app.user; color: theme.fg; font { family: theme.fontDisplay; pixelSize: 24; weight: Font.DemiBold } }
                    Text { text: "používateľ " + app.user; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 13 } }
                }
            }
            Heading { text: "OBRÁZOK ÚČTU (ukáže sa aj pri prihlásení)" }
            Flow {
                width: parent.width; spacing: 10
                Repeater {
                    model: app.avatarChoices
                    Rectangle {
                        required property string modelData
                        width: 72; height: 72; radius: 16; color: theme.field; clip: true
                        border { color: am2.containsMouse ? theme.primary : "transparent"; width: 2 }
                        Image { anchors { fill: parent; margins: modelData.indexOf("/mascots/") >= 0 ? 8 : 0 } source: "file://" + parent.modelData
                                fillMode: modelData.indexOf("/mascots/") >= 0 ? Image.PreserveAspectFit : Image.PreserveAspectCrop
                                smooth: modelData.indexOf("/mascots/") < 0; asynchronous: true; sourceSize { width: 144; height: 144 } }
                        MouseArea { id: am2; anchors.fill: parent; hoverEnabled: true; onClicked: app.setAvatar(parent.modelData) }
                    }
                }
            }
            Text { width: parent.width; wrapMode: Text.WordWrap; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 }
                   text: "Na výber sú maskoti LatteOS a posledné obrázky z priečinka Obrázky." }
            Row {
                spacing: 10
                Button { label: "Bez obrázka"; glyph: "x"; onClicked: app.setAvatar("") }
                Button { label: "Zmeniť heslo"; glyph: "lock"; onClicked: app.run(["foot", "-e", "passwd"], "Zmena hesla v termináli") }
            }
        }
    }
    Component {
        id: pUzamknutie
        Column {
            spacing: 14
            Heading { text: "ZAMKNÚŤ OBRAZOVKU PO" }
            Segments {
                options: [["0", "Nikdy"], ["5", "5 min"], ["10", "10 min"], ["15", "15 min"], ["30", "30 min"]]
                value: String(app.idleMin(app.idle.lock))
                onPicked: (v) => app.setIdle("lock", "lock", parseInt(v), v === "0" ? "Automatické zamknutie vypnuté" : "Zamknúť po " + v + " min")
            }
            Heading { text: "VYPNÚŤ OBRAZOVKU PO" }
            Segments {
                options: [["0", "Nikdy"], ["5", "5 min"], ["10", "10 min"], ["20", "20 min"], ["60", "1 h"]]
                value: String(app.idleMin(app.idle.screen))
                onPicked: (v) => app.setIdle("screen-off", "screen_off", parseInt(v), v === "0" ? "Obrazovka sa nevypína" : "Vypnúť obrazovku po " + v + " min")
            }
            Heading { text: "USPAŤ PO (pred uspaním zamkne)" }
            Segments {
                options: [["0", "Nikdy"], ["30", "30 min"], ["60", "1 h"], ["120", "2 h"]]
                value: String(app.idleMin(app.idle.suspend))
                onPicked: (v) => app.setIdle("lock-and-suspend", "lock_and_suspend", parseInt(v), v === "0" ? "Uspávanie vypnuté" : "Uspať po " + v + " min")
            }
            Text { width: parent.width; wrapMode: Text.WordWrap; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 }
                   text: "Vo VM uspanie nemusí fungovať. Počas hry na celú obrazovku a pri prehrávaní videa sa nečinnosť nepočíta (aplikácia to hlási sama)." }
            Button { label: "Zamknúť teraz (Super+L)"; glyph: "lock"; onClicked: app.run(["noctalia", "msg", "session", "lock"]) }
        }
    }
    Component {
        id: pPristupnost
        Column {
            spacing: 14
            Heading { text: "VEĽKOSŤ ROZHRANIA (lišta, panely)" }
            Segments {
                options: [["1", "100 %"], ["1.15", "115 %"], ["1.3", "130 %"], ["1.5", "150 %"]]
                value: String(parseFloat(app.access.ui_scale) || 1)
                onPicked: (v) => app.shellSet("accessibility.ui_scale", v === "1" ? null : parseFloat(v), "Mierka rozhrania " + Math.round(parseFloat(v) * 100) + " %")
            }
            Heading { text: "KONTRAST" }
            Segments {
                options: [["false", "Bežný"], ["true", "Vysoký kontrast"]]
                value: app.access.high_contrast === "true" ? "true" : "false"
                onPicked: (v) => app.shellSet("accessibility.high_contrast", v === "true" ? true : null, v === "true" ? "Vysoký kontrast zapnutý" : "Bežný kontrast")
            }
            Heading { text: "POHYB" }
            Segments {
                options: [["false", "Animácie podľa výkonu"], ["true", "Bez animácií"]]
                value: app.noAnim ? "true" : "false"
                onPicked: (v) => app.setNoAnim(v === "true")
            }
            Heading { text: "KURZOR" }
            Segments {
                options: [["24", "Bežný"], ["32", "Väčší"], ["48", "Veľký"], ["64", "Najväčší"]]
                value: app.cursorSize
                onPicked: (v) => { app.writePref("cursor-size", v === "24" ? "" : v, "Kurzor " + v + " px"); app.cursorSize = v; app.run(["hyprctl", "setcursor", "default", v]); }
            }
            Text { width: parent.width; wrapMode: Text.WordWrap; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 }
                   text: "Veľkosť písma v aplikáciách a čítačku obrazovky pripravujeme. Zmeny lišty a panelov platia hneď, kurzor v nových oknách po prihlásení." }
        }
    }
    Component {
        id: pOznamenia
        Column {
            spacing: 14
            Row {
                spacing: 10
                Rectangle {
                    width: 46; height: 26; radius: 13; anchors.verticalCenter: parent.verticalCenter
                    color: app.dnd ? theme.primary : theme.field; border { color: theme.line; width: 1 }
                    Rectangle { width: 20; height: 20; radius: 10; y: 3; x: app.dnd ? 23 : 3; color: app.dnd ? theme.fgOnPrimary : theme.fgDim }
                    MouseArea { anchors.fill: parent; onClicked: { app.dnd = !app.dnd; app.run(["noctalia", "msg", "notification-dnd-set", app.dnd ? "on" : "off"], app.dnd ? "Nerušiť zapnuté" : "Nerušiť vypnuté"); } }
                }
                Text { anchors.verticalCenter: parent.verticalCenter; text: "Nerušiť (oznámenia sa ukladajú do histórie, neukazujú sa)"; color: theme.fg; font { family: theme.fontUi; pixelSize: 13 } }
            }
            Heading { text: "KDE SA UKAZUJÚ" }
            Segments {
                options: [["top_right", "Vpravo hore"], ["top_center", "Hore v strede"], ["top_left", "Vľavo hore"], ["bottom_right", "Vpravo dole"], ["bottom_left", "Vľavo dole"]]
                value: app.notif.position || "top_right"
                onPicked: (v) => app.shellSet("notification.position", v, "Oznámenia: " + v)
            }
            Stepper { label: "Najviac naraz (0 = bez limitu)"; value: parseInt(app.notif.max_visible) || 0; step: 1; min: 0; max: 10; unit: ""
                      onStepped: (v) => app.shellSet("notification.max_visible", v, "Najviac naraz: " + v) }
            Heading { text: "OBSAH" }
            Segments {
                options: [["true", "Ukázať názov aplikácie"], ["false", "Bez názvu"]]
                value: app.notif.show_app_name === "false" ? "false" : "true"
                onPicked: (v) => app.shellSet("notification.show_app_name", v === "true", "Názov aplikácie: " + (v === "true" ? "áno" : "nie"))
            }
            Segments {
                options: [["true", "Tlačidlá akcií"], ["false", "Bez tlačidiel"]]
                value: app.notif.show_actions === "false" ? "false" : "true"
                onPicked: (v) => app.shellSet("notification.show_actions", v === "true", "Akcie v oznámení: " + (v === "true" ? "áno" : "nie"))
            }
            Heading { text: "Z MOBILU" }
            Text { width: parent.width; wrapMode: Text.WordWrap; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 }
                   text: "Oznámenia z telefónu cez KDE Connect (Android, iPhone obmedzene): panel Čas na lište › Oznámenia. Pravidlá podľa aplikácie pripravujeme." }
            Button { label: "Otestovať oznámenie"; glyph: "bell"; onClicked: app.run(["notify-send", "-a", "LatteOS", "Skúšobné oznámenie", "Takto vyzerá oznámenie LatteOS ☕"]) }
        }
    }
    Component {
        id: pKlavesy
        Column {
            spacing: 4
            Repeater {
                model: [["Super + Medzerník", "Text Bar / spúšťač"], ["Super + Tab", "Prehľad pásky (píš pre filter)"], ["Super + Shift + Tab", "Rýchly prepínač okien"],
                        ["Super + Z", "Rozloženie okna (polovice, štvrtiny…)"], ["Super + I", "AI rozhovor"], ["Super + G", "Herňa (hry)"], ["Super + E", "Súbory"],
                        ["Super + A", "Riadiace centrum"], ["Super + W", "Režim okien: páska → dlaždice → plávajúce"], ["Super + D", "Zobraziť plochu (a späť)"],
                        ["Super + Enter", "Terminál"], ["Super + Q", "Zavrieť okno"], ["Super + F", "Celá obrazovka"], ["Super + V", "Plávajúce okno"],
                        ["Super + šípky", "Fokus (v páske stĺpce)"], ["Super + Ctrl + šípky", "Presun okna"], ["Super + Shift + ←/→", "Okno na iný monitor"],
                        ["Super + 1…9", "Plocha 1…9"], ["Super + Shift + 1…9", "Okno na plochu"], ["Ctrl + Shift + Esc", "Monitor (správca procesov)"],
                        ["Super + L", "Zamknúť"], ["Alt + Shift", "Prepnúť rozloženie sk / us"], ["3 prsty ←/→", "Plochy"], ["4 prsty ↑ / ↓", "Prehľad pásky / plocha"]]
                Row {
                    required property var modelData
                    spacing: 16
                    Rectangle { width: 190; height: 30; radius: 8; color: theme.field
                                Text { anchors.centerIn: parent; text: modelData[0]; color: theme.fg; font { family: theme.fontMono; pixelSize: 12; weight: Font.Bold } } }
                    Text { anchors.verticalCenter: parent.verticalCenter; text: modelData[1]; color: theme.fg; font { family: theme.fontUi; pixelSize: 13 } }
                }
            }
            Text { topPadding: 10; width: parent.width; wrapMode: Text.WordWrap; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 }
                   text: "Vlastné skratky: ~/.config/latteos/hyprland.lua (načíta sa na konci a môže prepísať čokoľvek). Editor skratiek pripravujeme." }
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
