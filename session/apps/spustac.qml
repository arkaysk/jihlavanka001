// LatteOS — App Manager: rýchle spustenie (zadanie 24. 9. večer). Vyskakovacie okno z dlaždice aplikácií na lište:
//   Aplikácie   všetky nainštalované ako v mobile (hľadanie navrchu, často používané, skupiny podľa druhu, A–Z)
//   Na pozadí   aplikácie v oblasti oznámení (Discord, Steam…; ako skryté ikony vo Win11) a bežiace Flatpaky
// Klik na aplikáciu ju spustí a okno zavrie, klik mimo alebo Esc zavrie. Pripínačik vpravo hore otvorí plný
// App Manager ako klasické okno (– □ ✕). Beží na pozadí (rýchle otvorenie); prepína ho latte-spustac.
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Quickshell.Hyprland
import Quickshell.Services.SystemTray
import "common"

ShellRoot {
    id: sp
    LatteTheme { id: theme }

    readonly property string state: (Quickshell.env("XDG_STATE_HOME") || ((Quickshell.env("HOME") || "") + "/.local/state")) + "/latteos"
    property bool open: (Quickshell.env("LATTE_APP_ARGS") || "").includes("--ukaz")
    property string tab: "apps"
    property string query: ""
    property var usage: ({})                 // id → { n, t } (počet a čas spustení)

    IpcHandler {
        target: "spustac"
        // „show“ by sa bilo s podpríkazom `qs ipc show`
        function prepni(): void { sp.open = !sp.open; }
        function otvor(): void { sp.open = true; }
        function zavri(): void { sp.open = false; }
    }
    onOpenChanged: { if (open) { query = ""; tab = "apps"; flatpakPs.running = true; } else closeMenu(); }

    FileView {
        id: usageFile
        path: sp.state + "/spustac.json"; printErrors: false
        onLoaded: { try { sp.usage = JSON.parse(text()) || {}; } catch (e) { sp.usage = {}; } }
    }
    function launch(e) {
        const u = Object.assign({}, usage);
        u[e.id] = { n: ((u[e.id] || {}).n || 0) + 1, t: Date.now() };
        usage = u; usageFile.setText(JSON.stringify(u));
        e.execute();
        open = false;
    }
    function fullManager() { open = false; run.command = ["latte-app", "aplikacie"]; run.startDetached(); }
    Process { id: run }

    // skupiny podľa hlavných kategórií freedesktop
    readonly property var groups: [
        ["latte", "LatteOS"], ["Game", "Hry"], ["Network", "Internet a komunikácia"], ["AudioVideo", "Hudba a video"],
        ["Graphics", "Grafika a foto"], ["Office", "Kancelária"], ["Development", "Vývoj"], ["Education", "Vzdelávanie a veda"],
        ["Utility", "Nástroje"], ["System", "Systém"], ["other", "Ostatné"]
    ]
    function groupOf(e) {
        if (e.id.startsWith("latteos-")) return "latte";
        const c = e.categories || [];
        for (const g of groups) if (c.indexOf(g[0]) >= 0) return g[0];
        if (c.indexOf("Audio") >= 0 || c.indexOf("Video") >= 0) return "AudioVideo";
        if (c.indexOf("Science") >= 0) return "Education";
        if (c.indexOf("Settings") >= 0) return "System";
        return "other";
    }
    readonly property var apps: DesktopEntries.applications.values.filter(e => !e.noDisplay && e.name !== "")
                                 .sort((a, b) => a.name.localeCompare(b.name, "sk"))
    readonly property var found: query === "" ? [] : apps.filter(e => (e.name + " " + e.genericName + " " + e.comment + " " + (e.keywords || []).join(" "))
                                                                 .toLowerCase().includes(query.toLowerCase()))
    readonly property var frequent: apps.filter(e => usage[e.id]).sort((a, b) => (usage[b.id].n - usage[a.id].n) || (usage[b.id].t - usage[a.id].t)).slice(0, 6)

    // bežiace Flatpaky (aj bez ikony v oblasti oznámení)
    property var flatpaks: []
    Process {
        id: flatpakPs
        command: ["sh", "-c", "flatpak ps --columns=application 2>/dev/null | sort -u"]
        stdout: StdioCollector { onStreamFinished: sp.flatpaks = this.text.split("\n").filter(l => l !== "" && !l.startsWith("org.freedesktop.") && !l.endsWith(".Platform")) }
    }
    Process { id: killer; onExited: flatpakPs.running = true }

    // ponuka aplikácie z oblasti oznámení (DBusMenu) kreslená v paneli — natívne vyskakovacie menu sa nad
    // vrstvou s výhradným fokusom neukáže
    property var menuRoot: null
    property point menuAt: Qt.point(0, 0)
    function openMenu(item, x, y) { menuAt = Qt.point(x, y); opener.menu = item.menu; menuRoot = item; }
    function closeMenu() { menuRoot = null; opener.menu = null; }
    QsMenuOpener { id: opener }

    function iconFor(name) { return name ? Quickshell.iconPath(name, true) : ""; }

    // jedna vrstva cez celú obrazovku (priehľadná) s panelom vľavo dole: s výhradným fokusom klávesnice Hyprland
    // posiela vstup iba tejto vrstve, preto klik mimo panelu dopadne sem a panel zavrie (aj klik na lištu)
    PanelWindow {
        id: pop
        visible: sp.open
        anchors { top: true; bottom: true; left: true; right: true }
        exclusionMode: ExclusionMode.Ignore
        WlrLayershell.layer: WlrLayer.Overlay
        WlrLayershell.namespace: "latte-spustac"
        WlrLayershell.keyboardFocus: sp.open ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None
        color: "transparent"
        MouseArea { anchors.fill: parent; acceptedButtons: Qt.AllButtons; onPressed: sp.open = false }

        Rectangle {
            id: box
            x: 12; y: parent.height - height - 72; width: 660; height: 640; radius: 22
            color: Qt.rgba(theme.surface.r, theme.surface.g, theme.surface.b, 1)
            border { color: theme.outline; width: 1 }
            focus: true
            MouseArea { anchors.fill: parent; acceptedButtons: Qt.AllButtons }     // klik do panelu ho nezavrie
            Keys.onEscapePressed: sp.open = false
            Keys.onPressed: (ev) => {
                if (ev.key === Qt.Key_Return || ev.key === Qt.Key_Enter) { if (sp.found.length) sp.launch(sp.found[0]); ev.accepted = true; }
                else if (ev.text !== "" && ev.text >= " " && !search.activeFocus) { search.forceActiveFocus(); search.text += ev.text; ev.accepted = true; }
            }

            // hlavička: hľadanie, záložky, pripínačik
            Row {
                id: head
                x: 18; y: 16; width: parent.width - 36; spacing: 10
                Rectangle {
                    width: parent.width - tabs.width - pin.width - 20; height: 42; radius: 21; color: theme.field
                    border { color: search.activeFocus ? theme.primary : "transparent"; width: 1 }
                    Glyph { x: 14; anchors.verticalCenter: parent.verticalCenter; name: "search"; size: 16; color: theme.fgDim }
                    TextInput {
                        id: search
                        anchors { fill: parent; leftMargin: 40; rightMargin: 14 }
                        verticalAlignment: TextInput.AlignVCenter; color: theme.fg; font { family: theme.fontUi; pixelSize: 14 }
                        onTextChanged: { sp.query = text; if (text !== "") sp.tab = "apps"; }
                        Keys.onEscapePressed: { if (text !== "") text = ""; else sp.open = false; }
                        Keys.onReturnPressed: if (sp.found.length) sp.launch(sp.found[0])
                        Connections { target: sp; function onOpenChanged() { if (sp.open) { search.text = ""; search.forceActiveFocus(); } } }
                    }
                    Text { x: 40; anchors.verticalCenter: parent.verticalCenter; visible: search.text === ""; text: "Hľadať aplikáciu…"; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 14 } }
                }
                Row {
                    id: tabs; spacing: 4; anchors.verticalCenter: parent.verticalCenter
                    Repeater {
                        model: [["apps", "Aplikácie"], ["bg", "Na pozadí" + ((SystemTray.items.values.length + sp.flatpaks.length) ? " · " + (SystemTray.items.values.length) : "")]]
                        Rectangle {
                            required property var modelData
                            width: tt.implicitWidth + 24; height: 34; radius: 17
                            color: sp.tab === modelData[0] ? theme.primary : (tm.containsMouse ? theme.hover : "transparent")
                            Text { id: tt; anchors.centerIn: parent; text: modelData[1]; color: sp.tab === modelData[0] ? theme.fgOnPrimary : theme.fg; font { family: theme.fontUi; pixelSize: 13; weight: Font.DemiBold } }
                            MouseArea { id: tm; anchors.fill: parent; hoverEnabled: true; onClicked: { sp.tab = modelData[0]; if (sp.tab === "bg") flatpakPs.running = true; } }
                        }
                    }
                }
                Rectangle {   // pripnúť = plný App Manager ako okno
                    id: pin
                    width: pr.implicitWidth + 20; height: 34; radius: 17; anchors.verticalCenter: parent.verticalCenter
                    color: pm.containsMouse ? theme.hover : theme.field
                    Row { id: pr; anchors.centerIn: parent; spacing: 4
                          Text { text: "📌"; font.pixelSize: 14; anchors.verticalCenter: parent.verticalCenter }
                          Text { text: "Pripnúť"; color: theme.fg; font { family: theme.fontUi; pixelSize: 12; weight: Font.DemiBold }
                                 anchors.verticalCenter: parent.verticalCenter } }
                    MouseArea { id: pm; anchors.fill: parent; hoverEnabled: true; onClicked: sp.fullManager() }
                }
            }

            // dlaždica aplikácie (ikona ako v mobile, názov pod ňou)
            component AppTile: Item {
                id: at
                required property var entry
                width: 96; height: 92
                Rectangle { anchors.fill: parent; radius: 16; color: am.containsMouse ? theme.hover : "transparent" }
                Rectangle {
                    id: ib
                    width: 52; height: 52; radius: 15
                    anchors { horizontalCenter: parent.horizontalCenter; top: parent.top; topMargin: 6 }
                    color: ic.status === Image.Ready ? "transparent" : Qt.rgba(theme.primary.r, theme.primary.g, theme.primary.b, 0.18)
                    Image {
                        id: ic; anchors.fill: parent; anchors.margins: 2
                        source: sp.iconFor(at.entry.icon); sourceSize { width: 96; height: 96 }
                        fillMode: Image.PreserveAspectFit; asynchronous: true
                    }
                    Text { anchors.centerIn: parent; visible: ic.status !== Image.Ready; text: at.entry.name.charAt(0).toUpperCase()
                           color: theme.primary; font { family: theme.fontDisplay; pixelSize: 24; weight: Font.Bold } }
                }
                Text {
                    anchors { top: ib.bottom; topMargin: 5; horizontalCenter: parent.horizontalCenter }
                    width: parent.width - 6; horizontalAlignment: Text.AlignHCenter; elide: Text.ElideRight; maximumLineCount: 2; wrapMode: Text.WordWrap
                    text: at.entry.name; color: theme.fg; font { family: theme.fontUi; pixelSize: 11; weight: Font.Medium }
                }
                MouseArea { id: am; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: sp.launch(at.entry) }
            }
            component Section: Text { width: list.width; topPadding: 10; bottomPadding: 2; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 11; weight: Font.Bold; letterSpacing: 0.8 } }

            // aplikácie
            Flickable {
                id: list
                visible: sp.tab === "apps"
                anchors { left: parent.left; right: parent.right; top: head.bottom; bottom: foot.top; margins: 18; topMargin: 12 }
                contentHeight: appCol.implicitHeight; clip: true; boundsBehavior: Flickable.StopAtBounds
                Column {
                    id: appCol; width: list.width
                    Text { visible: sp.query !== "" && sp.found.length === 0; topPadding: 30; width: parent.width; horizontalAlignment: Text.AlignHCenter
                           text: "Nič také nie je nainštalované. Skús App Manager ›"; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 13 } }
                    Flow { visible: sp.query !== ""; width: parent.width; Repeater { model: sp.query !== "" ? sp.found : []; AppTile { required property var modelData; entry: modelData } } }
                    Section { visible: sp.query === "" && sp.frequent.length > 0; text: "ČASTO POUŽÍVANÉ" }
                    Flow { visible: sp.query === ""; width: parent.width; Repeater { model: sp.query === "" ? sp.frequent : []; AppTile { required property var modelData; entry: modelData } } }
                    Repeater {
                        model: sp.query === "" ? sp.groups : []
                        Column {
                            id: grp
                            required property var modelData
                            readonly property var items: sp.apps.filter(e => sp.groupOf(e) === modelData[0])
                            visible: items.length > 0; width: appCol.width
                            Section { text: grp.modelData[1].toUpperCase() + "  ·  " + grp.items.length }
                            Flow { width: parent.width; Repeater { model: grp.items; AppTile { required property var modelData; entry: modelData } } }
                        }
                    }
                }
            }

            // na pozadí: oblasť oznámení (SNI) + bežiace Flatpaky
            Flickable {
                id: bgList
                visible: sp.tab === "bg"
                anchors { left: parent.left; right: parent.right; top: head.bottom; bottom: foot.top; margins: 18; topMargin: 12 }
                contentHeight: bgCol.implicitHeight; clip: true
                Column {
                    id: bgCol; width: bgList.width; spacing: 6
                    Text { width: parent.width; wrapMode: Text.WordWrap; bottomPadding: 6; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 }
                           text: "Aplikácie, ktoré bežia aj bez okna (ako skryté ikony vo Windows). Klik = otvoriť, pravý klik = ich ponuka." }
                    Flow {
                        width: parent.width; spacing: 8
                        Repeater {
                            model: SystemTray.items
                            Rectangle {
                                id: ti
                                required property var modelData
                                width: 96; height: 92; radius: 16; color: tim.containsMouse ? theme.hover : theme.field
                                Image {
                                    id: tic
                                    width: 40; height: 40; anchors { horizontalCenter: parent.horizontalCenter; top: parent.top; topMargin: 12 }
                                    source: ti.modelData.icon; sourceSize { width: 80; height: 80 }
                                        fillMode: Image.PreserveAspectFit
                                }
                                Text { anchors { top: tic.bottom; topMargin: 6; horizontalCenter: parent.horizontalCenter } width: parent.width - 8
                                       horizontalAlignment: Text.AlignHCenter; elide: Text.ElideRight
                                       text: ti.modelData.tooltipTitle || ti.modelData.title || ti.modelData.id; color: theme.fg; font { family: theme.fontUi; pixelSize: 11 } }
                                MouseArea {
                                    id: tim; anchors.fill: parent; hoverEnabled: true; acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton
                                    onClicked: (m) => {
                                        if (m.button === Qt.RightButton && ti.modelData.hasMenu) { const q = mapToItem(box, m.x, m.y); sp.openMenu(ti.modelData, q.x, q.y); }
                                        else if (m.button === Qt.MiddleButton) ti.modelData.secondaryActivate();
                                        else { if (ti.modelData.onlyMenu && ti.modelData.hasMenu) { const q = mapToItem(box, m.x, m.y); sp.openMenu(ti.modelData, q.x, q.y); } else { ti.modelData.activate(); sp.open = false; } }
                                    }
                                }
                            }
                        }
                    }
                    Text { visible: SystemTray.items.values.length === 0; text: "Nič nebeží v oblasti oznámení."; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 13 } }
                    Section { visible: sp.flatpaks.length > 0; text: "BEŽIACE FLATPAKY" }
                    Repeater {
                        model: sp.flatpaks
                        Rectangle {
                            id: fr
                            required property string modelData
                            readonly property var entry: DesktopEntries.byId(modelData)
                            width: bgCol.width; height: 46; radius: 12; color: theme.field
                            Image { id: fic; x: 12; anchors.verticalCenter: parent.verticalCenter; width: 28; height: 28
                                    source: fr.entry ? sp.iconFor(fr.entry.icon) : ""; sourceSize { width: 56; height: 56 } }
                            Text { anchors { left: fic.right; leftMargin: 10; verticalCenter: parent.verticalCenter } text: fr.entry ? fr.entry.name : fr.modelData
                                   color: theme.fg; font { family: theme.fontUi; pixelSize: 13; weight: Font.DemiBold } }
                            Row {
                                anchors { right: parent.right; rightMargin: 8; verticalCenter: parent.verticalCenter } spacing: 6
                                Rectangle { visible: !!fr.entry; width: ot.implicitWidth + 20; height: 30; radius: 15; color: om.containsMouse ? theme.hover : theme.surface
                                            Text { id: ot; anchors.centerIn: parent; text: "Otvoriť"; color: theme.fg; font { family: theme.fontUi; pixelSize: 12 } }
                                            MouseArea { id: om; anchors.fill: parent; hoverEnabled: true; onClicked: sp.launch(fr.entry) } }
                                Rectangle { width: kt.implicitWidth + 20; height: 30; radius: 15; color: km.containsMouse ? Qt.rgba(theme.error.r, theme.error.g, theme.error.b, 0.2) : theme.surface
                                            Text { id: kt; anchors.centerIn: parent; text: "Ukončiť"; color: theme.error; font { family: theme.fontUi; pixelSize: 12 } }
                                            MouseArea { id: km; anchors.fill: parent; hoverEnabled: true; onClicked: { killer.command = ["flatpak", "kill", fr.modelData]; killer.running = true; } } }
                            }
                        }
                    }
                }
            }

            // ponuka aplikácie na pozadí
            MouseArea { anchors.fill: parent; visible: sp.menuRoot !== null; onClicked: sp.closeMenu() }
            Rectangle {
                id: trayMenu
                visible: sp.menuRoot !== null
                x: Math.min(sp.menuAt.x, box.width - width - 10); y: Math.min(sp.menuAt.y, box.height - height - 10)
                width: 260; height: mcol.implicitHeight + 12; radius: 14; z: 20
                color: theme.surfaceVariant; border { color: theme.outline; width: 1 }
                Column {
                    id: mcol; x: 6; y: 6; width: parent.width - 12
                    Repeater {
                        model: opener.children
                        Item {
                            id: me
                            required property var modelData
                            width: mcol.width; height: modelData.isSeparator ? 9 : 32
                            Rectangle { visible: me.modelData.isSeparator; anchors.centerIn: parent; width: parent.width - 12; height: 1; color: theme.line }
                            Rectangle {
                                visible: !me.modelData.isSeparator
                                anchors.fill: parent; radius: 8; color: mem.containsMouse && me.modelData.enabled ? theme.hover : "transparent"
                                Text {
                                    x: 10; anchors.verticalCenter: parent.verticalCenter; width: parent.width - 30; elide: Text.ElideRight
                                    text: (me.modelData.checkState === Qt.Checked ? "✓ " : "") + me.modelData.text.replace(/_/g, "")
                                    color: me.modelData.enabled ? theme.fg : theme.fgDim; font { family: theme.fontUi; pixelSize: 13 }
                                }
                                Text { visible: me.modelData.hasChildren; anchors { right: parent.right; rightMargin: 10; verticalCenter: parent.verticalCenter }
                                       text: "›"; color: theme.fgDim; font.pixelSize: 15 }
                                MouseArea {
                                    id: mem; anchors.fill: parent; hoverEnabled: true; enabled: me.modelData.enabled
                                    onClicked: { if (me.modelData.hasChildren) opener.menu = me.modelData; else { me.modelData.triggered(); sp.closeMenu(); } }
                                }
                            }
                        }
                    }
                }
            }

            // päta: plný App Manager
            Rectangle {
                id: foot
                anchors { left: parent.left; right: parent.right; bottom: parent.bottom; margins: 14 }
                height: 44; radius: 14; color: fm.containsMouse ? theme.hover : theme.field
                Row {
                    anchors.centerIn: parent; spacing: 10
                    Glyph { name: "apps"; size: 18; color: theme.primary; anchors.verticalCenter: parent.verticalCenter }
                    Text { text: "App Manager — inštalácia, aktualizácie, ovládače"; color: theme.fg; font { family: theme.fontUi; pixelSize: 13; weight: Font.DemiBold }
                           anchors.verticalCenter: parent.verticalCenter }
                }
                MouseArea { id: fm; anchors.fill: parent; hoverEnabled: true; onClicked: sp.fullManager() }
            }
        }
    }
}
