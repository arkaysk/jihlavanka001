// TileOverlay — textúra ostrova na lište pre GIF / obrázok (zadanie 25. 9.): Noctalia v dlaždici kreslí iba svoje textúry
// (para, matrix, farba), preto GIF nad ostrov dokreslí táto vrstva. Ukazuje presne ten výsek spoločného plátna, ktorý
// je v okne v tvare L pätou, takže po otvorení okna obraz plynule pokračuje do kmeňa. Ikona je v strede vždy.
// Kliknutia prepúšťa (prázdna maska) na dlaždicu Noctalie pod ňou. GIF je jeden (image) a zdieľa ho aj LPopup.
//   hrá: pohyb „vždy“ (bar-anim) alebo keď je okno otvorené; v hernom režime stojí a vrstva sa skryje.
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland

Scope {
    id: to
    required property var theme
    property var foot: ({ x: 12, y: 896, w: 100, h: 42 })
    property string spec: "para"
    property string motion: "vzdy"          // vzdy | vypnute (z bar-anim)
    property bool popupOpen: false
    property string glyph: "apps"
    property bool mirror: false
    property real footRadius: 16
    // spoločné plátno okna L (rovnaké čísla ako LPopup: ox/oy výseku päty, rozmer plátna)
    property real canvasW: 660
    property real canvasH: 100
    property real ox: 0
    property real oy: 50
    readonly property bool isFile: spec.startsWith("file:")
    readonly property alias image: gif
    // snímky GIF ako PNG (Canvas by inak kreslil stále prvý snímok)
    property string frameDir: ""
    property int frameCount: 0
    property var ohnisko: null
    readonly property bool animated: isFile && /\.(gif|webp)$/i.test(spec)
    // priamo zo spec (v onSpecChanged ešte nemusí byť prepočítané „animated“)
    function loadFrames() {
        frameDir = ""; frameCount = 0; ohnisko = null;
        if (/^file:.*\.(gif|webp)$/i.test(spec)) { frames.running = false; frames.command = ["latte-tapety", "snimky", spec.slice(5)]; frames.running = true; }
    }
    onSpecChanged: loadFrames()
    Component.onCompleted: loadFrames()
    Process {
        id: frames
        stdout: StdioCollector { onStreamFinished: { try { const j = JSON.parse(this.text); to.frameCount = j.count; to.ohnisko = j.focus || null; to.frameDir = j.dir; } catch (e) {} } }
    }
    property bool game: false
    FileView { path: (Quickshell.env("XDG_STATE_HOME") || ((Quickshell.env("HOME") || "") + "/.local/state")) + "/latteos/game-mode"
               printErrors: false; watchChanges: true; onFileChanged: reload()
               onLoaded: to.game = text().trim() === "1"; onLoadFailed: to.game = false }

    PanelWindow {
        visible: to.isFile && !to.game && to.foot.w > 0
        anchors { top: true; left: true }
        margins { left: to.foot.x; top: to.foot.y }
        implicitWidth: to.foot.w; implicitHeight: to.foot.h
        exclusionMode: ExclusionMode.Ignore
        WlrLayershell.layer: WlrLayer.Top
        WlrLayershell.namespace: "latte-dlazdica"
        WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
        mask: Region {}                      // kliknutie prejde na dlaždicu Noctalie
        color: "transparent"
        AnimatedImage {
            id: gif
            visible: false
            source: to.isFile ? "file://" + to.spec.slice(5) : ""
            // až po načítaní (zdroj sa mení za behu, keď sa načíta bar-scene; inak by AnimatedImage ostal stáť)
            playing: status === AnimatedImage.Ready && to.isFile && !to.game && (to.motion === "vzdy" || to.popupOpen)
            cache: false; asynchronous: true
        }
        Scena {
            anchors.fill: parent
            colors: to.theme; spec: to.spec; image: gif; mirror: to.mirror; frameDir: to.frameDir; frameCount: to.frameCount
            radii: [to.footRadius, to.footRadius, to.footRadius, to.footRadius]
            ox: to.ox; oy: to.oy; canvasW: to.canvasW; canvasH: to.canvasH
            ohnisko: to.ohnisko; anchorX: to.ox + to.foot.w / 2; anchorY: to.canvasH - to.foot.h / 2
        }
        Rectangle {
            anchors.centerIn: parent; width: 30; height: 30; radius: 10
            color: Qt.rgba(to.theme.surfaceVariant.r, to.theme.surfaceVariant.g, to.theme.surfaceVariant.b, 0.85)
            Glyph { anchors.centerIn: parent; name: to.glyph; size: 18; color: to.theme.primary }
        }
    }
}
