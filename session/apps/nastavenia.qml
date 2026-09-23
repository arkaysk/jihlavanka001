// LatteOS — Nastavenia (návrh V2: bočná lišta so stavom sekcie, hlavička, obsah, detail vpravo).
// Radar: „Všetko prepínačmi, žiadne editovanie súborov“. Spúšťa sa: latte-app nastavenia [sekcia]
import QtQuick
import Quickshell
import Quickshell.Io
import "common"

ShellRoot {
    id: app
    LatteTheme { id: theme }

    readonly property string home: Quickshell.env("HOME") || "/"
    readonly property string cfgHome: Quickshell.env("XDG_CONFIG_HOME") || (home + "/.config")
    readonly property string stateHome: Quickshell.env("XDG_STATE_HOME") || (home + "/.local/state")
    property string section: (Quickshell.env("LATTE_APP_ARGS") || "").trim() || "domov"
    property var history: []
    property int historyIndex: -1
    property string search: ""
    property string status: ""

    // stav LatteOS
    property var mode: ({})
    property string tierChoice: "auto"
    property string windowMode: "paska"
    property bool forceSafe: false
    property int crashCount: 0
    property var themes: []
    property var wallpapers: []
    property string greeter: "latte"

    // ── sekcie: done = hotové (plná bodka), inak plán (prázdna) ─────────────────
    readonly property var sections: [
        { key: "domov",    glyph: "home",        label: "Domov",       sub: "Stav systému", done: true,  area: "Systém" },
        { key: "vzhlad",   glyph: "palette",     label: "Vzhľad",      sub: "Téma, tapeta", done: true,  area: "Prostredie" },
        { key: "okna",     glyph: "layout-columns", label: "Okná",     sub: "Páska, dlaždice", done: true, area: "Prostredie" },
        { key: "vykon",    glyph: "bolt",        label: "Výkon",       sub: "Stupeň efektov", done: true, area: "Grafika" },
        { key: "start",    glyph: "shield",      label: "Štart a prihlásenie", sub: "NORMAL / SAFE", done: true, area: "Systém" },
        { key: "softver",  glyph: "apps",        label: "Softvér",     sub: "Zatiaľ len plán", done: false, area: "App Manager" },
        { key: "data",     glyph: "folder",      label: "Dáta",        sub: "Súbory, disky", done: false, area: "Data Manager" },
        { key: "zariadenia", glyph: "cpu",       label: "Zariadenia",  sub: "Zatiaľ len plán", done: false, area: "Device Manager" },
        { key: "ucet",     glyph: "user",        label: "Účet",        sub: "Zatiaľ len plán", done: false, area: "Session Manager" },
        { key: "sukromie", glyph: "world",       label: "Súkromie a NET", sub: "Zatiaľ len plán", done: false, area: "Bezpečnosť" }
    ]
    readonly property var current: sections.find(s => s.key === section) || sections[0]

    function go(key, push) {
        section = key;
        if (push !== false) { history = history.slice(0, historyIndex + 1).concat([key]); historyIndex = history.length - 1; }
    }
    Component.onCompleted: go(section)

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
    FileView { path: app.stateHome + "/latteos/window-mode"; printErrors: false; watchChanges: true; onFileChanged: reload()
               onLoaded: app.windowMode = text().trim() || "paska" }
    FileView { path: "/var/lib/latteos/crash-count"; printErrors: false; watchChanges: true; onFileChanged: reload()
               onLoaded: app.crashCount = parseInt(text()) || 0 }
    FileView { path: "/etc/latteos/boot.toml"; printErrors: false
               onLoaded: { const r = text().match(/^greeter = "(\w+)"/m); app.greeter = r ? r[1] : "latte"; } }
    Process {
        id: scan; running: true
        command: ["sh", "-c", "test -e /var/lib/latteos/force-safe && echo FORCE; for f in /usr/share/latteos/themes/*.theme; do printf 'T %s|%s|%s\\n' \"$(basename $f .theme)\" \"$(sed -n 's/^name = //p' $f)\" \"$(sed -n 's/^desc = //p' $f)\"; done; for f in /usr/share/backgrounds/latteos/*; do echo \"W $f\"; done"]
        stdout: StdioCollector {
            onStreamFinished: {
                const th = [], wp = []; let fs = false;
                for (const l of this.text.split("\n")) {
                    if (l === "FORCE") fs = true;
                    else if (l.startsWith("T ")) { const p = l.slice(2).split("|"); th.push({ id: p[0], name: p[1], desc: p[2] }); }
                    else if (l.startsWith("W ")) wp.push(l.slice(2));
                }
                app.forceSafe = fs; app.themes = th; app.wallpapers = wp;
            }
        }
    }
    Timer { interval: 4000; repeat: true; running: true; onTriggered: scan.running = true }

    Process { id: runner }
    function run(cmd, msg) { runner.command = cmd; runner.running = true; if (msg) app.status = msg; }
    function setTier(t) {
        if (t === "auto") run(["sh", "-c", "rm -f \"$1\" && hyprctl reload", "sh", app.cfgHome + "/latteos/tier"], "Stupeň: automaticky");
        else run(["sh", "-c", "mkdir -p \"$(dirname \"$1\")\" && printf '%s\\n' \"$2\" > \"$1\" && hyprctl reload", "sh", app.cfgHome + "/latteos/tier", t], "Stupeň: " + t);
        app.tierChoice = t;
    }

    // ── okno ─────────────────────────────────────────────────────────────────────
    FloatingWindow {
        title: "Nastavenia — LatteOS"
        implicitWidth: 1180; implicitHeight: 760
        color: theme.surface

        SideBar {
            id: side
            theme: theme
            anchors { left: parent.left; top: parent.top; bottom: parent.bottom }
            heading: "Nastavenia"; headingGlyph: "settings"
            current: app.section
            model: [{ title: "LatteOS", items: app.sections.filter(s => app.search === "" || (s.label + " " + s.sub).toLowerCase().includes(app.search.toLowerCase())) }]
            onActivated: (it) => app.go(it.key)
        }

        HeaderBar {
            id: header
            theme: theme
            anchors { left: side.right; right: parent.right; top: parent.top }
            title: app.current.label
            canBack: app.historyIndex > 0
            canForward: app.historyIndex < app.history.length - 1
            searchPlaceholder: "Hľadať nastavenie"
            onBack: { app.historyIndex--; app.go(app.history[app.historyIndex], false); }
            onForward: { app.historyIndex++; app.go(app.history[app.historyIndex], false); }
            onSearchChanged: (t) => app.search = t
            onCloseRequested: Qt.quit()
        }

        // obsah
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

        // detail (návrh V2: stav sekcie, oblasť)
        Rectangle {
            id: detail
            anchors { right: parent.right; top: header.bottom; bottom: parent.bottom; margins: 14 }
            width: 260; radius: theme.radius
            color: Qt.rgba(0, 0, 0, theme.mode === "dark" ? 0.16 : 0.04); border { color: theme.line; width: 1 }
            Column {
                anchors { fill: parent; margins: 18 }
                spacing: 12
                Text { text: app.current.label; color: theme.fg; font { family: theme.fontUi; pixelSize: 17; weight: Font.Bold } }
                Row {
                    spacing: 8
                    Rectangle { width: 10; height: 10; radius: 5; anchors.verticalCenter: parent.verticalCenter
                                color: app.current.done ? theme.primary : "transparent"; border { color: theme.primary; width: 1.5 } }
                    Text { text: app.current.done ? "Hotové" : "Plán"; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 13 } }
                }
                Text { text: "STAV"; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 10; weight: Font.Bold; letterSpacing: 0.8 } }
                Text { width: parent.width; wrapMode: Text.WordWrap; text: app.stateText(app.section); color: theme.fg; font { family: theme.fontUi; pixelSize: 12 } }
                Text { text: "OBLASŤ"; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 10; weight: Font.Bold; letterSpacing: 0.8 } }
                Text { text: app.current.area; color: theme.fg; font { family: theme.fontUi; pixelSize: 13 } }
                Text { text: "ULOŽENÉ V"; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 10; weight: Font.Bold; letterSpacing: 0.8 } }
                Text { width: parent.width; wrapMode: Text.WrapAnywhere; text: app.storedIn(app.section); color: theme.fgDim; font { family: theme.fontMono; pixelSize: 11 } }
            }
            Text {
                anchors { left: parent.left; right: parent.right; bottom: parent.bottom; margins: 18 }
                wrapMode: Text.WordWrap; text: app.status; color: theme.primary; font { family: theme.fontUi; pixelSize: 12 }
            }
        }
    }

    // ── texty sekcií ─────────────────────────────────────────────────────────────
    function intro(k) {
        return ({
            domov: "Prehľad: v akom režime LatteOS beží, ako kreslí grafiku a aká téma je aktívna.",
            vzhlad: "Téma prefarbí lištu, panely, okná aj aplikácie naraz. Materiály (mráz, kov, kameň) sa pohnú až pri stupni Plný.",
            okna: "Ako sa ukladajú okná. Super+W prepína režimy aj bez otvárania nastavení.",
            vykon: "Stupeň určuje efekty (sklo, tiene, žiara, animácie). Automaticky ho volí štart systému podľa hardvéru.",
            start: "Režim NORMAL (Hyprland) alebo SAFE (labwc bez GPU). SAFE naskočí sám po dvoch pádoch za sebou.",
            softver: "App Manager: inštalácia jedným klikom (Flatpak, RPM, .exe, .apk), aktualizácie a návrat systému. Pripravujeme.",
            data: "Súbory (Data Manager) sú prvá verzia — otvorí ich tlačidlo nižšie alebo Super+E.",
            zariadenia: "Device Manager: grafika, zvuk, sieť, Bluetooth, disky a stupeň výkonu podľa GPU. Pripravujeme.",
            ucet: "Session Manager: používatelia, prenos profilu (USB, cloud), prihlásenie mobilom. Pripravujeme.",
            sukromie: "Trusted/untrusted aplikácie a tlačidlo NET pre každú aplikáciu. Pripravujeme (hlavný odlišovací prvok LatteOS)."
        })[k] || "";
    }
    function stateText(k) {
        const m = app.mode;
        if (k === "domov" || k === "start") return (m.mode || "?").toUpperCase() + " · " + (m.renderer || "?") + " · stupeň " + (m.tier || "?") + (m.reason ? "\n" + m.reason : "");
        if (k === "vzhlad") return "Téma " + theme.themeName + " (" + theme.mode + ")";
        if (k === "okna") return ({ paska: "Nekonečná páska", dlazdice: "Dlaždice", plavajuce: "Plávajúce okná" })[app.windowMode] || app.windowMode;
        if (k === "vykon") return app.tierChoice === "auto" ? "Automaticky (" + (m.tier || "?") + ")" : "Vynútený: " + app.tierChoice;
        return "Zatiaľ len plán";
    }
    function storedIn(k) {
        return ({
            domov: "/run/latteos/mode.toml", vzhlad: "~/.config/latteos/theme", okna: "~/.local/state/latteos/window-mode",
            vykon: "~/.config/latteos/tier", start: "/etc/latteos/boot.toml\n/var/lib/latteos/"
        })[k] || "—";
    }

    // ── stránky ──────────────────────────────────────────────────────────────────
    component Card: Rectangle {
        id: card
        property string title; property string sub; property bool selected: false; property color swatch: "transparent"
        signal clicked()
        width: 200; height: 76; radius: 12
        color: selected ? Qt.rgba(theme.primary.r, theme.primary.g, theme.primary.b, 0.16) : (cm.containsMouse ? theme.hover : theme.field)
        border { color: selected ? theme.primary : "transparent"; width: 1.5 }
        Column {
            anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter; margins: 14 }
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

    function page(k) {
        return ({ domov: pDomov, vzhlad: pVzhlad, okna: pOkna, vykon: pVykon, start: pStart, data: pData })[k] || pPlan;
    }

    Component {
        id: pDomov
        Flow {
            spacing: 12
            Repeater {
                model: [
                    ["Režim", (app.mode.mode || "?").toUpperCase()], ["Grafika", app.mode.renderer || "?"],
                    ["Stupeň výkonu", app.mode.tier || "?"], ["Téma", theme.themeName],
                    ["Režim okien", ({ paska: "Páska", dlazdice: "Dlaždice", plavajuce: "Plávajúce" })[app.windowMode] || app.windowMode],
                    ["Pády NORMAL", app.crashCount + " / 2"]
                ]
                Card { required property var modelData; title: modelData[1]; sub: modelData[0] }
            }
        }
    }
    Component {
        id: pVzhlad
        Column {
            spacing: 14
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
            Heading { text: "TAPETA" }
            Flow {
                width: parent.width; spacing: 10
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
                Button { label: "Vynulovať"; glyph: "refresh"; onClicked: app.run(["latte-boot", "reset"], "Počítadlo vynulované") }
            }
            Heading { text: "OBRAZOVKA PRIHLÁSENIA" }
            Text {
                width: parent.width; wrapMode: Text.WordWrap
                text: "Aktuálne: " + ({ latte: "LatteOS (grafická)", tui: "textová (tuigreet)", noctalia: "Noctalia Greeter" })[app.greeter]
                      + ". Zmena vyžaduje administrátora: v /etc/latteos/boot.toml riadok greeter = \"latte\" alebo \"tui\"."
                color: theme.fgDim; font { family: theme.fontUi; pixelSize: 13 }
            }
        }
    }
    Component {
        id: pData
        Column {
            spacing: 12
            Button { label: "Otvoriť Súbory"; glyph: "folder"; primaryStyle: true; onClicked: app.run(["latte-app", "subory"]) }
        }
    }
    Component {
        id: pPlan
        Rectangle {
            width: 420; height: 120; radius: 14; color: theme.field
            Column {
                anchors.centerIn: parent; spacing: 6
                Glyph { anchors.horizontalCenter: parent.horizontalCenter; name: app.current.glyph; size: 34; color: theme.primary }
                Text { anchors.horizontalCenter: parent.horizontalCenter; text: "Zatiaľ len plán"; color: theme.fg; font { family: theme.fontUi; pixelSize: 15; weight: Font.Bold } }
                Text { anchors.horizontalCenter: parent.horizontalCenter; text: app.current.area + " · ROADMAP.md"; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 } }
            }
        }
    }
}
