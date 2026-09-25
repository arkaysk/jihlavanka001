// LPopup — vyskakovacie okno v tvare L, ktoré vyrastie z ostrova na lište (zadanie 25. 9., kresba; stará verzia:
// docs/lista-a-rohy.md, časť 3 a src/latte_shell/reveal.py).
//   päta  = ostrov na lište (foot: {x, y, w, h} v súradniciach obrazovky, z latte-ostrovy); pri otvorení sa
//           nakreslí presne na ostrov, s textúrou
//   kmeň  = pás nad lištou (trunkH) cez celú šírku panelu: textúra + informácie (obsah `trunk`)
//   panel = obsah nad kmeňom (predvolený obsah komponentu)
// Medzi kmeňom a pätou je vyduté zaoblenie (tvar L z kresby). Otváranie: kmeň sa vysunie z hornej hrany päty
// (šírka aj výška naraz, spomalený dobeh), v druhej polovici sa objaví panel. Zatváranie opačne.
// side: "left" (App Manager vľavo) alebo "right" (Zariadenia vpravo, zrkadlovo; obsah sa nezrkadlí).
import QtQuick
import Quickshell

Item {
    id: lp
    required property var theme
    property var foot: ({ x: 12, y: 896, w: 100, h: 42 })
    property string side: "left"
    property real panelW: 660
    property real panelH: 560
    property real trunkH: 50
    property bool open: false
    property string sceneSpec: "para"
    property string motion: "vzdy"
    property real dim: 0.55                 // stlmenie textúry pod textom kmeňa
    property var islands: []                // všetky ostrovy lišty (latte-ostrovy): L nesmie prekryť susedné položky
    property string footGlyph: ""           // ikona ostrova (päta ho prekryje, preto ju nakreslí znova)
    default property alias content: body.data
    property alias trunk: trunkContent.data
    readonly property bool anim: ["softver", "minimalny", "safe"].indexOf(Quickshell.env("LATTE_TIER") || "softver") < 0
    readonly property int openMs: anim ? 380 : 220
    property real p: 0                      // 0 zatvorené … 1 otvorené
    signal closed()
    anchors.fill: parent

    onOpenChanged: { pa.stop(); pa.from = p; pa.to = open ? 1 : 0; pa.duration = (open ? openMs : openMs * 0.8) * Math.abs(pa.to - p); pa.start(); }
    NumberAnimation { id: pa; target: lp; property: "p"; easing.type: Easing.Linear; onFinished: if (!lp.open) lp.closed() }
    function easeOut(x) { x = Math.max(0, Math.min(1, x)); return 1 - Math.pow(1 - x, 3); }
    function smooth(x) { x = Math.max(0, Math.min(1, x)); return x * x * (3 - 2 * x); }
    readonly property real armP: easeOut(p / 0.75)
    readonly property real panelP: smooth((p - 0.5) / 0.5)

    // geometria (obrazovka): pravý roh je zrkadlový
    readonly property bool isRight: side === "right"
    readonly property real footBottom: foot.y + foot.h
    readonly property real left0: isRight ? foot.x + foot.w - panelW : foot.x
    readonly property real armW: foot.w + (panelW - foot.w) * armP
    readonly property real armX: isRight ? foot.x + foot.w - armW : foot.x
    // spodok kmeňa = vrch najvyššieho ostrova pod panelom (iné položky lišty ostanú celé viditeľné)
    readonly property real barTop: {
        let t = foot.y;
        for (const o of islands) if (o.x < left0 + panelW && o.x + o.w > left0) t = Math.min(t, o.y);
        return t;
    }
    // voľné miesto vedľa päty smerom k panelu (vyduté zaoblenie sa zmestí iba do medzery k susedovi)
    readonly property real sideGap: {
        let g = 16;
        for (const o of islands) {
            if (o.x === foot.x && o.w === foot.w) continue;
            if (!isRight && o.x >= foot.x + foot.w) g = Math.min(g, o.x - (foot.x + foot.w) - 1);
            if (isRight && o.x + o.w <= foot.x) g = Math.min(g, foot.x - (o.x + o.w) - 1);
        }
        return Math.max(0, g);
    }
    readonly property real trunkY: barTop - trunkH * armP
    readonly property real rad: 16

    // spoločný čas textúry (päta a kmeň kreslia ten istý obraz vo fáze)
    property real t: 0
    Timer { interval: 1000 / (lp.anim ? 24 : 8); repeat: true; running: lp.p > 0 && lp.motion !== "vypnute"; onTriggered: lp.t += interval / 1000 }

    // ── pozadie L: panel + kmeň + päta ───────────────────────────────────────────────
    // panel (nad kmeňom): zaoblené horné rohy
    Rectangle {
        id: panelBg
        x: lp.left0; width: lp.panelW
        y: lp.trunkY - lp.panelH * lp.panelP; height: lp.panelH * lp.panelP + lp.rad
        visible: lp.panelP > 0.01
        radius: 22; color: lp.theme.surface; border { color: lp.theme.outline; width: 1 }
        opacity: lp.panelP
    }
    // kmeň: textúra, zaoblený vonkajší dolný roh
    Item {
        id: trunkClip
        x: lp.armX; y: lp.trunkY; width: lp.armW; height: lp.barTop - lp.trunkY
        visible: lp.armP > 0.01
        clip: true
        Rectangle { anchors.fill: parent; color: lp.theme.surfaceVariant; radius: 0 }
        Scena {
            id: trunkScene
            anchors.fill: parent
            colors: lp.theme; spec: lp.sceneSpec; motion: lp.motion; time: lp.t; mirror: lp.isRight
            ox: trunkClip.x - lp.left0; oy: lp.trunkY - (lp.barTop - lp.trunkH); canvasW: lp.panelW; canvasH: lp.trunkH + lp.foot.h + (lp.foot.y - lp.barTop)
        }
        // stlmenie pod textom: textúra ostáva viditeľná pri päte, pokojná pod písmom
        Rectangle {
            anchors.fill: parent
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0; color: Qt.rgba(lp.theme.surface.r, lp.theme.surface.g, lp.theme.surface.b, lp.isRight ? lp.dim : 0.05) }
                GradientStop { position: 1; color: Qt.rgba(lp.theme.surface.r, lp.theme.surface.g, lp.theme.surface.b, lp.isRight ? 0.05 : lp.dim) }
            }
        }
        Item { id: trunkContent; anchors.fill: parent; opacity: lp.panelP }
    }
    // päta = ostrov na lište (prekryje ho, rovnaká textúra ako kmeň)
    Item {
        id: footClip
        // od vrchu lišty (ak je susedný ostrov vyšší, päta sa k kmeňu dotiahne stĺpcom nad vlastným ostrovom)
        x: lp.foot.x; y: lp.barTop; width: lp.foot.w; height: lp.foot.y + lp.foot.h - lp.barTop
        visible: lp.p > 0.01
        clip: true
        Rectangle { anchors.fill: parent; color: lp.theme.surfaceVariant; radius: 0 }
        Scena {
            anchors.fill: parent
            colors: lp.theme; spec: lp.sceneSpec; motion: lp.motion; time: lp.t; mirror: lp.isRight
            ox: lp.foot.x - lp.left0; oy: lp.trunkH; canvasW: lp.panelW; canvasH: lp.trunkH + lp.foot.h + (lp.foot.y - lp.barTop)
        }
        Rectangle {
            visible: lp.footGlyph !== ""
            x: (parent.width - 30) / 2; y: parent.height - lp.foot.h / 2 - 15; width: 30; height: 30; radius: 10
            color: Qt.rgba(lp.theme.surfaceVariant.r, lp.theme.surfaceVariant.g, lp.theme.surfaceVariant.b, 0.85)
            Glyph { anchors.centerIn: parent; name: lp.footGlyph || "apps"; size: 18; color: lp.theme.primary }
        }
    }
    // zaoblenie päty dole (ostrov má zaoblené rohy)
    Canvas {
        x: lp.foot.x - 1; y: lp.foot.y; width: lp.foot.w + 2; height: lp.foot.h + 1
        visible: lp.p > 0.01
        onVisibleChanged: requestPaint()
        onPaint: {
            const c = getContext("2d"); c.reset();
            c.fillStyle = "rgba(0,0,0,0)";
            c.globalCompositeOperation = "source-over";
            const r = lp.rad, w = width, h = height;
            // vyrežeme dolné rohy do priehľadna tak, že nakreslíme okolie farbou pozadia nie je možné — preto obrys
            c.strokeStyle = lp.theme.outline; c.lineWidth = 1;
            c.beginPath(); c.moveTo(0.5, 0); c.lineTo(0.5, h - r); c.quadraticCurveTo(0.5, h - 0.5, r, h - 0.5);
            c.lineTo(w - r, h - 0.5); c.quadraticCurveTo(w - 0.5, h - 0.5, w - 0.5, h - r); c.lineTo(w - 0.5, 0); c.stroke();
        }
    }
    // vyduté zaoblenie medzi kmeňom a pätou (vnútorný roh L)
    Canvas {
        id: notch
        readonly property real s: Math.min(lp.rad, lp.sideGap)
        x: lp.isRight ? lp.foot.x - s : lp.foot.x + lp.foot.w; y: lp.barTop
        width: Math.max(1, s); height: Math.max(1, s)
        visible: lp.armP > 0.5 && s >= 2 && lp.barTop === lp.foot.y
        onSChanged: requestPaint()
        onVisibleChanged: requestPaint()
        onPaint: {
            const c = getContext("2d"); c.reset();
            c.fillStyle = lp.theme.surfaceVariant;
            c.beginPath();
            if (lp.isRight) { c.moveTo(s, 0); c.lineTo(s, s); c.quadraticCurveTo(s, 0, 0, 0); }
            else { c.moveTo(0, 0); c.lineTo(0, s); c.quadraticCurveTo(0, 0, s, 0); }
            c.closePath(); c.fill();
        }
    }
    // obsah panelu (nad kmeňom)
    Item {
        id: body
        x: lp.left0; width: lp.panelW
        y: lp.trunkY - lp.panelH; height: lp.panelH
        opacity: lp.panelP
        visible: lp.panelP > 0.02
        transform: Translate { y: (1 - lp.panelP) * 18 }
    }
}
