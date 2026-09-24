// LatteOS — Správca zariadení (Device Manager). Podľa old/docs/nastavenia.md („Správca zdrojov“):
// zariadenia ako dlaždice (veľká ikona v zaoblenom štvorci, názov, stav) po skupinách; ukazuje zariadenia,
// nie ich obsah. Obrazovky: rozlíšenie a mierka s potvrdením do 15 s, inak sa zmena vráti (Enter = ponechať,
// Esc = vrátiť). Backend: latte-devices. Spúšťa sa: latte-app zariadenia [skupina]
import QtQuick
import Quickshell
import Quickshell.Io
import "common"

ShellRoot {
    id: app
    LatteTheme { id: theme }

    property string group: (Quickshell.env("LATTE_APP_ARGS") || "").trim() || "vsetko"
    property var groups: []
    property var problems: []
    property var sel: null            // { group, item }
    property string status: ""
    // obrazovka: skúšaný režim a odpočet
    property string pickMode: ""
    property real pickScale: 1
    property int countdown: 0
    property var trial: null          // { connector, mode, scale }

    function count(n) { return n + (n === 1 ? " zariadenie" : (n >= 2 && n <= 4 ? " zariadenia" : " zariadení")); }
    readonly property var shownGroups: group === "vsetko" ? groups.filter(g => g.items.length > 0) : groups.filter(g => g.key === group)

    Process {
        id: listProc; running: true
        command: ["latte-devices", "list"]
        stdout: StdioCollector { onStreamFinished: { try { const d = JSON.parse(this.text); app.groups = d.groups; app.problems = d.problems; app.refreshSel(); } catch (e) {} } }
    }
    Timer { interval: 10000; repeat: true; running: app.countdown === 0; onTriggered: listProc.running = true }
    function refreshSel() {
        if (!sel) return;
        const g = groups.find(x => x.key === sel.group);
        const it = g ? g.items.find(i => i.name === sel.item.name) : null;
        if (it) sel = { group: sel.group, item: it };
    }
    function pick(g, it) {
        sel = { group: g.key, item: it };
        if (g.key === "obrazovky" && it.mode) { pickMode = it.mode; pickScale = it.scale; }
    }

    Process { id: runner; onExited: listProc.running = true }
    function run(cmd, msg) { runner.command = cmd; runner.running = true; if (msg) app.status = msg; }

    // 15 s na potvrdenie, potom návrat (aj pri zatvorení okna)
    function tryDisplay() {
        const it = sel.item;
        trial = { connector: it.connector, mode: pickMode, scale: pickScale, before: it.mode, beforeScale: it.scale };
        run(["latte-devices", "display", "try", it.connector, pickMode, String(pickScale)], "Skúšam " + pickMode + " · mierka " + pickScale);
        countdown = 15; tick.start();
    }
    function keep() {
        if (!trial) return;
        tick.stop(); countdown = 0;
        run(["latte-devices", "display", "keep", trial.connector, trial.mode, String(trial.scale)], "Uložené: " + trial.mode + " · mierka " + trial.scale);
        trial = null;
    }
    function revert() {
        if (!trial) return;
        tick.stop(); countdown = 0;
        run(["latte-devices", "display", "try", trial.connector, trial.before, String(trial.beforeScale)], "Vrátené na " + trial.before);
        trial = null;
    }
    Timer { id: tick; interval: 1000; repeat: true; onTriggered: { app.countdown--; if (app.countdown <= 0) app.revert(); } }

    FloatingWindow {
        id: win
        title: "Správca zariadení — LatteOS"
        implicitWidth: 1220; implicitHeight: 780
        color: theme.surface
        onVisibleChanged: if (!visible) app.revert()

        Item {
            id: root
            anchors.fill: parent
            focus: true
            Keys.onReturnPressed: app.keep()
            Keys.onEscapePressed: app.revert()

            SideBar {
                id: side
                theme: theme
                anchors { left: parent.left; top: parent.top; bottom: parent.bottom }
                heading: "Zariadenia"; headingGlyph: "cpu"
                current: app.group
                model: [
                    { title: "Prehľad", items: [{ key: "vsetko", glyph: "layout-grid", label: "Všetky zariadenia", sub: app.count(app.groups.reduce((n, g) => n + g.items.length, 0)) }] },
                    { title: "Skupiny", items: app.groups.map(g => ({ key: g.key, glyph: g.glyph, label: g.title, sub: g.items.length ? app.count(g.items.length) : "nič nepripojené", dim: g.items.length === 0 })) }
                ]
                onActivated: (it) => app.group = it.key
            }

            HeaderBar {
                id: header
                theme: theme
                anchors { left: side.right; right: parent.right; top: parent.top }
                title: app.group === "vsetko" ? "Všetky zariadenia" : ((app.groups.find(g => g.key === app.group) || {}).title || "")
                searchPlaceholder: "Hľadať zariadenie"
                netVisible: false
                onCloseRequested: { app.revert(); Qt.quit(); }
            }

            Flickable {
                id: content
                anchors { left: side.right; top: header.bottom; bottom: parent.bottom; right: detail.left; margins: 20 }
                contentHeight: col.implicitHeight + 20; clip: true
                Column {
                    id: col
                    width: content.width; spacing: 16
                    Repeater {
                        model: app.shownGroups
                        Column {
                            id: grp
                            required property var modelData
                            width: col.width; spacing: 8
                            Text { text: grp.modelData.title.toUpperCase(); color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12; weight: Font.Bold; letterSpacing: 0.8 } }
                            Text { visible: grp.modelData.items.length === 0; text: "Nič nepripojené."; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 13 } }
                            Flow {
                                width: parent.width; spacing: 10
                                Repeater {
                                    model: grp.modelData.items
                                    Rectangle {
                                        id: tile
                                        required property var modelData
                                        readonly property bool picked: !!app.sel && app.sel.group === grp.modelData.key && app.sel.item.name === modelData.name
                                        width: (col.width - 10) / 2; height: 76; radius: 14
                                        color: picked ? Qt.rgba(theme.primary.r, theme.primary.g, theme.primary.b, 0.16) : (tm.containsMouse ? theme.hover : theme.field)
                                        border { color: picked ? theme.primary : "transparent"; width: 1.5 }
                                        Rectangle {   // veľká ikona v zaoblenom štvorci
                                            id: ico
                                            x: 12; anchors.verticalCenter: parent.verticalCenter
                                            width: 52; height: 52; radius: 14
                                            color: Qt.rgba(theme.primary.r, theme.primary.g, theme.primary.b, 0.14)
                                            Glyph { anchors.centerIn: parent; name: grp.modelData.glyph; size: 26; color: theme.primary }
                                        }
                                        Column {
                                            anchors { left: ico.right; leftMargin: 12; right: parent.right; rightMargin: 12; verticalCenter: parent.verticalCenter }
                                            spacing: 3
                                            Text { width: parent.width; elide: Text.ElideRight; text: tile.modelData.name; color: theme.fg; font { family: theme.fontUi; pixelSize: 14; weight: Font.Bold } }
                                            Text {
                                                width: parent.width; elide: Text.ElideRight
                                                text: ({ ok: "● ", warn: "! ", off: "○ " })[tile.modelData.status] + tile.modelData.sub
                                                color: tile.modelData.status === "warn" ? theme.error : theme.fgDim
                                                font { family: theme.fontUi; pixelSize: 12 }
                                            }
                                        }
                                        MouseArea { id: tm; anchors.fill: parent; hoverEnabled: true; onClicked: app.pick(grp.modelData, tile.modelData); onDoubleClicked: app.pick(grp.modelData, tile.modelData) }
                                    }
                                }
                            }
                        }
                    }
                    Text { visible: app.problems.length > 0; width: parent.width; wrapMode: Text.WordWrap; text: "! " + app.problems.join(" · "); color: theme.error; font { family: theme.fontUi; pixelSize: 12 } }
                }
            }

            // detail / nastavenia vybraného zariadenia
            Rectangle {
                id: detail
                anchors { right: parent.right; top: header.bottom; bottom: parent.bottom; margins: 14 }
                width: 320; radius: theme.radius
                color: Qt.rgba(0, 0, 0, theme.mode === "dark" ? 0.16 : 0.04); border { color: theme.line; width: 1 }
                Flickable {
                    anchors { fill: parent; margins: 16 }
                    contentHeight: dcol.implicitHeight; clip: true
                    Column {
                        id: dcol
                        width: parent.width; spacing: 10
                        readonly property var it: app.sel ? app.sel.item : null
                        readonly property string g: app.sel ? app.sel.group : ""
                        Text { width: parent.width; wrapMode: Text.WordWrap; text: parent.it ? parent.it.name : "Vyber zariadenie"
                               color: theme.fg; font { family: theme.fontDisplay; pixelSize: 19; weight: Font.DemiBold } }
                        Text { width: parent.width; wrapMode: Text.WordWrap; text: parent.it ? parent.it.sub : "Klikni na dlaždicu. Zariadenie je vždy v jednej skupine podľa toho, čo robí."
                               color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 } }
                        Repeater {
                            model: parent.it ? Object.keys(parent.it.details) : []
                            Column {
                                required property string modelData
                                width: dcol.width; spacing: 1
                                Text { text: modelData.toUpperCase(); color: theme.fgDim; font { family: theme.fontUi; pixelSize: 10; weight: Font.Bold; letterSpacing: 0.6 } }
                                Text { width: parent.width; wrapMode: Text.WrapAnywhere; text: String(dcol.it.details[modelData]); color: theme.fg; font { family: theme.fontUi; pixelSize: 12 } }
                            }
                        }

                        // ── obrazovka: rozlíšenie a mierka ──
                        Column {
                            visible: dcol.g === "obrazovky" && !!dcol.it && !!dcol.it.modes
                            width: parent.width; spacing: 8
                            Text { text: "ROZLÍŠENIE"; topPadding: 6; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 11; weight: Font.Bold; letterSpacing: 0.6 } }
                            Flow {
                                width: parent.width; spacing: 6
                                Repeater {
                                    model: dcol.it && dcol.it.modes ? dcol.it.modes.slice(0, 12) : []
                                    Rectangle {
                                        required property string modelData
                                        readonly property bool on: app.pickMode === modelData
                                        width: mt.implicitWidth + 16; height: 28; radius: 8
                                        color: on ? Qt.rgba(theme.primary.r, theme.primary.g, theme.primary.b, 0.2) : theme.field
                                        border { color: on ? theme.primary : "transparent"; width: 1 }
                                        Text { id: mt; anchors.centerIn: parent; text: modelData.replace("x", " × ").replace("@", " · ") + " Hz"; color: theme.fg; font { family: theme.fontUi; pixelSize: 11 } }
                                        MouseArea { anchors.fill: parent; onClicked: app.pickMode = parent.modelData }
                                    }
                                }
                            }
                            Text { text: "MIERKA"; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 11; weight: Font.Bold; letterSpacing: 0.6 } }
                            Row {
                                spacing: 6
                                Repeater {
                                    // iba mierky s celočíselnou logickou veľkosťou (inak ich Hyprland odmietne a nechá 1)
                                    model: {
                                        const r = app.pickMode.match(/^(\d+)x(\d+)/);
                                        const w = r ? parseInt(r[1]) : 0, h = r ? parseInt(r[2]) : 0;
                                        return [1, 1.25, 1.5, 1.75, 2].filter(sc => sc === 1 || (Number.isInteger(w / sc) && Number.isInteger(h / sc)));
                                    }
                                    Rectangle {
                                        required property real modelData
                                        readonly property bool on: Math.abs(app.pickScale - modelData) < 0.01
                                        width: 50; height: 28; radius: 8
                                        color: on ? Qt.rgba(theme.primary.r, theme.primary.g, theme.primary.b, 0.2) : theme.field
                                        border { color: on ? theme.primary : "transparent"; width: 1 }
                                        Text { anchors.centerIn: parent; text: (modelData * 100) + " %"; color: theme.fg; font { family: theme.fontUi; pixelSize: 11 } }
                                        MouseArea { anchors.fill: parent; onClicked: app.pickScale = parent.modelData }
                                    }
                                }
                            }
                            Rectangle {
                                readonly property bool changed: !!dcol.it && (app.pickMode !== dcol.it.mode || Math.abs(app.pickScale - dcol.it.scale) > 0.01)
                                visible: app.countdown === 0
                                width: parent.width; height: 38; radius: 10
                                color: changed ? theme.primary : theme.field
                                Text { anchors.centerIn: parent; text: "Použiť"; font { family: theme.fontUi; pixelSize: 13; weight: Font.Bold }
                                       color: parent.changed ? theme.fgOnPrimary : theme.fgDim }
                                MouseArea { anchors.fill: parent; onClicked: if (parent.changed) app.tryDisplay() }
                            }
                            // potvrdenie do 15 s
                            Rectangle {
                                visible: app.countdown > 0
                                width: parent.width; height: cc.implicitHeight + 24; radius: 12; color: theme.field; border { color: theme.primary; width: 1.5 }
                                Column {
                                    id: cc
                                    x: 12; y: 12; width: parent.width - 24; spacing: 8
                                    Text { width: parent.width; wrapMode: Text.WordWrap; text: "Ponechať toto nastavenie? Návrat o " + app.countdown + " s."; color: theme.fg; font { family: theme.fontUi; pixelSize: 13; weight: Font.Bold } }
                                    Row {
                                        spacing: 8
                                        Rectangle { width: 110; height: 34; radius: 10; color: theme.primary
                                                    Text { anchors.centerIn: parent; text: "Ponechať (Enter)"; color: theme.fgOnPrimary; font { family: theme.fontUi; pixelSize: 12; weight: Font.Bold } }
                                                    MouseArea { anchors.fill: parent; onClicked: app.keep() } }
                                        Rectangle { width: 100; height: 34; radius: 10; color: theme.surface; border { color: theme.line; width: 1 }
                                                    Text { anchors.centerIn: parent; text: "Vrátiť (Esc)"; color: theme.fg; font { family: theme.fontUi; pixelSize: 12; weight: Font.Bold } }
                                                    MouseArea { anchors.fill: parent; onClicked: app.revert() } }
                                    }
                                }
                            }
                        }

                        // ── odkazy na nástroje podľa skupiny ──
                        component Link: Rectangle {
                            id: lk
                            property string glyph; property string label
                            signal clicked()
                            width: dcol.width; height: 36; radius: 10
                            color: lm.containsMouse ? theme.hover : theme.field
                            Row { x: 12; anchors.verticalCenter: parent.verticalCenter; spacing: 10
                                  Glyph { name: lk.glyph; size: 16; color: theme.fg }
                                  Text { text: lk.label; color: theme.fg; font { family: theme.fontUi; pixelSize: 13; weight: Font.DemiBold } } }
                            MouseArea { id: lm; anchors.fill: parent; hoverEnabled: true; onClicked: lk.clicked() }
                        }
                        Link { visible: dcol.g === "siet"; glyph: "wifi"; label: "Pripojenia (nmtui)"; onClicked: app.run(["foot", "-e", "nmtui"]) }
                        Link { visible: dcol.g === "zvuk"; glyph: "volume"; label: "Zvuk v riadiacom centre"; onClicked: app.run(["noctalia", "msg", "panel-open", "control-center", "audio"]) }
                        Link { visible: dcol.g === "bluetooth"; glyph: "bluetooth"; label: "Bluetooth v riadiacom centre"; onClicked: app.run(["noctalia", "msg", "panel-open", "control-center", "bluetooth"]) }
                        Link { visible: dcol.g === "disky"; glyph: "folder"; label: "Otvoriť v Súboroch"; onClicked: app.run(["latte-app", "subory"]) }
                        Link { visible: dcol.g === "grafika"; glyph: "bolt"; label: "Stupeň výkonu (Nastavenia)"; onClicked: app.run(["latte-app", "nastavenia", "vykon"]) }
                        Link { visible: dcol.g === "napajanie"; glyph: "battery"; label: "Profil výkonu v Zariadeniach na lište"; onClicked: app.run(["noctalia", "msg", "panel-toggle", "latteos/devices:panel"]) }
                        Link { visible: dcol.g === "pocitac"; glyph: "activity"; label: "Živý stav v Monitore"; onClicked: app.run(["latte-app", "monitor"]) }
                        Text { width: parent.width; wrapMode: Text.WordWrap; text: app.status; color: theme.primary; font { family: theme.fontUi; pixelSize: 12 } }
                    }
                }
            }
        }
    }
}
