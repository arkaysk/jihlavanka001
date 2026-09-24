// LatteOS — Aplikácie (App Manager). Podľa old/main_setting_v2.md §63: Objavovať · Aktualizácie ·
// Nainštalované · Oprávnenia, a „Bude to fungovať?“ pred inštaláciou súboru (.rpm, .flatpakref,
// .AppImage, .exe, .apk, .deb). Nastavenia › Softvér vedú sem, nie do druhej implementácie.
// Backend: latte-apps. Spúšťa sa: latte-app aplikacie [objavovat|aktualizacie|nainstalovane|opravnenia|check SÚBOR]
import QtQuick
import Quickshell
import Quickshell.Io
import "common"

ShellRoot {
    id: app
    LatteTheme { id: theme }

    readonly property string home: Quickshell.env("HOME") || "/"
    readonly property var args: (Quickshell.env("LATTE_APP_ARGS") || "").trim().split(" ")
    // „check“ bez súboru (spustenie z ponuky, .desktop má %f) = Objavovať
    property string section: args[0] === "check" ? (args.length > 1 && args[1] !== "" ? "check" : "objavovat")
                           : (({ aplikacie: "nainstalovane", instalacia: "objavovat" })[args[0]] || args[0] || "objavovat")
    property string status: ""
    property string query: ""
    property var results: []
    property bool searching: false
    property var installedApps: []
    property var updatesList: []
    property bool updatesLoading: false
    property string selId: ""
    property var perms: ({})
    property string checkPath: args[0] === "check" ? args.slice(1).join(" ") : ""
    property var verdict: null
    property var downloads: []
    property string busyId: ""

    readonly property var sel: installedApps.find(a => a.id === selId) || null

    // odporúčané (IDEAS: základný balík — prehrávač, kancelária, hry, komunikácia, kalendár a úlohy)
    readonly property var picks: [
        { title: "Základ", items: [["org.mozilla.firefox", "Firefox", "Prehliadač"], ["org.videolan.VLC", "VLC", "Prehrávač videa a hudby"],
                                   ["org.libreoffice.LibreOffice", "LibreOffice", "Kancelária (doc, xls, odt)"], ["org.gnome.Calculator", "Kalkulačka", "Kalkulačka"]] },
        { title: "Hry", items: [["com.valvesoftware.Steam", "Steam", "Obchod a knižnica hier"], ["com.heroicgameslauncher.hgl", "Heroic", "Epic, GOG, Amazon"],
                                ["org.zdoom.GZDoom", "GZDoom", "DOOM (vlastné WAD súbory)"], ["org.yamagi.YamagiQ2", "Yamagi Quake II", "Quake II"]] },
        { title: "Tvorba", items: [["org.gimp.GIMP", "GIMP", "Úprava fotiek"], ["org.kde.krita", "Krita", "Kreslenie"],
                                   ["com.obsproject.Studio", "OBS Studio", "Nahrávanie a streamovanie"], ["org.kde.kdenlive", "Kdenlive", "Strih videa"]] },
        { title: "Komunikácia a čas", items: [["com.discordapp.Discord", "Discord", "Hlas a chat"], ["org.signal.Signal", "Signal", "Bezpečné správy"],
                                              ["io.github.alainm23.planify", "Planify", "Úlohy a plánovač (Todoist, CalDAV)"], ["org.gnome.Calendar", "Kalendár", "Google, iCloud, CalDAV"]] }
    ]

    function human(b) {
        if (!b) return "";
        const u = ["B", "kB", "MB", "GB"]; let v = b, i = 0;
        while (v >= 1024 && i < u.length - 1) { v /= 1024; i++; }
        return v.toFixed(v < 10 && i > 0 ? 1 : 0).replace(".", ",") + " " + u[i];
    }
    function srcName(a) { return a.latteos ? "LatteOS" : ({ flatpak: "Flatpak", rpm: "Fedora (RPM)", local: "miestne" })[a.source] || a.source; }
    function isInstalled(id) { return installedApps.some(a => a.id === id || a.package === id); }

    component Cmd: Process {
        id: c
        signal done(string out, int code)
        property string buf: ""
        stdout: StdioCollector { onStreamFinished: c.buf = this.text }
        onExited: (code) => c.done(c.buf, code)
    }
    Cmd { id: listProc; command: ["latte-apps", "installed"]; running: true
          onDone: (out) => { try { app.installedApps = JSON.parse(out); } catch (e) {} } }
    Cmd { id: updProc; command: ["latte-apps", "updates"]
          onDone: (out) => { app.updatesLoading = false; try { app.updatesList = JSON.parse(out); } catch (e) {} } }
    Cmd { id: searchProc; onDone: (out) => { app.searching = false; try { app.results = JSON.parse(out); } catch (e) { app.results = []; } } }
    Cmd { id: permProc; onDone: (out) => { try { app.perms = JSON.parse(out); } catch (e) { app.perms = {}; } } }
    Cmd { id: checkProc; onDone: (out) => { try { app.verdict = JSON.parse(out); } catch (e) { app.verdict = null; } } }
    Cmd { id: dlProc
          command: ["sh", "-c", "ls -t \"$HOME\"/Stiahnuté/* \"$HOME\"/Downloads/* 2>/dev/null | grep -iE '\\.(rpm|flatpakref|flatpak|appimage|exe|msi|apk|deb|sh|run)$' | head -12"]
          onDone: (out) => app.downloads = out.split("\n").filter(l => l !== "") }
    Cmd { id: installProc
          onDone: (out, code) => { app.status = code === 0 ? "Hotovo: " + app.busyId : "Nepodarilo sa: " + app.busyId + " (kód " + code + ")"; app.busyId = ""; listProc.running = true; } }
    Process { id: runner }
    function run(cmd, msg) { runner.command = cmd; runner.running = true; if (msg) app.status = msg; }

    Timer { id: debounce; interval: 600; onTriggered: app.doSearch() }
    function doSearch() {
        if (query.trim().length < 2) { results = []; return; }
        searching = true; searchProc.command = ["latte-apps", "search", query.trim()]; searchProc.running = true;
    }
    function install(src, id, name) {
        if (src === "flatpak") {
            busyId = id; status = "Inštalujem " + (name || id) + " z Flathubu…";
            installProc.command = ["latte-apps", "install", "flatpak", id]; installProc.running = true;
        } else run(["foot", "-e", "sh", "-c", "sudo dnf install \"$1\"; echo; read -p 'Enter zavrie okno…' x", "sh", id], "Inštalácia v termináli: " + id);
    }
    function uninstall(a) {
        if (a.source === "flatpak") {
            busyId = a.id; status = "Odinštalujem " + a.name + "…";
            installProc.command = ["latte-apps", "remove", "flatpak", a.id]; installProc.running = true;
        } else if (a.package) run(["foot", "-e", "sh", "-c", "sudo dnf remove \"$1\"; echo; read -p 'Enter zavrie okno…' x", "sh", a.package], "Odinštalovanie v termináli: " + a.package);
    }
    function launch(a) {
        const ex = (a.exec || "").replace(/%[fFuUdDnNickvm]/g, "").trim();
        if (ex) run(["sh", "-c", "setsid " + ex + " >/dev/null 2>&1 &"], "Spúšťam " + a.name);
    }
    function check(p) { checkPath = p; verdict = null; checkProc.command = ["latte-apps", "check", p]; checkProc.running = true; }
    function go(k) {
        section = k;
        if (k === "aktualizacie" && updatesList.length === 0) { updatesLoading = true; updProc.running = true; }
        if (k === "check") { dlProc.running = true; if (checkPath !== "") check(checkPath); }
        if (k === "nainstalovane" || k === "opravnenia") listProc.running = true;
    }
    Component.onCompleted: go(section)

    FloatingWindow {
        title: "Aplikácie — LatteOS"
        implicitWidth: 1220; implicitHeight: 780
        color: theme.surface

        Item {
            id: root
            anchors.fill: parent

            SideBar {
                id: side
                theme: theme
                anchors { left: parent.left; top: parent.top; bottom: parent.bottom }
                heading: "Aplikácie"; headingGlyph: "apps"
                current: app.section
                model: [
                    { title: "App Manager", items: [
                        { key: "objavovat", glyph: "search", label: "Objavovať", sub: "Flathub a Fedora" },
                        { key: "aktualizacie", glyph: "refresh", label: "Aktualizácie", sub: app.updatesLoading ? "zisťujem…" : (app.updatesList.length ? app.updatesList.length + " dostupných" : "skontrolovať") },
                        { key: "nainstalovane", glyph: "apps", label: "Nainštalované", sub: app.installedApps.length + " aplikácií" },
                        { key: "opravnenia", glyph: "shield", label: "Oprávnenia a NET", sub: "internet, súbory, zariadenia" }
                    ] },
                    { title: "Inštalácia súboru", items: [
                        { key: "check", glyph: "help", label: "Bude to fungovať?", sub: ".rpm .exe .apk .AppImage .deb" }
                    ] }
                ]
                onActivated: (it) => app.go(it.key)
            }

            HeaderBar {
                id: header
                theme: theme
                appId: "latteos-aplikacie"
                anchors { left: side.right; right: parent.right; top: parent.top }
                title: ({ objavovat: "Objavovať", aktualizacie: "Aktualizácie", nainstalovane: "Nainštalované", opravnenia: "Oprávnenia a NET", check: "Bude to fungovať?" })[app.section] || ""
                searchPlaceholder: "Hľadať aplikáciu"
                onSearchChanged: (t) => { app.query = t; if (t !== "" && app.section !== "nainstalovane") app.section = "objavovat"; debounce.restart(); }
                onCloseRequested: Qt.quit()
            }

            Flickable {
                id: content
                anchors { left: side.right; top: header.bottom; bottom: statusBar.top; right: detail.left; margins: 20 }
                contentHeight: body.implicitHeight + 20; clip: true
                Loader {
                    id: body
                    width: content.width
                    sourceComponent: ({ objavovat: pDiscover, aktualizacie: pUpdates, nainstalovane: pInstalled, opravnenia: pPerms, check: pCheck })[app.section] || pDiscover
                }
            }

            // detail vybranej aplikácie
            Rectangle {
                id: detail
                anchors { right: parent.right; top: header.bottom; bottom: statusBar.top; margins: 14 }
                width: 280; radius: theme.radius
                color: Qt.rgba(0, 0, 0, theme.mode === "dark" ? 0.16 : 0.04); border { color: theme.line; width: 1 }
                Column {
                    anchors { fill: parent; margins: 16 }
                    spacing: 10
                    readonly property var a: app.sel
                    Text { width: parent.width; wrapMode: Text.WordWrap; text: parent.a ? parent.a.name : "App Manager"
                           color: theme.fg; font { family: theme.fontDisplay; pixelSize: 20; weight: Font.DemiBold } }
                    Text { width: parent.width; wrapMode: Text.WordWrap
                           text: parent.a ? (parent.a.comment || "") : "Inštalácia jedným klikom z Flathubu (bez hesla, v izolácii) alebo z Fedory. Pred inštaláciou súboru povie, či bude fungovať."
                           color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 } }
                    Repeater {
                        model: parent.a ? [["Zdroj", app.srcName(parent.a) + (parent.a.scope === "user" ? " · tvoj účet" : " · systém")],
                                           ["Balík", parent.a.package || "—"], ["Veľkosť", parent.a.sizeText || "—"], ["Spúšťa", parent.a.exec || "—"]] : []
                        Column {
                            required property var modelData
                            width: parent.width; spacing: 1
                            Text { text: modelData[0].toUpperCase(); color: theme.fgDim; font { family: theme.fontUi; pixelSize: 10; weight: Font.Bold; letterSpacing: 0.6 } }
                            Text { width: parent.width; wrapMode: Text.WrapAnywhere; maximumLineCount: 3; elide: Text.ElideRight; text: modelData[1]; color: theme.fg; font { family: theme.fontUi; pixelSize: 12 } }
                        }
                    }
                    Item { width: 1; height: 4 }
                    component Action: Rectangle {
                        id: act
                        property string glyph; property string label; property bool danger: false
                        signal clicked()
                        width: parent.width; height: 36; radius: 10
                        color: am.containsMouse ? (danger ? Qt.rgba(theme.error.r, theme.error.g, theme.error.b, 0.2) : theme.hover) : theme.field
                        Row { x: 12; anchors.verticalCenter: parent.verticalCenter; spacing: 10
                              Glyph { name: act.glyph; size: 16; color: act.danger ? theme.error : theme.fg }
                              Text { text: act.label; color: act.danger ? theme.error : theme.fg; font { family: theme.fontUi; pixelSize: 13; weight: Font.DemiBold } } }
                        MouseArea { id: am; anchors.fill: parent; hoverEnabled: true; onClicked: act.clicked() }
                    }
                    Action { visible: !!parent.a; glyph: "player-play"; label: "Spustiť"; onClicked: app.launch(app.sel) }
                    Action { visible: !!parent.a && parent.a.source === "flatpak"; glyph: "shield"; label: "Oprávnenia a NET"
                             onClicked: { app.section = "opravnenia"; permProc.command = ["latte-apps", "permissions", app.sel.id]; permProc.running = true; } }
                    Action { visible: !!parent.a && !parent.a.latteos && (parent.a.source === "flatpak" || !!parent.a.package); danger: true; glyph: "trash"
                             label: "Odinštalovať"; onClicked: app.uninstall(app.sel) }
                }
            }

            Rectangle {
                id: statusBar
                anchors { left: side.right; right: parent.right; bottom: parent.bottom }
                height: 30; color: "transparent"
                Rectangle { width: parent.width; height: 1; color: theme.line }
                Text { x: 14; anchors.verticalCenter: parent.verticalCenter; text: app.status || (app.busyId ? "Pracujem…" : "Flatpak: pre tvoj účet bez hesla · RPM: v termináli so sudo")
                       color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 } }
            }
            ContextMenu { id: ctx; theme: theme }
        }
    }

    // ── súčasti ──────────────────────────────────────────────────────────────────
    component Heading: Text { color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12; weight: Font.Bold; letterSpacing: 0.8 } }
    component Pill: Rectangle {
        id: pill
        property string label; property bool primaryStyle: false; property bool on: true
        signal clicked()
        width: pt.implicitWidth + 24; height: 32; radius: 10; opacity: on ? 1 : 0.5
        color: primaryStyle ? theme.primary : (pm.containsMouse ? theme.hover : theme.surface)
        border { color: primaryStyle ? "transparent" : theme.line; width: 1 }
        Text { id: pt; anchors.centerIn: parent; text: pill.label; color: pill.primaryStyle ? theme.fgOnPrimary : theme.fg; font { family: theme.fontUi; pixelSize: 12; weight: Font.Bold } }
        MouseArea { id: pm; anchors.fill: parent; hoverEnabled: true; onClicked: if (pill.on) pill.clicked() }
    }
    // riadok aplikácie (výsledok hľadania, odporúčanie, aktualizácia)
    component AppRow: Rectangle {
        id: ar
        property string title; property string sub; property string badge; property string glyph: "package"
        property string actionLabel: ""; property bool actionPrimary: true; property bool actionOn: true
        signal action()
        width: parent ? parent.width : 400; height: 58; radius: 12; color: theme.field
        Glyph { x: 14; anchors.verticalCenter: parent.verticalCenter; name: ar.glyph; size: 24; color: theme.primary }
        Column {
            x: 52; width: parent.width - 52 - (btn.visible ? btn.width + 24 : 16); anchors.verticalCenter: parent.verticalCenter; spacing: 2
            Row {
                spacing: 8
                Text { text: ar.title; color: theme.fg; font { family: theme.fontUi; pixelSize: 14; weight: Font.Bold } }
                Rectangle { visible: ar.badge !== ""; anchors.verticalCenter: parent.verticalCenter; width: bt.implicitWidth + 12; height: 18; radius: 9
                            color: Qt.rgba(theme.primary.r, theme.primary.g, theme.primary.b, 0.15)
                            Text { id: bt; anchors.centerIn: parent; text: ar.badge; color: theme.primary; font { family: theme.fontUi; pixelSize: 10; weight: Font.Bold } } }
            }
            Text { width: parent.width; elide: Text.ElideRight; text: ar.sub; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 } }
        }
        Pill { id: btn; visible: ar.actionLabel !== ""; anchors { right: parent.right; rightMargin: 12; verticalCenter: parent.verticalCenter }
               label: ar.actionLabel; primaryStyle: ar.actionPrimary; on: ar.actionOn; onClicked: ar.action() }
    }

    // ── stránky ──────────────────────────────────────────────────────────────────
    Component {
        id: pDiscover
        Column {
            spacing: 10
            Text { visible: app.query === ""; width: parent.width; wrapMode: Text.WordWrap; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 13 }
                   text: "Hľadaj hore, alebo vyber z odporúčaných. Flathub aplikácie bežia v izolácii a inštalujú sa pre tvoj účet bez hesla." }
            Text { visible: app.searching; text: "Hľadám „" + app.query + "“…"; color: theme.primary; font { family: theme.fontUi; pixelSize: 13 } }
            Repeater {
                model: app.query === "" ? app.picks : []
                Column {
                    id: grp
                    required property var modelData
                    width: parent.width; spacing: 6
                    Heading { text: grp.modelData.title.toUpperCase(); topPadding: 6 }
                    Repeater {
                        model: grp.modelData.items
                        AppRow {
                            required property var modelData
                            width: grp.width; title: modelData[1]; sub: modelData[2]; badge: "Flathub"
                            readonly property bool has: app.isInstalled(modelData[0])
                            actionLabel: app.busyId === modelData[0] ? "Inštalujem…" : (has ? "Nainštalované" : "Inštalovať")
                            actionPrimary: !has; actionOn: !has && app.busyId === ""
                            onAction: app.install("flatpak", modelData[0], modelData[1])
                        }
                    }
                }
            }
            Repeater {
                model: app.query !== "" ? app.results : []
                AppRow {
                    required property var modelData
                    width: parent.width; title: modelData.name; sub: modelData.comment + "  ·  " + modelData.note
                    badge: modelData.source === "flatpak" ? "Flathub" : "Fedora"; glyph: modelData.source === "flatpak" ? "package" : "box"
                    readonly property bool has: app.isInstalled(modelData.id)
                    actionLabel: app.busyId === modelData.id ? "Inštalujem…" : (has ? "Nainštalované" : (modelData.source === "rpm" ? "Inštalovať (heslo)" : "Inštalovať"))
                    actionPrimary: !has; actionOn: !has && app.busyId === ""
                    onAction: app.install(modelData.source, modelData.id, modelData.name)
                }
            }
            Text { visible: app.query !== "" && !app.searching && app.results.length === 0; text: "Nič sa nenašlo."; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 13 } }
        }
    }
    Component {
        id: pUpdates
        Column {
            spacing: 8
            Row {
                spacing: 10
                Pill { label: "Aktualizovať všetko"; primaryStyle: true; on: app.updatesList.length > 0
                       onClicked: app.run(["foot", "-e", "sh", "-c", "sudo dnf upgrade; flatpak update --user -y; echo; read -p 'Enter zavrie okno…' x"], "Aktualizácia v termináli") }
                Pill { label: app.updatesLoading ? "Zisťujem…" : "Skontrolovať znova"; on: !app.updatesLoading
                       onClicked: { app.updatesLoading = true; updProc.running = true; } }
            }
            Text { width: parent.width; wrapMode: Text.WordWrap; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 }
                   text: "Systém (Fedora) aj aplikácie (Flatpak) na jednom mieste. Na Fedora Atomic sa systém bude aktualizovať celý naraz s možnosťou vrátiť včerajší." }
            Text { visible: !app.updatesLoading && app.updatesList.length === 0; text: "Všetko je aktuálne (podľa poslednej kontroly dnf)."; color: theme.fg; font { family: theme.fontUi; pixelSize: 13 } }
            Repeater {
                model: app.updatesList.slice(0, 80)
                AppRow {
                    required property var modelData
                    width: parent.width; height: 48; title: modelData.id; sub: modelData.version + "  ·  " + modelData.repo
                    badge: modelData.source === "flatpak" ? "Flatpak" : "Fedora"; glyph: "refresh"
                }
            }
        }
    }
    Component {
        id: pInstalled
        Column {
            spacing: 6
            Repeater {
                model: app.installedApps.filter(a => app.query === "" || (a.name + " " + a.id).toLowerCase().includes(app.query.toLowerCase()))
                Rectangle {
                    id: ir
                    required property var modelData
                    width: parent.width; height: 52; radius: 12
                    color: app.selId === modelData.id ? Qt.rgba(theme.primary.r, theme.primary.g, theme.primary.b, 0.16) : (im.containsMouse ? theme.hover : theme.field)
                    Glyph { x: 14; anchors.verticalCenter: parent.verticalCenter; name: ir.modelData.latteos ? "coffee" : (ir.modelData.source === "flatpak" ? "package" : "box"); size: 22; color: theme.primary }
                    Column {
                        x: 50; width: parent.width - 210; anchors.verticalCenter: parent.verticalCenter
                        Text { width: parent.width; elide: Text.ElideRight; text: ir.modelData.name; color: theme.fg; font { family: theme.fontUi; pixelSize: 14; weight: Font.DemiBold } }
                        Text { width: parent.width; elide: Text.ElideRight; text: ir.modelData.comment || ir.modelData.id; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 11 } }
                    }
                    Text { anchors { right: parent.right; rightMargin: 16; verticalCenter: parent.verticalCenter }
                           text: app.srcName(ir.modelData) + (ir.modelData.sizeText ? "  ·  " + ir.modelData.sizeText : ""); color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 } }
                    MouseArea {
                        id: im; anchors.fill: parent; hoverEnabled: true; acceptedButtons: Qt.LeftButton | Qt.RightButton
                        onClicked: (m) => {
                            app.selId = ir.modelData.id;
                            if (m.button !== Qt.RightButton) return;
                            const a = ir.modelData, p = mapToItem(null, m.x, m.y);
                            const items = [{ glyph: "player-play", label: "Spustiť", action: () => app.launch(a) }];
                            if (a.source === "flatpak") items.push({ glyph: "shield", label: "Oprávnenia a NET", action: () => { app.section = "opravnenia"; permProc.command = ["latte-apps", "permissions", a.id]; permProc.running = true; } });
                            items.push({ glyph: "folder", label: "Súbor .desktop", action: () => app.run(["latte-app", "subory", a.desktop.substring(0, a.desktop.lastIndexOf("/"))]) });
                            if (!a.latteos && (a.source === "flatpak" || a.package)) { items.push({ separator: true }); items.push({ glyph: "trash", label: "Odinštalovať", danger: true, action: () => app.uninstall(a) }); }
                            ctx.open(p.x, p.y, items, a.name + " · " + app.srcName(a));
                        }
                        onDoubleClicked: app.launch(ir.modelData)
                    }
                }
            }
        }
    }
    Component {
        id: pPerms
        Column {
            spacing: 10
            Text { width: parent.width; wrapMode: Text.WordWrap; color: theme.fg; font { family: theme.fontUi; pixelSize: 13 }
                   text: "NET = smie aplikácia na internet. Vypnutie platí pri každom spustení z LatteOS (lišta, Text Bar, App Manager): Flatpak cez jeho izoláciu, ostatné aplikácie bežia bez siete (bubblewrap). Zmena platí po reštarte aplikácie." }
            Repeater {
                model: app.installedApps.filter(a => !a.latteos)
                AppRow {
                    required property var modelData
                    width: parent.width; height: 54; title: modelData.name; sub: modelData.id + (modelData.source === "flatpak" ? "  ·  podrobnosti: klik na riadok" : "")
                    badge: app.srcName(modelData); glyph: modelData.net === "off" ? "world-off" : "world"
                    actionLabel: modelData.net === "off" ? "○ NET vypnutý" : "● NET zapnutý"; actionPrimary: modelData.net !== "off"
                    onAction: { app.run(["latte-apps", "net", modelData.id, modelData.net === "off" ? "on" : "off"], "NET " + (modelData.net === "off" ? "zapnutý" : "vypnutý") + ": " + modelData.name); netRefresh.restart(); }
                    MouseArea { anchors { left: parent.left; top: parent.top; bottom: parent.bottom; right: parent.right; rightMargin: 150 }
                                enabled: parent.modelData.source === "flatpak"
                                onClicked: { app.selId = parent.modelData.id; permProc.command = ["latte-apps", "permissions", parent.modelData.id]; permProc.running = true; } }
                }
            }
            Timer { id: netRefresh; interval: 700; onTriggered: listProc.running = true }
            Rectangle {
                visible: !!app.perms.app
                width: parent.width; height: pc.implicitHeight + 28; radius: 14; color: theme.field; border { color: theme.primary; width: 1 }
                Column {
                    id: pc
                    x: 14; y: 14; width: parent.width - 28; spacing: 8
                    Row {
                        width: parent.width; spacing: 12
                        Text { width: parent.width - netBtn.width - 12; elide: Text.ElideRight; anchors.verticalCenter: parent.verticalCenter
                               text: app.perms.app || ""; color: theme.fg; font { family: theme.fontUi; pixelSize: 15; weight: Font.Bold } }
                        Pill {
                            id: netBtn
                            label: app.perms.network ? "● NET zapnutý" : "○ NET vypnutý"; primaryStyle: app.perms.network
                            onClicked: { app.run(["latte-apps", "net", app.perms.app, app.perms.network ? "off" : "on"], "NET " + (app.perms.network ? "vypnutý" : "zapnutý") + ": " + app.perms.app); refreshPerm.start(); }
                        }
                    }
                    Repeater {
                        model: app.perms.summary || []
                        Row {
                            required property var modelData
                            spacing: 10
                            Text { width: 110; text: modelData[0]; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 } }
                            Text { width: pc.width - 120; wrapMode: Text.WrapAnywhere; text: modelData[1]; color: theme.fg; font { family: theme.fontUi; pixelSize: 12 } }
                        }
                    }
                    Text { text: "Zmena platí po reštarte aplikácie."; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 11 } }
                }
                Timer { id: refreshPerm; interval: 600; onTriggered: { permProc.command = ["latte-apps", "permissions", app.perms.app]; permProc.running = true; } }
            }
        }
    }
    Component {
        id: pCheck
        Column {
            spacing: 12
            Text { width: parent.width; wrapMode: Text.WordWrap; color: theme.fg; font { family: theme.fontUi; pixelSize: 13 }
                   text: "Stiahol si inštalačku? LatteOS povie vopred, či pôjde a ako. V Súboroch: pravý klik na súbor › Bude to fungovať?" }
            Heading { text: "NEDÁVNO STIAHNUTÉ" }
            Text { visible: app.downloads.length === 0; text: "V priečinku Stiahnuté nie sú inštalačné súbory."; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 } }
            Flow {
                width: parent.width; spacing: 8
                Repeater {
                    model: app.downloads
                    Pill { required property string modelData; label: modelData.split("/").pop(); primaryStyle: app.checkPath === modelData; onClicked: app.check(modelData) }
                }
            }
            Rectangle {
                visible: !!app.verdict
                width: parent.width; height: vc.implicitHeight + 32; radius: 14
                color: theme.field
                border { color: !app.verdict ? theme.line : (app.verdict.verdict === "ano" ? theme.primary : (app.verdict.verdict === "nie" ? theme.error : theme.fgDim)); width: 1.5 }
                Column {
                    id: vc
                    x: 16; y: 16; width: parent.width - 32; spacing: 8
                    Text {
                        text: app.verdict ? (({ ano: "✓ Áno, bude to fungovať", podmienecne: "◐ Pravdepodobne, s podmienkou", nie: "× Zatiaľ nie" })[app.verdict.verdict] + " — " + app.verdict.title) : ""
                        color: app.verdict && app.verdict.verdict === "nie" ? theme.error : theme.fg; font { family: theme.fontUi; pixelSize: 16; weight: Font.Bold }
                    }
                    Text { text: app.verdict ? app.verdict.name : ""; color: theme.fgDim; font { family: theme.fontMono; pixelSize: 11 } }
                    Repeater {
                        model: app.verdict ? app.verdict.reasons : []
                        Text { required property string modelData; width: vc.width; wrapMode: Text.WordWrap; text: "•  " + modelData; color: theme.fg; font { family: theme.fontUi; pixelSize: 13 } }
                    }
                    Pill {
                        visible: !!app.verdict && app.verdict.action.length > 0 && app.verdict.verdict !== "nie"
                        label: "Inštalovať / spustiť"; primaryStyle: true
                        // argv sa odovzdá ako argumenty ("$@"), názov súboru sa nikdy nevkladá do príkazu shellu
                        onClicked: app.run(["foot", "-e", "sh", "-c", "\"$@\"; echo; read -p 'Enter zavrie okno…' x", "sh"].concat(app.verdict.action), "V termináli: " + app.verdict.action.join(" "))
                    }
                }
            }
        }
    }
}
