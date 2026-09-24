// HeaderBar — hlavička okna aplikácie LatteOS (návrh V2): ‹ › · názov · [nástroje] · hľadanie · NET · okno.
// Nástroje aplikácie sa vkladajú ako deti (default property → tools).
import QtQuick
import Quickshell.Io
// NET: appId = názov .desktop súboru aplikácie (napr. latteos-subory); stav a prepnutie cez latte-net,
// platí od ďalšieho spustenia aplikácie (bubblewrap bez siete).

Rectangle {
    id: hb
    required property var theme
    property string title: ""
    property bool canBack: false
    property bool canForward: false
    property string searchPlaceholder: "Hľadať"
    property bool netVisible: true
    property bool netOn: true
    property string appId: ""
    Process { id: netStatus; running: hb.appId !== ""; command: ["latte-net", "status", hb.appId]
              stdout: StdioCollector { onStreamFinished: hb.netOn = this.text.trim() !== "off" } }
    Process { id: netSet }
    default property alias tools: toolRow.data
    signal back()
    signal forward()
    signal searchChanged(string text)
    signal searchSubmitted(string text)    // Enter v hľadaní
    signal closeRequested()
    signal netToggled(bool on)
    property alias searchText: search.text

    height: 52
    color: "transparent"

    Row {
        id: left
        anchors { left: parent.left; leftMargin: 10; verticalCenter: parent.verticalCenter }
        spacing: 4
        Rectangle {
            width: 76; height: 36; radius: 10; color: hb.theme.field
            Row {
                anchors.centerIn: parent
                IconButton { theme: hb.theme; glyph: "chevron-left"; enabledState: hb.canBack; onClicked: hb.back() }
                IconButton { theme: hb.theme; glyph: "chevron-right"; enabledState: hb.canForward; onClicked: hb.forward() }
            }
        }
        Row { id: toolRow; spacing: 2; leftPadding: 8; anchors.verticalCenter: parent.verticalCenter }
    }

    Text {
        anchors.centerIn: parent
        width: Math.min(implicitWidth, parent.width - left.width - right.width - 40)
        elide: Text.ElideMiddle
        text: hb.title; color: hb.theme.fg
        font { family: hb.theme.fontUi; pixelSize: 14; weight: Font.Bold }
    }

    Row {
        id: right
        anchors { right: parent.right; rightMargin: 10; verticalCenter: parent.verticalCenter }
        spacing: 8
        Rectangle {
            width: 230; height: 36; radius: 10; color: hb.theme.field
            border { color: search.activeFocus ? hb.theme.primary : "transparent"; width: 1 }
            Glyph { x: 10; anchors.verticalCenter: parent.verticalCenter; name: "search"; size: 15; color: hb.theme.fgDim }
            TextInput {
                id: search
                anchors { fill: parent; leftMargin: 32; rightMargin: 10 }
                verticalAlignment: TextInput.AlignVCenter; clip: true
                color: hb.theme.fg; selectionColor: hb.theme.primary
                font { family: hb.theme.fontUi; pixelSize: 13 }
                onTextChanged: hb.searchChanged(text)
                onAccepted: hb.searchSubmitted(text)
                Keys.onEscapePressed: { text = ""; focus = false }
            }
            Text {
                x: 32; anchors.verticalCenter: parent.verticalCenter; visible: search.text === ""
                text: hb.searchPlaceholder; color: hb.theme.fgDim
                font { family: hb.theme.fontUi; pixelSize: 13 }
            }
        }
        // NET: sieťový prístup aplikácie (bezpečnostný model F6) — zatiaľ iba zobrazenie
        Rectangle {
            visible: hb.netVisible
            width: netRow.implicitWidth + 16; height: 36; radius: 10
            color: hb.netOn ? Qt.rgba(hb.theme.primary.r, hb.theme.primary.g, hb.theme.primary.b, 0.14) : hb.theme.field
            Row {
                id: netRow; anchors.centerIn: parent; spacing: 6
                Rectangle { width: 8; height: 8; radius: 4; anchors.verticalCenter: parent.verticalCenter; color: hb.netOn ? hb.theme.primary : hb.theme.error }
                Text { text: "NET"; color: hb.theme.fg; font { family: hb.theme.fontUi; pixelSize: 12; weight: Font.ExtraBold } }
            }
            MouseArea {
                anchors.fill: parent
                onClicked: {
                    hb.netOn = !hb.netOn; hb.netToggled(hb.netOn);
                    if (hb.appId !== "") { netSet.command = ["latte-net", hb.netOn ? "on" : "off", hb.appId]; netSet.running = true; }
                }
            }
        }
        IconButton { theme: hb.theme; glyph: "x"; tip: "Zavrieť"; onClicked: hb.closeRequested() }
    }
    Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 2; color: hb.theme.primary; opacity: 0.55 }
}
