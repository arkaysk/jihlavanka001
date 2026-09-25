// Scena — animovaná textúra lišty a kmeňa L (stará verzia: latte_common/scenes.py, docs/lista-a-rohy.md, časť 4).
//   spec:  para · matrix · gears (ozubené kolesá) · glow (pomalé svetlo) · solid:#RRGGBB · file:/cesta (GIF, WebP, obrázok)
// Obraz je čistá funkcia času a polohy na spoločnom plátne (ox, oy = posun tohto výseku), takže päta v lište a kmeň
// nad ňou kreslia ten istý obraz vo fáze a bez švu. Pohyb pasívny a pokojný (cyklus 6–12 s), softvér ~8 obr/s, GPU 24.
// motion: vzdy · kurzor (iba keď awake) · vypnute (statický snímok).
import QtQuick
import Quickshell

Item {
    id: sc
    required property var colors
    property string spec: "para"
    property string motion: "vzdy"
    property bool awake: true
    property real ox: 0                     // poloha výseku na spoločnom plátne
    property real oy: 0
    property real canvasW: width            // šírka celého plátna (kvôli rozloženiu stĺpcov / kolies)
    property real canvasH: height
    property real time: 0                   // spoločný čas (nastaví rodič, aby výseky boli vo fáze)
    property bool mirror: false             // pravý roh: zrkadlová geometria
    readonly property bool gpu: ["softver", "minimalny", "safe"].indexOf(Quickshell.env("LATTE_TIER") || "softver") < 0
    readonly property int fps: gpu ? 24 : 8
    readonly property bool moving: motion === "vzdy" || (motion === "kurzor" && awake)
    readonly property string kind: spec.indexOf(":") > 0 ? spec.slice(0, spec.indexOf(":")) : spec
    readonly property string arg: spec.indexOf(":") > 0 ? spec.slice(spec.indexOf(":") + 1) : ""
    clip: true

    function rgba(c, a) { return Qt.rgba(c.r, c.g, c.b, a); }

    Rectangle { anchors.fill: parent; visible: sc.kind === "solid"; color: sc.arg || sc.colors.surfaceVariant }
    AnimatedImage {
        visible: sc.kind === "file"
        x: -sc.ox; y: -sc.oy; width: sc.canvasW; height: sc.canvasH
        source: sc.kind === "file" ? "file://" + sc.arg : ""
        fillMode: Image.PreserveAspectCrop; playing: sc.moving && visible; cache: false; asynchronous: true
    }
    Canvas {
        id: cv
        anchors.fill: parent
        visible: ["para", "matrix", "gears", "glow"].indexOf(sc.kind) >= 0
        renderStrategy: Canvas.Immediate
        property real t: sc.time
        onTChanged: requestPaint()
        onWidthChanged: requestPaint()
        onPaint: {
            const c = getContext("2d"); c.reset();
            const W = sc.canvasW, H = sc.canvasH, ox = sc.ox, oy = sc.oy, t = sc.time, pc = sc.colors.primary;
            c.save(); c.translate(-ox, -oy);
            if (sc.mirror && sc.kind !== "matrix") { c.translate(W, 0); c.scale(-1, 1); }   // písmená sa nezrkadlia
            if (sc.kind === "para") {                   // stĺpce ako para nad šálkou, pomaly dýchajú
                const n = Math.max(6, Math.floor(W / 9));
                for (let i = 0; i < n; i++) {
                    const x = 4 + i * (W - 8) / n, ph = t * (2 * Math.PI / 8) + i * 0.7;
                    const h = H * (0.25 + 0.55 * (0.5 + 0.5 * Math.sin(ph))) * (1 - 0.35 * (i / n));
                    c.fillStyle = sc.rgba(pc, 0.16 + 0.26 * (1 - i / n));
                    c.fillRect(x, H - h - 3, 3, h);
                }
            } else if (sc.kind === "matrix") {          // stekajúci kód v akcente motívu
                const cw = 9, cols = Math.ceil(W / cw), rows = Math.ceil(H / 11), chars = "01LATTE7392ABCDEF";
                c.font = "bold 9px monospace";
                for (let i = 0; i < cols; i++) {
                    const speed = 0.6 + ((i * 37) % 11) / 11, head = ((t * speed * 4 + i * 5.3) % (rows + 8)) - 4;
                    for (let r = 0; r < rows; r++) {
                        const d = head - r; if (d < 0 || d > 7) continue;
                        c.fillStyle = sc.rgba(pc, d < 0.9 ? 0.95 : 0.55 * (1 - d / 8));
                        c.fillText(chars[(i * 7 + r * 3 + Math.floor(t * 2)) % chars.length], i * cw + 1, r * 11 + 9);
                    }
                }
            } else if (sc.kind === "gears") {           // ozubené prevody, pomalé otáčanie
                const gear = (cx, cy, r, teeth, ang, alpha) => {
                    c.beginPath();
                    for (let k = 0; k < teeth * 2; k++) {
                        const a0 = ang + k * Math.PI / teeth, rr = k % 2 ? r * 0.82 : r;
                        c.lineTo(cx + Math.cos(a0) * rr, cy + Math.sin(a0) * rr);
                        c.lineTo(cx + Math.cos(a0 + Math.PI / teeth * 0.6) * rr, cy + Math.sin(a0 + Math.PI / teeth * 0.6) * rr);
                    }
                    c.closePath(); c.fillStyle = sc.rgba(pc, alpha); c.fill();
                    c.beginPath(); c.arc(cx, cy, r * 0.32, 0, 2 * Math.PI); c.fillStyle = sc.colors.surfaceVariant; c.fill();
                };
                const R = H * 0.42;
                let x = R * 0.9, big = true, i = 0;
                while (x < W + R) {
                    const r = big ? R : R * 0.62, teeth = big ? 12 : 8, dir = i % 2 ? -1 : 1;
                    gear(x, H * (big ? 0.62 : 0.4), r, teeth, dir * t * (0.5 / (r / R)) + i, big ? 0.28 : 0.2);
                    x += r * 1.72; big = !big; i++;
                }
            } else if (sc.kind === "glow") {            // pomalé svetlo: mäkké škvrny po dráhach
                for (let k = 0; k < 5; k++) {
                    const cx = W * (0.5 + 0.45 * Math.sin(t * 0.13 + k * 1.7)), cy = H * (0.5 + 0.4 * Math.cos(t * 0.17 + k * 2.3)), r = H * (0.9 + 0.3 * k);
                    const g = c.createRadialGradient(cx, cy, 0, cx, cy, r);
                    g.addColorStop(0, sc.rgba(pc, 0.28)); g.addColorStop(1, sc.rgba(pc, 0));
                    c.fillStyle = g; c.fillRect(0, 0, W, H);
                }
            }
            c.restore();
        }
    }
}
