// LatteOS — výbehy maskota z ostrova (zadanie 24. 9. večer: „ako by sa dali spraviť úniky z prideleného miesta?“).
// Malé priehľadné okno vo vrstve nad oknami (layer-shell Top, bez klávesnice), ktoré sa posúva po obrazovke:
//   world  občas (alebo pri „Hrať sa“) vybehne z ostrova, chodí po hornej hrane lišty, sadá na titulky okien
//          (lietajúce postavy letia rovno, ostatné kráčajú a šplhajú), po chvíli sa vráti domov;
//          keď si 3 min nečinný, zdriemne si pri kurzore a keď sa vrátiš, zobudí sa a ide domov
//   chaos  behá častejšie a naháňa kurzor
// Klik = pohladkať, pravý klik = domov. Pri hre / okne na celú obrazovku sa hneď schová.
// Kliky mimo maskota prechádzajú (okno má veľkosť maskota). Snímky: plugin cat/mascots, rovnaké ako na lište.
// Súradnice domova (ostrov maskota): ~/.config/latteos/mascot-home „x y“ (inak odhad vpravo dole).
// Synchronizácia s widgetom lišty: $XDG_RUNTIME_DIR/latteos/maskot-von (vychadza | von | prichadza | domov | hrat).
// Spúšťa: latte-app maskot (hyprland.lua). Pri stupni Softvér 4 kroky/s, s GPU 20 krokov/s.
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland

