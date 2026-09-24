// LatteOS — živá tapeta: pokojné pohyblivé textúry podľa materiálu témy nad tapetou, pod oknami.
// Vrstva Bottom, priehľadná a neklikateľná (klik prejde na plochu). Jeden časovač hýbe desiatkami malých
// prvkov (žiadne shadery — beží aj pri softvérovom kreslení, stojí však CPU; vo VM je predvolene vypnutá).
// Scéna: ~/.config/latteos/live-wallpaper = tema | para | bublinky | sneh | iskry | trblietky | prach
// V hernom režime (~/.local/state/latteos/game-mode) stojí. Spúšťa: latte-app zivatapeta (hyprland.lua pri štarte).
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import "common"

ShellRoot {
    id: live
    LatteTheme { id: theme }

    readonly property string cfg: (Quickshell.env("XDG_CONFIG_HOME") || ((Quickshell.env("HOME") || "") + "/.config")) + "/latteos"
    readonly property string state: (Quickshell.env("XDG_STATE_HOME") || ((Quickshell.env("HOME") || "") + "/.local/state")) + "/latteos"
    property string pref: Quickshell.env("LATTE_APP_ARGS") || ""
    property string material: "sklo"
    property bool game: false
    readonly property var byMaterial: ({ sklo: "para", jantar: "bublinky", mraz: "sneh", kov: "iskry", fazety: "trblietky", kamen: "prach" })
    readonly property string scene: (pref === "" || pref === "tema") ? (byMaterial[material] || "") : pref
    readonly property bool running: scene !== "" && !game

    FileView { path: live.cfg + "/live-wallpaper"; printErrors: false; watchChanges: true; onFileChanged: reload()
               onLoaded: if (Quickshell.env("LATTE_APP_ARGS") === "") live.pref = text().trim() || "tema"
               onLoadFailed: if (Quickshell.env("LATTE_APP_ARGS") === "") Qt.quit() }       // vypnuté → skončiť
    FileView { path: "/usr/share/latteos/themes/" + theme.themeId + ".theme"; printErrors: false
               onLoaded: { const m = text().match(/^material = (\w+)/m); live.material = m ? m[1] : ""; } }
    FileView { path: live.state + "/game-mode"; printErrors: false; watchChanges: true; onFileChanged: reload()
               onLoaded: live.game = text().trim() === "1"; onLoadFailed: live.game = false }

    // parametre scén: počet, smer (vy < 0 = hore), veľkosť, tvar, trvanie života v krokoch
    readonly property var scenes: ({
        para:      { n: 22, vx: 0.15, vy: -0.9, size: [30, 90], round: true,  alpha: 0.05, life: 420, spawn: "bottom", wobble: 0.6, color: "fg" },
        bublinky:  { n: 26, vx: 0.0,  vy: -0.7, size: [6, 22],   round: true,  alpha: 0.35, life: 400, spawn: "bottom", wobble: 0.4, ring: true, color: "primary" },
        sneh:      { n: 40, vx: 0.2,  vy: 0.8,  size: [3, 8],    round: true,  alpha: 0.55, life: 700, spawn: "top",    wobble: 0.8, color: "fg" },
        iskry:     { n: 6,  vx: 3.5,  vy: 0.0,  size: [180, 320], round: false, alpha: 0.06, life: 260, spawn: "left",   wobble: 0.0, streak: true, color: "fg" },
        trblietky: { n: 30, vx: 0.0,  vy: 0.0,  size: [3, 7],    round: true,  alpha: 0.8,  life: 90,  spawn: "any",    wobble: 0.0, twinkle: true, color: "primary" },
        prach:     { n: 30, vx: 0.12, vy: -0.05, size: [2, 5],   round: true,  alpha: 0.35, life: 900, spawn: "any",    wobble: 0.3, color: "fg" }
    })

    Variants {
        model: Quickshell.screens
        PanelWindow {
            id: win
            required property var modelData
            screen: modelData
            anchors { top: true; bottom: true; left: true; right: true }
            exclusionMode: ExclusionMode.Ignore
            WlrLayershell.layer: WlrLayer.Bottom
            WlrLayershell.namespace: "latte-live-wallpaper"
            WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
            color: "transparent"
            mask: Region {}                       // klik prejde na plochu pod ňou
            visible: live.scene !== ""

            property var parts: []
            property int frame: 0             // polia v JS objektoch nie sú sledované → väzby závisia od frame
            readonly property var sp: live.scenes[live.scene] || live.scenes.para
            function spawn(p, fresh) {
                const s = sp, w = win.width, h = win.height;
                p.size = s.size[0] + Math.random() * (s.size[1] - s.size[0]);
                // prvé rozmiestnenie po celej obrazovke, ďalšie zrodenie na okraji, odkiaľ scéna prichádza
                p.x = (s.spawn === "left" && !fresh) ? -p.size : Math.random() * w;
                p.y = fresh || s.spawn === "any" || s.spawn === "left" ? Math.random() * h : (s.spawn === "bottom" ? h + p.size : -p.size);
                p.age = fresh ? Math.floor(Math.random() * s.life) : 0;
                p.seed = Math.random() * 6.28;
                return p;
            }
            function reset() { const a = []; for (let i = 0; i < sp.n; i++) a.push(spawn({}, true)); parts = a; }
            // rozmiestniť až keď okno pozná veľkosť (pri vytvorení je 0 × 0)
            onWidthChanged: if (width > 0 && height > 0) reset()
            onHeightChanged: if (width > 0 && height > 0) reset()
            onSpChanged: if (width > 0 && height > 0) reset()

            Timer {
                interval: 50; repeat: true; running: live.running && win.visible     // 20 obr/s, v hernom režime stojí
                onTriggered: {
                    const s = win.sp, a = win.parts;
                    for (const p of a) {
                        p.age++;
                        p.x += s.vx * (1 + p.size / 60) + Math.sin(p.age / 30 + p.seed) * s.wobble;
                        p.y += s.vy * (1 + p.size / 80);
                        const out = (s.vy < 0 && p.y < -p.size * 2) || (s.vy > 0 && p.y > win.height + p.size * 2)
                                 || (s.vx > 1 && p.x > win.width + p.size) || p.age > s.life;
                        if (out) win.spawn(p, false);
                    }
                    win.frame++;
                }
            }
            Repeater {
                model: win.parts.length
                Rectangle {
                    required property int index
                    readonly property var p: (win.frame, win.parts[index]) || { x: 0, y: 0, size: 0, age: 0, seed: 0 }
                    readonly property var s: win.sp
                    x: (win.frame, p.x); y: (win.frame, p.y)
                    width: (win.frame, p.size); height: s.streak ? 2 : (win.frame, p.size)
                    radius: s.round ? height / 2 : 1
                    rotation: s.streak ? -12 : 0
                    color: s.ring ? "transparent" : (s.color === "primary" ? theme.primary : theme.fg)
                    border { width: s.ring ? 1.5 : 0; color: theme.primary }
                    // mäkký nástup a doznenie; trblietky blikajú
                    opacity: (win.frame, s.alpha) * (s.twinkle ? Math.max(0, Math.sin(p.age / s.life * 3.14159))
                                                  : Math.min(1, p.age / 30, (s.life - p.age) / 40))
                }
            }
        }
    }
}
