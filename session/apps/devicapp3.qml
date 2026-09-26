// LatteOS — Správca zariadení 3 „Doska“ (skúšobný návrh 26. 9., alternatíva k Uzlom). Počítač ako základná doska:
// každá kategória je súčiastka tam, kde ju hráč pozná z vlastného PC — procesor a pamäť, grafická karta v slote,
// disky (M.2, SATA), napájanie (ATX), zvukový čip, sieťový čip, Wi-Fi/Bluetooth modul, konektory na prednom paneli.
//   Na každej súčiastke svieti LED: zelená = funguje, červená (bliká) = problém, zhasnutá = nič nepripojené.
//   Zadný panel vľavo je živý: obrazovky (HDMI/DP), USB, sieťový konektor s LED linky a farebné audio jacky
//   (zelený výstup, ružový mikrofón, modrý linkový vstup) — svieti aktívny; klik na jack prepne vstup/výstup.
//   Klik na súčiastku = ovládanie vpravo (ten istý komponent SpravcaZariadeni ako v okne L a v Nastaveniach).
//   Pravý klik = ponuka, Esc = zrušiť výber, hľadanie v hlavičke vyberie súčiastku.
// Spúšťa sa: latte-app devicapp3 [skupina | siete] (ikona na ploche)
import QtQuick
import Quickshell
import Quickshell.Io
import "common"

