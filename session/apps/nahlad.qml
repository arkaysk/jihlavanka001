// LatteOS — živý náhľad okna nad oválom okien na lište (zadanie 24. 9., bod 3): keď myš podrží ikonu okna,
// widget latteos/okna zapíše jeho adresu do ~/.local/state/latteos/nahlad a tu sa nad kurzorom ukáže
// živý obraz okna (ScreencopyView cez Hyprland toplevel export) s názvom. Klik na náhľad prepne na okno.
// Pri softvérovom kreslení sa obraz obnovuje iba 4× za sekundu (šetrí CPU). Spúšťa: latte-app nahlad.
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Quickshell.Hyprland
import "common"

ShellRoot {
    id: nh
    LatteTheme { id: theme }

    readonly property string state: (Quickshell.env("XDG_STATE_HOME") || ((Quickshell.env("HOME") || "") + "/.local/state")) + "/latteos"
    readonly property bool cheap: ["softver", "safe", "minimalny"].includes(Quickshell.env("LATTE_TIER") || "softver")
    property string addr: ""
    property int cx: 0
    property var top: null                      // HyprlandToplevel
    property bool overPreview: false

    FileView {
        path: nh.state + "/nahlad"; printErrors: false; watchChanges: true; onFileChanged: reload()
        onLoaded: nh.want(text().trim())
        onLoadFailed: nh.want("")
    }
    // krátke oneskorenie: náhľad až po zastavení myši nad ikonou, zmiznutie až po odchode aj z náhľadu
    Timer { id: showT; interval: 350; onTriggered: { Hyprland.refreshToplevels(); pos.running = true; } }
    Timer { id: hideT; interval: 250; onTriggered: if (!nh.overPreview) nh.addr = "" }
    property string pending: ""
    function want(a) {
        pending = a.replace(/^0x/, "");
        if (pending !== "") { hideT.stop(); showT.restart(); } else { showT.stop(); hideT.restart(); }
    }
    Process {
        id: pos
        command: ["hyprctl", "cursorpos"]
        stdout: StdioCollector {
            onStreamFinished: {
                const m = this.text.match(/(-?\d+),\s*(-?\d+)/);
                if (m) nh.cx = parseInt(m[1]);
                nh.addr = nh.pending;
            }
        }
    }
    onAddrChanged: top = addr === "" ? null : (Hyprland.toplevels.values.find(t => t.address === addr || t.address === "0x" + addr) || null)

    PanelWindow {
        id: win
        visible: nh.top !== null && nh.top.wayland !== null
        anchors { bottom: true; left: true }
        margins { bottom: 74; left: Math.max(8, nh.cx - width / 2) }
        implicitWidth: 300; implicitHeight: 210
        exclusionMode: ExclusionMode.Ignore
        WlrLayershell.layer: WlrLayer.Top               // pod panelmi Noctalie (ponuka okna ho prekryje)
        WlrLayershell.namespace: "latte-nahlad"
        WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
        color: "transparent"

        Rectangle {
            anchors.fill: parent; radius: 16
            color: theme.surface; border { color: theme.outline; width: 1 }
            Column {
                anchors { fill: parent; margins: 10 }
                spacing: 8
                Text {
                    width: parent.width; elide: Text.ElideRight
                    text: nh.top ? nh.top.title : ""
                    color: theme.fg; font { family: theme.fontUi; pixelSize: 12; weight: Font.DemiBold }
                }
                ScreencopyView {
                    id: shot
                    width: parent.width; height: parent.height - 26
                    captureSource: win.visible && nh.top ? nh.top.wayland : null
                    live: !nh.cheap
                    constraintSize: Qt.size(width, height)
                    Timer { interval: 250; repeat: true; running: nh.cheap && win.visible; onTriggered: shot.captureFrame() }
                    Text { anchors.centerIn: parent; visible: !shot.hasContent; text: "…"; color: theme.fgDim; font.pixelSize: 20 }
                }
            }
            MouseArea {
                anchors.fill: parent; hoverEnabled: true
                onEntered: { nh.overPreview = true; hideT.stop(); }
                onExited: { nh.overPreview = false; hideT.restart(); }
                onClicked: { act.command = ["hyprctl", "eval", 'latte.win.activate("0x' + nh.addr + '")']; act.running = true; nh.addr = ""; }
            }
        }
    }
    Process { id: act }
}
