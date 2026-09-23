// LatteOS — Súbory (Data Manager), prototyp v Quickshelli.
// Vzor ovládania: Forklift (bočná lišta, hlavička, detail), funkčnosť až po Total Commander (dva panely,
// F5 kopírovať, F6 presunúť). Skutočná štruktúra Linuxu ostáva, pohľad „Tento počítač“ je iba zobrazenie
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
    property var disks: []
    property string confirm: ""          // "trash" = čaká na potvrdenie koša
    property string status: ""
    readonly property var activePane: activeIndex === 0 ? paneA : paneB
    readonly property var otherPane: activeIndex === 0 ? paneB : paneA
    readonly property var sel: activePane ? activePane.current : null

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
                         JSON.stringify({ dual: app.dual, left: paneA.path, right: paneB.path })];
        saver.running = true;
    }
    Process { id: saver }
    onDualChanged: saveState()

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
    Timer { interval: 15000; running: true; repeat: true; onTriggered: lsblk.running = true }

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
            { key: "fav:video", path: app.home + "/Videá", glyph: "movie", label: "Videá" }
        ] },
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
        run(move ? ["mv", "-n", "--", e.path, dst] : ["cp", "-rn", "--", e.path, dst],
            (move ? "Presúvam " : "Kopírujem ") + e.name + " → " + dst);
    }
    function trash() {
        const e = app.sel; if (!e) return;
        if (app.confirm !== "trash") { app.confirm = "trash"; app.status = "Stlač Delete znova (alebo tlačidlo) na presun do koša: " + e.name; return; }
        app.confirm = "";
        run(["gio", "trash", "--", e.path], "Do koša: " + e.name);
    }

    FloatingWindow {
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
                if (ev.key === Qt.Key_Down) { p.moveSelection(1); ev.accepted = true; }
                else if (ev.key === Qt.Key_Up) { p.moveSelection(-1); ev.accepted = true; }
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
                onActivated: (it) => { app.activePane.go(it.path); root.forceActiveFocus(); }
            }

            HeaderBar {
                id: header
                theme: theme
                anchors { left: side.right; right: parent.right; top: parent.top }
                title: app.activePane ? app.activePane.path : ""
                canBack: app.activePane && app.activePane.historyIndex > 0
                canForward: app.activePane && app.activePane.historyIndex < app.activePane.history.length - 1
                searchPlaceholder: "Hľadať v priečinku"
                onBack: app.activePane.back()
                onForward: app.activePane.forward()
                onSearchChanged: (t) => app.activePane.filter = t
                onCloseRequested: Qt.quit()

                IconButton { theme: theme; glyph: "arrow-up"; tip: "O úroveň vyššie (Backspace)"; onClicked: app.activePane.up() }
                IconButton { theme: theme; glyph: "columns-2"; checked: app.dual; tip: "Dva panely (F3)"; onClicked: { app.dual = !app.dual; if (!app.dual) app.activeIndex = 0; } }
                IconButton { theme: theme; glyph: app.activePane && app.activePane.showHidden ? "eye" : "eye-off"; tip: "Skryté súbory (Ctrl+H)"; onClicked: app.activePane.showHidden = !app.activePane.showHidden }
                IconButton { theme: theme; glyph: "terminal-2"; tip: "Terminál tu"; onClicked: app.run(["foot", "--working-directory=" + app.activePane.path]) }
            }

            // panely + detail
            Row {
                id: body
                anchors { left: side.right; right: parent.right; top: header.bottom; bottom: statusBar.top; margins: 10 }
                spacing: 10
                readonly property real detailW: 280
                readonly property real paneW: (width - detailW - spacing * (app.dual ? 2 : 1)) / (app.dual ? 2 : 1)

                FilePane {
                    id: paneA
                    theme: theme
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
                            text: parent.e ? parent.e.name : (app.activePane ? app.activePane.path.split("/").pop() || "/" : "")
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
                Text {
                    x: 14; anchors.verticalCenter: parent.verticalCenter
                    text: (app.activePane ? app.activePane.count + " položiek" : "") + (app.status !== "" ? "   ·   " + app.status : "")
                    color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 }
                }
                Text {
                    anchors { right: parent.right; rightMargin: 14; verticalCenter: parent.verticalCenter }
                    text: "F3 dva panely · F5 kopírovať · F6 presunúť · Del kôš · Ctrl+H skryté · téma " + theme.themeName
                    color: theme.fgDim; opacity: 0.8; font { family: theme.fontUi; pixelSize: 11 }
                }
            }
        }
    }
}
