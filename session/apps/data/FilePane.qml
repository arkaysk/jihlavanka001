// FilePane — jeden panel súborov (Data Manager). Dva panely vedľa seba = štýl Total Commander.
// Zobrazenie ako vo Windows 11: podrobnosti (stĺpce), zoznam (iba názvy) alebo ikony s veľkosťou
// iconSize (malé 48 · stredné 72 · veľké 112 · extra veľké 176); obrázky majú v ikonách náhľad.
import QtQuick
import Qt.labs.folderlistmodel
import "../common"

Rectangle {
    id: pane
    required property var theme
    property string path: "/"
    property bool active: false
    property bool showHidden: false
    property string filter: ""
    property var history: []
    property int historyIndex: -1
    property int sortField: FolderListModel.Name
    property bool sortReversed: false
    property string view: "detaily"          // detaily | zoznam | ikony
    property int iconSize: 72
    property int cur: -1                     // vybraná položka (spoločná pre zoznam aj mriežku)
    readonly property bool icons: view === "ikony"
    readonly property int cols: icons ? Math.max(1, Math.floor(grid.width / grid.cellWidth)) : 1
    readonly property var current: cur >= 0 && cur < folder.count ? entryAt(cur) : null
    readonly property alias count: folder.count

    readonly property bool wide: width > 620        // stĺpec Druh
    readonly property bool mid: width > 520         // stĺpec Upravené
    readonly property real nameW: head.width - (mid ? 150 : 0) - 90 - (wide ? 120 : 0)
    property var tags: ({})              // cesta → farba štítka (#rrggbb), spravuje subory.qml
    signal focusRequested()
    signal openFile(string path)
    signal contextRequested(var entry, real x, real y)   // entry = null → pravý klik na prázdne miesto

    color: "transparent"
    border { color: active ? Qt.rgba(theme.primary.r, theme.primary.g, theme.primary.b, 0.45) : "transparent"; width: 1 }
    radius: 10

    function go(p, push) {
        if (!p) return;
        if (p.length > 1 && p.endsWith("/")) p = p.slice(0, -1);
        path = p;
        cur = -1;
        if (push !== false) {
            history = history.slice(0, historyIndex + 1).concat([p]);
            historyIndex = history.length - 1;
        }
    }
    // znovu načíta priečinok (napr. keď vznikol až po otvorení — Kôš pri prvom spustení)
    function refresh() { const p = path; path = "/"; path = p; }
    function up() { if (path !== "/") go(path.substring(0, path.lastIndexOf("/")) || "/"); }
    function back() { if (historyIndex > 0) { historyIndex--; go(history[historyIndex], false); } }
    function forward() { if (historyIndex < history.length - 1) { historyIndex++; go(history[historyIndex], false); } }
    function openCurrent() {
        const e = current; if (!e) return;
        if (e.isDir) go(e.path); else pane.openFile(e.path);
    }
    function entryAt(i) {
        return {
            name: folder.get(i, "fileName"), path: folder.get(i, "filePath"), isDir: folder.get(i, "fileIsDir"),
            size: folder.get(i, "fileSize"), modified: folder.get(i, "fileModified"), suffix: (folder.get(i, "fileSuffix") || "").toLowerCase()
        };
    }

    // druh a ikona podľa prípony
    function kind(e) {
        if (e.isDir) return ["Priečinok", "folder"];
        const s = e.suffix;
        const m = {
            "jpg": ["Obrázok", "photo"], "jpeg": ["Obrázok", "photo"], "png": ["Obrázok", "photo"], "webp": ["Obrázok", "photo"], "gif": ["Obrázok", "photo"], "svg": ["Obrázok", "photo"],
            "mp3": ["Hudba", "music"], "flac": ["Hudba", "music"], "ogg": ["Hudba", "music"], "wav": ["Hudba", "music"],
            "mp4": ["Video", "movie"], "mkv": ["Video", "movie"], "webm": ["Video", "movie"],
            "txt": ["Text", "file-text"], "md": ["Text", "file-text"], "toml": ["Nastavenia", "file-text"], "conf": ["Nastavenia", "file-text"], "json": ["Dáta", "file-code"],
            "pdf": ["PDF dokument", "file-text"], "zip": ["Archív", "file-zip"], "gz": ["Archív", "file-zip"], "xz": ["Archív", "file-zip"], "tar": ["Archív", "file-zip"],
            "rpm": ["Balík", "package"], "flatpakref": ["Balík", "package"], "appimage": ["Aplikácia", "apps"], "desktop": ["Aplikácia", "apps"],
            "sh": ["Skript", "terminal-2"], "py": ["Kód", "file-code"], "rs": ["Kód", "file-code"], "qml": ["Kód", "file-code"], "lua": ["Kód", "file-code"], "luau": ["Kód", "file-code"],
            "exe": ["Windows program", "apps"], "iso": ["Obraz disku", "device-floppy"]
        };
        return m[s] || [s ? s.toUpperCase() + " súbor" : "Súbor", "file"];
    }
    function human(bytes) {
        if (bytes < 1024) return bytes + " B";
        const u = ["kB", "MB", "GB", "TB"]; let v = bytes / 1024, i = 0;
        while (v >= 1024 && i < u.length - 1) { v /= 1024; i++; }
        return v.toFixed(v < 10 ? 1 : 0).replace(".", ",") + " " + u[i];
    }

    FolderListModel {
        id: folder
        folder: "file://" + pane.path
        showDirsFirst: true
        showDotAndDotDot: false
        showHidden: pane.showHidden
        caseSensitive: false
        nameFilters: pane.filter === "" ? [] : ["*" + pane.filter + "*"]
        sortField: pane.sortField
        sortReversed: pane.sortReversed
    }

    // hlavička stĺpcov
    Row {
        id: head
        visible: pane.view === "detaily"
        x: 8; y: 6; width: parent.width - 16; height: visible ? 28 : 0
        component Col: Item {
            id: c
            property string label
            property int field
            property real w
            width: w; height: parent.height
            Text {
                anchors { left: parent.left; leftMargin: 8; verticalCenter: parent.verticalCenter }
                text: c.label + (pane.sortField === c.field ? (pane.sortReversed ? "  ↓" : "  ↑") : "")
                color: pane.theme.fgDim; font { family: pane.theme.fontUi; pixelSize: 12; weight: Font.Bold }
            }
            MouseArea {
                anchors.fill: parent
                onClicked: { if (pane.sortField === c.field) pane.sortReversed = !pane.sortReversed; else { pane.sortField = c.field; pane.sortReversed = false; } }
            }
        }
        Col { label: "Názov"; field: FolderListModel.Name; w: pane.nameW }
        Col { label: "Upravené"; field: FolderListModel.Time; w: 150; visible: pane.mid }
        Col { label: "Veľkosť"; field: FolderListModel.Size; w: 90 }
        Col { label: "Druh"; field: FolderListModel.Type; w: 120; visible: pane.wide }
    }
    Rectangle { visible: head.visible; x: 8; y: head.y + head.height; width: parent.width - 16; height: 1; color: pane.theme.line }

    // pravý klik na prázdne miesto pod položkami (riadky ho zachytia samy)
    MouseArea {
        anchors.fill: pane.icons ? grid : list; acceptedButtons: Qt.RightButton
        onClicked: (m) => { pane.focusRequested(); const p = mapToItem(null, m.x, m.y); pane.contextRequested(null, p.x, p.y); }
    }

    ListView {
        id: list
        ScrollHint { flick: list; colors: pane.theme }
        visible: !pane.icons
        anchors { top: head.bottom; topMargin: 4; left: parent.left; right: parent.right; bottom: parent.bottom; margins: 8 }
        clip: true
        model: pane.icons ? null : folder
        currentIndex: pane.cur
        boundsBehavior: Flickable.StopAtBounds
        highlightMoveDuration: 0
        keyNavigationEnabled: true

        delegate: Rectangle {
            id: rowItem
            required property int index
            required property string fileName
            required property bool fileIsDir
            required property var fileModified
            required property real fileSize
            required property string fileSuffix
            required property string filePath
            readonly property var k: pane.kind({ isDir: fileIsDir, suffix: (fileSuffix || "").toLowerCase() })
            readonly property bool selected: ListView.isCurrentItem
            readonly property bool compact: pane.view === "zoznam"
            width: list.width; height: compact ? 26 : 32; radius: 8
            color: selected ? (pane.active ? Qt.rgba(pane.theme.primary.r, pane.theme.primary.g, pane.theme.primary.b, 0.22) : pane.theme.hover)
                            : (rma.containsMouse ? Qt.rgba(pane.theme.fg.r, pane.theme.fg.g, pane.theme.fg.b, 0.04) : "transparent")
            Row {
                anchors.verticalCenter: parent.verticalCenter
                Item {
                    width: rowItem.compact ? list.width : pane.nameW; height: rowItem.height
                    readonly property string tag: pane.tags[rowItem.filePath] || ""
                    Glyph {
                        x: 8; anchors.verticalCenter: parent.verticalCenter
                        name: rowItem.fileIsDir && parent.tag !== "" ? "folder-filled" : rowItem.k[1]; size: 17
                        color: parent.tag !== "" ? parent.tag : (rowItem.fileIsDir ? pane.theme.primary : pane.theme.fgDim)
                    }
                    Text {
                        id: nameText
                        x: 34; width: Math.min(implicitWidth, parent.width - 40 - (parent.tag !== "" ? 18 : 0)); anchors.verticalCenter: parent.verticalCenter; elide: Text.ElideRight
                        text: rowItem.fileName; color: pane.theme.fg
                        font { family: pane.theme.fontUi; pixelSize: 13; weight: rowItem.fileIsDir ? Font.DemiBold : Font.Normal }
                    }
                    Rectangle {   // farebný štítok za názvom (farba nie je jediný nosič: aj plná ikona priečinka)
                        visible: parent.tag !== ""
                        anchors { left: nameText.right; leftMargin: 8; verticalCenter: parent.verticalCenter }
                        width: 9; height: 9; radius: 5; color: parent.tag || "transparent"
                    }
                }
                Text {
                    visible: pane.mid && !rowItem.compact; width: 150; leftPadding: 8; anchors.verticalCenter: parent.verticalCenter
                    text: Qt.formatDateTime(rowItem.fileModified, "d. M. yyyy  HH:mm"); color: pane.theme.fgDim
                    font { family: pane.theme.fontUi; pixelSize: 12 }
                }
                Text {
                    visible: !rowItem.compact; width: 90; leftPadding: 8; anchors.verticalCenter: parent.verticalCenter
                    text: rowItem.fileIsDir ? "—" : pane.human(rowItem.fileSize); color: pane.theme.fgDim
                    font { family: pane.theme.fontUi; pixelSize: 12 }
                }
                Text {
                    visible: pane.wide && !rowItem.compact; width: 120; leftPadding: 8; anchors.verticalCenter: parent.verticalCenter; elide: Text.ElideRight
                    text: rowItem.k[0]; color: pane.theme.fgDim
                    font { family: pane.theme.fontUi; pixelSize: 12 }
                }
            }
            MouseArea {
                id: rma; anchors.fill: parent; hoverEnabled: true
                acceptedButtons: Qt.LeftButton | Qt.RightButton
                onClicked: (m) => {
                    pane.cur = rowItem.index; pane.focusRequested();
                    if (m.button === Qt.RightButton) { const p = mapToItem(null, m.x, m.y); pane.contextRequested(pane.entryAt(rowItem.index), p.x, p.y); }
                }
                onDoubleClicked: { pane.cur = rowItem.index; pane.openCurrent(); }
            }
        }

        Text {
            anchors.centerIn: parent; visible: !pane.icons && folder.count === 0 && folder.status === FolderListModel.Ready
            text: pane.filter !== "" ? "Nič nevyhovuje „" + pane.filter + "“" : "Priečinok je prázdny"
            color: pane.theme.fgDim; font { family: pane.theme.fontUi; pixelSize: 13 }
        }
    }

    // ikony: mriežka ako vo Win11 (ikona alebo náhľad obrázka, pod ňou názov na dva riadky)
    GridView {
        id: grid
        ScrollHint { flick: grid; colors: pane.theme }
        visible: pane.icons
        anchors { top: parent.top; left: parent.left; right: parent.right; bottom: parent.bottom; margins: 8 }
        clip: true
        model: pane.icons ? folder : null
        currentIndex: pane.cur
        boundsBehavior: Flickable.StopAtBounds
        highlightMoveDuration: 0
        cellWidth: pane.iconSize + 44; cellHeight: pane.iconSize + 50
        delegate: Item {
            id: cell
            required property int index
            required property string fileName
            required property bool fileIsDir
            required property string fileSuffix
            required property string filePath
            readonly property var k: pane.kind({ isDir: fileIsDir, suffix: (fileSuffix || "").toLowerCase() })
            readonly property bool selected: GridView.isCurrentItem
            readonly property string tag: pane.tags[filePath] || ""
            width: grid.cellWidth; height: grid.cellHeight
            Rectangle {
                anchors { fill: parent; margins: 3 }
                radius: 10
                color: cell.selected ? Qt.rgba(pane.theme.primary.r, pane.theme.primary.g, pane.theme.primary.b, 0.22)
                                     : (cma.containsMouse ? Qt.rgba(pane.theme.fg.r, pane.theme.fg.g, pane.theme.fg.b, 0.05) : "transparent")
            }
            Item {
                id: iconBox
                width: pane.iconSize; height: pane.iconSize
                anchors { horizontalCenter: parent.horizontalCenter; top: parent.top; topMargin: 8 }
                Glyph {
                    anchors.centerIn: parent; visible: thumb.status !== Image.Ready
                    name: cell.fileIsDir && cell.tag !== "" ? "folder-filled" : cell.k[1]; size: pane.iconSize * 0.78
                    color: cell.tag !== "" ? cell.tag : (cell.fileIsDir ? pane.theme.primary : pane.theme.fgDim)
                }
                Image {
                    id: thumb
                    anchors.fill: parent; fillMode: Image.PreserveAspectFit; asynchronous: true
                    sourceSize { width: pane.iconSize * 2; height: pane.iconSize * 2 }
                    source: cell.k[0] === "Obrázok" && pane.iconSize >= 72 ? "file://" + cell.filePath : ""
                }
            }
            Text {
                anchors { top: iconBox.bottom; topMargin: 4; horizontalCenter: parent.horizontalCenter }
                width: parent.width - 10; horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WrapAnywhere; maximumLineCount: 2; elide: Text.ElideRight
                text: cell.fileName; color: pane.theme.fg
                font { family: pane.theme.fontUi; pixelSize: 12; weight: cell.fileIsDir ? Font.DemiBold : Font.Normal }
            }
            MouseArea {
                id: cma; anchors.fill: parent; hoverEnabled: true
                acceptedButtons: Qt.LeftButton | Qt.RightButton
                onClicked: (m) => {
                    pane.cur = cell.index; pane.focusRequested();
                    if (m.button === Qt.RightButton) { const p = mapToItem(null, m.x, m.y); pane.contextRequested(pane.entryAt(cell.index), p.x, p.y); }
                }
                onDoubleClicked: { pane.cur = cell.index; pane.openCurrent(); }
            }
        }
        Text {
            anchors.centerIn: parent; visible: folder.count === 0 && folder.status === FolderListModel.Ready
            text: pane.filter !== "" ? "Nič nevyhovuje „" + pane.filter + "“" : "Priečinok je prázdny"
            color: pane.theme.fgDim; font { family: pane.theme.fontUi; pixelSize: 13 }
        }
    }

    function moveSelection(d) {
        const n = Math.max(0, Math.min(folder.count - 1, cur + d));
        cur = n;
        if (icons) grid.positionViewAtIndex(n, GridView.Contain); else list.positionViewAtIndex(n, ListView.Contain);
    }
    // šípky hore/dole: v mriežke o celý riadok
    function moveRow(d) { moveSelection(d * cols); }
}
