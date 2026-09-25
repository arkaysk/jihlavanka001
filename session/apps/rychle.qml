// LatteOS — Zariadenia: rýchle nastavenia vyrastajúce z ostrova zariadení na lište (tvar L zrkadlovo vpravo,
// common/LPopup.qml; zadanie 25. 9. — kresba). Nahrádza panel Noctalie (plugins/devices/panel.luau), ktorý sa
// k ostrovu pripojiť nevie. Wi-Fi/sieť, Bluetooth, Nerušiť, Nočné svetlo, hlasitosť, jas, herný režim, profil výkonu.
// Kmeň L: súhrn Správcu zariadení (latte-devices list) a tlačidlo na plného Správcu. Beží na pozadí, prepína latte-rychle.
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

    // ── stav ────────────────────────────────────────────────────────────────────────
    property var wifi: null                 // true | false | null (neznáme)
    property string ssid: ""
    property string wired: ""
    property var bt: null
    property bool btAvail: true
    property var dnd: null
    property bool night: false
    property var volume: null
    property bool muted: false
    property var brightness: null
    property string profile: ""
    property var profiles: []
    property bool game: false
    property string tier: "softver"
    property bool tierForced: false
    property string devSummary: ""
    property int devTotal: 0
    property int devFaults: 0

    // výsledok až keď skončí proces aj výstup (onExited môže prísť skôr než text)
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
    Q { id: qWifi; command: ["sh", "-c", "nmcli -t -f WIFI radio; nmcli -t -f ACTIVE,SSID dev wifi 2>/dev/null | sed -n 's/^yes://p' | head -1; echo ---; nmcli -t -f TYPE,STATE,CONNECTION dev 2>/dev/null | sed -n 's/^ethernet:connected://p' | head -1"]
        done: (o) => { const [a, b] = o.split("---\n"); const l = a.split("\n"); rq.wifi = l[0].trim() === "enabled"; rq.ssid = (l[1] || "").trim(); rq.wired = (b || "").trim(); } }
    Q { id: qBt; command: ["noctalia", "msg", "bluetooth-status"]; done: (o, c) => { rq.btAvail = c === 0; rq.bt = c === 0 && o.toLowerCase().includes("on"); } }
    Q { id: qDnd; command: ["noctalia", "msg", "notification-dnd-status"]; done: (o) => { const s = o.toLowerCase(); rq.dnd = s.includes("on") || s.includes("true"); } }
    Q { id: qNight; command: ["noctalia", "msg", "nightlight-status"]; done: (o, c) => { const s = o.toLowerCase(); rq.night = c === 0 && (s.includes("on") || s.includes("true")); } }
    Q { id: qVol; command: ["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"]
        done: (o) => { const m = o.match(/Volume: ([\d.]+)/); rq.volume = m ? Math.round(parseFloat(m[1]) * 100) : null; rq.muted = o.includes("MUTED"); } }
    Q { id: qBri; command: ["brightnessctl", "-m", "-c", "backlight"]; done: (o, c) => { const m = o.match(/,(\d+)%,/); rq.brightness = c === 0 && m ? parseInt(m[1]) : null; } }
    Q { id: qProf; command: ["sh", "-c", "powerprofilesctl get 2>/dev/null; echo ---; powerprofilesctl list 2>/dev/null | sed -n 's/^[* ] *\\([a-z-]*\\):$/\\1/p'"]
        done: (o) => { const [a, b] = o.split("---\n"); rq.profile = a.trim(); rq.profiles = (b || "").split("\n").filter(x => x).reverse(); } }
    Q { id: qTier; command: ["sh", "-c", "sed -n 's/^tier = \"\\([a-z]*\\)\"/\\1/p' /run/latteos/mode.toml 2>/dev/null; echo ---; cat \"$1/tier\" 2>/dev/null; echo ---; cat \"$2/game-mode\" 2>/dev/null", "sh", rq.cfg, rq.stateDir]
        done: (o) => { const p = o.split("---\n"); const forced = (p[1] || "").trim(); rq.tierForced = forced !== ""; rq.tier = forced || p[0].trim() || "softver"; rq.game = (p[2] || "").trim() === "1"; } }
    Q { id: qDev; command: ["latte-devices", "list"]
        done: (o) => { try { const d = JSON.parse(o); rq.devSummary = d.summary || ""; rq.devTotal = d.total || 0; rq.devFaults = (d.faults || []).length; } catch (e) {} } }
    function refresh() { for (const p of [qWifi, qBt, qDnd, qNight, qVol, qBri, qProf, qTier]) if (!p.running) p.running = true; }
    onOpenChanged: if (open) { refresh(); if (!qDev.running) qDev.running = true; }
    Timer { interval: 3000; repeat: true; running: rq.open; onTriggered: rq.refresh() }
    Process { id: act; onExited: rq.refresh() }
    function run(argv) { act.running = false; act.command = argv; act.running = true; }
    Process { id: det }
    function detached(argv) { rq.open = false; det.command = argv; det.startDetached(); }

    readonly property var tierNames: ({ plny: "Plný", standard: "Štandard", usporny: "Úsporný", minimalny: "Minimálny", softver: "Softvér", safe: "SAFE" })
    readonly property var profileNames: ({ "power-saver": "Úsporný", balanced: "Vyvážený", performance: "Výkon" })

    // GIF / obrázok priamo v ostrove na lište, súvislý s pätou okna L (Noctalia sama GIF nekreslí)
    TileOverlay {
        id: tile
        theme: theme
        foot: rq.foot; spec: rq.sceneRight || rq.sceneAll; glyph: "adjustments"; mirror: true
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
            panelW: 420; panelH: 540; trunkH: 50
            sceneSpec: rq.sceneRight || rq.sceneAll; motion: rq.barMotion; dim: rq.dim; footGlyph: "adjustments"; image: tile.image; frameDir: tile.frameDir; frameCount: tile.frameCount; ohnisko: tile.ohnisko
            trunk: [
                Row {
                    anchors { left: parent.left; leftMargin: 14; verticalCenter: parent.verticalCenter }
                    spacing: 10
                    Rectangle {
                        width: dm.implicitWidth + 44; height: 32; radius: 10
                        color: dmm.containsMouse ? theme.hover : Qt.rgba(theme.surface.r, theme.surface.g, theme.surface.b, 0.85)
                        border { color: theme.outline; width: 1 }
                        Glyph { x: 12; anchors.verticalCenter: parent.verticalCenter; name: "cpu"; size: 16; color: theme.primary }
                        Text { id: dm; x: 34; anchors.verticalCenter: parent.verticalCenter; text: "Správca zariadení"; color: theme.fg; font { family: theme.fontUi; pixelSize: 13; weight: Font.DemiBold } }
                        MouseArea { id: dmm; anchors.fill: parent; hoverEnabled: true; onClicked: rq.detached(["latte-app", "zariadenia"]) }
                    }
                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        text: rq.devFaults ? (rq.devFaults + (rq.devFaults === 1 ? " problém" : rq.devFaults < 5 ? " problémy" : " problémov")) : (rq.devTotal ? rq.devTotal + " zariadení · v poriadku" : "")
                        color: rq.devFaults ? theme.error : theme.fgDim
                        font { family: theme.fontUi; pixelSize: 12; weight: rq.devFaults ? Font.Bold : Font.Normal }
                    }
                }
            ]

            Item {
                id: box
                anchors.fill: parent
                focus: true
                Keys.onEscapePressed: rq.open = false
                MouseArea { anchors.fill: parent }          // klik do panelu ho nezavrie

                component Tile: Rectangle {
                    id: t
                    property string glyph; property string title; property string sub
                    property bool on: false; property bool enabled: true
                    signal clicked()
                    width: (col.width - 10) / 2; height: 78; radius: 14
                    color: on ? theme.primary : (tm.containsMouse && enabled ? theme.hover : theme.surfaceVariant)
                    opacity: enabled ? 1 : 0.5
                    Behavior on color { ColorAnimation { duration: theme.animMs } }
                    Column {
                        anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter; margins: 12 }
                        spacing: 3
                        Glyph { name: t.glyph; size: 20; color: t.on ? theme.fgOnPrimary : theme.fg }
                        Text { text: t.title; color: t.on ? theme.fgOnPrimary : theme.fg; font { family: theme.fontUi; pixelSize: 13; weight: Font.Bold } }
                        Text { width: parent.width; text: t.sub; elide: Text.ElideRight; color: t.on ? theme.fgOnPrimary : theme.fgDim; font { family: theme.fontUi; pixelSize: 11 } }
                    }
                    MouseArea { id: tm; anchors.fill: parent; hoverEnabled: true; enabled: t.enabled; onClicked: t.clicked() }
                }
                component Heading: Text { color: theme.fgDim; font { family: theme.fontUi; pixelSize: 11; weight: Font.Bold; letterSpacing: 0.6 } }
                component Slider: Item {
                    id: s
                    property real from: 0; property real to: 100; property real value: 0; property bool enabled: true
                    property string glyph
                    signal moved(real v)
                    signal glyphClicked()
                    width: col.width; height: 32
                    opacity: enabled ? 1 : 0.45
                    Glyph { id: sg; anchors.verticalCenter: parent.verticalCenter; name: s.glyph; size: 18; color: theme.fg
                            MouseArea { anchors.fill: parent; anchors.margins: -6; onClicked: s.glyphClicked() } }
                    Item {
                        id: track
                        anchors { left: sg.right; leftMargin: 12; right: parent.right; verticalCenter: parent.verticalCenter }
                        height: 24
                        readonly property real frac: Math.max(0, Math.min(1, ((sm.pressed ? sm.v : s.value) - s.from) / (s.to - s.from)))
                        Rectangle { anchors.verticalCenter: parent.verticalCenter; width: parent.width; height: 8; radius: 4; color: theme.field }
                        Rectangle { anchors.verticalCenter: parent.verticalCenter; width: Math.max(8, parent.width * track.frac); height: 8; radius: 4; color: theme.primary }
                        Rectangle { x: (parent.width - 18) * track.frac; anchors.verticalCenter: parent.verticalCenter; width: 18; height: 18; radius: 9
                                    color: theme.fg; border { color: theme.primary; width: 2 } }
                        MouseArea {
                            id: sm
                            anchors.fill: parent; enabled: s.enabled
                            property real v: 0
                            function at(x) { return Math.round(s.from + Math.max(0, Math.min(1, x / width)) * (s.to - s.from)); }
                            onPressed: (m) => v = at(m.x)
                            onPositionChanged: (m) => v = at(m.x)
                            onReleased: s.moved(v)
                            onWheel: (w) => s.moved(Math.max(s.from, Math.min(s.to, s.value + (w.angleDelta.y > 0 ? 5 : -5))))
                        }
                    }
                }

                Column {
                    id: col
                    anchors { fill: parent; margins: 18 }
                    spacing: 12
                    Row {
                        width: parent.width
                        Column {
                            width: parent.width - 32
                            Text { text: "Zariadenia"; color: theme.fg; font { family: theme.fontUi; pixelSize: 17; weight: Font.Bold } }
                            Text { text: "Stupeň: " + (rq.tierNames[rq.tier] || rq.tier) + (rq.tierForced ? " (vynútený)" : " (auto)"); color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 } }
                        }
                        IconButton { theme: theme; glyph: "x"; onClicked: rq.open = false }
                    }
                    Flow {
                        width: parent.width; spacing: 10
                        Tile {
                            glyph: rq.wired ? "network" : "wifi"; title: rq.wired ? "Sieť" : "Wi-Fi"
                            sub: rq.wired ? "Kábel · " + rq.wired : (rq.wifi === null ? "…" : rq.wifi ? (rq.ssid || "nepripojené") : "vypnuté")
                            on: rq.wired ? true : rq.wifi === true
                            onClicked: rq.wired ? rq.detached(["latte-app", "zariadenia", "siete"]) : rq.run(["noctalia", "msg", "wifi-toggle"])
                        }
                        Tile {
                            glyph: "bluetooth"; title: "Bluetooth"; enabled: rq.btAvail
                            sub: !rq.btAvail ? "nedostupné" : rq.bt ? "zapnuté" : "vypnuté"; on: rq.bt === true
                            onClicked: rq.run(["noctalia", "msg", "bluetooth-toggle"])
                        }
                        Tile {
                            glyph: "bell"; title: "Nerušiť"; sub: rq.dnd ? "zapnuté" : "vypnuté"; on: rq.dnd === true
                            onClicked: rq.run(["noctalia", "msg", "notification-dnd-toggle"])
                        }
                        Tile {
                            glyph: "moon"; title: "Nočné svetlo"; sub: rq.night ? "zapnuté" : "podľa rozvrhu"; on: rq.night
                            onClicked: rq.run(["noctalia", "msg", "nightlight-toggle"])
                        }
                    }
                    Heading { text: "HLASITOSŤ" + (rq.volume === null ? "  (bez zvukového zariadenia)" : "  " + rq.volume + " %" + (rq.muted ? " · stlmené" : "")) }
                    Slider {
                        glyph: "volume"; to: 100; value: rq.volume === null ? 0 : rq.volume; enabled: rq.volume !== null
                        onMoved: (v) => { rq.volume = v; rq.run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", v + "%"]); }
                        onGlyphClicked: rq.run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"])
                    }
                    Heading { text: "JAS" + (rq.brightness === null ? "  (monitor bez ovládania jasu)" : "  " + rq.brightness + " %") }
                    Slider {
                        glyph: "sun"; from: 5; to: 100; value: rq.brightness === null ? 100 : rq.brightness; enabled: rq.brightness !== null
                        onMoved: (v) => { rq.brightness = v; rq.run(["brightnessctl", "-c", "backlight", "set", v + "%"]); }
                    }
                    Heading { text: "HERNÝ REŽIM A VÝKON" }
                    Row {
                        width: parent.width; spacing: 10
                        Rectangle {
                            id: gm
                            width: 44; height: 24; radius: 12; anchors.verticalCenter: parent.verticalCenter
                            color: rq.game ? theme.primary : theme.field; border { color: theme.outline; width: rq.game ? 0 : 1 }
                            Rectangle { x: rq.game ? 22 : 2; y: 2; width: 20; height: 20; radius: 10; color: rq.game ? theme.fgOnPrimary : theme.fgDim
                                        Behavior on x { NumberAnimation { duration: theme.animMs } } }
                            MouseArea { anchors.fill: parent; onClicked: { rq.game = !rq.game; rq.run(["hyprctl", "eval", "latte.game(" + rq.game + ")"]); } }
                        }
                        Text { width: parent.width - 54; anchors.verticalCenter: parent.verticalCenter; wrapMode: Text.Wrap
                               text: rq.game ? "Herný režim zapnutý: bez efektov, medzier a animácií" : "Herný režim vypnutý"
                               color: theme.fg; font { family: theme.fontUi; pixelSize: 12 } }
                    }
                    Row {
                        spacing: 6
                        visible: rq.profiles.length > 0
                        Repeater {
                            model: rq.profiles
                            Rectangle {
                                required property string modelData
                                readonly property bool cur: rq.profile === modelData
                                width: (col.width - 12) / 3; height: 32; radius: 10
                                color: cur ? Qt.rgba(theme.primary.r, theme.primary.g, theme.primary.b, 0.25) : (pm.containsMouse ? theme.hover : theme.field)
                                border { color: cur ? theme.primary : "transparent"; width: 1 }
                                Text { anchors.centerIn: parent; text: rq.profileNames[modelData] || modelData; color: theme.fg; font { family: theme.fontUi; pixelSize: 12; weight: parent.cur ? Font.Bold : Font.Normal } }
                                MouseArea { id: pm; anchors.fill: parent; hoverEnabled: true; onClicked: { rq.profile = modelData; rq.run(["powerprofilesctl", "set", modelData]); } }
                            }
                        }
                    }
                    Text { visible: rq.profiles.length === 0; text: "Profily výkonu nie sú dostupné (power-profiles-daemon)."; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 } }
                    Rectangle { width: parent.width; height: 1; color: theme.line }
                    Row {
                        spacing: 8
                        component Link: Rectangle {
                            id: lk
                            property string glyph; property string label
                            signal clicked()
                            width: lt.implicitWidth + 42; height: 32; radius: 10
                            color: lkm.containsMouse ? theme.hover : theme.field
                            Glyph { x: 12; anchors.verticalCenter: parent.verticalCenter; name: lk.glyph; size: 15; color: theme.primary }
                            Text { id: lt; x: 33; anchors.verticalCenter: parent.verticalCenter; text: lk.label; color: theme.fg; font { family: theme.fontUi; pixelSize: 12 } }
                            MouseArea { id: lkm; anchors.fill: parent; hoverEnabled: true; onClicked: lk.clicked() }
                        }
                        Link { glyph: "world"; label: "NET aplikácií"; onClicked: rq.detached(["latte-app", "aplikacie", "opravnenia"]) }
                        Link { glyph: "volume"; label: "Zvuk"; onClicked: rq.detached(["latte-app", "zariadenia", "zvuk"]) }
                        Link { glyph: "settings"; label: "Nastavenia"; onClicked: rq.detached(["latte-app", "nastavenia"]) }
                    }
                }
            }
        }
    }
}
