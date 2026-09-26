// LatteOS — Správca zariadení 2 „Uzly“ (skúšobný návrh 26. 9.). Inšpirácia: Serpantinum od ilyamiro (r/unixporn
// „Hyprland as fluid as it gets“, AGPL-3.0) — panel Bluetooth ako veľký kruh zariadenia so spojenými uzlami okolo.
// Kód je vlastný, prevzatá je iba myšlienka rozloženia.
//   Stred = to, na čo sa pozeráš: počítač → kategória → zariadenie. Okolo sú spojené uzly (kategórie, zariadenia,
//   vlastnosti a akcie). Klik na uzol = ísť doň; ← v hlavičke, reťaz vľavo hore, Esc, Backspace alebo bočné
//   tlačidlo myši = späť. Pravý klik = ponuka. Hľadanie v hlavičke skočí na zariadenie (Enter).
//   Ovládanie (zvuk, obrazovka, Wi-Fi…) sa vysúva sprava — je to ten istý komponent SpravcaZariadeni ako v okne L
//   a v Nastaveniach, nič nie je napísané dvakrát. Dole prepínač Zariadenia / Siete, vpravo dole obnoviť.
// Siete: pripojenia, SSH, firewall a „Sieť okolo“ = inšpektor siete (latte-inspektor, ako ESET Network Inspector):
// router v strede a okolo všetko, čo je v sieti (telefóny, televízory, tlačiarne, receivery…), nové zariadenia sú označené.
// Spúšťa sa: latte-app devicapp2 [siete | okolie | skupina[/zariadenie]][+]   (ikona na ploche; „+“ = hneď vysunúť ovládanie)
import QtQuick
import Quickshell
import Quickshell.Io
import "common"

