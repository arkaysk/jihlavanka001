// LatteOS — ikony na ploche (zadanie 24. 9., bod 7): Kôš je na ploche vždy (počet položiek, pustenie súboru
// naň = do koša), pod ním súbory a priečinky z ~/Plocha. Klik vyberie, dvojklik otvorí, pravý klik = ponuka
// (Otvoriť, Otvoriť v…, Do koša; na koši Otvoriť a Vysypať). Súbor pretiahnutý z inej aplikácie na plochu sa
// skopíruje do ~/Plocha. Vrstva Bottom: nad tapetou (aj živou), pod oknami; vstup iba nad ikonami a ponukou.
// Vypnutie: Nastavenia › Pozadie (~/.config/latteos/desktop-icons = off). Spúšťa: latte-app plocha.
import QtQuick
import Qt.labs.folderlistmodel
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import "common"

ShellRoot {
    id: pl
    LatteTheme { id: theme }

    readonly property string home: Quickshell.env("HOME") || "/"
    readonly property string cfg: (Quickshell.env("XDG_CONFIG_HOME") || (home + "/.config")) + "/latteos"
    property string desk: home + "/Plocha"
    readonly property string trashDir: home + "/.local/share/Trash/files"
    property int trashCount: 0
    property string sel: ""
    property var menuItems: []
    property point menuAt: Qt.point(0, 0)

    // vypnuté v Nastaveniach → skončiť
    FileView { path: pl.cfg + "/desktop-icons"; printErrors: false; watchChanges: true; onFileChanged: reload()
               onLoaded: if (text().trim() === "off") Qt.quit() }
    // priečinok plochy podľa xdg-user-dirs (slovensky „Plocha“)
    Process {
        running: true; command: ["sh", "-c", "xdg-user-dir DESKTOP 2>/dev/null || echo \"$HOME/Plocha\""]
        stdout: StdioCollector { onStreamFinished: { const d = this.text.trim(); if (d !== "" && d !== pl.home) pl.desk = d; mk.running = true; } }
    }
    Process { id: mk; command: ["mkdir", "-p", pl.desk, pl.trashDir, pl.home + "/.local/share/Trash/info"] }
    Process {
        id: trashProc
        command: ["sh", "-c", "ls -A \"$1\" 2>/dev/null | wc -l", "sh", pl.trashDir]
        stdout: StdioCollector { onStreamFinished: pl.trashCount = parseInt(this.text) || 0 }
    }
    Timer { interval: 4000; repeat: true; running: true; triggeredOnStart: true; onTriggered: if (!trashProc.running) trashProc.running = true }
    Process { id: run }
    function sh(cmd, args) { run.command = ["sh", "-c", cmd, "sh"].concat(args || []); run.running = true; }
    // spúšťač aplikácie (.desktop, napr. z rýchleho spustenia › Pridať na plochu) sa spustí, ostatné otvorí
    function open(p) { sh(p === pl.trashDir ? 'latte-app subory "$1" >/dev/null 2>&1 &' : (p.endsWith(".desktop") ? 'gio launch "$1" >/dev/null 2>&1 &' : 'xdg-open "$1" >/dev/null 2>&1 &'), [p]); }

    // „Otvoriť v…“ cez latte-otvor (rovnaké ako v Súboroch)
    Process {
        id: withProc
        property string path: ""
        stdout: StdioCollector {
            onStreamFinished: {
                const l = this.text.split("\n").filter(x => x !== "").slice(1).map(x => x.split("\t")).filter(a => a[0] !== "nainstalovat");
                pl.menuItems = l.map(a => ({ label: (a[0] === "predvolena" ? "✓ " : "") + a[2], act: () => pl.sh('latte-otvor spusti "$1" "$2"', [a[1], withProc.path]) }));
                if (pl.menuItems.length === 0) pl.menuItems = [{ label: "Žiadna aplikácia", act: () => {} }];
            }
        }
    }

    function menuFor(path, isDir, x, y) {
        sel = path; menuAt = Qt.point(x, y);
        if (path === trashDir) {
            menuItems = [{ label: "Otvoriť kôš", act: () => pl.open(pl.trashDir) },
                         { label: "Vysypať kôš (" + trashCount + ")", danger: true, act: () => { pl.sh("latte-kos vysypat"); trashProc.running = true; } }];
            return;
        }
        const items = [{ label: "Otvoriť", act: () => pl.open(path) }];
        if (!isDir) items.push({ label: "Otvoriť v…", keep: true, act: () => { withProc.path = path; withProc.command = ["latte-otvor", "aplikacie", path]; withProc.running = true; } });
        items.push({ label: "Ukázať v Súboroch", act: () => pl.sh('latte-app subory "$1" >/dev/null 2>&1 &', [pl.desk]) });
        items.push({ label: "Do koša", danger: true, act: () => { pl.sh('latte-kos vyhod "$1"', [path]); trashProc.running = true; } });
        menuItems = items;
    }

    FolderListModel {
        id: files
        folder: "file://" + pl.desk
        showDirsFirst: true; showDotAndDotDot: false; showHidden: false
        sortField: FolderListModel.Name
    }

    function glyphFor(name, isDir) {
        if (isDir) return "folder";
        const s = (name.split(".").pop() || "").toLowerCase();
        if (["jpg", "jpeg", "png", "webp", "gif", "svg"].includes(s)) return "photo";
        if (["mp3", "flac", "ogg", "wav"].includes(s)) return "music";
        if (["mp4", "mkv", "webm"].includes(s)) return "movie";
        if (["zip", "gz", "xz", "tar", "7z"].includes(s)) return "file-zip";
        if (["txt", "md", "odt", "docx", "pdf", "rtf"].includes(s)) return "file-text";
        if (s === "desktop") return "apps";
        return "file";
    }

    PanelWindow {
        id: win
        anchors { top: true; bottom: true; left: true; right: true }
        exclusionMode: ExclusionMode.Normal          // rešpektuje lištu (ikony sa nekreslia pod ňu)
        WlrLayershell.layer: WlrLayer.Bottom
        WlrLayershell.namespace: "latte-plocha"
        WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
        color: "transparent"
        mask: Region {
            item: grid
            Region { item: menu.visible ? menu : null }
        }

        // pustenie súboru z inej aplikácie medzi ikony = kopírovať na Plochu (vstup má vrstva iba nad ikonami;
        // Kôš má vlastný cieľ navrchu)
        DropArea {
            anchors.fill: grid; keys: ["text/uri-list"]
            onDropped: (d) => { if (d.hasUrls) { pl.sh('for u in "$@"; do cp -rn -- "$u" "' + pl.desk + '/"; done', d.urls.map(u => decodeURIComponent(String(u).replace(/^file:\/\//, "")))); d.accept(Qt.CopyAction); } }
        }

        Flow {
            id: grid
            x: 16; y: 16
            // stĺpce zhora nadol ako vo Windows; ďalší stĺpec, keď sa stĺpec zaplní
            readonly property int perCol: Math.max(1, Math.floor((win.height - 32 + 6) / 102))
            readonly property int n: 1 + files.count
            width: Math.ceil(n / perCol) * 116 - 6
            height: Math.min(n, perCol) * 102 - 6
            flow: Flow.TopToBottom; spacing: 6

            component Icon: Item {
                id: ic
                property string path
                property string name
                property bool isDir: false
                property string glyph: "file"
                property string badge: ""
                property string iconSrc: ""          // ikona aplikácie (spúšťač .desktop)
                readonly property bool selected: pl.sel === path
                width: 110; height: 96
                Rectangle {
                    anchors.fill: parent; radius: 12
                    color: ic.selected ? Qt.rgba(theme.primary.r, theme.primary.g, theme.primary.b, 0.35)
                                       : (ima.containsMouse || dz.containsDrag ? Qt.rgba(1, 1, 1, 0.14) : "transparent")
                    border { color: dz.containsDrag ? theme.primary : "transparent"; width: 2 }
                }
                Rectangle {
                    id: tile
                    width: 52; height: 52; radius: 14
                    anchors { horizontalCenter: parent.horizontalCenter; top: parent.top; topMargin: 8 }
                    color: Qt.rgba(theme.surface.r, theme.surface.g, theme.surface.b, 0.88)
                    border { color: Qt.rgba(theme.outline.r, theme.outline.g, theme.outline.b, 0.6); width: 1 }
                    Glyph { anchors.centerIn: parent; visible: appImg.status !== Image.Ready; name: ic.glyph; size: 28; color: ic.isDir || ic.glyph === "trash" ? theme.primary : theme.fg }
                    Image { id: appImg; anchors { fill: parent; margins: 6 } source: ic.iconSrc; sourceSize { width: 80; height: 80 } fillMode: Image.PreserveAspectFit; asynchronous: true }
                    Rectangle {
                        visible: ic.badge !== ""
                        anchors { right: parent.right; top: parent.top; rightMargin: -6; topMargin: -6 }
                        width: Math.max(20, bt.implicitWidth + 10); height: 20; radius: 10; color: theme.primary
                        Text { id: bt; anchors.centerIn: parent; text: ic.badge; color: theme.fgOnPrimary; font { family: theme.fontUi; pixelSize: 11; weight: Font.Bold } }
                    }
                }
                Text {
                    anchors { top: tile.bottom; topMargin: 4; horizontalCenter: parent.horizontalCenter }
                    width: parent.width - 8; horizontalAlignment: Text.AlignHCenter; wrapMode: Text.WrapAnywhere; maximumLineCount: 2; elide: Text.ElideRight
                    text: ic.name; color: "white"; style: Text.Outline; styleColor: Qt.rgba(0, 0, 0, 0.55)
                    font { family: theme.fontUi; pixelSize: 12; weight: Font.DemiBold }
                }
                Drag.active: ima.drag.active && ic.path !== pl.trashDir
                Drag.dragType: Drag.Automatic
                Drag.supportedActions: Qt.CopyAction | Qt.MoveAction
                Drag.mimeData: ({ "text/uri-list": "file://" + ic.path + "\r\n" })
                MouseArea {
                    id: ima; anchors.fill: parent; hoverEnabled: true; acceptedButtons: Qt.LeftButton | Qt.RightButton
                    drag.target: ic.path !== pl.trashDir ? dragProxy : null
                    onClicked: (m) => { pl.sel = ic.path; if (m.button === Qt.RightButton) { const q = mapToItem(null, m.x, m.y); pl.menuFor(ic.path, ic.isDir, q.x, q.y); } else pl.menuItems = []; }
                    onDoubleClicked: pl.open(ic.path)
                }
                Item { id: dragProxy }
                // Kôš: pustený súbor ide do koša
                DropArea {
                    id: dz; anchors.fill: parent; keys: ["text/uri-list"]; enabled: ic.path === pl.trashDir
                    onDropped: (d) => { if (d.hasUrls) { pl.sh('latte-kos vyhod "$@"', d.urls.map(u => decodeURIComponent(String(u).replace(/^file:\/\//, "")))); trashProc.running = true; d.accept(Qt.MoveAction); } }
                }
            }

            Icon { path: pl.trashDir; name: "Kôš"; glyph: "trash"; badge: pl.trashCount > 0 ? String(pl.trashCount) : "" }
            Repeater {
                model: files
                Icon {
                    required property string fileName
                    required property string filePath
                    required property bool fileIsDir
                    readonly property var de: fileName.endsWith(".desktop") ? DesktopEntries.byId(fileName.slice(0, -8)) : null
                    path: filePath; name: de ? de.name : fileName; isDir: fileIsDir; glyph: pl.glyphFor(fileName, fileIsDir)
                    iconSrc: de && de.icon ? Quickshell.iconPath(de.icon, true) : ""
                }
            }
        }

        // ponuka (pravý klik)
        Rectangle {
            id: menu
            visible: pl.menuItems.length > 0
            x: Math.min(pl.menuAt.x, win.width - width - 8); y: Math.min(pl.menuAt.y, win.height - height - 8)
            width: 220; height: mcol.implicitHeight + 12; radius: 12
            color: theme.surface; border { color: theme.outline; width: 1 }
            Column {
                id: mcol; x: 6; y: 6; width: parent.width - 12
                Repeater {
                    model: pl.menuItems
                    Rectangle {
                        required property var modelData
                        width: mcol.width; height: 32; radius: 8; color: mma.containsMouse ? theme.hover : "transparent"
                        Text { x: 10; anchors.verticalCenter: parent.verticalCenter; text: modelData.label; color: modelData.danger ? theme.error : theme.fg
                               font { family: theme.fontUi; pixelSize: 13 } }
                        MouseArea { id: mma; anchors.fill: parent; hoverEnabled: true
                                    onClicked: { const a = modelData.act; if (!modelData.keep) pl.menuItems = []; a(); } }
                    }
                }
            }
        }
    }
}
