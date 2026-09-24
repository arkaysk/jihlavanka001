// LatteOS — Monitor (Process Manager / Latte System Monitor), podľa old/IDEAS.md:
// živý stav (CPU, RAM, disky, sieť, teploty), procesy (druh, vlastník, príkaz, ukončenie s varovaním),
// Po štarte (autostart, systemd, časovače, cron s pôvodom) a Výstupy telemetrie. Nie je to nastavenie
// aplikácií (App Manager) ani hardvéru (Device Manager). Spúšťa sa: latte-app monitor, Ctrl+Shift+Esc
import QtQuick
import Quickshell
import Quickshell.Io
import "common"

ShellRoot {
    id: app
    LatteTheme { id: theme }

    property string section: ({ strom: "procesy" })[(Quickshell.env("LATTE_APP_ARGS") || "").trim()] || (Quickshell.env("LATTE_APP_ARGS") || "").trim() || "prehlad"
    property string search: ""
    property string status: ""
    property var snap: ({ cpu: 0, cores: [], mem: { total: 1, used: 0 }, disk: {}, net: {}, load: [], temps: [], fs: [], procs: [] })
    property var cpuHist: []
    property var memHist: []
    property var netHist: []
    property string kindFilter: ""
    property string sortKey: "cpu"
    property bool tree: (Quickshell.env("LATTE_APP_ARGS") || "").trim() === "strom"   // strom procesov (rodič → deti)
    property int selPid: -1
    property string confirm: ""           // "term:PID" | "kill:PID" čaká na druhé kliknutie
    property var autorun: []
    readonly property var sel: snap.procs ? (snap.procs.find(p => p.pid === selPid) || null) : null

    readonly property var kinds: ({ app: "Aplikácia", desktop: "Prostredie", helper: "Pomocný", system: "Systém" })
    readonly property var kindHints: ({
        app: "Má okno. Ukončenie zavrie aplikáciu (neuložená práca sa môže stratiť).",
        desktop: "Časť plochy LatteOS (kompozitor, lišta, zvuk, portály). Ukončenie môže zhodiť lištu alebo celú reláciu.",
        helper: "Proces tvojho účtu bez okna (služba, skript, terminál).",
        system: "Patrí systému alebo inému účtu. Ukončiť ho môže iba správca."
    })

    function human(b) {
        if (!b || b < 1024) return (b || 0) + " B";
        const u = ["kB", "MB", "GB", "TB"]; let v = b / 1024, i = 0;
        while (v >= 1024 && i < u.length - 1) { v /= 1024; i++; }
        return v.toFixed(v < 10 ? 1 : 0).replace(".", ",") + " " + u[i];
    }
    function push(arr, v) { const a = arr.concat([v]); return a.length > 60 ? a.slice(a.length - 60) : a; }
    function progName(p) {   // „MainThread“ a podobné názvy vlákien nahradí menom programu z príkazu
        const generic = ["MainThread", "Main", "python3", "python", "node", "sh", "bash"];
        if (p.cmd && generic.indexOf(p.name) >= 0) {
            const parts = p.cmd.split(" ");
            const pick = (p.name === "python3" || p.name === "python" || p.name === "node" || p.name === "sh" || p.name === "bash") && parts[1] ? parts[1] : parts[0];
            return pick.split("/").pop() || p.name;
        }
        return p.name;
    }

    // ── dáta: latte-sysmon stream (JSON riadok za sekundu) ─────────────────────────
    Process {
        id: stream
        running: true
        command: ["latte-sysmon", "stream", "1"]
        stdout: SplitParser {
            onRead: (line) => {
                try {
                    const s = JSON.parse(line);
                    app.snap = s;
                    app.cpuHist = app.push(app.cpuHist, s.cpu);
                    app.memHist = app.push(app.memHist, 100 * s.mem.used / Math.max(1, s.mem.total));
                    app.netHist = app.push(app.netHist, (s.net.rx || 0) + (s.net.tx || 0));
                } catch (e) {}
            }
        }
        onExited: restart.start()
    }
    Timer { id: restart; interval: 2000; onTriggered: stream.running = true }

    Process {
        id: autorunProc
        command: ["latte-sysmon", "autorun"]
        stdout: StdioCollector { onStreamFinished: { try { app.autorun = JSON.parse(this.text); } catch (e) {} } }
    }
    function go(k) { section = k; if (k === "autorun") autorunProc.running = true; }
    Component.onCompleted: go(section)

    Process { id: runner; onExited: (code) => { if (code !== 0 && app.status.indexOf("…") > 0) app.status = "Nepodarilo sa (kód " + code + ")"; } }
    function run(cmd, msg) { runner.command = cmd; runner.running = true; if (msg) app.status = msg; }

    function stop(p, force) {
        if (!p) return;
        if (p.kind === "system") { status = "Systémový proces: ukončiť ho môže iba správca"; return; }
        const key = (force ? "kill:" : "term:") + p.pid;
        if (confirm !== key) { confirm = key; status = (force ? "Vynútiť ukončenie " : "Ukončiť ") + progName(p) + "? Klikni znova."; return; }
        confirm = "";
        run(["kill", force ? "-KILL" : "-TERM", String(p.pid)], (force ? "Vynútené ukončenie: " : "Ukončujem: ") + progName(p) + "…");
    }
    function toggleAutorun(it) {
        if (it.kind === "autostart") {
            const dst = (Quickshell.env("HOME") || "") + "/.config/autostart/" + it.id;
            if (it.enabled) run(["sh", "-c", "mkdir -p \"$(dirname \"$2\")\"; [ \"$1\" = \"$2\" ] || cp -f \"$1\" \"$2\"; grep -q '^Hidden=' \"$2\" && sed -i 's/^Hidden=.*/Hidden=true/' \"$2\" || printf 'Hidden=true\\n' >> \"$2\"", "sh", it.origin, dst],
                                "Vypnuté pri štarte: " + it.name + " (iba pre tvoj účet)");
            else run(["sh", "-c", "if [ -e \"/etc/xdg/autostart/$(basename \"$1\")\" ] && grep -q '^Hidden=true' \"$1\"; then rm -f \"$1\"; else sed -i 's/^Hidden=.*/Hidden=false/' \"$1\"; fi", "sh", dst],
                     "Zapnuté pri štarte: " + it.name);
        } else if (it.kind === "user-service" || (it.kind === "timer" && it.owner === "používateľ")) {
            run(["systemctl", "--user", it.enabled ? "disable" : "enable", it.id], (it.enabled ? "Vypnuté: " : "Zapnuté: ") + it.id);
        } else { status = "Systémovú položku mení iba správca"; return; }
        reloadAutorun.start();
    }
    Timer { id: reloadAutorun; interval: 700; onTriggered: autorunProc.running = true }

    readonly property var shown: {
        let list = (snap.procs || []).filter(p => (kindFilter === "" || p.kind === kindFilter)
            && (search === "" || (p.name + " " + (p.cmd || "") + " " + p.pid).toLowerCase().includes(search.toLowerCase())));
        const k = sortKey;
        const cmp = (a, b) => k === "name" ? progName(a).localeCompare(progName(b)) : (k === "pid" ? a.pid - b.pid : (b[k] - a[k]));
        if (!tree) return list.slice().sort(cmp).slice(0, 150);
        // strom: koreň = proces, ktorého rodič nie je v zozname; deti pod rodičom, poradie podľa triedenia
        const byPid = {}, kids = {};
        for (const p of list) byPid[p.pid] = p;
        for (const p of list) { const pp = byPid[p.ppid] ? p.ppid : 0; (kids[pp] = kids[pp] || []).push(p); }
        const out = [];
        const walk = (pid, depth) => { for (const c of (kids[pid] || []).sort(cmp)) { out.push(Object.assign({ depth: depth }, c)); if (out.length < 400) walk(c.pid, depth + 1); } };
        walk(0, 0);
        return out;
    }

    // ── okno ─────────────────────────────────────────────────────────────────────
    FloatingWindow {
        title: "Monitor — LatteOS"
        implicitWidth: 1220; implicitHeight: 760
        color: theme.surface

        Item {
            id: root
            anchors.fill: parent

            SideBar {
                id: side
                theme: theme
                anchors { left: parent.left; top: parent.top; bottom: parent.bottom }
                heading: "Monitor"; headingGlyph: "activity"
                current: app.section
                model: [
                    { title: "Stav", items: [
                        { key: "prehlad", glyph: "activity", label: "Prehľad", sub: "CPU " + Math.round(app.snap.cpu) + " % · RAM " + app.human(app.snap.mem.used) },
                        { key: "procesy", glyph: "list-check", label: "Procesy", sub: (app.snap.procCount || 0) + " bežiacich" }
                    ] },
                    { title: "Správa", items: [
                        { key: "autorun", glyph: "player-play", label: "Po štarte", sub: "autostart, služby, časovače" },
                        { key: "telemetria", glyph: "device-desktop", label: "Výstupy telemetrie", sub: "OLED, Stream Deck, panel" }
                    ] }
                ]
                onActivated: (it) => app.go(it.key)
            }

            HeaderBar {
                id: header
                theme: theme
                appId: "latteos-monitor"
                anchors { left: side.right; right: parent.right; top: parent.top }
                title: ({ prehlad: "Prehľad", procesy: "Procesy", autorun: "Po štarte", telemetria: "Výstupy telemetrie" })[app.section]
                searchPlaceholder: "Hľadať proces"
                onSearchChanged: (t) => { app.search = t; if (t !== "") app.section = "procesy"; }
                onCloseRequested: Qt.quit()
            }

            Loader {
                id: content
                anchors { left: side.right; top: header.bottom; bottom: statusBar.top; right: detail.left; margins: 20 }
                sourceComponent: ({ prehlad: pPrehlad, procesy: pProcesy, autorun: pAutorun, telemetria: pTelemetria })[app.section] || pPrehlad
            }

            // detail vybraného procesu (návrh V2: pravý panel)
            Rectangle {
                id: detail
                anchors { right: parent.right; top: header.bottom; bottom: statusBar.top; margins: 14 }
                width: 280; radius: theme.radius
                color: Qt.rgba(0, 0, 0, theme.mode === "dark" ? 0.16 : 0.04); border { color: theme.line; width: 1 }
                Column {
                    anchors { fill: parent; margins: 16 }
                    spacing: 10
                    readonly property var p: app.sel
                    Text {
                        width: parent.width; wrapMode: Text.WrapAnywhere; maximumLineCount: 2; elide: Text.ElideRight
                        text: parent.p ? app.progName(parent.p) : "Vyber proces"
                        color: theme.fg; font { family: theme.fontDisplay; pixelSize: 19; weight: Font.DemiBold }
                    }
                    Text {
                        visible: !!parent.p
                        text: parent.p ? "● " + app.kinds[parent.p.kind] + (parent.p.window ? " · okno " + parent.p.window : "") : ""
                        color: parent.p && (parent.p.kind === "desktop" || parent.p.kind === "system") ? theme.error : theme.primary
                        font { family: theme.fontUi; pixelSize: 12; weight: Font.Bold }
                    }
                    Text {
                        width: parent.width; wrapMode: Text.WordWrap
                        text: parent.p ? app.kindHints[parent.p.kind] : "Klikni na proces v zozname. Pravý klik otvorí ponuku."
                        color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 }
                    }
                    Repeater {
                        model: parent.p ? [["PID / rodič", parent.p.pid + " / " + parent.p.ppid], ["Vlastník", parent.p.user],
                                           ["CPU", parent.p.cpu.toFixed(1).replace(".", ",") + " %"], ["Pamäť", app.human(parent.p.rss)],
                                           ["Príkaz", parent.p.cmd || parent.p.name]] : []
                        Column {
                            required property var modelData
                            width: parent.width; spacing: 1
                            Text { text: modelData[0].toUpperCase(); color: theme.fgDim; font { family: theme.fontUi; pixelSize: 10; weight: Font.Bold; letterSpacing: 0.6 } }
                            Text { width: parent.width; wrapMode: Text.WrapAnywhere; maximumLineCount: 5; elide: Text.ElideRight; text: modelData[1]; color: theme.fg
                                   font { family: modelData[0] === "Príkaz" ? theme.fontMono : theme.fontUi; pixelSize: modelData[0] === "Príkaz" ? 11 : 12 } }
                        }
                    }
                    Item { width: 1; height: 4 }
                    component Action: Rectangle {
                        id: act
                        property string glyph; property string label; property bool danger: false; property bool on: true
                        signal clicked()
                        width: parent.width; height: 36; radius: 10; opacity: on ? 1 : 0.45
                        color: am.containsMouse && on ? (danger ? Qt.rgba(theme.error.r, theme.error.g, theme.error.b, 0.2) : theme.hover) : theme.field
                        Row { x: 12; anchors.verticalCenter: parent.verticalCenter; spacing: 10
                              Glyph { name: act.glyph; size: 16; color: act.danger ? theme.error : theme.fg }
                              Text { text: act.label; color: act.danger ? theme.error : theme.fg; font { family: theme.fontUi; pixelSize: 13; weight: Font.DemiBold } } }
                        MouseArea { id: am; anchors.fill: parent; hoverEnabled: true; onClicked: if (act.on) act.clicked() }
                    }
                    Action { visible: !!parent.p; on: !!parent.p && parent.p.kind !== "system"; glyph: "x"
                             label: parent.p && app.confirm === "term:" + parent.p.pid ? "Naozaj ukončiť?" : "Ukončiť"; onClicked: app.stop(app.sel, false) }
                    Action { visible: !!parent.p; on: !!parent.p && parent.p.kind !== "system"; danger: true; glyph: "alert-triangle"
                             label: parent.p && app.confirm === "kill:" + parent.p.pid ? "Naozaj vynútiť?" : "Vynútiť ukončenie"; onClicked: app.stop(app.sel, true) }
                    Action { visible: !!parent.p; glyph: "clipboard"; label: "Kopírovať príkaz"; onClicked: app.run(["wl-copy", "--", app.sel.cmd || app.sel.name], "Príkaz skopírovaný") }
                }
            }

            Rectangle {
                id: statusBar
                anchors { left: side.right; right: parent.right; bottom: parent.bottom }
                height: 30; color: "transparent"
                Rectangle { width: parent.width; height: 1; color: theme.line }
                Text {
                    x: 14; anchors.verticalCenter: parent.verticalCenter
                    text: "záťaž " + (app.snap.load || []).join(" · ") + "   ·   beží " + Math.floor((app.snap.uptime || 0) / 3600) + " h " + Math.floor(((app.snap.uptime || 0) % 3600) / 60) + " min"
                          + (app.status !== "" ? "   ·   " + app.status : "")
                    color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 }
                }
            }

            ContextMenu { id: ctx; theme: theme }
        }
    }

    // ── súčasti ──────────────────────────────────────────────────────────────────
    component Graph: Rectangle {
        id: gr
        property string title; property string value; property var values: []; property real maxValue: 100
        height: 160; radius: 14; color: theme.field
        Text { x: 14; y: 10; text: gr.title; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12; weight: Font.Bold } }
        Text { x: 14; y: 28; width: parent.width - 28; elide: Text.ElideRight; text: gr.value; color: theme.fg; font { family: theme.fontUi; pixelSize: 18; weight: Font.Bold } }
        Canvas {
            id: cv
            anchors { left: parent.left; right: parent.right; bottom: parent.bottom; top: parent.top; margins: 14; topMargin: 58 }
            onPaint: {
                const c = getContext("2d"); c.reset();
                const v = gr.values, n = v.length; if (n < 2) return;
                const mx = Math.max(gr.maxValue, ...v);
                c.strokeStyle = theme.primary; c.lineWidth = 2; c.beginPath();
                for (let i = 0; i < n; i++) { const x = width * (i + 60 - n) / 59, y = height - height * v[i] / mx; if (i === 0) c.moveTo(x, y); else c.lineTo(x, y); }
                c.stroke();
                c.lineTo(width, height); c.lineTo(width * (60 - n) / 59, height); c.closePath();
                c.fillStyle = Qt.rgba(theme.primary.r, theme.primary.g, theme.primary.b, 0.14); c.fill();
            }
            Connections { target: gr; function onValuesChanged() { cv.requestPaint(); } }
        }
    }
    component Heading: Text { color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12; weight: Font.Bold; letterSpacing: 0.8 } }

    // ── stránky ──────────────────────────────────────────────────────────────────
    Component {
        id: pPrehlad
        Flickable {
            contentHeight: col.implicitHeight; clip: true
            Column {
                id: col
                width: parent.width; spacing: 14
                Row {
                    width: parent.width; spacing: 12
                    Graph { width: (parent.width - 24) / 3; title: "PROCESOR"; value: Math.round(app.snap.cpu) + " %"; values: app.cpuHist }
                    Graph { width: (parent.width - 24) / 3; title: "PAMÄŤ"; value: app.human(app.snap.mem.used) + " / " + app.human(app.snap.mem.total); values: app.memHist }
                    Graph { width: (parent.width - 24) / 3; title: "SIEŤ"; value: "↓ " + app.human(app.snap.net.rx) + "/s  ↑ " + app.human(app.snap.net.tx) + "/s"; values: app.netHist; maxValue: 1024 * 64 }
                }
                Heading { text: "JADRÁ PROCESORA" }
                Flow {
                    width: parent.width; spacing: 8
                    Repeater {
                        model: app.snap.cores || []
                        Rectangle {
                            required property real modelData
                            required property int index
                            width: 110; height: 44; radius: 10; color: theme.field
                            Text { x: 10; y: 6; text: "jadro " + index; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 11 } }
                            Text { anchors { right: parent.right; rightMargin: 10 } y: 5; text: Math.round(modelData) + " %"; color: theme.fg; font { family: theme.fontUi; pixelSize: 13; weight: Font.Bold } }
                            Rectangle { x: 10; y: 30; width: parent.width - 20; height: 4; radius: 2; color: theme.line
                                        Rectangle { width: parent.width * Math.min(1, parent.parent.modelData / 100); height: 4; radius: 2; color: theme.primary } }
                        }
                    }
                }
                Heading { text: "DISKY" }
                Repeater {
                    model: app.snap.fs || []
                    Rectangle {
                        required property var modelData
                        width: Math.min(parent.width, 620); height: 50; radius: 12; color: theme.field
                        Text { x: 14; y: 8; text: modelData.mount + "  ·  " + modelData.fs; color: theme.fg; font { family: theme.fontUi; pixelSize: 13; weight: Font.Bold } }
                        Text { anchors { right: parent.right; rightMargin: 14 } y: 8; text: app.human(modelData.used) + " z " + app.human(modelData.total); color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 } }
                        Rectangle { x: 14; y: 34; width: parent.width - 28; height: 4; radius: 2; color: theme.line
                                    Rectangle { width: parent.width * parent.parent.modelData.used / Math.max(1, parent.parent.modelData.total); height: 4; radius: 2; color: theme.primary } }
                    }
                }
                Text { text: "Čítanie " + app.human(app.snap.disk.read) + "/s · zápis " + app.human(app.snap.disk.write) + "/s"; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 } }
                Heading { text: "TEPLOTY" }
                Text {
                    width: parent.width; wrapMode: Text.WordWrap
                    text: (app.snap.temps || []).length ? app.snap.temps.map(t => t.label + " " + Math.round(t.c) + " °C").join("   ·   ")
                                                        : "Senzory teploty nie sú dostupné (vo VM bežné; na reálnom HW sa ukážu CPU, GPU a disky)."
                    color: theme.fg; font { family: theme.fontUi; pixelSize: 13 }
                }
            }
        }
    }

    Component {
        id: pProcesy
        Item {
            Row {
                id: filters
                spacing: 6
                Rectangle {
                    width: tt.implicitWidth + 26; height: 32; radius: 10
                    color: app.tree ? Qt.rgba(theme.primary.r, theme.primary.g, theme.primary.b, 0.18) : theme.field
                    border { color: app.tree ? theme.primary : "transparent"; width: 1.5 }
                    Text { id: tt; anchors.centerIn: parent; text: app.tree ? "Strom ✓" : "Strom"; color: theme.fg; font { family: theme.fontUi; pixelSize: 12; weight: Font.Bold } }
                    MouseArea { anchors.fill: parent; onClicked: app.tree = !app.tree }
                }
                Item { width: 8; height: 1 }
                Repeater {
                    model: [["", "Všetky"], ["app", "Aplikácie"], ["desktop", "Prostredie"], ["helper", "Pomocné"], ["system", "Systém"]]
                    Rectangle {
                        required property var modelData
                        readonly property bool on: app.kindFilter === modelData[0]
                        width: ft.implicitWidth + 26; height: 32; radius: 10
                        color: on ? Qt.rgba(theme.primary.r, theme.primary.g, theme.primary.b, 0.18) : (fm.containsMouse ? theme.hover : theme.field)
                        border { color: on ? theme.primary : "transparent"; width: 1.5 }
                        Text { id: ft; anchors.centerIn: parent; text: modelData[1]; color: theme.fg; font { family: theme.fontUi; pixelSize: 12; weight: on ? Font.Bold : Font.Medium } }
                        MouseArea { id: fm; anchors.fill: parent; hoverEnabled: true; onClicked: app.kindFilter = modelData[0] }
                    }
                }
            }
            Row {
                id: head
                anchors { top: filters.bottom; topMargin: 12; left: parent.left; right: parent.right }
                height: 28
                readonly property real nameW: width - 110 - 80 - 100 - 80
                component Col: Item {
                    id: c
                    property string label; property string key; property real w
                    width: w; height: parent.height
                    Text { anchors.verticalCenter: parent.verticalCenter; leftPadding: 8
                           text: c.label + (app.sortKey === c.key ? "  ↓" : ""); color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12; weight: Font.Bold } }
                    MouseArea { anchors.fill: parent; onClicked: app.sortKey = c.key }
                }
                Col { label: "Názov"; key: "name"; w: head.nameW }
                Col { label: "Druh"; key: "kind"; w: 110 }
                Col { label: "CPU"; key: "cpu"; w: 80 }
                Col { label: "Pamäť"; key: "rss"; w: 100 }
                Col { label: "PID"; key: "pid"; w: 80 }
            }
            ListView {
                id: list
                anchors { top: head.bottom; left: parent.left; right: parent.right; bottom: parent.bottom }
                clip: true; boundsBehavior: Flickable.StopAtBounds
                model: app.shown
                delegate: Rectangle {
                    id: row
                    required property var modelData
                    readonly property bool picked: app.selPid === modelData.pid
                    width: list.width; height: 32; radius: 8
                    color: picked ? Qt.rgba(theme.primary.r, theme.primary.g, theme.primary.b, 0.18) : (rm.containsMouse ? theme.hover : "transparent")
                    Row {
                        anchors.verticalCenter: parent.verticalCenter
                        Item {
                            width: head.nameW; height: 32
                            Glyph { x: 8 + (row.modelData.depth || 0) * 16; anchors.verticalCenter: parent.verticalCenter; size: 15
                                    name: ({ app: "window", desktop: "coffee", helper: "terminal-2", system: "shield" })[row.modelData.kind]
                                    color: row.modelData.kind === "app" ? theme.primary : theme.fgDim }
                            Text { x: 32 + (row.modelData.depth || 0) * 16; width: parent.width - 40 - (row.modelData.depth || 0) * 16; anchors.verticalCenter: parent.verticalCenter; elide: Text.ElideRight
                                   text: ((row.modelData.depth || 0) > 0 ? "└ " : "") + app.progName(row.modelData) + (row.modelData.window ? "  —  " + row.modelData.window : ""); color: theme.fg
                                   font { family: theme.fontUi; pixelSize: 13; weight: row.modelData.kind === "app" ? Font.DemiBold : Font.Normal } }
                        }
                        Text { width: 110; leftPadding: 8; anchors.verticalCenter: parent.verticalCenter; text: app.kinds[row.modelData.kind]; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 } }
                        Text { width: 80; leftPadding: 8; anchors.verticalCenter: parent.verticalCenter; text: row.modelData.cpu.toFixed(1).replace(".", ",") + " %"
                               color: row.modelData.cpu > 50 ? theme.error : theme.fg; font { family: theme.fontUi; pixelSize: 12; weight: Font.DemiBold } }
                        Text { width: 100; leftPadding: 8; anchors.verticalCenter: parent.verticalCenter; text: app.human(row.modelData.rss); color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 } }
                        Text { width: 80; leftPadding: 8; anchors.verticalCenter: parent.verticalCenter; text: row.modelData.pid; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 } }
                    }
                    MouseArea {
                        id: rm; anchors.fill: parent; hoverEnabled: true; acceptedButtons: Qt.LeftButton | Qt.RightButton
                        onClicked: (m) => {
                            app.selPid = row.modelData.pid; app.confirm = "";
                            if (m.button !== Qt.RightButton) return;
                            const p = row.modelData, pt = mapToItem(null, m.x, m.y), sys = p.kind === "system";
                            ctx.open(pt.x, pt.y, [
                                { glyph: "x", label: "Ukončiť", hint: sys ? "správca" : "", enabled: !sys, action: () => { app.confirm = "term:" + p.pid; app.stop(p, false); } },
                                { glyph: "alert-triangle", label: "Vynútiť ukončenie", danger: true, enabled: !sys, action: () => { app.confirm = "kill:" + p.pid; app.stop(p, true); } },
                                { separator: true },
                                { glyph: "clipboard", label: "Kopírovať príkaz", action: () => app.run(["wl-copy", "--", p.cmd || p.name], "Príkaz skopírovaný") },
                                { glyph: "folder", label: "Priečinok programu", action: () => app.run(["sh", "-c", "d=$(dirname \"$(readlink /proc/$1/exe)\") && latte-app subory \"$d\"", "sh", String(p.pid)]) }
                            ], app.progName(p) + " · " + app.kinds[p.kind]);
                        }
                    }
                }
            }
        }
    }

    Component {
        id: pAutorun
        Flickable {
            contentHeight: acol.implicitHeight; clip: true
            Column {
                id: acol
                width: parent.width; spacing: 6
                Text { width: parent.width; wrapMode: Text.WordWrap; bottomPadding: 6; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 13 }
                       text: "Čo sa spúšťa po prihlásení a pri štarte systému, odkiaľ to je a aký príkaz. Položky tvojho účtu sa dajú vypnúť; systémové mení iba správca." }
                Repeater {
                    model: [["autostart", "AUTOŠTART APLIKÁCIÍ (XDG)"], ["user-service", "SLUŽBY TVOJHO ÚČTU (systemd --user)"], ["timer", "ČASOVAČE"],
                            ["service", "SYSTÉMOVÉ SLUŽBY"], ["cron", "CRON"]]
                    Column {
                        id: grp
                        required property var modelData
                        readonly property var items: app.autorun.filter(x => x.kind === modelData[0])
                        visible: items.length > 0
                        width: acol.width; spacing: 4
                        Heading { text: grp.modelData[1] + "  ·  " + grp.items.length; topPadding: 8 }
                        Repeater {
                            model: grp.items
                            Rectangle {
                                id: ar
                                required property var modelData
                                width: grp.width; height: 48; radius: 10; color: theme.field
                                opacity: modelData.enabled ? 1 : 0.6
                                Column {
                                    x: 14; width: parent.width - 150; anchors.verticalCenter: parent.verticalCenter
                                    Text { width: parent.width; elide: Text.ElideRight; text: ar.modelData.name + (ar.modelData.note ? "  (" + ar.modelData.note + ")" : "")
                                           color: theme.fg; font { family: theme.fontUi; pixelSize: 13; weight: Font.DemiBold } }
                                    Text { width: parent.width; elide: Text.ElideMiddle; text: ar.modelData.owner + " · " + (ar.modelData.command || ar.modelData.origin)
                                           color: theme.fgDim; font { family: theme.fontUi; pixelSize: 11 } }
                                }
                                Rectangle {   // prepínač zapnuté / vypnuté
                                    anchors { right: parent.right; rightMargin: 14; verticalCenter: parent.verticalCenter }
                                    width: 96; height: 30; radius: 15
                                    color: ar.modelData.enabled ? Qt.rgba(theme.primary.r, theme.primary.g, theme.primary.b, 0.2) : theme.surface
                                    border { color: ar.modelData.enabled ? theme.primary : theme.line; width: 1 }
                                    opacity: ar.modelData.canToggle ? 1 : 0.5
                                    Text { anchors.centerIn: parent; text: (ar.modelData.enabled ? "● zapnuté" : "○ vypnuté"); color: theme.fg; font { family: theme.fontUi; pixelSize: 12; weight: Font.Bold } }
                                    MouseArea { anchors.fill: parent; onClicked: app.toggleAutorun(ar.modelData) }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    Component {
        id: pTelemetria
        Column {
            spacing: 12
            Text { width: parent.width; wrapMode: Text.WordWrap; color: theme.fg; font { family: theme.fontUi; pixelSize: 14 }
                   text: "Monitor dáva živé údaje iným zobrazovačom (OLED displej vodného chladenia, Stream Deck, panel lišty) cez jednoduché lokálne rozhranie. Nič na nich nenastavuje." }
            Heading { text: "SÚBOR (obnovuje sa každú sekundu, kým beží Monitor alebo latte-sysmon stream)" }
            Rectangle {
                width: parent.width; height: 40; radius: 10; color: theme.field
                Text { x: 14; anchors.verticalCenter: parent.verticalCenter; text: "$XDG_RUNTIME_DIR/latteos/telemetry.json"; color: theme.fg; font { family: theme.fontMono; pixelSize: 12 } }
            }
            Heading { text: "UKÁŽKA" }
            Rectangle {
                width: parent.width; height: sample.implicitHeight + 24; radius: 10; color: theme.field
                Text {
                    id: sample
                    x: 12; y: 12; width: parent.width - 24; wrapMode: Text.WrapAnywhere
                    text: JSON.stringify({ cpu: app.snap.cpu, mem: app.snap.mem, net: app.snap.net, disk: app.snap.disk, temps: app.snap.temps, load: app.snap.load })
                    color: theme.fgDim; font { family: theme.fontMono; pixelSize: 11 }
                }
            }
            Text { width: parent.width; wrapMode: Text.WordWrap; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 }
                   text: "Pripravujeme: stála služba (bez otvoreného Monitora), výber údajov pre každý výstup, pluginy pre Stream Deck a displeje (liquidctl)." }
        }
    }
}
