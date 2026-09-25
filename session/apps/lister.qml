// LatteOS — Lister (F3 v Súboroch, ako Lister v Total Commanderi): rýchly náhľad súboru v samostatnom okne.
//   text (automatické kódovanie UTF-8 / CP1250 / ISO-8859-2, dá sa prepnúť), hex (klávesa 3), obrázok, zalamovanie (W),
//   hľadanie (Ctrl+F, F3 ďalšie), veľké súbory po 256 kB (načíta ďalšie pri konci), N/P = ďalší/predošlý súbor v priečinku,
//   Esc zavrie. Dáta: latte-tc nahlad. Spúšťa sa: latte-app lister SÚBOR
import QtQuick
import Quickshell
import Quickshell.Io
import "common"

ShellRoot {
    id: app
    LatteTheme { id: theme }
    property string path: (Quickshell.env("LATTE_APP_ARGS") || "").trim().replace(/^file:\/\//, "")
    property string mode: "text"            // text | hex | obrazok
    property string enc: ""
    property var data: null
    property string content: ""
    property int loaded: 0
    property bool wrap: true
    property string find: ""
    property int findPos: -1
    property var siblings: []
    readonly property string name: path.split("/").pop()
    readonly property bool isImage: /\.(png|jpe?g|gif|webp|bmp|svg|avif)$/i.test(path)

    Process {
        id: load
        property bool append: false
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const d = JSON.parse(this.text);
                    app.data = d;
                    app.content = load.append ? app.content + (d.mode === "hex" ? "\n" : "") + d.text : d.text;
                    app.loaded = d.start + d.len;
                    if (!load.append && d.binary && app.mode === "text" && !app.enc) app.mode = "hex";
                } catch (e) { app.content = "Súbor sa nedá prečítať."; }
            }
        }
    }
    function reload(more) {
        if (isImage && mode !== "hex") { mode = "obrazok"; return; }
        if (mode === "obrazok") mode = "text";
        load.append = !!more;
        load.command = ["latte-tc", "nahlad", path, "--od", String(more ? loaded : 0)].concat(mode === "hex" ? ["--hex"] : []).concat(enc ? ["--kodovanie", enc] : []);
        load.running = true;
    }
    Component.onCompleted: { reload(false); sib.running = true; }
    Process {
        id: sib
        command: ["sh", "-c", 'ls -1Ap "$(dirname "$1")" | grep -v /$', "sh", app.path]
        stdout: StdioCollector { onStreamFinished: app.siblings = this.text.split("\n").filter(l => l !== "") }
    }
    function step(d) {
        const i = siblings.indexOf(name); if (i < 0 || !siblings.length) return;
        const n = siblings[(i + d + siblings.length) % siblings.length];
        path = path.substring(0, path.lastIndexOf("/") + 1) + n; mode = isImage ? "obrazok" : "text"; enc = ""; content = ""; reload(false);
    }
    function doFind(next) {
        if (!find) return;
        const low = content.toLowerCase(), q = find.toLowerCase();
        let i = low.indexOf(q, next ? findPos + 1 : 0); if (i < 0) i = low.indexOf(q);
        findPos = i;
        if (i >= 0) { txt.select(i, i + q.length); const r = txt.positionToRectangle(i); flick.contentY = Math.max(0, r.y - flick.height / 3); }
    }
    function human(b) { const u = ["B", "KB", "MB", "GB"]; let v = b || 0, i = 0; while (v >= 1024 && i < 3) { v /= 1024; i++; } return v.toFixed(i ? 1 : 0).replace(".", ",") + " " + u[i]; }

    FloatingWindow {
        onClosed: Qt.quit()
        title: app.name + " — Lister"
        implicitWidth: 1000; implicitHeight: 720
        color: theme.surface
        Item {
            id: root
            anchors.fill: parent; focus: true
            Keys.onPressed: (ev) => {
                const ctrl = ev.modifiers & Qt.ControlModifier; ev.accepted = true;
                if (findBox.visible && ev.key !== Qt.Key_F3 && ev.key !== Qt.Key_Escape) { ev.accepted = false; return; }
                if (ev.key === Qt.Key_Escape) { if (findBox.visible) findBox.visible = false; else Qt.quit(); }
                else if (ev.key === Qt.Key_F && ctrl) { findBox.visible = true; findIn.forceActiveFocus(); findIn.selectAll(); }
                else if (ev.key === Qt.Key_F3) app.doFind(true);
                else if (ev.key === Qt.Key_1) { app.mode = "text"; app.reload(false); }
                else if (ev.key === Qt.Key_3) { app.mode = "hex"; app.reload(false); }
                else if (ev.key === Qt.Key_W) app.wrap = !app.wrap;
                else if (ev.key === Qt.Key_N) app.step(1);
                else if (ev.key === Qt.Key_P) app.step(-1);
                else if (ev.key === Qt.Key_Down) flick.contentY = Math.min(flick.contentHeight - flick.height, flick.contentY + 40);
                else if (ev.key === Qt.Key_Up) flick.contentY = Math.max(0, flick.contentY - 40);
                else if (ev.key === Qt.Key_PageDown || ev.key === Qt.Key_Space) flick.contentY = Math.min(Math.max(0, flick.contentHeight - flick.height), flick.contentY + flick.height - 40);
                else if (ev.key === Qt.Key_PageUp) flick.contentY = Math.max(0, flick.contentY - flick.height + 40);
                else if (ev.key === Qt.Key_Home) flick.contentY = 0;
                else if (ev.key === Qt.Key_End) flick.contentY = Math.max(0, flick.contentHeight - flick.height);
                else ev.accepted = false;
            }
            HeaderBar {
                id: header
                theme: theme; appId: "latteos-subory"
                anchors { left: parent.left; right: parent.right; top: parent.top }
                title: app.name
                onCloseRequested: Qt.quit()
            }
            Row {
                id: bar
                anchors { left: parent.left; top: header.bottom; margins: 10 }
                spacing: 6
                component Chip: Rectangle {
                    id: c
                    property string label; property bool on: false
                    signal clicked()
                    width: cl.implicitWidth + 20; height: 28; radius: 8
                    color: on ? Qt.rgba(theme.primary.r, theme.primary.g, theme.primary.b, 0.22) : (cm.containsMouse ? theme.hover : theme.field)
                    Text { id: cl; anchors.centerIn: parent; text: c.label; color: theme.fg; font { family: theme.fontUi; pixelSize: 12; weight: c.on ? Font.Bold : Font.Normal } }
                    MouseArea { id: cm; anchors.fill: parent; hoverEnabled: true; onClicked: { c.clicked(); root.forceActiveFocus(); } }
                }
                Chip { label: "1 Text"; on: app.mode === "text"; onClicked: { app.mode = "text"; app.reload(false); } }
                Chip { label: "3 Hex"; on: app.mode === "hex"; onClicked: { app.mode = "hex"; app.reload(false); } }
                Chip { visible: app.isImage; label: "Obrázok"; on: app.mode === "obrazok"; onClicked: app.mode = "obrazok" }
                Chip { label: "W Zalamovať"; on: app.wrap; onClicked: app.wrap = !app.wrap }
                Item { width: 10; height: 1 }
                Repeater { model: ["", "utf-8", "cp1250", "iso-8859-2", "latin-1"]
                    Chip { required property string modelData; label: modelData || "auto"; on: app.enc === modelData; onClicked: { app.enc = modelData; app.mode = "text"; app.reload(false); } } }
                Item { width: 10; height: 1 }
                Chip { label: "Ctrl+F Hľadať"; onClicked: { findBox.visible = true; findIn.forceActiveFocus(); } }
                Chip { label: "Otvoriť v aplikácii"; onClicked: runner.running = true }
            }
            Process { id: runner; command: ["xdg-open", app.path] }
            Rectangle {
                id: findBox
                visible: false
                anchors { right: parent.right; top: header.bottom; margins: 10 }
                width: 320; height: 30; radius: 8; color: theme.field; border { color: theme.primary; width: 1 }
                z: 5
                TextInput { id: findIn; anchors { fill: parent; leftMargin: 10; rightMargin: 10 } verticalAlignment: TextInput.AlignVCenter; color: theme.fg
                            font { family: theme.fontUi; pixelSize: 13 }
                            onTextChanged: { app.find = text; app.doFind(false); }
                            Keys.onReturnPressed: (ev) => { ev.accepted = true; app.doFind(true); }
                            Keys.onEscapePressed: { findBox.visible = false; root.forceActiveFocus(); } }
            }
            Flickable {
                id: flick
                visible: app.mode !== "obrazok"
                anchors { left: parent.left; right: parent.right; top: bar.bottom; bottom: status.top; margins: 10 }
                contentWidth: app.wrap ? width : Math.max(width, txt.implicitWidth); contentHeight: txt.implicitHeight; clip: true
                boundsBehavior: Flickable.StopAtBounds
                ScrollHint { flick: flick; colors: theme }
                onContentYChanged: if (app.data && app.data.more && !load.running && contentY > contentHeight - height * 2) app.reload(true)
                TextEdit {
                    id: txt
                    width: app.wrap ? flick.width - 14 : implicitWidth
                    readOnly: true; selectByMouse: true; textFormat: TextEdit.PlainText
                    wrapMode: app.wrap ? TextEdit.WrapAnywhere : TextEdit.NoWrap
                    text: app.content; color: theme.fg; selectionColor: theme.primary; selectedTextColor: theme.fgOnPrimary
                    font { family: theme.fontMono; pixelSize: 13 }
                }
            }
            Image {
                visible: app.mode === "obrazok"
                anchors { left: parent.left; right: parent.right; top: bar.bottom; bottom: status.top; margins: 10 }
                source: app.mode === "obrazok" ? "file://" + app.path : ""; fillMode: Image.PreserveAspectFit; asynchronous: true
            }
            Rectangle {
                id: status
                anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
                height: 28; color: "transparent"
                Rectangle { width: parent.width; height: 1; color: theme.line }
                Text { x: 12; anchors.verticalCenter: parent.verticalCenter; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 11 }
                       text: app.data ? app.human(app.data.size) + " · " + (app.data.mime || "") + (app.data.encoding && app.mode === "text" ? " · " + app.data.encoding : "")
                                        + (app.data.more ? " · načítané " + app.human(app.loaded) + " (pri konci ďalšie)" : "") : "" }
                Text { anchors { right: parent.right; rightMargin: 12; verticalCenter: parent.verticalCenter } color: theme.fgDim; font { family: theme.fontUi; pixelSize: 11 }
                       text: "1 text · 3 hex · W zalamovanie · N/P ďalší/predošlý súbor · Ctrl+F hľadať · Esc zavrieť" }
            }
        }
    }
}
