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
    property var diskHist: []
    property var gpuHist: []
    property var hw: null
    // Digitálna pohoda (pohoda.qml meria, latte-sysmon pohoda sčíta)
    property var well: null
    property var limits: ({})
    property bool wellOff: false
    readonly property var wellColors: [theme.primary, "#C75B4A", "#6FA8DC", "#8BC48A", "#B58ED8", "#E8C33B"]
    readonly property var wellTop: well ? well.apps.filter(a => a.today > 0).sort((x, y) => y.today - x.today).slice(0, 6) : []
    function wellColor(cls) { const i = wellTop.findIndex(a => a["class"] === cls); return i >= 0 ? wellColors[i] : Qt.rgba(theme.fg.r, theme.fg.g, theme.fg.b, 0.25); }
    function dur(sec) {
        sec = Math.round(sec || 0);
        const h = Math.floor(sec / 3600), m = Math.floor(sec % 3600 / 60);
        return h > 0 ? h + " h " + m + " min" : (m > 0 ? m + " min" : (sec > 0 ? "< 1 min" : "0 min"));
    }
    Process {
        id: wellProc
        command: ["latte-sysmon", "pohoda", "7"]
        stdout: StdioCollector { onStreamFinished: { try { app.well = JSON.parse(this.text); } catch (e) {} } }
    }
    Timer { interval: 60000; repeat: true; running: app.section === "pohoda"; onTriggered: if (!wellProc.running) wellProc.running = true }
    FileView {
        id: limitsFile
        path: (Quickshell.env("XDG_CONFIG_HOME") || ((Quickshell.env("HOME") || "") + "/.config")) + "/latteos/pohoda-limity.json"
        printErrors: false; watchChanges: true; onFileChanged: reload()
        onLoaded: { try { app.limits = JSON.parse(text()) || {}; } catch (e) { app.limits = {}; } }
    }
    FileView {
        path: (Quickshell.env("XDG_CONFIG_HOME") || ((Quickshell.env("HOME") || "") + "/.config")) + "/latteos/pohoda"
        printErrors: false; watchChanges: true; onFileChanged: reload()
        onLoaded: app.wellOff = text().trim() === "off"; onLoadFailed: app.wellOff = false
    }
    function setLimit(cls, minutes) {
        const l = Object.assign({}, limits);
        if (minutes > 0) l[cls] = minutes; else delete l[cls];
        limits = l;
        run(["sh", "-c", 'mkdir -p "$(dirname "$1")" && printf "%s" "$2" > "$1"', "sh", limitsFile.path, JSON.stringify(l)], minutes > 0 ? "Denný limit " + minutes + " min" : "Limit zrušený");
    }
    function setWellOff(off) {
        wellOff = off;
        const f = (Quickshell.env("XDG_CONFIG_HOME") || ((Quickshell.env("HOME") || "") + "/.config")) + "/latteos/pohoda";
        if (off) run(["sh", "-c", 'printf off > "$1"; pkill -f "apps/[p]ohoda.qml"', "sh", f], "Meranie času pozastavené");
        else run(["sh", "-c", 'rm -f "$1"; pgrep -f "apps/[p]ohoda.qml" >/dev/null || setsid latte-app pohoda >/dev/null 2>&1 &', "sh", f], "Meranie času zapnuté");
    }                  // latte-sysmon hw (Hardvér, ako CPU-Z/HWiNFO)
    property string autorunFilter: ""
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
                    app.diskHist = app.push(app.diskHist, (s.disk.read || 0) + (s.disk.write || 0));
                    if (s.gpu) app.gpuHist = app.push(app.gpuHist, s.gpu.busy);
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
    function go(k) { section = k; if (k === "pohoda" && !wellProc.running) wellProc.running = true; if (k === "autorun") autorunProc.running = true; if (k === "hardver" && !hwProc.running) hwProc.running = true; }
    Process {
        id: hwProc
        command: ["latte-sysmon", "hw"]
        stdout: StdioCollector { onStreamFinished: { try { app.hw = JSON.parse(this.text); } catch (e) {} } }
    }
    function uptimeText(sec) {
        const d = Math.floor(sec / 86400), h = Math.floor(sec % 86400 / 3600), m = Math.floor(sec % 3600 / 60);
        return (d ? d + " d " : "") + h + " h " + m + " min";
    }
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
        onClosed: Qt.quit()              // zavretie z kompozitora (✕ v titulku, Super+Q) ukončí aj proces
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
                    { title: "Ty", items: [
                        { key: "pohoda", glyph: "clock", label: "Čas v aplikáciách", sub: app.well ? "dnes " + app.dur(app.well.days[app.well.days.length - 1].s) : "digitálna pohoda" }
                    ] },
                    { title: "Systém", items: [
                        { key: "hardver", glyph: "cpu", label: "Hardvér", sub: "procesor, doska, grafika, senzory" }
                    ] },
                    { title: "Správa", items: [
                        { key: "autorun", glyph: "player-play", label: "Po štarte", sub: "ako Autoruns: všetko, čo sa spúšťa" },
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
                title: ({ prehlad: "Prehľad", procesy: "Procesy", autorun: "Po štarte", telemetria: "Výstupy telemetrie", hardver: "Hardvér", pohoda: "Čas v aplikáciách" })[app.section]
                searchPlaceholder: app.section === "autorun" ? "Hľadať v štarte" : "Hľadať proces"
                onSearchChanged: (t) => { if (app.section === "autorun") { app.autorunFilter = t; return; } app.search = t; if (t !== "") app.section = "procesy"; }
                onCloseRequested: Qt.quit()
            }

            Loader {
                id: content
                anchors { left: side.right; top: header.bottom; bottom: statusBar.top; right: app.section === "procesy" ? detail.left : parent.right; margins: 20 }
                sourceComponent: ({ prehlad: pPrehlad, procesy: pProcesy, autorun: pAutorun, telemetria: pTelemetria, hardver: pHardver, pohoda: pPohoda })[app.section] || pPrehlad
            }

            // detail vybraného procesu (návrh V2: pravý panel)
            Rectangle {
                id: detail
                visible: app.section === "procesy"
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
            id: rolovanie1
            ScrollHint { flick: rolovanie1; colors: theme }
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
                Row {
                    width: parent.width; spacing: 12
                    Graph { width: app.snap.gpu ? (parent.width - 24) / 3 : (parent.width - 12) / 2; title: "DISK"; value: "čítanie " + app.human(app.snap.disk.read) + "/s · zápis " + app.human(app.snap.disk.write) + "/s"; values: app.diskHist; maxValue: 1024 * 1024 }
                    Graph { visible: !!app.snap.gpu; width: (parent.width - 24) / 3; title: "GRAFIKA"; value: app.snap.gpu ? app.snap.gpu.busy + " %" + (app.snap.gpu.vramTotal ? " · VRAM " + app.human(app.snap.gpu.vramUsed) + " / " + app.human(app.snap.gpu.vramTotal) : "") : ""; values: app.gpuHist }
                    // súhrn ako vo Win11 Správcovi úloh › Výkon
                    Rectangle {
                        width: app.snap.gpu ? (parent.width - 24) / 3 : (parent.width - 12) / 2; height: 160; radius: 14; color: theme.field
                        Grid {
                            x: 14; y: 12; columns: 2; columnSpacing: 18; rowSpacing: 8
                            Repeater {
                                model: [["Rýchlosť", (app.snap.freq ? (app.snap.freq / 1000).toFixed(2).replace(".", ",") + " GHz" : "—")],
                                        ["Procesy", String(app.snap.procCount || 0)], ["Vlákna", String(app.snap.threads || 0)],
                                        ["Záťaž", (app.snap.load || []).join(" · ")], ["Doba behu", app.uptimeText(app.snap.uptime || 0)],
                                        ["Swap", app.human(app.snap.mem.swapUsed || 0) + " / " + app.human(app.snap.mem.swapTotal || 0)]]
                                Column {
                                    required property var modelData
                                    Text { text: modelData[0].toUpperCase(); color: theme.fgDim; font { family: theme.fontUi; pixelSize: 10; weight: Font.Bold } }
                                    Text { text: modelData[1]; color: theme.fg; font { family: theme.fontUi; pixelSize: 14; weight: Font.DemiBold } }
                                }
                            }
                        }
                    }
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
                ScrollHint { flick: list; colors: theme }
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
            id: rolovanie3
            ScrollHint { flick: rolovanie3; colors: theme }
            contentHeight: acol.implicitHeight; clip: true
            Column {
                id: acol
                width: parent.width; spacing: 6
                Text { width: parent.width; wrapMode: Text.WordWrap; bottomPadding: 6; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 13 }
                       text: "Čo sa spúšťa po prihlásení a pri štarte systému, odkiaľ to je a aký príkaz. Položky tvojho účtu sa dajú vypnúť; systémové mení iba správca." }
                Repeater {
                    model: [["session", "ŠTART RELÁCIE LatteOS (hyprland.lua)"], ["autostart", "AUTOŠTART APLIKÁCIÍ (XDG)"], ["user-service", "SLUŽBY TVOJHO ÚČTU (systemd --user)"],
                            ["timer", "ČASOVAČE"], ["service", "SYSTÉMOVÉ SLUŽBY"], ["cron", "CRON"], ["login", "PRIHLÁSENIE A PROSTREDIE"], ["module", "MODULY JADRA"]]
                    Column {
                        id: grp
                        required property var modelData
                        readonly property var items: app.autorun.filter(x => x.kind === modelData[0] && (app.autorunFilter === ""
                                                     || (x.name + " " + (x.command || "") + " " + (x.origin || "")).toLowerCase().includes(app.autorunFilter.toLowerCase())))
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
                                    Text { width: parent.width; elide: Text.ElideRight; text: (ar.modelData.missing ? "⚠ " : "") + ar.modelData.name + (ar.modelData.note ? "  (" + ar.modelData.note + ")" : "") + (ar.modelData.missing ? "  · súbor chýba" : "")
                                           color: ar.modelData.missing ? theme.error : theme.fg; font { family: theme.fontUi; pixelSize: 13; weight: Font.DemiBold } }
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
        id: pHardver
        Flickable {
            id: rolovanie4
            ScrollHint { flick: rolovanie4; colors: theme }
            contentHeight: hcol.implicitHeight; clip: true
            Column {
                id: hcol
                width: parent.width; spacing: 14
                readonly property var h: app.hw
                Text { visible: !hcol.h; text: "Zisťujem hardvér…"; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 13 } }
                component Card: Rectangle {
                    id: card
                    property string title; property string glyph; property var rows: []
                    width: (hcol.width - 14) / 2; height: ccol.implicitHeight + 28; radius: 14; color: theme.field
                    Column {
                        id: ccol; x: 16; y: 14; width: parent.width - 32; spacing: 6
                        Row { spacing: 8
                              Glyph { name: card.glyph; size: 18; color: theme.primary; anchors.verticalCenter: parent.verticalCenter }
                              Text { text: card.title; color: theme.fg; font { family: theme.fontUi; pixelSize: 14; weight: Font.Bold }
                                     anchors.verticalCenter: parent.verticalCenter } }
                        Repeater {
                            model: card.rows.filter(r => r[1] !== "" && r[1] !== undefined && r[1] !== null)
                            Row {
                                required property var modelData
                                width: ccol.width
                                Text { width: 130; text: modelData[0]; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 } }
                                Text { width: parent.width - 130; wrapMode: Text.WordWrap; text: String(modelData[1]); color: theme.fg; font { family: theme.fontUi; pixelSize: 12; weight: Font.DemiBold } }
                            }
                        }
                    }
                }
                Flow {
                    visible: !!hcol.h; width: parent.width; spacing: 14
                    Card {
                        title: "Procesor"; glyph: "cpu"
                        rows: hcol.h ? [["Názov", hcol.h.cpu.model], ["Výrobca", hcol.h.cpu.vendor], ["Jadrá / vlákna", hcol.h.cpu.cores + " / " + hcol.h.cpu.threads],
                                        ["Frekvencia", hcol.h.cpu.curMHz + " MHz" + (hcol.h.cpu.maxMHz ? " (max " + hcol.h.cpu.maxMHz + " MHz)" : "")],
                                        ["Rodina · model · stepping", hcol.h.cpu.family + " · " + hcol.h.cpu.modelId + " · " + hcol.h.cpu.stepping],
                                        ["Mikrokód", hcol.h.cpu.microcode], ["Režim výkonu", hcol.h.cpu.governor],
                                        ["Cache", hcol.h.cpu.cache.map(c => c.level + " " + c.size).join(" · ")],
                                        ["Inštrukcie", hcol.h.cpu.flags.filter(f => f !== "hypervisor").join(", ").toUpperCase()],
                                        ["Virtualizácia", hcol.h.cpu.flags.includes("hypervisor") ? "beží vo VM (" + hcol.h.system.virt + ")" : (hcol.h.cpu.flags.includes("vmx") || hcol.h.cpu.flags.includes("svm") ? "podporovaná" : "")]] : []
                    }
                    Card {
                        title: "Doska a firmvér"; glyph: "server"
                        rows: hcol.h ? [["Počítač", (hcol.h.board.sys_vendor + " " + hcol.h.board.product_name).trim()], ["Doska", (hcol.h.board.board_vendor + " " + hcol.h.board.board_name).trim()],
                                        ["BIOS", (hcol.h.board.bios_vendor + " " + hcol.h.board.bios_version).trim()], ["Dátum BIOS", hcol.h.board.bios_date],
                                        ["Štart", hcol.h.board.efi ? "UEFI" : "Legacy BIOS"], ["Secure Boot", hcol.h.board.secureBoot === null ? "" : (hcol.h.board.secureBoot ? "zapnutý" : "vypnutý")]] : []
                    }
                    Card {
                        title: "Pamäť"; glyph: "database"
                        rows: hcol.h ? [["Operačná pamäť", app.human(hcol.h.memory.total)], ["Použitá teraz", app.human(app.snap.mem.used)], ["Swap", app.human(hcol.h.memory.swap)], ["Moduly", hcol.h.memory.note]] : []
                    }
                    Card {
                        title: "Grafika"; glyph: "device-desktop"
                        rows: hcol.h ? hcol.h.gpu.map(g => [g.vendor.replace(/\s*\[[0-9a-f]+\]$/, ""), g.name.replace(/\s*\[[0-9a-f]+\]$/, "") + (g.driver ? " · ovládač " + g.driver : "") + (g.vram ? " · " + app.human(g.vram) : "")])
                                      .concat([["Vykresľovanie", (hcol.h.renderer.match(/renderer = "([^"]*)"/) || [, ""])[1] + " · stupeň " + ((hcol.h.renderer.match(/tier = "([^"]*)"/) || [, ""])[1])]]) : []
                    }
                    Card {
                        title: "Disky"; glyph: "database"
                        rows: hcol.h ? hcol.h.disks.map(d => [d.name + " · " + d.kind, (d.model || "disk") + " · " + app.human(d.size) + (d.bus ? " · " + d.bus.toUpperCase() : "")]) : []
                    }
                    Card {
                        title: "Systém"; glyph: "info-circle"
                        rows: hcol.h ? [["Systém", hcol.h.system.os], ["Jadro", hcol.h.system.kernel + " · " + hcol.h.system.arch], ["Názov PC", hcol.h.system.host],
                                        ["Virtualizácia", hcol.h.system.virt === "none" ? "skutočný hardvér" : hcol.h.system.virt], ["Doba behu", app.uptimeText(hcol.h.system.uptime)]] : []
                    }
                    Card {
                        title: "Senzory"; glyph: "activity"
                        rows: hcol.h ? (hcol.h.sensors.length ? hcol.h.sensors.map(x => [x.chip + " · " + x.label, x.value + " " + x.unit])
                                                              : [["", ""], ["Senzory", "ovládač nehlási žiadne (vo VM bežné; na reálnom HW teploty, ventilátory a napätia)"]]) : []
                    }
                    Card {
                        visible: !!hcol.h && hcol.h.battery.length > 0
                        title: "Batéria"; glyph: "battery"
                        rows: hcol.h ? hcol.h.battery.map(b => [b.name, b.capacity + " % · " + b.status + (b.health ? " · zdravie " + b.health + " %" : "") + (b.cycles ? " · " + b.cycles + " cyklov" : "")]) : []
                    }
                }
                Row {
                    visible: !!hcol.h; spacing: 10
                    Rectangle {
                        width: rh.implicitWidth + 24; height: 34; radius: 10; color: rhm.containsMouse ? theme.hover : theme.field
                        Text { id: rh; anchors.centerIn: parent; text: "Obnoviť"; color: theme.fg; font { family: theme.fontUi; pixelSize: 12; weight: Font.Bold } }
                        MouseArea { id: rhm; anchors.fill: parent; hoverEnabled: true; onClicked: hwProc.running = true }
                    }
                    Rectangle {
                        width: ch.implicitWidth + 24; height: 34; radius: 10; color: chm.containsMouse ? theme.hover : theme.field
                        Text { id: ch; anchors.centerIn: parent; text: "Kopírovať ako text"; color: theme.fg; font { family: theme.fontUi; pixelSize: 12; weight: Font.Bold } }
                        MouseArea { id: chm; anchors.fill: parent; hoverEnabled: true
                                    onClicked: app.run(["wl-copy", "--", JSON.stringify(app.hw, null, 1)], "Hardvér skopírovaný (JSON)") }
                    }
                }
            }
        }
    }

    Component {
        id: pPohoda
        Flickable {
            id: wf
            ScrollHint { flick: wf; colors: theme }
            contentHeight: wcol.implicitHeight; clip: true
            Column {
                id: wcol
                width: parent.width - 12; spacing: 16
                readonly property var w: app.well
                readonly property var days: w ? w.days : []
                readonly property real todayS: days.length ? days[days.length - 1].s : 0
                readonly property real yestS: days.length > 1 ? days[days.length - 2].s : 0
                readonly property real weekS: w ? w.total : 0
                Text { visible: !wcol.w; text: "Načítavam…"; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 13 } }
                // súhrn
                Row {
                    visible: !!wcol.w; width: parent.width; spacing: 12
                    component Stat: Rectangle {
                        id: st
                        property string label; property string value; property string sub; property string icon: ""
                        width: (wcol.width - 24) / 3; height: 108; radius: 18; color: theme.field
                        Text { x: 18; y: 14; text: st.label.toUpperCase(); color: theme.fgDim; font { family: theme.fontUi; pixelSize: 11; weight: Font.Bold; letterSpacing: 0.8 } }
                        Row {
                            x: 18; y: 36; spacing: 10
                            Image { visible: st.icon !== ""; width: 34; height: 34; source: st.icon; sourceSize { width: 68; height: 68 } anchors.verticalCenter: parent.verticalCenter }
                            Text { text: st.value; color: theme.fg; font { family: theme.fontDisplay; pixelSize: 28; weight: Font.DemiBold } }
                        }
                        Text { x: 18; anchors { bottom: parent.bottom; bottomMargin: 14 } width: parent.width - 36; elide: Text.ElideRight; text: st.sub; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 } }
                    }
                    Stat { label: "Dnes"; value: app.dur(wcol.todayS)
                           sub: wcol.yestS > 0 ? (wcol.todayS >= wcol.yestS ? "▲ " : "▼ ") + Math.abs(Math.round(100 * (wcol.todayS - wcol.yestS) / wcol.yestS)) + " % oproti včerajšku" : "včera bez záznamu" }
                    Stat { label: "Posledných 7 dní"; value: app.dur(wcol.weekS); sub: "priemer " + app.dur(wcol.weekS / Math.max(1, wcol.days.filter(d => d.s > 0).length)) + " denne" }
                    Stat { readonly property var best: app.wellTop[0]
                           label: "Najviac dnes"; value: best ? best.name : "—"; sub: best ? app.dur(best.today) : "zatiaľ nič"
                           icon: best && best.icon ? Quickshell.iconPath(best.icon, true) : "" }
                }
                // časová os dňa (hodiny, farba = aplikácia)
                Rectangle {
                    visible: !!wcol.w; width: parent.width; height: 190; radius: 18; color: theme.field
                    Text { x: 18; y: 14; text: "DNES PO HODINÁCH"; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 11; weight: Font.Bold; letterSpacing: 0.8 } }
                    Row {
                        id: bars
                        x: 18; y: 40; width: parent.width - 36; height: 110; spacing: 3
                        readonly property real bw: (width - 23 * 3) / 24
                        Repeater {
                            model: 24
                            Item {
                                required property int index
                                readonly property var row: wcol.w ? wcol.w.hoursApps[index] : ({})
                                readonly property real tot: wcol.w ? wcol.w.hours[index] : 0
                                width: bars.bw; height: bars.height
                                Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: parent.height; radius: 4; color: Qt.rgba(theme.fg.r, theme.fg.g, theme.fg.b, 0.05) }
                                Column {
                                    anchors.bottom: parent.bottom; width: parent.width
                                    Repeater {
                                        model: Object.keys(parent.parent.row).sort((a, b) => parent.parent.row[a] - parent.parent.row[b])
                                        Rectangle {
                                            required property string modelData
                                            width: bars.bw; height: bars.height * parent.parent.row[modelData] / 3600
                                            color: app.wellColor(modelData); radius: 2
                                        }
                                    }
                                }
                                MouseArea { id: hm; anchors.fill: parent; hoverEnabled: true }
                                Rectangle {
                                    visible: hm.containsMouse && parent.tot > 0; z: 5
                                    x: Math.min(0, bars.width - parent.x - width); y: -34; width: tipT.implicitWidth + 16; height: 26; radius: 8; color: theme.surface; border { color: theme.outline; width: 1 }
                                    Text { id: tipT; anchors.centerIn: parent; text: parent.parent.index + ":00 · " + app.dur(parent.parent.tot); color: theme.fg; font { family: theme.fontUi; pixelSize: 11 } }
                                }
                            }
                        }
                    }
                    Row {
                        x: 18; y: 156; width: parent.width - 36
                        Repeater {
                            model: ["00:00", "06:00", "12:00", "18:00", "23:00"]
                            Text { required property string modelData; required property int index
                                   width: index < 4 ? (parent.width - 30) / 4 : 30; text: modelData; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 10 } }
                        }
                    }
                }
                Row {
                    visible: !!wcol.w; width: parent.width; spacing: 12
                    // koláč dňa
                    Rectangle {
                        width: 330; height: 260; radius: 18; color: theme.field
                        Canvas {
                            id: donut
                            x: 18; y: 30; width: 160; height: 160
                            readonly property var parts: app.wellTop
                            onPartsChanged: requestPaint()
                            onPaint: {
                                const c = getContext("2d"); c.reset();
                                const top = parts; const tot = top.reduce((s, a) => s + a.today, 0);
                                const cx = width / 2, cy = height / 2, r = 72;
                                c.lineWidth = 22; c.lineCap = "butt";
                                c.strokeStyle = Qt.rgba(theme.fg.r, theme.fg.g, theme.fg.b, 0.08); c.beginPath(); c.arc(cx, cy, r, 0, Math.PI * 2); c.stroke();
                                let a0 = -Math.PI / 2;
                                for (let i = 0; i < top.length; i++) {
                                    const a1 = a0 + Math.PI * 2 * top[i].today / Math.max(1, tot);
                                    c.strokeStyle = app.wellColors[i]; c.beginPath(); c.arc(cx, cy, r, a0 + 0.02, a1 - 0.02); c.stroke();
                                    a0 = a1;
                                }
                            }
                        }
                        Column {
                            anchors.centerIn: donut
                            Text { anchors.horizontalCenter: parent.horizontalCenter; text: app.dur(wcol.todayS); color: theme.fg; font { family: theme.fontUi; pixelSize: 15; weight: Font.Bold } }
                            Text { anchors.horizontalCenter: parent.horizontalCenter; text: "dnes"; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 11 } }
                        }
                        Column {
                            x: 196; y: 36; width: parent.width - 210; spacing: 8
                            Repeater {
                                model: app.wellTop
                                Row {
                                    required property var modelData; required property int index
                                    spacing: 6
                                    Rectangle { width: 10; height: 10; radius: 5; color: app.wellColors[index]; anchors.verticalCenter: parent.verticalCenter }
                                    Text { width: 110; elide: Text.ElideRight; text: modelData.name; color: theme.fg; font { family: theme.fontUi; pixelSize: 12 } }
                                }
                            }
                        }
                        Text { x: 18; y: 212; width: parent.width - 36; wrapMode: Text.WordWrap; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 11 }
                               text: app.wellTop.length ? "" : "Dnes zatiaľ žiadny čas v aplikáciách." }
                    }
                    // týždeň
                    Rectangle {
                        width: parent.width - 342; height: 260; radius: 18; color: theme.field
                        Text { x: 18; y: 14; text: "POSLEDNÝCH 7 DNÍ"; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 11; weight: Font.Bold; letterSpacing: 0.8 } }
                        Row {
                            id: week
                            x: 18; y: 40; width: parent.width - 36; height: 170; spacing: 12
                            readonly property real mx: Math.max(3600, ...wcol.days.map(d => d.s))
                            Repeater {
                                model: wcol.days
                                Item {
                                    required property var modelData; required property int index
                                    width: (week.width - 6 * 12) / 7; height: week.height
                                    readonly property bool isToday: index === wcol.days.length - 1
                                    Text { anchors { horizontalCenter: parent.horizontalCenter; bottom: bar.top; bottomMargin: 4 } text: modelData.s > 0 ? app.dur(modelData.s).replace(" min", "m").replace(" h ", "h ") : ""
                                           color: theme.fgDim; font { family: theme.fontUi; pixelSize: 10 } }
                                    Rectangle {
                                        id: bar
                                        anchors { bottom: dayL.top; bottomMargin: 6; horizontalCenter: parent.horizontalCenter }
                                        width: Math.min(34, parent.width); height: Math.max(4, (parent.height - 40) * modelData.s / week.mx); radius: 8
                                        color: parent.isToday ? theme.primary : Qt.rgba(theme.primary.r, theme.primary.g, theme.primary.b, 0.35)
                                    }
                                    Text { id: dayL; anchors { bottom: parent.bottom; horizontalCenter: parent.horizontalCenter }
                                           text: Qt.locale("sk_SK").toString(new Date(modelData.date + "T12:00:00"), "ddd"); color: parent.isToday ? theme.fg : theme.fgDim
                                           font { family: theme.fontUi; pixelSize: 11; weight: parent.isToday ? Font.Bold : Font.Normal } }
                                }
                            }
                        }
                    }
                }
                // aplikácie
                Row {
                    visible: !!wcol.w; spacing: 12
                    Heading { text: "APLIKÁCIE  ·  7 DNÍ"; anchors.verticalCenter: parent.verticalCenter }
                    Text { text: "pravý klik: denný limit"; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 11 }
                        anchors.verticalCenter: parent.verticalCenter }
                }
                Repeater {
                    model: wcol.w ? wcol.w.apps.slice(0, 30) : []
                    Rectangle {
                        id: ar
                        required property var modelData
                        readonly property var lim: app.limits[modelData["class"]]
                        width: wcol.width; height: 56; radius: 14; color: arm.containsMouse ? theme.hover : theme.field
                        Image { id: aic; x: 14; anchors.verticalCenter: parent.verticalCenter; width: 32; height: 32
                                source: ar.modelData.icon ? Quickshell.iconPath(ar.modelData.icon, true) : ""; sourceSize { width: 64; height: 64 } }
                        Glyph { anchors.centerIn: aic; visible: aic.status !== Image.Ready; name: "app-window"; size: 22; color: theme.primary }
                        Column {
                            x: 60; anchors.verticalCenter: parent.verticalCenter; width: parent.width - 60 - 260; spacing: 5
                            Text { width: parent.width; elide: Text.ElideRight; text: ar.modelData.name + (ar.lim ? "   ·   limit " + ar.lim + " min/deň" : "")
                                   color: theme.fg; font { family: theme.fontUi; pixelSize: 13; weight: Font.DemiBold } }
                            Rectangle {
                                width: parent.width; height: 6; radius: 3; color: Qt.rgba(theme.fg.r, theme.fg.g, theme.fg.b, 0.08)
                                Rectangle { width: parent.width * ar.modelData.s / Math.max(1, wcol.w.apps[0].s); height: 6; radius: 3; color: app.wellColor(ar.modelData["class"]) }
                                Rectangle { visible: !!ar.lim; x: parent.width * Math.min(1, (ar.lim || 0) * 60 / Math.max(1, wcol.w.apps[0].s)) - 1; y: -3; width: 2; height: 12; color: theme.error }
                            }
                        }
                        Column {
                            anchors { right: parent.right; rightMargin: 16; verticalCenter: parent.verticalCenter } width: 230
                            Text { anchors.right: parent.right; text: "dnes " + app.dur(ar.modelData.today) + "  ·  7 dní " + app.dur(ar.modelData.s)
                                   color: ar.lim && ar.modelData.today >= ar.lim * 60 ? theme.error : theme.fg; font { family: theme.fontUi; pixelSize: 12; weight: Font.DemiBold } }
                            Text { anchors.right: parent.right; visible: ar.modelData.rss > 0; text: "obvykle " + app.human(ar.modelData.rss * 1024) + " RAM"
                                   color: theme.fgDim; font { family: theme.fontUi; pixelSize: 11 } }
                        }
                        MouseArea {
                            id: arm; anchors.fill: parent; hoverEnabled: true; acceptedButtons: Qt.RightButton | Qt.LeftButton
                            onClicked: (m) => {
                                const c = ar.modelData["class"], q = mapToItem(null, m.x, m.y);
                                const items = [];
                                for (const mins of [15, 30, 60, 120, 180])
                                    items.push({ glyph: "clock", label: "Denný limit " + (mins < 60 ? mins + " min" : (mins / 60) + " h"), hint: ar.lim === mins ? "✓" : "", action: () => app.setLimit(c, mins) });
                                if (ar.lim) items.push({ glyph: "x", label: "Zrušiť limit", action: () => app.setLimit(c, 0) });
                                if (ar.modelData.desktop) { items.push({ separator: true });
                                    items.push({ glyph: "apps", label: "Detail v App Manageri", action: () => app.run(["latte-app", "aplikacie", "detail", ar.modelData.desktop]) }); }
                                ctx.open(q.x, q.y, items, ar.modelData.name);
                            }
                        }
                    }
                }
                Row {
                    spacing: 12; topPadding: 6
                    Rectangle {
                        width: 46; height: 26; radius: 13; anchors.verticalCenter: parent.verticalCenter
                        color: !app.wellOff ? theme.primary : theme.field; border { color: theme.line; width: 1 }
                        Rectangle { width: 20; height: 20; radius: 10; y: 3; x: !app.wellOff ? 23 : 3; color: !app.wellOff ? theme.fgOnPrimary : theme.fgDim }
                        MouseArea { anchors.fill: parent; onClicked: app.setWellOff(!app.wellOff) }
                    }
                    Text { anchors.verticalCenter: parent.verticalCenter; width: wcol.width - 70; wrapMode: Text.WordWrap; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 }
                           text: "Merať čas v aplikáciách. Ráta sa iba aktívne okno, keď nie si 5 minút nečinný (prehrávané video sa ráta). Údaje ostávajú v tomto PC (~/.local/share/latteos/pohoda)." }
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