ShellRoot {
    id: mk
    readonly property string home: Quickshell.env("HOME") || "/"
    readonly property string cfg: (Quickshell.env("XDG_CONFIG_HOME") || (home + "/.config")) + "/latteos"
    readonly property string runFile: (Quickshell.env("XDG_RUNTIME_DIR") || "/tmp") + "/latteos/maskot-von"
    readonly property string dir: "/usr/share/latteos/noctalia/plugins/cat/mascots/"
    readonly property bool gpu: ["softver", "minimalny", "safe"].indexOf(Quickshell.env("LATTE_TIER") || "softver") < 0
    readonly property int fps: gpu ? 20 : 4
    readonly property real speed: (gpu ? 90 : 110) / fps        // px za krok (~100 px/s)
    readonly property var flyers: ["drak", "svetluska", "void", "robot"]
    readonly property var scr: Quickshell.screens.length ? Quickshell.screens[0] : null
    readonly property int sw: scr ? scr.width : 1920
    readonly property int sh: scr ? scr.height : 1080
    readonly property int pw: 66                                // 44×36 × 1,5
    readonly property int phh: 54
    readonly property int barTop: sh - 58 - phh + 6             // stojí na hornej hrane lišty
    property int homeX: sw - 280
    property string kind: "macka"
    property string mode: "world"
    property string phase: "doma"      // doma | cakam | chodi | sedi | spi | hra | domov
    property real px: homeX
    property real py: barTop
    property real tx: 0
    property real ty: 0
    property string sitOn: ""          // adresa okna, na ktorom sedí
    property real sitDx: 0
    property int stops: 0
    property int waitTicks: 0
    property int frameN: 0
    property bool faceRight: false
    property bool happy: false
    property var wins: []
    property point cursor: Qt.point(sw / 2, sh / 2)
    property bool fullscreen: false
    property real tripStart: 0

    function trim(s) { return (s || "").trim(); }
    FileView { path: mk.cfg + "/mascot"; printErrors: false; watchChanges: true; onFileChanged: reload()
               onLoaded: { const k = mk.trim(text()); mk.kind = k || "macka"; } onLoadFailed: mk.kind = "macka" }
    FileView { path: mk.cfg + "/mascot-mode"; printErrors: false; watchChanges: true; onFileChanged: reload()
               onLoaded: mk.mode = mk.trim(text()) || "world"; onLoadFailed: mk.mode = "world" }
    FileView { path: mk.cfg + "/mascot-home"; printErrors: false
               onLoaded: { const f = text().trim().split(/\s+/); if (f.length >= 1 && parseInt(f[0])) mk.homeX = parseInt(f[0]); } }
    FileView {
        id: run
        path: mk.runFile; printErrors: false; watchChanges: true; onFileChanged: reload()
        onLoaded: {
            const v = mk.trim(text());
            if (v === "domov" && mk.phase !== "doma") mk.goHome(true);
            if (v === "hrat" && mk.phase === "doma") mk.startTrip("hra");
        }
    }
    Process { id: mkdir; running: true; command: ["mkdir", "-p", mk.runFile.replace(/\/[^/]*$/, "")] }
    function setRun(v) { run.setText(v); }

    readonly property bool active: kind !== "ziadny" && (mode === "world" || mode === "chaos")
    readonly property bool flyer: flyers.indexOf(kind) >= 0

    // okná aktuálnej plochy (titulky = miesta na sedenie) a celá obrazovka
    Process {
        id: winProc
        command: ["sh", "-c", "hyprctl -j activeworkspace; echo @@; hyprctl -j clients; echo @@; hyprctl cursorpos"]
        stdout: StdioCollector {
            onStreamFinished: {
                const parts = this.text.split("@@");
                try {
                    const ws = JSON.parse(parts[0]), all = JSON.parse(parts[1]);
                    mk.wins = all.filter(c => c.workspace && c.workspace.id === ws.id && c.mapped && !c.hidden && c.size[0] > 200)
                                 .map(c => ({ a: c.address, x: c.at[0], y: c.at[1], w: c.size[0], h: c.size[1], fs: c.fullscreen }));
                    mk.fullscreen = mk.wins.some(w => w.fs === 2 || w.fs === true);
                } catch (e) {}
                const m = (parts[2] || "").match(/(-?\d+),\s*(-?\d+)/);
                if (m) mk.cursor = Qt.point(parseInt(m[1]), parseInt(m[2]));
                mk.followWindow();
            }
        }
    }
    Timer { interval: 2000; repeat: true; running: mk.active; triggeredOnStart: true; onTriggered: if (!winProc.running) winProc.running = true }

    IdleMonitor { id: idle; timeout: 180; respectInhibitors: true }

    // ── rozhodovanie raz za minútu: výbeh? ─────────────────────────────────────────────────
    Timer {
        interval: 60000; repeat: true; running: mk.active
        onTriggered: {
            const h = new Date().getHours();
            if (mk.phase !== "doma" || mk.fullscreen || h >= 23 || h < 6) return;
            if (idle.isIdle) { mk.startTrip("spanok"); return; }
            if (Math.random() < (mk.mode === "chaos" ? 0.35 : 0.08)) mk.startTrip("vylet");
        }
    }
    onActiveChanged: if (!active && phase !== "doma") goHome(true)
    Connections { target: idle; function onIsIdleChanged() { if (idle.isIdle && mk.phase === "doma" && mk.active && !mk.fullscreen) mk.startTrip("spanok"); } }

    property string tripKind: "vylet"
    function startTrip(k) {
        if (!active || phase !== "doma") return;
        tripKind = k; stops = 0; tripStart = Date.now();
        setRun("vychadza");                   // widget prehrá odchod z ostrova
        phase = "cakam"; waitTicks = fps * 2;
        px = homeX; py = barTop;
    }
    function goHome(fast) {
        if (phase === "doma") return;
        sitOn = ""; phase = "domov"; tx = homeX; ty = barTop; happy = false;
        if (fast === true && fullscreen) arrive();
    }
    function arrive() {                       // doma: skryť, widget prehrá príchod
        phase = "doma"; sitOn = ""; px = homeX; py = barTop;
        setRun("prichadza");
    }
    function pickTarget() {
        stops++;
        if (tripKind === "hra" || mode === "chaos") { tx = Math.max(0, Math.min(sw - pw, cursor.x - pw / 2)); ty = Math.max(0, Math.min(barTop, cursor.y - phh + 10)); sitOn = ""; return; }
        const onWin = wins.length && Math.random() < 0.6;
        if (onWin) {
            const w = wins[Math.floor(Math.random() * wins.length)];
            sitDx = 20 + Math.random() * Math.max(1, w.w - pw - 40);
            tx = w.x + sitDx; ty = Math.max(0, w.y - phh + 8); sitOn = w.a;
        } else {
            tx = 40 + Math.random() * (sw - pw - 80); ty = barTop; sitOn = "";
        }
    }
    function followWindow() {                 // sedí na okne, ktoré sa pohlo alebo zmizlo
        if (phase !== "sedi" || sitOn === "") return;
        const w = wins.find(x => x.a === sitOn);
        if (!w) { sitOn = ""; tx = px; ty = barTop; phase = "chodi"; return; }      // okno zmizlo → zoskočí na lištu
        px = w.x + sitDx; py = Math.max(0, w.y - phh + 8); tx = px; ty = py;
    }

    // ── pohyb ─────────────────────────────────────────────────────────────────────────────
    Timer {
        interval: 1000 / mk.fps; repeat: true; running: mk.active && mk.phase !== "doma"
        onTriggered: {
            mk.frameN++;
            if (mk.fullscreen && mk.phase !== "doma") { mk.arrive(); return; }
            if (mk.phase === "cakam") {
                if (--mk.waitTicks <= 0) { mk.setRun("von"); mk.phase = "chodi"; mk.pickTarget(); }
                return;
            }
            if (mk.phase === "chodi" || mk.phase === "domov") {
                const dx = mk.tx - mk.px, dy = mk.ty - mk.py, sp = mk.speed * (mk.phase === "domov" ? 1.6 : 1);
                if (Math.abs(dx) > 0.5) mk.faceRight = dx > 0;
                if (mk.flyer) {
                    const d = Math.hypot(dx, dy);
                    if (d <= sp) { mk.px = mk.tx; mk.py = mk.ty; } else { mk.px += dx / d * sp; mk.py += dy / d * sp; }
                } else {
                    const onBar = mk.py >= mk.barTop - 1;
                    if (!onBar && (Math.abs(dx) > 1 || mk.ty > mk.py))
                        mk.py += Math.min(mk.barTop - mk.py, sp * 2);                          // z okna zoskočí na lištu
                    else if (Math.abs(dx) > 0.5)
                        mk.px += Math.sign(dx) * Math.min(Math.abs(dx), sp);                  // kráča po lište
                    else if (Math.abs(dy) > 1)
                        mk.py += Math.sign(dy) * Math.min(Math.abs(dy), sp);                  // šplhá hore k titulku
                }
                if (Math.abs(mk.tx - mk.px) < 1 && Math.abs(mk.ty - mk.py) < 1) {
                    if (mk.phase === "domov") { mk.arrive(); return; }
                    if (mk.tripKind === "spanok") { mk.phase = "spi"; return; }
                    mk.phase = "sedi"; mk.waitTicks = mk.fps * (5 + Math.floor(Math.random() * 15));
                }
                return;
            }
            if (mk.phase === "sedi") {
                if (mk.tripKind === "hra" || mk.mode === "chaos") {                    // naháňa kurzor
                    if (Math.hypot(mk.cursor.x - (mk.px + mk.pw / 2), mk.cursor.y - (mk.py + mk.phh / 2)) > 90) { mk.phase = "chodi"; mk.pickTarget(); return; }
                }
                if (--mk.waitTicks <= 0) {
                    const long = Date.now() - mk.tripStart > (mk.tripKind === "hra" ? 45000 : 150000);
                    if (long || mk.stops >= 4) mk.goHome(); else { mk.phase = "chodi"; mk.pickTarget(); }
                }
                return;
            }
            if (mk.phase === "spi" && !idle.isIdle) { mk.happy = true; mk.phase = "sedi"; mk.waitTicks = mk.fps * 2; mk.tripKind = "vylet"; mk.stops = 9; }
        }
    }
    // spánok pri kurzore: dojde k miestu, kde si nechal myš
    onPhaseChanged: if (phase === "chodi" && tripKind === "spanok") { tx = Math.max(0, Math.min(sw - pw, cursor.x + 20)); ty = Math.max(0, Math.min(barTop, cursor.y - phh / 2)); sitOn = ""; }

    readonly property string frame: {
        if (phase === "spi") return "spi-von";
        if (happy) return "hlad-von";
        if (phase === "chodi" || phase === "domov") return (frameN % 2 ? "chodza-1" : "chodza-2") + (faceRight ? "-r" : "");
        return "stoji" + (faceRight ? "-r" : "");
    }
    Timer { id: happyOff; interval: 2000; onTriggered: mk.happy = false }
    Process { id: petProc }

    PanelWindow {
        visible: mk.active && mk.phase !== "doma" && mk.phase !== "cakam" && !mk.fullscreen
        anchors { top: true; left: true }
        margins { left: Math.round(mk.px); top: Math.round(mk.py) }
        implicitWidth: mk.pw; implicitHeight: mk.phh
        exclusionMode: ExclusionMode.Ignore
        WlrLayershell.layer: WlrLayer.Top
        WlrLayershell.namespace: "latte-maskot"
        WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
        color: "transparent"
        Image {
            anchors.fill: parent
            source: "file://" + mk.dir + mk.kind + "-" + mk.frame + ".png"
            smooth: false; fillMode: Image.PreserveAspectFit
            sourceSize { width: 44; height: 36 }
        }
        MouseArea {
            anchors.fill: parent; acceptedButtons: Qt.LeftButton | Qt.RightButton; cursorShape: Qt.PointingHandCursor
            onClicked: (m) => {
                if (m.button === Qt.RightButton) { mk.goHome(); return; }
                mk.happy = true; happyOff.restart();
                // pohladkanie: +nálada v spoločnom stave (rovnaký súbor ako widget a panel)
                petProc.command = ["python3", "-c", "import json,os,time;p=os.path.expanduser('~/.local/state/latteos/maskot.json');d=json.load(open(p)) if os.path.exists(p) else {};d['nalada']=min(100,d.get('nalada',80)+12);d['posledne']=int(time.time());os.makedirs(os.path.dirname(p),exist_ok=True);json.dump(d,open(p,'w'))"];
                petProc.running = true;
            }
        }
    }
}
