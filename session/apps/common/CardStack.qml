// CardStack — vrstvené karty oblastí (old/main_setting_v2.md §6–9): Softvér · Dáta · Hardvér · Účet ·
// Prostredie · Systém. Vždy je otvorená jedna karta so zoznamom stránok; ostatné sú zmenšené „chrbty“
// s názvom, súhrnom a stavom. Hlavné karty sa neposúvajú (§7) — posúva sa iba zoznam v otvorenej karte.
// Stav nikdy nenesie iba farba: symbol ● hotové · ◐ časť · ○ plán + text (§55).
// areas: [{ key, title, glyph, summary, pages: [{ key, label, glyph, status: "ready"|"partial"|"planned" }] }]
import QtQuick

Rectangle {
    id: stack
    required property var theme
    property var areas: []
    property string openArea: areas.length ? areas[0].key : ""
    property string current: ""          // kľúč stránky
    property string heading: "Nastavenia"
    property string headingGlyph: "settings"
    property bool homeActive: current === "domov"
    signal activated(string area, string page)
    signal homeRequested()
    signal contextRequested(string area, string page, string label, real x, real y)   // pravý klik na stránku

    readonly property int spineH: 50
    readonly property int overlap: 8
    readonly property int rowH: 36

    width: 262
    color: Qt.rgba(0, 0, 0, theme.mode === "dark" ? 0.18 : 0.04)

    function statusMark(s) { return s === "ready" ? "●" : (s === "partial" ? "◐" : "○"); }

    Column {
        id: top
        x: 0; y: 14; width: parent.width
        spacing: 6
        Row {
            x: 16; spacing: 10; height: 40
            Glyph { name: stack.headingGlyph; size: 22; color: stack.theme.primary; anchors.verticalCenter: parent.verticalCenter }
            Text {
                text: stack.heading; color: stack.theme.fg; anchors.verticalCenter: parent.verticalCenter
                font { family: stack.theme.fontDisplay; pixelSize: 20; weight: Font.DemiBold }
            }
        }
        Rectangle {   // Domov = stavový prehľad, nie ďalšia kategória (§5)
            x: 10; width: parent.width - 20; height: 40; radius: 10
            color: stack.homeActive ? Qt.rgba(stack.theme.primary.r, stack.theme.primary.g, stack.theme.primary.b, 0.16)
                                    : (hm.containsMouse ? stack.theme.hover : "transparent")
            Glyph { x: 12; anchors.verticalCenter: parent.verticalCenter; name: "home"; size: 18; color: stack.homeActive ? stack.theme.primary : stack.theme.fg }
            Text {
                x: 42; anchors.verticalCenter: parent.verticalCenter; text: "Domov · stav systému"; color: stack.theme.fg
                font { family: stack.theme.fontUi; pixelSize: 13; weight: stack.homeActive ? Font.Bold : Font.Medium }
            }
            MouseArea { id: hm; anchors.fill: parent; hoverEnabled: true; onClicked: stack.homeRequested() }
        }
    }

    // karty
    Item {
        id: deck
        anchors { left: parent.left; right: parent.right; top: top.bottom; topMargin: 10; bottom: parent.bottom; bottomMargin: 12 }
        readonly property real openH: Math.max(stack.spineH + 60, height - (stack.areas.length - 1) * (stack.spineH - stack.overlap))

        Repeater {
            model: stack.areas
            Rectangle {
                id: card
                required property var modelData
                required property int index
                readonly property bool open: stack.openArea === modelData.key
                readonly property int openIndex: stack.areas.findIndex(a => a.key === stack.openArea)
                readonly property var pages: modelData.pages || []
                readonly property int readyCount: pages.filter(p => p.status === "ready").length
                readonly property string areaStatus: readyCount === pages.length ? "ready" : (readyCount > 0 || pages.some(p => p.status === "partial") ? "partial" : "planned")

                x: 10; width: deck.width - 20
                y: index * (stack.spineH - stack.overlap) + (index > openIndex ? deck.openH - stack.spineH : 0)
                height: open ? deck.openH : stack.spineH
                z: open ? 100 : stack.areas.length - index        // vyššie karty ležia na nižších (chrbty)
                radius: 14
                color: open ? stack.theme.surface : Qt.tint(stack.theme.surface, Qt.rgba(stack.theme.fg.r, stack.theme.fg.g, stack.theme.fg.b, card.hovered ? 0.07 : 0.035))
                border { color: open ? Qt.rgba(stack.theme.primary.r, stack.theme.primary.g, stack.theme.primary.b, 0.55) : stack.theme.line; width: 1 }
                property bool hovered: spineMouse.containsMouse
                Behavior on y { NumberAnimation { duration: stack.theme.animMs; easing.type: Easing.OutCubic } }
                Behavior on height { NumberAnimation { duration: stack.theme.animMs; easing.type: Easing.OutCubic } }

                // chrbát karty: ikona · NÁZOV · súhrn · stav
                Item {
                    id: spine
                    width: parent.width; height: stack.spineH
                    Glyph {
                        x: 14; y: (stack.spineH - height) / 2 + (card.index > 0 ? stack.overlap / 2 : 0)
                        name: card.modelData.glyph; size: 18; color: card.open ? stack.theme.primary : stack.theme.fg
                    }
                    Column {
                        x: 44; width: parent.width - 80
                        y: (stack.spineH - height) / 2 + (card.index > 0 ? stack.overlap / 2 : 0)
                        Text {
                            text: card.modelData.title.toUpperCase(); color: stack.theme.fg
                            font { family: stack.theme.fontUi; pixelSize: 12; weight: Font.ExtraBold; letterSpacing: 0.9 }
                        }
                        Text {
                            width: parent.width; elide: Text.ElideRight
                            text: card.modelData.summary || ""; color: stack.theme.fgDim
                            font { family: stack.theme.fontUi; pixelSize: 11 }
                        }
                    }
                    Text {
                        anchors { right: parent.right; rightMargin: 14 }
                        y: (stack.spineH - height) / 2 + (card.index > 0 ? stack.overlap / 2 : 0)
                        text: stack.statusMark(card.areaStatus)
                        color: card.areaStatus === "planned" ? stack.theme.fgDim : stack.theme.primary
                        font { family: stack.theme.fontUi; pixelSize: 13 }
                    }
                    MouseArea {
                        id: spineMouse; anchors.fill: parent; hoverEnabled: true
                        onClicked: {
                            stack.openArea = card.modelData.key;
                            const first = card.pages.find(p => p.status !== "planned") || card.pages[0];
                            if (first) stack.activated(card.modelData.key, first.key);
                        }
                    }
                }

                // stránky otvorenej karty (posúvajú sa iba tie)
                Flickable {
                    visible: card.open
                    anchors { left: parent.left; right: parent.right; top: spine.bottom; bottom: parent.bottom; bottomMargin: 8 }
                    contentHeight: pagesCol.implicitHeight
                    clip: true; boundsBehavior: Flickable.StopAtBounds
                    Column {
                        id: pagesCol
                        width: parent.width
                        Repeater {
                            model: card.pages
                            Rectangle {
                                id: row
                                required property var modelData
                                readonly property bool active: stack.current === modelData.key
                                x: 6; width: pagesCol.width - 12; height: stack.rowH; radius: 9
                                color: active ? Qt.rgba(stack.theme.primary.r, stack.theme.primary.g, stack.theme.primary.b, 0.16)
                                              : (rm.containsMouse ? stack.theme.hover : "transparent")
                                opacity: modelData.status === "planned" ? 0.6 : 1
                                Glyph { x: 10; anchors.verticalCenter: parent.verticalCenter; name: row.modelData.glyph || "point"; size: 16; color: row.active ? stack.theme.primary : stack.theme.fg }
                                Text {
                                    x: 36; width: parent.width - 62; anchors.verticalCenter: parent.verticalCenter; elide: Text.ElideRight
                                    text: row.modelData.label; color: stack.theme.fg
                                    font { family: stack.theme.fontUi; pixelSize: 13; weight: row.active ? Font.Bold : Font.Medium }
                                }
                                Text {
                                    anchors { right: parent.right; rightMargin: 10; verticalCenter: parent.verticalCenter }
                                    text: stack.statusMark(row.modelData.status); color: row.modelData.status === "planned" ? stack.theme.fgDim : stack.theme.primary
                                    font { family: stack.theme.fontUi; pixelSize: 11 }
                                }
                                MouseArea { id: rm; anchors.fill: parent; hoverEnabled: true; acceptedButtons: Qt.LeftButton | Qt.RightButton
                                            onClicked: (m) => { if (m.button === Qt.RightButton) { const q = mapToItem(null, m.x, m.y); stack.contextRequested(card.modelData.key, row.modelData.key, row.modelData.label, q.x, q.y); }
                                                                else stack.activated(card.modelData.key, row.modelData.key); } }
                            }
                        }
                    }
                }
            }
        }
    }
    Rectangle { anchors.right: parent.right; width: 1; height: parent.height; color: stack.theme.line }
}