ShellRoot {
    id: app
    LatteTheme { id: theme }
    readonly property var th: theme

    // ── dáta (priradia sa iba pri zmene, aby sa uzly zbytočne neprekresľovali) ────────────────────────────
    property var inv: ({ groups: [], summary: "", faults: [] })
    property var nets: ({ connections: [], wifi: [], addresses: [] })
    property var sec: ({ ssh: {}, firewall: { zones: [] }, tunnels: [] })
    property string host: "Počítač"
    property string cpu: ""
    component Q: Process {
        id: q
        property var done: null
        property string last: ""
        stdout: StdioCollector { onStreamFinished: { if (this.text === q.last) return; q.last = this.text; try { q.done(JSON.parse(this.text)); } catch (e) {} } }
    }
    Q { id: qInv; command: ["latte-devices", "list"]; done: (d) => app.inv = d }
    Q { id: qNets; command: ["latte-devices", "siete"]; done: (d) => app.nets = d }
    Q { id: qSec; command: ["latte-devices", "bezpecnost"]; done: (d) => app.sec = d }
    // inšpektor siete: posledný sken hneď, nový na požiadanie (uzol „Prehľadať znova“)
    property var insp: ({ ok: false, devices: [], audio: [] })
    Q { id: qInspLast; command: ["latte-inspektor", "posledny"]; running: true; done: (d) => app.insp = d }
    Q { id: qInsp; command: ["latte-inspektor", "sken"]; done: (d) => { app.insp = d; app.status = "Sieť prehľadaná"; } }
    readonly property var kindGlyph: ({ router: "router", tv: "device-tv", audio: "device-speaker", printer: "printer", nas: "server", iot: "bulb",
                                        phone: "device-mobile", pc: "device-desktop", console: "device-gamepad", device: "devices" })
    readonly property var kindName: ({ router: "router", tv: "televízor", audio: "zvuk", printer: "tlačiareň", nas: "úložisko", iot: "inteligentná domácnosť",
                                       phone: "telefón / tablet", pc: "počítač", console: "konzola", device: "zariadenie" })
    function devLabel(d) { const v = d.vendor && d.vendor.indexOf("súkromná") < 0 ? d.vendor : "";
                           return d.name || v || (d.gateway ? "Router" : (d.kind !== "device" ? kindName[d.kind].charAt(0).toUpperCase() + kindName[d.kind].slice(1) : "Neznáme zariadenie")); }
    Process {
        running: true; command: ["sh", "-c", "hostname; grep -m1 'model name' /proc/cpuinfo | sed 's/.*: //'"]
        stdout: StdioCollector { onStreamFinished: { const l = this.text.split("\n"); app.host = l[0] || "Počítač";
                                                     app.cpu = (l[1] || "").replace(/\(R\)|\(TM\)|CPU|@.*$/g, "").replace(/\s+/g, " ").trim(); } }
    }
    function refresh() { for (const q of [qInv, qNets, qSec]) if (!q.running) q.running = true; }
    Timer { interval: 5000; repeat: true; running: true; triggeredOnStart: true; onTriggered: app.refresh() }
    // začiatok podľa argumentu (napr. „zvuk“, „zvuk/Intel 82801AA-ICH“, „siete+“)
    readonly property string arg: (Quickshell.env("LATTE_APP_ARGS") || "").trim()
    Component.onCompleted: {
        let a = arg; const open = a.endsWith("+"); if (open) a = a.slice(0, -1);
        if (a === "siete") view = "siete"; else if (a === "okolie") { view = "siete"; path = ["okolie"]; } else if (a) path = a.split("/").slice(0, 2);
        if (open) Qt.callLater(() => openDrawer(view === "siete" ? "siet" : (path[0] || ""), view, path[1] || ""));
    }

    // ── kde sme ────────────────────────────────────────────────────────────────────────────────────────
    property string view: "zariadenia"          // zariadenia | siete
    property var path: []                       // [] · [skupina] · [skupina, zariadenie] · v Sieťach [] · ["wifi"] · ["okolie"]
    readonly property var grp: view === "zariadenia" && path.length ? (inv.groups || []).find(g => g.key === path[0]) || null : null
    readonly property var dev: path.length > 1 && grp ? grp.items.find(i => i.name === path[1]) || null : null
    function bad(it) { return !!it && !!it.state && it.state !== "ok" && it.state !== "off"; }
    function go(p) { path = p; grow.restart(); }
    function up() { if (drawer.open) { drawer.open = false; return; } if (path.length) go(path.slice(0, -1)); }
    function setView(v) { if (view === v) return; view = v; drawer.open = false; go([]); }
    property real g: 1                          // 0 → 1: uzly vyrastú zo stredu pri každom prechode
    NumberAnimation { id: grow; target: app; property: "g"; from: 0; to: 1; duration: 460; easing.type: Easing.OutCubic }

    function human(n) { n = +n || 0; for (const u of ["B", "kB", "MB", "GB", "TB"]) { if (n < 1024) return (n >= 10 || u === "B" ? Math.round(n) : n.toFixed(1)) + " " + u; n /= 1024; } return n.toFixed(1) + " PB"; }
    function count(n) { return n + (n === 1 ? " zariadenie" : (n >= 2 && n <= 4 ? " zariadenia" : " zariadení")); }
    function copy(t) { Quickshell.execDetached(["wl-copy", t]); status = "Skopírované"; }
    function fix(it) {
        if (it.packages && it.packages.length && !it.repo)
            Quickshell.execDetached(["latte-app", "instalator", "--nazov=Ovládač_" + it.name.replace(/[^\w]+/g, "_").slice(0, 30), "install"].concat(it.packages));
        else Quickshell.execDetached(["latte-app", "aplikacie", "aktualizacie"]);
    }
    property string status: ""
    Timer { running: app.status !== ""; interval: 2500; onTriggered: app.status = "" }

    // stred (hub) a uzly okolo (sats): { glyph, title, sub, kind: "node"|"info"|"action", bad, go: fn, menu: [] }
    readonly property var hub: {
        if (view === "siete") {
            if (path[0] === "wifi") return { glyph: "wifi", title: "Wi-Fi v okolí", sub: (nets.wifi || []).length + " sietí" };
            if (path[0] === "okolie") { const gw = (insp.devices || []).find(d => d.gateway);
                                        return { glyph: "router", title: gw ? devLabel(gw) : "Sieť", sub: (gw ? gw.ip + " · " : "") + (insp.subnet || "") }; }
            const a = (nets.connections || []).filter(c => c.active);
            return { glyph: "world", title: a.length ? "Pripojené" : "Bez pripojenia", sub: a.map(c => c.name).join(" · ") || "žiadne aktívne pripojenie", bad: !a.length };
        }
        if (dev) return { glyph: grp.glyph, title: dev.name, sub: dev.stateTitle || "", bad: bad(dev) };
        if (grp) return { glyph: grp.glyph, title: grp.title, sub: count(grp.items.length), bad: grp.items.some(bad) };
        return { glyph: "device-desktop", title: host, sub: cpu || inv.summary || "", bad: (inv.faults || []).length > 0 };
    }
    readonly property var sats: {
        const out = [];
        if (view === "siete") {
            if (path[0] === "okolie") {
                // ako ESET Network Inspector: router v strede, okolo všetko v sieti; tento počítač zvýraznený
                if (insp.me) out.push({ glyph: "device-desktop", title: "Tento počítač", sub: insp.me.ip + " · ↓ " + human(insp.me.rx) + " ↑ " + human(insp.me.tx), kind: "action",
                                        go: () => openDrawer("siet", "siete", "") });
                for (const d of (insp.devices || []).filter(d => !d.gateway).slice(0, 10))
                    out.push({ glyph: kindGlyph[d.kind] || "devices", title: (d.new ? "● " : "") + devLabel(d), sub: d.ip + " · " + (kindName[d.kind] || ""),
                               bad: d.new, go: () => openDrawer("siet", "siete", ""),
                               menu: [{ glyph: "world", label: "Otvoriť webové rozhranie", action: () => Quickshell.execDetached(["xdg-open", "http://" + d.ip]) },
                                      { glyph: "copy", label: "Kopírovať IP adresu", action: () => copy(d.ip) }] });
                out.push({ glyph: "radar", title: qInsp.running ? "Prehľadávam…" : "Prehľadať znova", sub: insp.time ? "naposledy " + new Date(insp.time * 1000).toLocaleTimeString(Qt.locale(), "HH:mm") : "ešte nikdy",
                           kind: "action", go: () => { qInsp.last = ""; qInsp.running = true; } });
                return out;
            }
            if (path[0] === "wifi") {
                for (const w of (nets.wifi || []).slice(0, 12))
                    out.push({ glyph: "wifi", title: w.ssid, sub: (w.security ? "zabezpečená · " : "otvorená · ") + w.signal + " %", kind: w.inUse ? "action" : "node",
                               go: () => openDrawer("siet", "siete", "") });
                return out;
            }
            for (const c of (nets.connections || []))
                out.push({ glyph: c.vpn ? "lock" : (c.type === "Wi-Fi" ? "wifi" : "network"), title: c.name,
                           sub: c.type + (c.device ? " · " + c.device : "") + (c.active ? " · pripojené" : ""), kind: c.active ? "action" : "node",
                           go: () => openDrawer("siet", "siete", ""),
                           menu: [{ glyph: "plug", label: c.active ? "Odpojiť" : "Pripojiť", bold: true,
                                    action: () => Quickshell.execDetached(["latte-devices", "siet", c.active ? "odpoj" : "pripoj", c.name]) }] });
            out.push({ glyph: "radar", title: "Sieť okolo", sub: insp.ok ? (insp.devices || []).length + " zariadení · inšpektor" : "prehľadať sieť", kind: "action",
                       go: () => { if (!insp.ok && !qInsp.running) qInsp.running = true; go(["okolie"]); } });
            if ((nets.wifi || []).length) out.push({ glyph: "wifi", title: "Wi-Fi v okolí", sub: nets.wifi.length + " sietí", go: () => go(["wifi"]) });
            const ssh = sec.ssh || {};
            out.push({ glyph: "terminal", title: "SSH server", sub: ssh.active ? "beží na porte " + (ssh.port || 22) : "vypnutý", go: () => openDrawer("siet", "siete", "") });
            const fw = sec.firewall || {};
            out.push({ glyph: "shield", title: "Firewall", sub: fw.active ? "zapnutý · " + (fw.default || "") : "vypnutý", bad: !fw.active, go: () => openDrawer("siet", "siete", "") });
            for (const t of (sec.tunnels || [])) out.push({ glyph: "network", title: t.name || "Tunel", sub: t.kind || "tunel", go: () => openDrawer("siet", "siete", "") });
            for (const a of (nets.addresses || []).slice(0, 3)) out.push({ glyph: "info-circle", title: a.split(" ")[1] || a, sub: "adresa · " + a.split(" ")[0], kind: "info",
                                                                         go: () => copy(a.split(" ")[1] || a) });
            return out;
        }
        if (dev) {
            out.push({ glyph: "info-circle", title: dev.sub || "—", sub: "popis", kind: "info", go: () => copy(dev.sub || "") });
            const d = dev.details || {};
            const sk = { connected: "pripojené", disconnected: "odpojené", unavailable: "nedostupné", unmanaged: "nespravované" };
            for (const k of Object.keys(d).slice(0, 7)) out.push({ glyph: "info-circle", title: sk[d[k]] || String(d[k]), sub: k, kind: "info", go: () => copy(String(d[k])) });
            if (bad(dev)) out.push({ glyph: "alert-triangle", title: "Opraviť", sub: dev.reason || dev.stateTitle, kind: "action", bad: true, go: () => fix(dev) });
            out.push({ glyph: "adjustments", title: "Ovládanie", sub: "nastavenia ovládača", kind: "action", go: () => openDrawer(grp.key, "zariadenia", dev.name) });
            return out;
        }
        if (grp) {
            for (const it of grp.items.slice(0, 11))
                out.push({ glyph: grp.glyph, title: it.name, sub: it.sub || it.stateTitle, bad: bad(it), go: () => go([grp.key, it.name]),
                           menu: [{ glyph: "adjustments", label: "Ovládanie", action: () => openDrawer(grp.key, "zariadenia", it.name) },
                                  { glyph: "copy", label: "Kopírovať údaje", action: () => copy(it.name + "\n" + (it.sub || "") + "\n" + Object.keys(it.details || {}).map(k => k + ": " + it.details[k]).join("\n")) }] });
            out.push({ glyph: "adjustments", title: "Ovládanie", sub: grp.title.toLowerCase(), kind: "action", go: () => openDrawer(grp.key, "zariadenia", "") });
            return out;
        }
        for (const gg of present) out.push({ glyph: gg.glyph, title: gg.title, sub: gg.items.length === 1 ? gg.items[0].name : count(gg.items.length),
                                             bad: gg.items.some(bad), go: () => go([gg.key]),
                                             menu: [{ glyph: "adjustments", label: "Ovládanie", action: () => openDrawer(gg.key, "zariadenia", "") }] });
        return out;
    }
    readonly property var order: ["obrazovky", "grafika", "zvuk", "siet", "bluetooth", "napajanie", "disky", "vstup", "kamery", "tlac", "usb", "pocitac", "ostatne"]
    readonly property var present: order.map(k => (inv.groups || []).find(x => x.key === k)).filter(x => x && x.items.length)
    readonly property var absent: order.map(k => (inv.groups || []).find(x => x.key === k)).filter(x => x && !x.items.length)
    // reťaz (drobné spojené uzly vľavo hore): kde som a cesta späť
    readonly property var crumbs: {
        if (view === "siete") return path.length ? [{ glyph: "world", p: [] }, { glyph: path[0] === "okolie" ? "router" : "wifi", p: path }] : [];
        const c = [];
        if (path.length) c.push({ glyph: "device-desktop", p: [] });
        if (grp) c.push({ glyph: grp.glyph, p: [grp.key] });
        if (dev) c.push({ glyph: "info-circle", p: [grp.key, dev.name] });
        return c;
    }

    // ── ovládanie vysunuté sprava (SpravcaZariadeni) ────────────────────────────────────────────────────
    function openDrawer(group, tab, item) {
        dmLoader.active = false;
        drawer.group = group; drawer.tab = tab; drawer.item = item;
        dmLoader.active = true; drawer.open = true;
    }

    FloatingWindow {
        id: win
        title: "Správca zariadení — Uzly"
        implicitWidth: 1180; implicitHeight: 780
        color: theme.surface
        onClosed: Qt.quit()

        Item {
            id: root
            anchors.fill: parent
            focus: true
            Keys.onEscapePressed: app.up()
            Keys.onPressed: (e) => { if (e.key === Qt.Key_Backspace) { app.up(); e.accepted = true; } }

            HeaderBar {
                id: header
                theme: theme
                anchors { left: parent.left; right: parent.right; top: parent.top }
                title: app.view === "siete" ? "Siete" : (app.dev ? app.dev.name : (app.grp ? app.grp.title : "Správca zariadení"))
                canBack: app.path.length > 0 || drawer.open
                onBack: app.up()
                netVisible: false
                searchPlaceholder: "Nájsť zariadenie"
                onSearchSubmitted: (t) => {
                    const q = t.toLowerCase().trim(); if (!q) return;
                    for (const gg of app.present) for (const it of gg.items)
                        if (it.name.toLowerCase().includes(q) || (it.sub || "").toLowerCase().includes(q)) { app.view = "zariadenia"; app.go([gg.key, it.name]); return; }
                    const gg = app.present.find(x => x.title.toLowerCase().includes(q));
                    if (gg) { app.view = "zariadenia"; app.go([gg.key]); } else app.status = "Nenájdené: " + t;
                }
                onCloseRequested: Qt.quit()
            }

            // plocha grafu (pri vysunutom ovládaní sa posunie doľava)
            Item {
                id: stage
                anchors { left: parent.left; top: header.bottom; bottom: foot.top }
                width: parent.width - (drawer.open ? drawer.width : 0)
                Behavior on width { NumberAnimation { duration: 260; easing.type: Easing.OutCubic } }
                clip: true

                readonly property real cx: width / 2
                readonly property real cy: height / 2 + 6
                readonly property real hubD: Math.min(200, height * 0.3)
                readonly property real rx: Math.max(hubD * 0.9, Math.min(width * 0.37, width / 2 - 125))
                readonly property real ry: Math.max(hubD * 0.75, height / 2 - 48)
                function spot(i, n) {
                    // rovnomerne po elipse od vrchu v smere hodinových ručičiek; jeden uzol vpravo, dva vľavo/vpravo
                    const a = n === 1 ? 0 : (n === 2 ? Math.PI * i : -Math.PI / 2 + i * 2 * Math.PI / n);
                    return { x: cx + rx * Math.cos(a), y: cy + ry * Math.sin(a) };
                }

                // svätožiara a spojnice (Canvas: funguje aj pri softvérovom kreslení)
                Canvas {
                    id: wires
                    anchors.fill: parent
                    property real g: app.g
                    onGChanged: requestPaint()
                    onWidthChanged: requestPaint()
                    onHeightChanged: requestPaint()
                    Connections { target: app; function onSatsChanged() { wires.requestPaint(); } function onViewChanged() { wires.requestPaint(); } }
                    onPaint: {
                        const c = getContext("2d"); c.reset();
                        const p = theme.primary, e = theme.error;
                        const cx = stage.cx, cy = stage.cy;
                        // mäkké sústredné kruhy okolo stredu (ako v Serpantinum)
                        for (const [r, a] of [[stage.hubD * 0.75, 0.10], [stage.hubD * 1.25, 0.06], [stage.hubD * 1.9, 0.045], [stage.hubD * 2.7, 0.03]]) {
                            c.beginPath(); c.arc(cx, cy, r * (0.7 + 0.3 * g), 0, 2 * Math.PI);
                            c.fillStyle = Qt.rgba(p.r, p.g, p.b, a * g); c.fill();
                        }
                        const n = app.sats.length;
                        for (let i = 0; i < n; i++) {
                            const s = app.sats[i], t = stage.spot(i, n);
                            const x1 = cx, y1 = cy, x2 = cx + (t.x - cx) * g, y2 = cy + (t.y - cy) * g;
                            const dx = x2 - x1, dy = y2 - y1, L = Math.sqrt(dx * dx + dy * dy); if (L < 4) continue;
                            const nx = -dy / L, ny = dx / L;
                            const col = s.bad ? e : p;
                            c.strokeStyle = Qt.rgba(col.r, col.g, col.b, s.kind === "info" ? 0.35 : 0.6);
                            c.lineWidth = s.kind === "action" ? 2 : 1.5;
                            c.beginPath();
                            // od okraja stredu po uzol; v strede spojnice malá vlnka (ako „blesk“ v predlohe)
                            const k0 = (stage.hubD / 2 + 6) / L;
                            for (let k = k0; k <= 1.0001; k += 0.02) {
                                const w = (k > 0.45 && k < 0.62) ? Math.sin((k - 0.45) / 0.17 * Math.PI * 2) * 5 : 0;
                                const x = x1 + dx * k + nx * w, y = y1 + dy * k + ny * w;
                                if (k === k0) c.moveTo(x, y); else c.lineTo(x, y);
                            }
                            c.stroke();
                        }
                    }
                }

                // stred
                Item {
                    id: hubItem
                    width: stage.hubD; height: width
                    x: stage.cx - width / 2; y: stage.cy - height / 2
                    scale: 0.82 + 0.18 * app.g
                    Rectangle { anchors.centerIn: parent; width: parent.width + 34; height: width; radius: width / 2
                                color: "transparent"; border { width: 10; color: Qt.rgba(ring.color.r, ring.color.g, ring.color.b, 0.22) } }
                    Rectangle {
                        id: ring
                        anchors.fill: parent; radius: width / 2
                        color: app.hub.bad ? theme.error : theme.primary
                        Column {
                            anchors.centerIn: parent; width: parent.width - 36; spacing: 3
                            Glyph { anchors.horizontalCenter: parent.horizontalCenter; name: app.hub.glyph; size: 30; color: theme.fgOnPrimary }
                            Text { width: parent.width; horizontalAlignment: Text.AlignHCenter; text: app.hub.title; color: theme.fgOnPrimary
                                   wrapMode: Text.Wrap; maximumLineCount: 2; elide: Text.ElideRight
                                   font { family: theme.fontUi; pixelSize: 15; weight: Font.Bold } }
                            Text { width: parent.width; horizontalAlignment: Text.AlignHCenter; text: app.hub.sub; color: theme.fgOnPrimary; opacity: 0.8
                                   wrapMode: Text.Wrap; maximumLineCount: 2; elide: Text.ElideRight; font { family: theme.fontUi; pixelSize: 11 } }
                        }
                    }
                    MouseArea {
                        anchors.fill: parent; acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.BackButton; cursorShape: Qt.PointingHandCursor
                        onClicked: (m) => {
                            if (m.button === Qt.BackButton) return app.up();
                            if (m.button === Qt.RightButton) {
                                const q = mapToItem(root, m.x, m.y);
                                return menu.open(q.x, q.y, [{ glyph: "arrow-left", label: "Späť", enabled: app.path.length > 0, action: () => app.up() },
                                                           { glyph: "adjustments", label: "Ovládanie", enabled: !!app.grp || app.view === "siete",
                                                             action: () => app.openDrawer(app.grp ? app.grp.key : "siet", app.view, app.dev ? app.dev.name : "") },
                                                           { glyph: "refresh", label: "Obnoviť", action: () => app.refresh() }], app.hub.title);
                            }
                            // klik na stred: o úroveň vyššie (ako „hore“ v Prieskumníkovi), v koreni ovládanie
                            if (app.path.length) app.up(); else if (app.view === "siete") app.openDrawer("siet", "siete", "");
                        }
                    }
                }

                // uzly okolo
                Repeater {
                    model: app.sats
                    Rectangle {
                        id: node
                        required property var modelData
                        required property int index
                        readonly property var t: stage.spot(index, app.sats.length)
                        readonly property bool act: modelData.kind === "action"
                        width: modelData.kind === "info" ? 230 : 204; height: 56; radius: 16
                        x: stage.cx + (t.x - stage.cx) * app.g - width / 2
                        y: stage.cy + (t.y - stage.cy) * app.g - height / 2
                        opacity: app.g
                        scale: (0.6 + 0.4 * app.g) * (ma.containsMouse ? 1.04 : 1)
                        Behavior on scale { NumberAnimation { duration: 120 } }
                        // nepriehľadné, aby spojnica končila na okraji karty
                        color: act ? Qt.tint(theme.surfaceVariant, Qt.rgba(theme.primary.r, theme.primary.g, theme.primary.b, 0.16))
                                   : (modelData.kind === "info" ? Qt.tint(theme.surface, Qt.rgba(1, 1, 1, 0.03)) : theme.surfaceVariant)
                        border { width: ma.containsMouse || act || modelData.bad ? 1.5 : 1
                                 color: modelData.bad ? theme.error : (ma.containsMouse || act ? theme.primary : theme.outline) }
                        Rectangle {
                            id: ico
                            x: 9; anchors.verticalCenter: parent.verticalCenter; width: 38; height: 38; radius: 12
                            color: node.modelData.bad ? Qt.rgba(theme.error.r, theme.error.g, theme.error.b, 0.2) : theme.field
                            Glyph { anchors.centerIn: parent; name: node.modelData.bad ? "alert-triangle" : node.modelData.glyph; size: 19
                                    color: node.modelData.bad ? theme.error : theme.primary }
                        }
                        Column {
                            id: lbl
                            anchors { left: ico.right; leftMargin: 9; right: parent.right; rightMargin: 10; verticalCenter: parent.verticalCenter }
                            spacing: 1
                            Text { width: parent.width; text: node.modelData.title; elide: Text.ElideRight; color: theme.fg
                                   font { family: node.modelData.kind === "info" ? theme.fontMono : theme.fontUi; pixelSize: 13; weight: Font.DemiBold } }
                            Text { width: parent.width; text: node.modelData.sub || ""; elide: Text.ElideRight; color: theme.fgDim; visible: text !== ""
                                   font { family: theme.fontUi; pixelSize: 11 } }
                        }
                        MouseArea {
                            id: ma
                            anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                            acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.BackButton
                            onClicked: (m) => {
                                if (m.button === Qt.BackButton) return app.up();
                                if (m.button === Qt.RightButton) {
                                    const q = mapToItem(root, m.x, m.y), d = node.modelData;
                                    return menu.open(q.x, q.y, [{ glyph: d.glyph, label: d.kind === "info" ? "Kopírovať" : "Otvoriť", bold: true, action: d.go }]
                                                     .concat(d.menu || []).concat([{ separator: true }, { glyph: "copy", label: "Kopírovať text", action: () => app.copy(d.title + (d.sub ? " · " + d.sub : "")) }]), d.title);
                                }
                                node.modelData.go();
                            }
                        }
                    }
                }

                // reťaz vľavo hore: drobné spojené uzly = cesta späť
                Row {
                    x: 18; y: 14; spacing: 0
                    visible: app.crumbs.length > 0
                    Repeater {
                        model: app.crumbs
                        Row {
                            required property var modelData
                            required property int index
                            Rectangle { visible: index > 0; width: 18; height: 2; anchors.verticalCenter: parent.verticalCenter
                                        color: Qt.rgba(theme.primary.r, theme.primary.g, theme.primary.b, 0.6) }
                            Rectangle {
                                readonly property bool last: index === app.crumbs.length - 1
                                width: 34; height: 34; radius: 17
                                color: last ? theme.primary : (cm.containsMouse ? theme.hover : theme.surfaceVariant)
                                border { width: 1; color: theme.primary }
                                Glyph { anchors.centerIn: parent; name: modelData.glyph; size: 16; color: parent.last ? theme.fgOnPrimary : theme.primary }
                                MouseArea { id: cm; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: app.go(modelData.p) }
                            }
                        }
                    }
                }
            }

            // ── dolný pruh: stav · prepínač Zariadenia / Siete · obnoviť ──
            Item {
                id: foot
                anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
                height: 64
                Text {
                    anchors { left: parent.left; leftMargin: 20; verticalCenter: parent.verticalCenter; right: seg.left; rightMargin: 16 }
                    elide: Text.ElideRight; color: (app.inv.faults || []).length ? theme.error : theme.fgDim
                    font { family: theme.fontUi; pixelSize: 12 }
                    text: app.status || (app.view === "zariadenia"
                          ? app.inv.summary + (app.absent.length && !app.path.length ? " · nepripojené: " + app.absent.map(x => x.title.toLowerCase()).join(", ") : "")
                          : (app.nets.addresses || []).join(" · "))
                }
                Rectangle {
                    id: seg
                    anchors.centerIn: parent
                    width: segRow.width + 8; height: 42; radius: 14; color: theme.surfaceVariant; border { width: 1; color: theme.outline }
                    Row {
                        id: segRow
                        anchors.centerIn: parent; spacing: 4
                        Repeater {
                            model: [["zariadenia", "Zariadenia", "cpu"], ["siete", "Siete", "network"]]
                            Rectangle {
                                required property var modelData
                                readonly property bool on: app.view === modelData[0]
                                width: sl.implicitWidth + 52; height: 34; radius: 11
                                color: on ? theme.primary : (sm.containsMouse ? theme.hover : "transparent")
                                Behavior on color { ColorAnimation { duration: 160 } }
                                Row {
                                    anchors.centerIn: parent; spacing: 8
                                    Glyph { name: modelData[2]; size: 15; color: parent.parent.on ? theme.fgOnPrimary : theme.fgDim; anchors.verticalCenter: parent.verticalCenter }
                                    Text { id: sl; text: modelData[1]; color: parent.parent.on ? theme.fgOnPrimary : theme.fg
                                           font { family: theme.fontUi; pixelSize: 13; weight: Font.DemiBold } anchors.verticalCenter: parent.verticalCenter }
                                }
                                MouseArea { id: sm; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: app.setView(modelData[0]) }
                            }
                        }
                    }
                }
                Rectangle {
                    anchors { right: parent.right; rightMargin: 20; verticalCenter: parent.verticalCenter }
                    width: 42; height: 42; radius: 21; color: rm.containsMouse ? theme.primary : theme.surfaceVariant; border { width: 1; color: theme.primary }
                    Glyph { anchors.centerIn: parent; name: "refresh"; size: 18; color: rm.containsMouse ? theme.fgOnPrimary : theme.primary }
                    MouseArea { id: rm; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                                onClicked: { for (const q of [qInv, qNets, qSec]) q.last = ""; app.refresh(); app.status = "Obnovené"; } }
                }
            }

            // ── vysúvané ovládanie ──
            Rectangle {
                id: drawer
                property bool open: false
                property string group: ""
                property string tab: "zariadenia"
                property string item: ""
                width: Math.min(540, parent.width * 0.48)
                anchors { top: header.bottom; bottom: foot.top }
                x: open ? parent.width - width : parent.width
                Behavior on x { NumberAnimation { duration: 260; easing.type: Easing.OutCubic } }
                visible: x < parent.width
                color: theme.surfaceVariant; radius: 18
                border { width: 1; color: theme.outline }
                Row {
                    id: dh
                    x: 18; y: 12; spacing: 10
                    Glyph { name: "adjustments"; size: 18; color: theme.primary; anchors.verticalCenter: parent.verticalCenter }
                    Text { text: "Ovládanie" + (drawer.item ? " · " + drawer.item : ""); color: theme.fg; width: drawer.width - 110; elide: Text.ElideRight
                           font { family: theme.fontUi; pixelSize: 14; weight: Font.Bold } anchors.verticalCenter: parent.verticalCenter }
                }
                Rectangle {
                    anchors { right: parent.right; rightMargin: 12; top: parent.top; topMargin: 8 }
                    width: 32; height: 32; radius: 10; color: xm.containsMouse ? theme.hover : "transparent"
                    Glyph { anchors.centerIn: parent; name: "x"; size: 16; color: theme.fgDim }
                    MouseArea { id: xm; anchors.fill: parent; hoverEnabled: true; onClicked: drawer.open = false }
                }
                Loader {
                    id: dmLoader
                    active: false
                    anchors { left: parent.left; right: parent.right; top: dh.bottom; bottom: parent.bottom; margins: 14 }
                    sourceComponent: SpravcaZariadeni {
                        theme: app.th; compact: true
                        only: drawer.group; tab: drawer.tab; wantItem: drawer.item
                        active: drawer.open
                        onOpenWindow: (a) => Quickshell.execDetached(a)
                    }
                }
            }

            ContextMenu { id: menu; theme: theme }
        }
    }
}
