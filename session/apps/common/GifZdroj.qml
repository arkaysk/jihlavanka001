// GifZdroj — jeden zdroj GIF / WebP textúry pre okná L, dlaždicu na lište aj náhľad v Nastaveniach (rovnaký obraz všade).
//   image     skrytý AnimatedImage (určuje aktuálny snímok a časovanie)
//   frameDir  snímky ako PNG (latte-tapety snimky) — Canvas by z AnimatedImage kreslil stále prvý snímok
//   ohnisko   kde sa v animácii niečo hýbe (podiel šírky/výšky); ostrov na lište ho ukáže. Vypnuté voľbou
//             „celý obrázok“ (~/.config/latteos/bar-priblizenie = off) → obraz sa iba vyplní a vycentruje.
import QtQuick
import Quickshell
import Quickshell.Io

Item {
    id: gz
    property string spec: ""
    property bool playing: true
    readonly property bool isFile: spec.startsWith("file:")
    readonly property alias image: gif
    property string frameDir: ""
    property int frameCount: 0
    property var focusRaw: null
    property bool zoom: true
    readonly property var ohnisko: zoom ? focusRaw : null
    visible: false

    FileView { path: (Quickshell.env("XDG_CONFIG_HOME") || ((Quickshell.env("HOME") || "") + "/.config")) + "/latteos/bar-priblizenie"
               printErrors: false; watchChanges: true; onFileChanged: reload()
               onLoaded: gz.zoom = text().trim() !== "off"; onLoadFailed: gz.zoom = true }
    AnimatedImage {
        id: gif
        visible: false
        source: gz.isFile ? "file://" + gz.spec.slice(5) : ""
        // až po načítaní (zdroj sa mení za behu, keď sa načíta bar-scene; inak by AnimatedImage ostal stáť)
        playing: status === AnimatedImage.Ready && gz.isFile && gz.playing
        cache: false; asynchronous: true
    }
    // priamo zo spec (v onSpecChanged ešte nemusia byť prepočítané odvodené vlastnosti)
    function loadFrames() {
        frameDir = ""; frameCount = 0; focusRaw = null;
        if (/^file:.*\.(gif|webp)$/i.test(spec)) { frames.running = false; frames.command = ["latte-tapety", "snimky", spec.slice(5)]; frames.running = true; }
    }
    onSpecChanged: loadFrames()
    Component.onCompleted: loadFrames()
    Process {
        id: frames
        stdout: StdioCollector { onStreamFinished: { try { const j = JSON.parse(this.text); gz.frameCount = j.count; gz.focusRaw = j.focus || null; gz.frameDir = j.dir; } catch (e) {} } }
    }
}