ShellRoot {
    id: app
    LatteTheme { id: theme }
    readonly property var th: theme

    // ── dáta ──
    property var inv: ({ groups: [], summary: "", faults: [] })
    property var cards: ({ cards: [], active: {} })
    component Q: Process {
        id: q
        property var done: null
        property string last: ""
        stdout: StdioCollector { onStreamFinished: { if (this.text === q.last) return; q.last = this.text; try { q.done(JSON.parse(this.text)); } catch (e) {} } }
    }
    Q { id: qInv; command: ["latte-devices", "list"]; done: (d) => app.inv = d }
    Q { id: qCards; command: ["latte-devices", "audio", "karty"]; done: (d) => app.cards = d }
    function refresh() { for (const q of [qInv, qCards]) if (!q.running) q.running = true; }
    Timer { interval: 4000; repeat: true; running: true; triggeredOnStart: true; onTriggered: app.refresh() }
    Process { id: runner; onExited: { qCards.last = ""; app.refresh(); } }
    function run(cmd, msg) { runner.command = cmd; runner.running = true; if (msg) status = msg; }
    property string status: ""
    Timer { running: app.status !== ""; interval: 2600; onTriggered: app.status = "" }

    function group(k) { return (inv.groups || []).find(g => g.key === k) || null; }
    function bad(it) { return !!it && !!it.state && it.state !== "ok" && it.state !== "off"; }
    function led(k) { const g = group(k); return !g || !g.items.length ? "off" : (g.items.some(bad) ? "bad" : "ok"); }
    function count(n) { return n + (n === 1 ? " zariadenie" : (n >= 2 && n <= 4 ? " zariadenia" : " zariadení")); }

    // ── výber ──
    property string sel: ""                     // kľúč skupiny, "siete" alebo ""
    property string hot: ""                     // súčiastka pod kurzorom
    function pick(k) {
        panelLoader.active = false; sel = k; if (k) panelLoader.active = true;
    }
    readonly property string arg: (Quickshell.env("LATTE_APP_ARGS") || "").trim()
    Component.onCompleted: if (arg) pick(arg)

    // súčiastky na doske (jednotky 100 × 66; x, y, w, h); kód = potlač na doske ako na skutočnej
    readonly property var parts: [
        { key: "bluetooth", shape: "module", x: 14, y: 5,  w: 13, h: 9,  code: "WIFI_BT",     title: "Wi-Fi a Bluetooth" },
        { key: "siet",      shape: "chip",   x: 14, y: 20, w: 7,  h: 7,  code: "LAN",         title: "Sieťový čip" },
        { key: "pocitac",   shape: "socket", x: 35, y: 6,  w: 21, h: 21, code: "CPU1",        title: "Procesor" },
        { key: "pocitac",   shape: "dimm",   x: 61, y: 4,  w: 11, h: 26, code: "DIMM_A1–B2",  title: "Pamäť" },
        { key: "napajanie", shape: "atx",    x: 87, y: 6,  w: 7,  h: 24, code: "ATX_24P",     title: "Napájanie" },
        { key: "grafika",   shape: "gpu",    x: 14, y: 33, w: 54, h: 12, code: "PCIEX16_1",   title: "Grafická karta" },
        { key: "zvuk",      shape: "chip",   x: 14, y: 51, w: 8,  h: 8,  code: "CODEC",       title: "Zvukový čip" },
        { key: "disky",     shape: "m2",     x: 28, y: 52, w: 26, h: 5,  code: "M.2_1",       title: "Disk M.2" },
        { key: "disky",     shape: "sata",   x: 85, y: 36, w: 9,  h: 15, code: "SATA6G",      title: "Disky SATA" },
        { key: "ostatne",   shape: "pch",    x: 70, y: 38, w: 11, h: 11, code: "PCH",         title: "Čipová sada a ostatné" },
        { key: "vstup",     shape: "header", x: 60, y: 58, w: 9,  h: 4,  code: "F_USB",       title: "Klávesnica a myš" },
        { key: "kamery",    shape: "header", x: 72, y: 58, w: 7,  h: 4,  code: "CAM",         title: "Kamery" },
        { key: "tlac",      shape: "header", x: 82, y: 58, w: 7,  h: 4,  code: "PRN",         title: "Tlačiarne" }
    ]
    readonly property var titles: ({ obrazovky: "Obrazovky", grafika: "Grafická karta", zvuk: "Zvuk", siet: "Sieť", bluetooth: "Wi-Fi a Bluetooth",
                                     napajanie: "Napájanie", disky: "Disky", vstup: "Klávesnica a myš", kamery: "Kamery", tlac: "Tlačiarne",
                                     usb: "USB", pocitac: "Procesor a pamäť", ostatne: "Ostatné zariadenia", siete: "Siete a firewall" })
    // audio jacky zadného panela z prvej zvukovej karty: farba podľa druhu (ako na skutočnom PC)
    readonly property var card0: (cards.cards || [])[0] || null
    readonly property var jacks: card0 ? card0.ports.filter(p => p.type !== "Video").slice(0, 6) : []
    function jackColor(p) { return p.dir === "out" ? "#8BC34A" : (p.type === "Mic" ? "#E68AB0" : (p.type === "Line" ? "#6FA8DC" : "#9E9E9E")); }
    function devFor(dir) {
        if (!card0) return "";
        const id = card0.name.replace("alsa_card.", ""), a = cards.active || {};
        return Object.keys(a).find(k => a[k].kind === (dir === "out" ? "sink" : "source") && !k.endsWith(".monitor") && k.indexOf(id) >= 0) || "";
    }
    function jackOn(p) { const d = devFor(p.dir); return !!d && cards.active[d].port === p.name; }
    function useJack(p) {
        const d = devFor(p.dir);
        if (!d) { status = "Konektor sa nedá prepnúť: zariadenie nie je aktívne"; return; }
        run(["latte-devices", "audio", "port", p.dir === "out" ? "sink" : "source", d, p.name], "Konektor: " + p.desc);
    }

    FloatingWindow {
        id: win
        title: "Správca zariadení — Doska"
        implicitWidth: 1280; implicitHeight: 800
        color: theme.surface
        onClosed: Qt.quit()

        Item {
            id: root
            anchors.fill: parent
            focus: true
            Keys.onEscapePressed: app.pick("")

            HeaderBar {
                id: header
                theme: theme
                anchors { left: parent.left; right: parent.right; top: parent.top }
                title: app.sel ? app.titles[app.sel] || app.sel : "Správca zariadení · Doska"
                canBack: app.sel !== ""
                onBack: app.pick("")
                netVisible: false
                searchPlaceholder: "Nájsť súčiastku"
                onSearchSubmitted: (t) => {
                    const q = t.toLowerCase().trim(); if (!q) return;
                    const g = (app.inv.groups || []).find(g => g.title.toLowerCase().includes(q) || (app.titles[g.key] || "").toLowerCase().includes(q)
                                                         || g.items.some(i => i.name.toLowerCase().includes(q)));
                    if (g) app.pick(g.key); else app.status = "Nenájdené: " + t;
                }
                onCloseRequested: Qt.quit()
            }

            // ── doska ──
            Item {
                id: area
                anchors { left: parent.left; top: header.bottom; bottom: foot.top; right: side.left; margins: 18 }
                readonly property real u: Math.min(width / 100, height / 66)
                readonly property real ox: (width - 100 * u) / 2
                readonly property real oy: (height - 66 * u) / 2
                function px(v) { return ox + v * u; }
                function py(v) { return oy + v * u; }

                // plošný spoj: doska, otvory, mriežka, potlač a spoje (prekreslí sa iba pri zmene veľkosti alebo výberu)
                Canvas {
                    id: pcb
                    anchors.fill: parent
                    onWidthChanged: requestPaint()
                    onHeightChanged: requestPaint()
                    Connections { target: app; function onSelChanged() { pcb.requestPaint(); } function onHotChanged() { pcb.requestPaint(); } function onInvChanged() { pcb.requestPaint(); } }
                    onPaint: {
                        const c = getContext("2d"); c.reset();
                        const u = area.u, X = area.px, Y = area.py, p = theme.primary, f = theme.fg;
                        // doska
                        c.fillStyle = Qt.tint(theme.surface, Qt.rgba(p.r, p.g, p.b, 0.07));
                        c.strokeStyle = Qt.rgba(p.r, p.g, p.b, 0.35); c.lineWidth = 1.5;
                        const r = 2.2 * u; c.beginPath(); c.roundedRect(X(0), Y(0), 100 * u, 66 * u, r, r); c.fill(); c.stroke();
                        // bodová mriežka
                        c.fillStyle = Qt.rgba(f.r, f.g, f.b, 0.05);
                        for (let gx = 12; gx < 99; gx += 2.5) for (let gy = 2; gy < 65; gy += 2.5) c.fillRect(X(gx), Y(gy), 1.2, 1.2);
                        // montážne otvory
                        for (const [hx, hy] of [[12.5, 2.5], [97, 2.5], [12.5, 63.5], [97, 63.5], [58, 32]]) {
                            c.beginPath(); c.arc(X(hx), Y(hy), 1.1 * u, 0, 2 * Math.PI); c.fillStyle = theme.surface; c.fill();
                            c.strokeStyle = Qt.rgba(p.r, p.g, p.b, 0.5); c.lineWidth = 0.4 * u; c.stroke();
                        }
                        // spoje od procesora ku každej súčiastke (zbernica = 3 rovnobežné čiary, vybraná svieti)
                        const cx = 45.5, cy = 16.5;
                        const drawn = {};
                        for (const pt of app.parts) {
                            if (pt.shape === "socket") continue;
                            const tx = pt.x + pt.w / 2, ty = pt.y + pt.h / 2, on = app.sel === pt.key || app.hot === pt.key;
                            c.strokeStyle = Qt.rgba(p.r, p.g, p.b, on ? 0.85 : (app.led(pt.key) === "off" ? 0.10 : 0.22));
                            c.lineWidth = on ? 1.6 : 1;
                            for (let k = -1; k <= 1; k++) {
                                const o = k * 0.7;
                                c.beginPath();
                                // najprv vodorovne, potom zvislo, roh zrezaný pod 45° (ako skutočné spoje)
                                const midY = cy + o, sx = tx > cx ? 1 : -1, sy = ty > midY ? 1 : -1, bend = Math.min(2, Math.abs(ty - midY));
                                c.moveTo(X(cx), Y(midY));
                                c.lineTo(X(tx + o - sx * bend), Y(midY));
                                c.lineTo(X(tx + o), Y(midY + sy * bend));
                                c.lineTo(X(tx + o), Y(ty));
                                c.stroke();
                            }
                        }
                        // spoje zadného panela ku konektorom (obrazovky, USB, sieť, zvuk)
                        c.strokeStyle = Qt.rgba(p.r, p.g, p.b, 0.18); c.lineWidth = 1;
                        for (const [yy, tx, ty] of [[10, 14, 9], [23, 14, 23], [33, 14, 39], [50, 14, 55]]) {
                            c.beginPath(); c.moveTo(X(10), Y(yy)); c.lineTo(X(tx), Y(ty)); c.stroke();
                        }
                        // potlač
                        c.fillStyle = Qt.rgba(f.r, f.g, f.b, 0.30);
                        c.font = "bold " + Math.round(1.5 * u) + "px '" + theme.fontMono + "'";
                        const n = (app.inv.groups || []).reduce((a, g) => a + g.items.length, 0);
                        c.fillText("LATTE-OS  ·  REV 1.0  ·  " + n + " DEV", X(27), Y(64.3));
                    }
                }

                // ── zadný panel (vľavo) ──
                Rectangle {
                    id: io
                    x: area.px(1); y: area.py(3); width: 8.5 * area.u; height: 60 * area.u; radius: area.u
                    color: Qt.tint(theme.surfaceVariant, Qt.rgba(1, 1, 1, 0.06)); border { width: 1; color: theme.outline }
                    Text { anchors { horizontalCenter: parent.horizontalCenter; bottom: parent.top; bottomMargin: 2 } text: "I/O"; color: theme.fgDim
                           font { family: theme.fontMono; pixelSize: Math.max(9, 1.4 * area.u); weight: Font.Bold } }
                    Column {
                        anchors { horizontalCenter: parent.horizontalCenter; top: parent.top; topMargin: 1.2 * area.u }
                        spacing: 1.1 * area.u
                        // obrazovky: HDMI / DP podľa počtu monitorov (aspoň jeden obrys)
                        Repeater {
                            model: Math.max(1, Math.min(2, (app.group("obrazovky") || { items: [] }).items.length))
                            Port {
                                required property int index
                                key: "obrazovky"; w: 6; h: 2.6; lit: app.led("obrazovky") === "ok"
                                tip: "Obrazovka: " + (((app.group("obrazovky") || { items: [] }).items[index] || {}).name || "nepripojená")
                                label: index === 0 ? "HDMI" : "DP"
                            }
                        }
                        Repeater {
                            model: 2
                            Port { key: "usb"; w: 5.2; h: 2.2; lit: app.led("usb") === "ok" || app.led("vstup") === "ok"; label: "USB"
                                   tip: "USB: " + ((app.group("usb") || { items: [] }).items.length ? count((app.group("usb")).items.length) : "nič navyše") }
                        }
                        // sieť: RJ45 s dvoma LED (linka / aktivita)
                        Port {
                            key: "siet"; w: 5.6; h: 5; lit: app.led("siet") === "ok"; label: "LAN"
                            tip: "Sieť: " + (((app.group("siet") || { items: [] }).items[0] || {}).name || "bez pripojenia")
                            Row {
                                anchors { top: parent.top; topMargin: 0.5 * area.u; horizontalCenter: parent.horizontalCenter }
                                spacing: 2.4 * area.u
                                Rectangle { width: 0.9 * area.u; height: width; radius: 1; color: app.led("siet") === "ok" ? "#3FB950" : theme.outline }
                                Rectangle {
                                    width: 0.9 * area.u; height: width; radius: 1; color: "#F0B232"
                                    SequentialAnimation on opacity { running: app.led("siet") === "ok" && win.visible; loops: Animation.Infinite
                                        NumberAnimation { to: 0.2; duration: 380 } NumberAnimation { to: 1; duration: 520 } PauseAnimation { duration: 900 } }
                                    opacity: app.led("siet") === "ok" ? 1 : 0.2
                                }
                            }
                        }
                        Item { width: 1; height: 0.6 * area.u }
                        // audio jacky
                        Repeater {
                            model: app.jacks
                            Rectangle {
                                id: jack
                                required property var modelData
                                readonly property bool on: app.jackOn(modelData)
                                anchors.horizontalCenter: parent.horizontalCenter
                                width: 3.6 * area.u; height: width; radius: width / 2
                                color: app.jackColor(modelData)
                                opacity: modelData.plugged ? 1 : 0.35
                                border { width: on ? 0.55 * area.u : 1; color: on ? theme.fg : Qt.darker(color, 1.6) }
                                Rectangle { anchors.centerIn: parent; width: parent.width * 0.38; height: width; radius: width / 2; color: "#15110E" }
                                Rectangle { visible: jack.on; anchors.centerIn: parent; width: parent.width + 1.4 * area.u; height: width; radius: width / 2
                                            color: "transparent"; border { width: 1.5; color: Qt.rgba(jack.color.r, jack.color.g, jack.color.b, 0.55) } }
                                MouseArea {
                                    anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                                    acceptedButtons: Qt.LeftButton | Qt.RightButton
                                    onEntered: tipBox.show(jack, (jack.on ? "● " : "") + jack.modelData.desc + (jack.modelData.dir === "out" ? " · výstup" : " · vstup") + (jack.on ? " (aktívny)" : " · klik = použiť"))
                                    onExited: tipBox.hide()
                                    onClicked: (m) => {
                                        if (m.button === Qt.RightButton) { const q = mapToItem(root, m.x, m.y);
                                            return menu.open(q.x, q.y, [{ glyph: "plug", label: "Použiť tento konektor", bold: true, enabled: !jack.on, action: () => app.useJack(jack.modelData) },
                                                                        { glyph: "adjustments", label: "Nastavenia zvuku", action: () => app.pick("zvuk") }], jack.modelData.desc); }
                                        app.useJack(jack.modelData); app.pick("zvuk");
                                    }
                                }
                            }
                        }
                    }
                }

                // ── súčiastky ──
                Repeater {
                    model: app.parts
                    Item {
                        id: part
                        required property var modelData
                        readonly property string st: app.led(modelData.key)
                        readonly property bool picked: app.sel === modelData.key
                        readonly property bool over: app.hot === modelData.key
                        x: area.px(modelData.x); y: area.py(modelData.y); width: modelData.w * area.u; height: modelData.h * area.u
                        opacity: st === "off" && !picked ? 0.5 : 1
                        // výber: svetelný obrys
                        Rectangle { anchors.fill: parent; anchors.margins: -0.8 * area.u; radius: area.u; color: "transparent"; visible: part.picked || part.over
                                    border { width: part.picked ? 2 : 1; color: part.st === "bad" ? theme.error : theme.primary } }
                        Canvas {
                            id: art
                            anchors.fill: parent
                            onWidthChanged: requestPaint(); onHeightChanged: requestPaint()
                            property bool lit: part.picked || part.over
                            onLitChanged: requestPaint()
                            onPaint: {
                                const c = getContext("2d"); c.reset();
                                const w = width, h = height, u = area.u, p = theme.primary, s = part.modelData.shape;
                                const body = Qt.tint(theme.surfaceVariant, Qt.rgba(1, 1, 1, 0.04)), edge = lit ? p : theme.outline;
                                const rr = (x, y, ww, hh, r, fill, stroke) => { c.beginPath(); c.roundedRect(x, y, ww, hh, r, r); if (fill) { c.fillStyle = fill; c.fill(); } if (stroke) { c.strokeStyle = stroke; c.lineWidth = 1; c.stroke(); } };
                                if (s === "socket") {
                                    rr(0, 0, w, h, u, body, edge);
                                    c.fillStyle = Qt.rgba(p.r, p.g, p.b, 0.45);
                                    for (let i = 1; i < 14; i++) { const t = i / 14; c.fillRect(t * w, 0.6 * u, 1.2, 1.2); c.fillRect(t * w, h - 0.6 * u - 1, 1.2, 1.2); c.fillRect(0.6 * u, t * h, 1.2, 1.2); c.fillRect(w - 0.6 * u - 1, t * h, 1.2, 1.2); }
                                    rr(w * 0.18, h * 0.18, w * 0.64, h * 0.64, u * 0.6, Qt.tint(theme.surface, Qt.rgba(1, 1, 1, 0.10)), edge);
                                } else if (s === "dimm") {
                                    for (let i = 0; i < 4; i++) { const x = i * w / 4 + w * 0.06; rr(x, 0, w / 4 - w * 0.12, h, u * 0.3, body, edge);
                                        c.fillStyle = Qt.rgba(p.r, p.g, p.b, 0.30); for (let k = 0; k < 6; k++) c.fillRect(x + u * 0.35, h * (0.08 + k * 0.15), w / 4 - w * 0.12 - u * 0.7, h * 0.09); }
                                } else if (s === "gpu") {
                                    rr(0, 0, w, h, u, Qt.tint(theme.surface, Qt.rgba(1, 1, 1, 0.07)), edge);
                                    for (const fx of [0.22, 0.5]) { c.beginPath(); c.arc(w * fx, h / 2, h * 0.38, 0, 2 * Math.PI); c.strokeStyle = Qt.rgba(p.r, p.g, p.b, 0.55); c.lineWidth = 1.2; c.stroke();
                                        for (let b = 0; b < 7; b++) { const a = b * Math.PI * 2 / 7; c.beginPath(); c.moveTo(w * fx, h / 2); c.lineTo(w * fx + Math.cos(a) * h * 0.34, h / 2 + Math.sin(a) * h * 0.34); c.strokeStyle = Qt.rgba(p.r, p.g, p.b, 0.25); c.stroke(); } }
                                    c.fillStyle = Qt.rgba(p.r, p.g, p.b, 0.5); c.fillRect(0, h - 0.5 * u, w * 0.8, 0.5 * u);   // zlaté kontakty
                                } else if (s === "atx") {
                                    rr(0, 0, w, h, u * 0.5, body, edge);
                                    for (let i = 0; i < 12; i++) for (let j = 0; j < 2; j++) rr(w * (0.18 + j * 0.38), h * (0.03 + i * 0.08), w * 0.26, h * 0.06, 1, Qt.rgba(p.r, p.g, p.b, 0.25), null);
                                } else if (s === "m2") {
                                    rr(0, 0, w, h, u * 0.4, body, edge);
                                    for (let i = 0; i < 3; i++) rr(w * (0.12 + i * 0.27), h * 0.2, w * 0.2, h * 0.6, 1, Qt.tint(theme.surface, Qt.rgba(1, 1, 1, 0.12)), null);
                                } else if (s === "sata") {
                                    for (let i = 0; i < 4; i++) rr(0, i * h / 4 + h * 0.04, w, h / 4 - h * 0.08, u * 0.3, body, edge);
                                } else if (s === "pch") {
                                    rr(0, 0, w, h, u * 0.6, body, edge);
                                    c.strokeStyle = Qt.rgba(p.r, p.g, p.b, 0.28); for (let i = 1; i < 8; i++) { c.beginPath(); c.moveTo(w * 0.12, i * h / 8); c.lineTo(w * 0.88, i * h / 8); c.stroke(); }
                                } else if (s === "header") {
                                    rr(0, 0, w, h, u * 0.3, body, edge);
                                    c.fillStyle = Qt.rgba(p.r, p.g, p.b, 0.55); for (let i = 0; i < 5; i++) for (let j = 0; j < 2; j++) c.fillRect(w * (0.12 + i * 0.18), h * (0.22 + j * 0.4), 1.6, 1.6);
                                } else if (s === "module") {
                                    rr(0, 0, w, h, u * 0.5, body, edge);
                                    c.strokeStyle = Qt.rgba(p.r, p.g, p.b, 0.5);   // anténne káble
                                    for (const ay of [0.35, 0.65]) { c.beginPath(); c.arc(w * 0.85, h * ay, u * 0.6, 0, 2 * Math.PI); c.stroke(); }
                                    rr(w * 0.1, h * 0.25, w * 0.45, h * 0.5, 1, Qt.tint(theme.surface, Qt.rgba(1, 1, 1, 0.12)), null);
                                } else {   // čip
                                    rr(0, 0, w, h, u * 0.5, Qt.tint(theme.surface, Qt.rgba(1, 1, 1, 0.10)), edge);
                                    c.fillStyle = Qt.rgba(p.r, p.g, p.b, 0.45);
                                    for (let i = 1; i < 6; i++) { const t = i / 6; c.fillRect(t * w, -1, 1, 2); c.fillRect(t * w, h - 1, 1, 2); c.fillRect(-1, t * h, 2, 1); c.fillRect(w - 1, t * h, 2, 1); }
                                }
                            }
                        }
                        // text na súčiastke (iba ak je dosť miesta) a potlač pod ňou
                        Text {
                            visible: part.width > 9 * area.u && part.height > 6 * area.u
                            anchors.centerIn: parent; width: parent.width * 0.62; horizontalAlignment: Text.AlignHCenter; wrapMode: Text.Wrap; maximumLineCount: 3; elide: Text.ElideRight
                            text: { const g = app.group(part.modelData.key); return part.modelData.shape === "socket" && g && g.items[0] ? g.items[0].name.replace(/\(R\)|\(TM\)|CPU|@.*$/g, "").trim() : part.modelData.title; }
                            color: theme.fg; font { family: theme.fontUi; pixelSize: Math.max(10, 1.35 * area.u); weight: Font.DemiBold }
                        }
                        Text {
                            anchors { left: parent.left; top: parent.bottom; topMargin: 0.3 * area.u }
                            text: part.modelData.code; color: theme.fgDim; opacity: 0.8
                            font { family: theme.fontMono; pixelSize: Math.max(8, 1.15 * area.u); weight: Font.Bold }
                        }
                        // LED stavu
                        Rectangle {
                            x: parent.width - width - 0.5 * area.u; y: -height / 2
                            width: 1.3 * area.u; height: width; radius: width / 2
                            color: part.st === "ok" ? "#3FB950" : (part.st === "bad" ? theme.error : theme.outline)
                            border { width: 1; color: Qt.darker(color, 1.5) }
                            SequentialAnimation on opacity { running: part.st === "bad" && win.visible; loops: Animation.Infinite
                                NumberAnimation { to: 0.25; duration: 500 } NumberAnimation { to: 1; duration: 500 } }
                        }
                        MouseArea {
                            anchors.fill: parent; anchors.margins: -0.6 * area.u; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                            acceptedButtons: Qt.LeftButton | Qt.RightButton
                            onEntered: { app.hot = part.modelData.key; const g = app.group(part.modelData.key);
                                         tipBox.show(part, part.modelData.title + " · " + (g && g.items.length ? (g.items.length === 1 ? g.items[0].name : count(g.items.length)) : "nič nepripojené")); }
                            onExited: { app.hot = ""; tipBox.hide(); }
                            onClicked: (m) => {
                                if (m.button === Qt.RightButton) { const q = mapToItem(root, m.x, m.y), k = part.modelData.key, g = app.group(k);
                                    return menu.open(q.x, q.y, [{ glyph: "adjustments", label: "Otvoriť", bold: true, action: () => app.pick(k) },
                                                                { glyph: "copy", label: "Kopírovať údaje", enabled: !!g && g.items.length > 0,
                                                                  action: () => Quickshell.execDetached(["wl-copy", g.items.map(i => i.name + " — " + (i.sub || "")).join("\n")]) },
                                                                { glyph: "share", label: "Ukázať v Uzloch", action: () => Quickshell.execDetached(["latte-app", "devicapp2", k]) }], part.modelData.title); }
                                app.pick(app.sel === part.modelData.key ? "" : part.modelData.key);
                            }
                        }
                    }
                }

                // bublina
                Rectangle {
                    id: tipBox
                    property string text: ""
                    function show(item, t) { text = t; const q = item.mapToItem(area, item.width / 2, 0); x = Math.max(0, Math.min(area.width - width, q.x - width / 2)); y = Math.max(0, q.y - height - 8); visible = true; }
                    function hide() { visible = false; }
                    visible: false; z: 10
                    width: tt.implicitWidth + 20; height: 28; radius: 8; color: theme.surfaceVariant; border { width: 1; color: theme.primary }
                    Text { id: tt; anchors.centerIn: parent; text: tipBox.text; color: theme.fg; font { family: theme.fontUi; pixelSize: 12 } }
                }
            }

            // ── pravý panel: prehľad alebo ovládanie vybranej súčiastky ──
            Rectangle {
                id: side
                anchors { right: parent.right; top: header.bottom; bottom: foot.top; margins: 14 }
                width: Math.min(470, parent.width * 0.38)
                radius: 18; color: theme.surfaceVariant; border { width: 1; color: theme.outline }

                // prehľad (nič nie je vybrané)
                Flickable {
                    visible: app.sel === ""
                    anchors { fill: parent; margins: 16 }
                    contentHeight: ov.implicitHeight; clip: true; boundsBehavior: Flickable.StopAtBounds
                    Column {
                        id: ov
                        width: parent.width; spacing: 8
                        Text { text: "Prehľad dosky"; color: theme.fg; font { family: theme.fontDisplay; pixelSize: 22; weight: Font.DemiBold } }
                        Text { width: parent.width; wrapMode: Text.WordWrap; text: app.inv.summary || "Načítavam…"
                               color: (app.inv.faults || []).length ? theme.error : theme.fgDim; font { family: theme.fontUi; pixelSize: 13 } }
                        Item { width: 1; height: 4 }
                        Repeater {
                            model: ["obrazovky", "grafika", "zvuk", "siet", "bluetooth", "napajanie", "disky", "vstup", "kamery", "tlac", "usb", "pocitac", "ostatne"]
                                   .filter(k => app.led(k) !== "off")
                            Rectangle {
                                required property string modelData
                                width: ov.width; height: 44; radius: 11
                                color: rm.containsMouse ? theme.hover : theme.field
                                Rectangle { x: 12; anchors.verticalCenter: parent.verticalCenter; width: 10; height: 10; radius: 5
                                            color: app.led(parent.modelData) === "bad" ? theme.error : "#3FB950" }
                                Column {
                                    x: 32; anchors.verticalCenter: parent.verticalCenter; width: parent.width - 44
                                    Text { text: app.titles[parent.parent.modelData]; color: theme.fg; font { family: theme.fontUi; pixelSize: 13; weight: Font.DemiBold } }
                                    Text { width: parent.width; elide: Text.ElideRight; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 11 }
                                           text: { const g = app.group(parent.parent.modelData); return g ? g.items.map(i => i.name).join(" · ") : ""; } }
                                }
                                MouseArea { id: rm; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                                            onEntered: app.hot = parent.modelData; onExited: app.hot = ""; onClicked: app.pick(parent.modelData) }
                            }
                        }
                        Text { topPadding: 8; width: parent.width; wrapMode: Text.WordWrap; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 }
                               text: "Nepripojené: " + ["bluetooth", "kamery", "tlac", "usb", "ostatne"].filter(k => app.led(k) === "off").map(k => app.titles[k].toLowerCase()).join(", ") }
                        Item { width: 1; height: 6 }
                        Text { text: "AUDIO JACKY"; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 11; weight: Font.Bold; letterSpacing: 0.6 } }
                        Row {
                            spacing: 14
                            Repeater {
                                model: [["#8BC34A", "výstup"], ["#E68AB0", "mikrofón"], ["#6FA8DC", "linka"]]
                                Row { required property var modelData; spacing: 6
                                      Rectangle { width: 12; height: 12; radius: 6; color: modelData[0]; anchors.verticalCenter: parent.verticalCenter }
                                      Text { text: modelData[1]; color: theme.fg; font { family: theme.fontUi; pixelSize: 12 } } }
                            }
                        }
                        Text { width: parent.width; wrapMode: Text.WordWrap; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 }
                               text: "Aktívny jack má svetlý okraj. Klik na jack ho použije (napr. slúchadlá vpredu namiesto reproduktorov vzadu)." }
                        Item { width: 1; height: 6 }
                        Rectangle {
                            width: sn.implicitWidth + 60; height: 38; radius: 11; color: nm.containsMouse ? theme.primary : theme.field; border { width: 1; color: theme.primary }
                            Row { anchors.centerIn: parent; spacing: 8
                                  Glyph { name: "shield"; size: 16; color: nm.containsMouse ? theme.fgOnPrimary : theme.primary; anchors.verticalCenter: parent.verticalCenter }
                                  Text { id: sn; text: "Siete, SSH a firewall"; color: nm.containsMouse ? theme.fgOnPrimary : theme.fg; font { family: theme.fontUi; pixelSize: 13; weight: Font.DemiBold } } }
                            MouseArea { id: nm; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: app.pick("siete") }
                        }
                    }
                }

                // ovládanie vybranej súčiastky
                Loader {
                    id: panelLoader
                    active: false
                    anchors { fill: parent; margins: 14 }
                    sourceComponent: SpravcaZariadeni {
                        theme: app.th; compact: true
                        only: app.sel === "siete" ? "siet" : app.sel
                        tab: app.sel === "siete" ? "siete" : "zariadenia"
                        onOpenWindow: (a) => Quickshell.execDetached(a)
                    }
                }
            }

            Item {
                id: foot
                anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
                height: 34
                Text {
                    anchors { left: parent.left; leftMargin: 20; verticalCenter: parent.verticalCenter }
                    color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 }
                    text: app.status || "LED: zelená = funguje · červená = problém · zhasnutá = nič nepripojené · klik na súčiastku = ovládanie · pravý klik = ponuka"
                }
            }

            ContextMenu { id: menu; theme: theme }
        }
    }

    // konektor zadného panela
    component Port: Rectangle {
        id: port
        property string key: ""
        property real w: 5
        property real h: 2.4
        property bool lit: false
        property string label: ""
        property string tip: ""
        anchors.horizontalCenter: parent ? parent.horizontalCenter : undefined
        width: w * area.u; height: h * area.u; radius: 0.35 * area.u
        color: "#15110E"
        border { width: app.sel === key || app.hot === key ? 1.5 : 1; color: app.sel === key || app.hot === key ? theme.primary : (lit ? Qt.rgba(theme.primary.r, theme.primary.g, theme.primary.b, 0.6) : theme.outline) }
        Text { anchors.centerIn: parent; text: port.label; color: port.lit ? theme.primary : theme.fgDim; font { family: theme.fontMono; pixelSize: Math.max(7, 0.95 * area.u); weight: Font.Bold } }
        MouseArea {
            anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
            onEntered: { app.hot = port.key; tipBox.show(port, port.tip); }
            onExited: { app.hot = ""; tipBox.hide(); }
            onClicked: app.pick(port.key)
        }
    }
}
