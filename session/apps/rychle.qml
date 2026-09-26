// LatteOS — Správca zariadení v okne v tvare L z pravého rohu lišty (zadanie 26. 9.; tvar L zrkadlovo vpravo, common/LPopup.qml).
// Hore karty Zariadenia / Siete, dlaždice hardvéru a detail so softvérom ovládačov (common/SpravcaZariadeni.qml, rovnaký
// ako samostatné okno a stránky Nastavení). Dole pás (kmeň L, textúra aj GIF): keď nie je nič vybrané, základné voľby
// hardvéru — hlasitosť a mikrofón, Wi-Fi, Bluetooth, jas, batéria a režim výkonu, nočné svetlo, bezpečné odobratie USB;
// po výbere kategórie alebo zariadenia jeho stav a akcie. Beží na pozadí, prepína latte-rychle (klik na rohovú dlaždicu).
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import "common"

ShellRoot {
    id: rq
    LatteTheme { id: theme }

    property bool open: (Quickshell.env("LATTE_APP_ARGS") || "").includes("--ukaz")
    IpcHandler {
        target: "rychle"
        function prepni(): void { rq.open = !rq.open; }
        function otvor(): void { rq.open = true; }
        function zavri(): void { rq.open = false; }
    }
    readonly property string cfg: (Quickshell.env("XDG_CONFIG_HOME") || ((Quickshell.env("HOME") || "") + "/.config")) + "/latteos"
    readonly property string stateDir: (Quickshell.env("XDG_STATE_HOME") || ((Quickshell.env("HOME") || "") + "/.local/state")) + "/latteos"
    readonly property string runDir: (Quickshell.env("XDG_RUNTIME_DIR") || "/tmp") + "/latteos"

    // päta = posledný ostrov na lište (Zariadenia)
    property var foot: ({ x: (Quickshell.screens.length ? Quickshell.screens[0].width : 1920) - 196, y: (Quickshell.screens.length ? Quickshell.screens[0].height : 1080) - 56, w: 184, h: 42 })
    FileView { path: rq.runDir + "/ostrovy.json"; printErrors: false; watchChanges: true; onFileChanged: reload()
               onLoaded: { try { const l = JSON.parse(text()); if (l.length) { rq.foot = l[l.length - 1]; rq.islands = l; } } catch (e) {} } }
    property var islands: []
    // textúra: vlastná pre pravé L (bar-scene-vpravo), inak spoločná bar-scene
    property string sceneAll: "para"
    property string sceneRight: ""
    property string barMotion: "vzdy"
    property real dim: 0.55
    FileView { path: rq.cfg + "/bar-scene"; printErrors: false; watchChanges: true; onFileChanged: reload(); onLoaded: rq.sceneAll = text().trim() || "para"; onLoadFailed: rq.sceneAll = "para" }
    FileView { path: rq.cfg + "/bar-scene-vpravo"; printErrors: false; watchChanges: true; onFileChanged: reload(); onLoaded: rq.sceneRight = text().trim(); onLoadFailed: rq.sceneRight = "" }
    FileView { path: rq.cfg + "/bar-anim"; printErrors: false; watchChanges: true; onFileChanged: reload()
               onLoadFailed: rq.barMotion = "vzdy"; onLoaded: { rq.barAnimRaw = text().trim(); rq.barMotion = ({ vypnuty: "vypnute", vypnute: "vypnute" })[rq.barAnimRaw] || "vzdy"; } }
    property string barAnimRaw: ""
    FileView { path: rq.cfg + "/bar-stlmenie"; printErrors: false; watchChanges: true; onFileChanged: reload()
               onLoaded: { const v = parseFloat(text()); rq.dim = isNaN(v) ? 0.55 : Math.max(0, Math.min(0.9, v)); } }

    // ── stav pre pás (základné voľby) ───────────────────────────────────────────────
    property var wifi: null
    property string ssid: ""
    property string wired: ""
    property var bt: null
    property bool btAvail: true
    property bool night: false
    property var volume: null
    property bool muted: false
    property bool micMuted: false
    property bool hasMic: false
    property var brightness: null
    property string profile: ""
    property var profiles: []
    property bool game: false
    property var battery: null               // { pct, state } alebo null (bez batérie)
    property var usbDrives: []               // [{ path, label }] vymeniteľné disky (bezpečné odobratie)

    component Q: Process {
        id: q
        property var done: null
        property string out: ""
        property int code: 0
        property int parts: 0
        function part() { if (++parts === 2 && done) done(out, code); }
        onRunningChanged: if (running) parts = 0
        stdout: StdioCollector { onStreamFinished: { q.out = this.text; q.part(); } }
        onExited: (c) => { q.code = c; q.part(); }
    }
    Q { id: qWifi; command: ["sh", "-c", "nmcli -t -f WIFI radio; nmcli -t -f ACTIVE,SSID dev wifi list --rescan no 2>/dev/null | sed -n 's/^yes://p' | head -1; echo ---; nmcli -t -f TYPE,STATE,CONNECTION dev 2>/dev/null | sed -n 's/^ethernet:connected://p' | head -1"]
        done: (o) => { const [a, b] = o.split("---\n"); const l = a.split("\n"); rq.wifi = l[0].trim() === "enabled"; rq.ssid = (l[1] || "").trim(); rq.wired = (b || "").trim(); } }
    Q { id: qBt; command: ["noctalia", "msg", "bluetooth-status"]; done: (o, c) => { rq.btAvail = c === 0 && !/unavailable|no adapter/i.test(o); rq.bt = c === 0 && /\bon\b|true|enabled/i.test(o); } }
    Q { id: qNight; command: ["noctalia", "msg", "nightlight-status"]; done: (o, c) => { const s = o.toLowerCase(); rq.night = c === 0 && (s.includes("on") || s.includes("true")); } }
    Q { id: qVol; command: ["sh", "-c", "wpctl get-volume @DEFAULT_AUDIO_SINK@; echo ---; wpctl get-volume @DEFAULT_AUDIO_SOURCE@"]
        done: (o) => { const [a, b] = o.split("---\n"); const m = a.match(/Volume: ([\d.]+)/); rq.volume = m ? Math.round(parseFloat(m[1]) * 100) : null; rq.muted = a.includes("MUTED");
                       rq.hasMic = /Volume:/.test(b || ""); rq.micMuted = (b || "").includes("MUTED"); } }
    Q { id: qBri; command: ["brightnessctl", "-m", "-c", "backlight"]; done: (o, c) => { const m = o.match(/,(\d+)%,/); rq.brightness = c === 0 && m ? parseInt(m[1]) : null; } }
    Q { id: qProf; command: ["sh", "-c", "powerprofilesctl get 2>/dev/null; echo ---; powerprofilesctl list 2>/dev/null | sed -n 's/^[* ] *\\([a-z-]*\\):$/\\1/p'; echo ---; cat \"$1/game-mode\" 2>/dev/null", "sh", rq.stateDir]
        done: (o) => { const p = o.split("---\n"); rq.profile = p[0].trim(); rq.profiles = (p[1] || "").split("\n").filter(x => x).reverse(); rq.game = (p[2] || "").trim() === "1"; } }
    Q { id: qBat; command: ["sh", "-c", "for b in /sys/class/power_supply/BAT*; do [ -r \"$b/capacity\" ] && { cat \"$b/capacity\"; cat \"$b/status\"; break; }; done"]
        done: (o) => { const m = o.match(/(\d+)\s+(\w+)/); rq.battery = m ? { pct: parseInt(m[1]), state: m[2] } : null; } }
    Q { id: qUsb; command: ["lsblk", "-J", "-o", "PATH,RM,TRAN,TYPE,LABEL,MOUNTPOINT,MODEL"]
        done: (o) => { try { const out = [], walk = (l) => { for (const d of l) { if (d.type === "disk" && (d.rm || d.tran === "usb")) out.push({ path: d.path, label: d.label || d.model || d.path });
                                                                               if (d.children) walk(d.children); } };
                             walk(JSON.parse(o).blockdevices || []); rq.usbDrives = out; } catch (e) {} } }
    function refresh() { for (const p of [qWifi, qBt, qNight, qVol, qBri, qProf, qBat, qUsb]) if (!p.running) p.running = true; }
    onOpenChanged: { if (open) refresh(); else { dmv.group = ""; dmv.tab = "zariadenia"; dmv.sel = null; } }
    Timer { interval: 3000; repeat: true; running: rq.open; onTriggered: rq.refresh() }
    Process { id: act; onExited: rq.refresh() }
    function run(argv) { act.running = false; act.command = argv; act.running = true; }
    Process { id: det }
    function detached(argv) { rq.open = false; det.command = argv; det.startDetached(); }
    readonly property var profileNames: ({ "power-saver": "Úsporný", balanced: "Vyvážený", performance: "Výkon" })

    // GIF / obrázok priamo v ostrove na lište, súvislý s pätou okna L (Noctalia sama GIF nekreslí)
    TileOverlay {
        id: tile
        theme: theme
        foot: rq.foot; spec: rq.sceneRight || rq.sceneAll; mirror: true
        motion: rq.barAnimRaw === "vzdy" ? "vzdy" : "vypnute"; popupOpen: rq.open
        canvasW: lpop.panelW; canvasH: lpop.sceneH; ox: lpop.footOx; oy: lpop.trunkH
    }
    PanelWindow {
        visible: rq.open || lpop.p > 0
        anchors { top: true; bottom: true; left: true; right: true }
        exclusionMode: ExclusionMode.Ignore
        WlrLayershell.layer: WlrLayer.Overlay
        WlrLayershell.namespace: "latte-rychle"
        WlrLayershell.keyboardFocus: rq.open ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None
        color: "transparent"
        MouseArea { anchors.fill: parent; acceptedButtons: Qt.AllButtons; onPressed: rq.open = false }

        LPopup {
            id: lpop
            theme: theme
            foot: rq.foot; islands: rq.islands
            side: "right"
            open: rq.open
            panelW: 660; panelH: 590; trunkH: 54
            sceneSpec: rq.sceneRight || rq.sceneAll; motion: rq.barMotion; dim: rq.dim; footGlyph: "adjustments"; image: tile.image; frameDir: tile.frameDir; frameCount: tile.frameCount; ohnisko: tile.ohnisko
            trunk: [
                // ── pás: základné voľby hardvéru (nič nie je vybrané) ──
                Row {
                    visible: dmv.tab === "zariadenia" && dmv.group === ""
                    anchors { left: parent.left; leftMargin: 12; verticalCenter: parent.verticalCenter }
                    spacing: 6
                    component Chip: Rectangle {
                        id: ch
                        property string glyph; property string label: ""; property bool on: false; property bool warn: false
                        default property alias extra: ex.data
                        signal clicked()
                        width: cr.implicitWidth + 18; height: 34; radius: 11
                        color: on ? Qt.rgba(theme.primary.r, theme.primary.g, theme.primary.b, 0.28) : (chm.containsMouse ? theme.hover : Qt.rgba(theme.surface.r, theme.surface.g, theme.surface.b, 0.85))
                        border { color: warn ? theme.error : theme.outline; width: 1 }
                        Row { id: cr; x: 9; anchors.verticalCenter: parent.verticalCenter; spacing: 6
                              Glyph { name: ch.glyph; size: 16; color: ch.warn ? theme.error : (ch.on ? theme.primary : theme.fg); anchors.verticalCenter: parent.verticalCenter }
                              Text { visible: ch.label !== ""; text: ch.label; color: theme.fg; font { family: theme.fontUi; pixelSize: 12; weight: Font.DemiBold } anchors.verticalCenter: parent.verticalCenter }
                              Row { id: ex; spacing: 6; anchors.verticalCenter: parent.verticalCenter } }
                        MouseArea { id: chm; anchors.fill: parent; hoverEnabled: true; z: -1; onClicked: ch.clicked() }
                    }
                    component MiniSlider: Item {
                        id: ms
                        property real value: 0; property real from: 0; property real to: 100
                        signal moved(real v)
                        width: 84; height: 20
                        readonly property real frac: Math.max(0, Math.min(1, ((mm.pressed ? mm.v : value) - from) / (to - from)))
                        Rectangle { anchors.verticalCenter: parent.verticalCenter; width: parent.width; height: 5; radius: 3; color: theme.field }
                        Rectangle { anchors.verticalCenter: parent.verticalCenter; width: Math.max(5, parent.width * ms.frac); height: 5; radius: 3; color: theme.primary }
                        Rectangle { x: (parent.width - 12) * ms.frac; anchors.verticalCenter: parent.verticalCenter; width: 12; height: 12; radius: 6; color: theme.fg }
                        MouseArea { id: mm; anchors { fill: parent; margins: -6 } property real v: 0
                                    function at(x) { return Math.round(ms.from + Math.max(0, Math.min(1, x / width)) * (ms.to - ms.from)); }
                                    onPressed: (m) => v = at(m.x); onPositionChanged: (m) => v = at(m.x); onReleased: ms.moved(v)
                                    onWheel: (w) => ms.moved(Math.max(ms.from, Math.min(ms.to, ms.value + (w.angleDelta.y > 0 ? 5 : -5)))) }
                    }
                    Chip { glyph: rq.muted ? "volume-off" : "volume"; label: rq.volume === null ? "—" : rq.volume + ""; warn: rq.muted
                           onClicked: rq.run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"])
                           MiniSlider { value: rq.volume || 0; onMoved: (v) => { rq.volume = v; rq.run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", v + "%"]); } } }
                    Chip { visible: rq.hasMic; glyph: rq.micMuted ? "microphone-off" : "microphone"; warn: rq.micMuted
                           onClicked: rq.run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SOURCE@", "toggle"]) }
                    Chip { glyph: rq.wired ? "network" : "wifi"; on: !!rq.ssid || !!rq.wired
                           label: rq.wired ? "Kábel" : (rq.wifi === false ? "Wi-Fi vyp." : (rq.ssid || "Wi-Fi"))
                           onClicked: dmv.tab = "siete" }
                    Chip { visible: rq.btAvail; glyph: "bluetooth"; on: rq.bt === true; onClicked: rq.run(["noctalia", "msg", "bluetooth-toggle"]) }
                    Chip { visible: rq.brightness !== null; glyph: "sun"
                           MiniSlider { width: 64; from: 5; value: rq.brightness || 0; onMoved: (v) => { rq.brightness = v; rq.run(["brightnessctl", "-c", "backlight", "set", v + "%"]); } } }
                    Chip { glyph: rq.battery ? (rq.battery.state === "Charging" ? "battery-charging" : "battery") : "bolt"; warn: !!rq.battery && rq.battery.pct < 15 && rq.battery.state !== "Charging"
                           label: (rq.battery ? rq.battery.pct + " % · " : "") + (rq.game ? "Hra" : (rq.profileNames[rq.profile] || "Výkon"))
                           onClicked: { const q = mapToItem(pmenu.parent, 0, 0);
                                        pmenu.open(q.x, q.y - 200, rq.profiles.map(p => ({ glyph: "bolt", label: rq.profileNames[p] || p, checked: rq.profile === p, action: () => rq.run(["powerprofilesctl", "set", p]) }))
                                                   .concat([{ separator: true }, { glyph: "device-gamepad", label: "Herný režim", checked: rq.game, action: () => rq.run(["hyprctl", "eval", "latte.game(" + !rq.game + ")"]) }]), "Režim výkonu"); } }
                    Chip { glyph: "moon"; on: rq.night; onClicked: rq.run(["noctalia", "msg", "nightlight-toggle"]) }
                    Chip { visible: rq.usbDrives.length > 0; glyph: "usb"; label: rq.usbDrives.length === 1 ? "Odobrať" : "Odobrať (" + rq.usbDrives.length + ")"
                           onClicked: { const q = mapToItem(pmenu.parent, 0, 0);
                                        pmenu.open(q.x, q.y - 40 * rq.usbDrives.length - 20, rq.usbDrives.map(d => ({ glyph: "usb", label: "Bezpečne odobrať " + d.label, action: () => dmv.safeRemove(d.path, d.label) })), "USB"); } }
                },
                // ── pás: vybraná kategória / zariadenie ──
                Row {
                    visible: !(dmv.tab === "zariadenia" && dmv.group === "")
                    anchors { left: parent.left; leftMargin: 14; verticalCenter: parent.verticalCenter }
                    spacing: 10
                    Glyph { anchors.verticalCenter: parent.verticalCenter; name: dmv.tab === "siete" ? "network" : (dmv.curGroup ? dmv.curGroup.glyph : "cpu"); size: 20; color: theme.primary }
                    Column { anchors.verticalCenter: parent.verticalCenter
                             Text { text: dmv.tab === "siete" ? "Siete" : ((dmv.curGroup ? dmv.curGroup.title : "") + (dmv.sel ? " › " + dmv.sel.item.name : ""))
                                    color: theme.fg; font { family: theme.fontUi; pixelSize: 13; weight: Font.Bold } }
                             Text { text: dmv.tab === "siete" ? (rq.wired ? "Kábel · " + rq.wired : (rq.ssid ? "Wi-Fi · " + rq.ssid : "nepripojené"))
                                                              : (dmv.sel ? (dmv.sel.item.stateTitle || "funguje") + " · " + dmv.sel.item.sub : (dmv.curGroup ? dmv.count(dmv.curGroup.items.length) : ""))
                                    color: theme.fgDim; font { family: theme.fontUi; pixelSize: 11 } } }
                }
            ]

            Item {
                id: box
                anchors.fill: parent
                focus: true
                Keys.onEscapePressed: { if (dmv.countdown > 0) dmv.revert(); else if (dmv.group !== "") dmv.group = ""; else rq.open = false; }
                Keys.onReturnPressed: dmv.keep()
                MouseArea { anchors.fill: parent }          // klik do panelu ho nezavrie
                SpravcaZariadeni {
                    id: dmv
                    theme: theme
                    anchors { fill: parent; margins: 16; topMargin: 14 }
                    active: rq.open
                    onOpenWindow: (a) => rq.detached(a)
                }
                Row {
                    anchors { right: parent.right; top: parent.top; margins: 12 }
                    spacing: 4
                    IconButton { theme: theme; glyph: "external-link"; tip: "Otvoriť ako okno"; onClicked: rq.detached(["latte-app", "zariadenia"]) }
                    IconButton { theme: theme; glyph: "x"; onClicked: rq.open = false }
                }
                ContextMenu { id: pmenu; theme: theme }
            }
        }
    }
}
