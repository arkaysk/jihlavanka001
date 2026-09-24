// LatteOS — obrazovka prihlásenia (Quickshell + greetd).
// Spúšťa ju latte-greeter pod labwc s pixmanom a Qt software backendom: žiadne GL, žiadne GPU.
// Vzhľad podľa inspo/LatteOS – návrh plochy: teplé tmavé sklo, karamelový akcent, Manrope/Fraunces.
//
// Vstupy (premenné prostredia z latte-greeter):
//   LATTE_MODE (normal|safe), LATTE_RENDERER, LATTE_REASON — z /run/latteos (latte-boot select)
//   LATTE_GREETER_TEST=1 — náhľad bez greetd (tlačidlo Prihlásiť iba ukáže stav)
// Súbory (skupina latte smie zapisovať z Nastavení, greeter iba číta):
//   /var/lib/latteos/greeter/greeter.conf    background, color, dim, panel (log|text|none), panel_title, panel_text
//   /var/lib/latteos/greeter/last-crash.log  prvý log z posledného pádu (píše latte-session)
//   /var/lib/greetd/latte-recent             posledné dva prihlásené účty (píše greeter)
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Quickshell.Services.Greetd

ShellRoot {
    id: root

    // ── paleta Latte (session/noctalia/palettes/Latte.json) ──────────────────────
    readonly property color cBg: "#1B1410"
    readonly property color cGlass: Qt.rgba(38 / 255, 29 / 255, 23 / 255, 0.90)
    readonly property color cField: Qt.rgba(0, 0, 0, 0.28)
    readonly property color cOutline: Qt.rgba(243 / 255, 235 / 255, 221 / 255, 0.12)
    readonly property color cText: "#F3EBDD"
    readonly property color cDim: "#CDBCA6"
    readonly property color cAccent: "#E4B283"
    readonly property color cOnAccent: "#1E1712"
    readonly property color cError: "#E07A5F"
    readonly property string fUi: "Manrope"
    readonly property string fDisplay: "Fraunces"

    readonly property string mode: Quickshell.env("LATTE_MODE") || "safe"
    readonly property string renderer: Quickshell.env("LATTE_RENDERER") || "pixman"
    readonly property string reason: Quickshell.env("LATTE_REASON") || ""
    readonly property bool testMode: Quickshell.env("LATTE_GREETER_TEST") === "1"

    // relácie: LatteOS spustí režim zvolený pri štarte, LatteOS SAFE vynúti núdzový režim
    readonly property var sessions: [
        { name: "LatteOS", cmd: ["/usr/bin/latte-session"], hint: "Hyprland + Noctalia" },
        { name: "LatteOS SAFE", cmd: ["/usr/bin/latte-session", "safe"], hint: "labwc, bez GPU" }
    ]
    property int sessionIndex: mode === "safe" ? 1 : 0

    property string status: ""
    property bool statusError: false
    property bool busy: false

    // ── vzhľad z Nastavení › Účet › Prihlasovanie ──────────────────────────────
    property var conf: ({ background: "/usr/share/backgrounds/latteos/latteos-wallpaper1.jpg", color: "#1B1410",
                          dim: "0.55", panel: "log", panel_title: "", panel_text: "" })
    property string crashLog: ""
    FileView {
        path: "/var/lib/latteos/greeter/greeter.conf"
        printErrors: false
        onLoaded: {
            const c = Object.assign({}, root.conf);
            for (const l of text().split("\n")) { const r = l.match(/^\s*(\w+)\s*=\s*"(.*)"\s*$/); if (r) c[r[1]] = r[2].replace(/\\n/g, "\n"); }
            root.conf = c;
        }
    }
    FileView {
        path: "/var/lib/latteos/greeter/last-crash.log"
        printErrors: false
        onLoaded: root.crashLog = text().trim()
    }
    readonly property bool panelVisible: conf.panel === "text" ? conf.panel_text !== "" : conf.panel === "log"

    // ── používatelia: prvý bežný účet z /etc/passwd, alebo naposledy prihlásený ───
    property string lastUser: ""
    property var users: []
    property var recent: []          // posledné dva prihlásené účty (najnovší prvý)
    property var fullNames: ({})

    FileView {
        path: "/etc/passwd"
        onLoaded: {
            const list = [], names = {};
            for (const line of text().split("\n")) {
                const f = line.split(":");
                const uid = parseInt(f[2]);
                if (f.length > 6 && uid >= 1000 && uid < 60000 && !f[6].endsWith("nologin")) {
                    list.push(f[0]);
                    names[f[0]] = (f[4] || "").split(",")[0] || f[0];
                }
            }
            root.users = list;
            root.fullNames = names;
        }
    }
    FileView {
        id: lastUserFile
        path: "/var/lib/greetd/latte-last-user"
        printErrors: false
        onLoaded: root.lastUser = text().trim()
    }
    FileView {
        path: "/var/lib/greetd/latte-recent"
        printErrors: false
        onLoaded: root.recent = text().split("\n").map(x => x.trim()).filter(x => x !== "").slice(0, 2)
    }
    readonly property var recentUsers: {
        const r = recent.filter(u => users.indexOf(u) >= 0);
        if (r.length === 0 && lastUser !== "" && users.indexOf(lastUser) >= 0) r.push(lastUser);
        return r.slice(0, 2);
    }

    function defaultUser() {
        if (recentUsers.length > 0) return recentUsers[0];
        return users.length > 0 ? users[0] : "";
    }

    // ── greetd ────────────────────────────────────────────────────────────────
    property string pendingPassword: ""

    function login(user, password) {
        if (user === "") { setStatus("Zadaj meno používateľa.", true); return; }
        if (testMode || !Greetd.available) {
            setStatus("Náhľad: greetd nebeží, prihlásenie sa nevykoná (" + sessions[sessionIndex].name + ").", false);
            return;
        }
        busy = true;
        pendingPassword = password;
        setStatus("Overujem…", false);
        Greetd.createSession(user);
    }

    function setStatus(text, isError) { status = text; statusError = isError; }

    Connections {
        target: Greetd
        function onAuthMessage(message, error, responseRequired, echoResponse) {
            if (responseRequired) {
                Greetd.respond(root.pendingPassword);
                root.pendingPassword = "";
            } else if (message !== "") {
                root.setStatus(message, error);
            }
        }
        function onAuthFailure(message) {
            root.busy = false;
            root.pendingPassword = "";
            root.setStatus("Nesprávne heslo alebo meno.", true);
            Greetd.cancelSession();
            passwordFocus.start();
        }
        function onReadyToLaunch() {
            root.setStatus("Spúšťam " + root.sessions[root.sessionIndex].name + "…", false);
            saveUser.running = true;
            Greetd.launch(root.sessions[root.sessionIndex].cmd);
        }
        function onError(error) {
            root.busy = false;
            root.setStatus("greetd: " + error, true);
        }
    }

    Process {
        id: saveUser
        command: ["sh", "-c", "printf '%s\\n' \"$1\" > /var/lib/greetd/latte-last-user; { printf '%s\\n' \"$1\"; grep -vx \"$1\" /var/lib/greetd/latte-recent 2>/dev/null | head -1; } > /var/lib/greetd/latte-recent.new && mv -f /var/lib/greetd/latte-recent.new /var/lib/greetd/latte-recent", "sh", Greetd.user]
    }
    Process { id: reboot; command: ["systemctl", "reboot"] }
    Process { id: poweroff; command: ["systemctl", "poweroff"] }

    Timer { id: passwordFocus; interval: 50; onTriggered: root.focusPassword() }
    signal focusPassword()

    // ── obrazovka (na každom monitore) ────────────────────────────────────────
    Variants {
        model: Quickshell.screens

        PanelWindow {
            id: win
            required property var modelData
            screen: modelData
            anchors { top: true; bottom: true; left: true; right: true }
            exclusionMode: ExclusionMode.Ignore
            WlrLayershell.layer: WlrLayer.Overlay
            WlrLayershell.keyboardFocus: WlrKeyboardFocus.Exclusive
            WlrLayershell.namespace: "latte-greeter"
            color: root.conf.color || root.cBg

            Image {
                anchors.fill: parent
                visible: root.conf.background !== ""
                source: root.conf.background !== "" ? "file://" + root.conf.background : ""
                fillMode: Image.PreserveAspectCrop
                asynchronous: true
                smooth: false          // pixman/software: lacnejšie škálovanie
            }
            Rectangle { anchors.fill: parent; color: Qt.rgba(0.07, 0.05, 0.04, parseFloat(root.conf.dim) || 0) }

            // ľavý panel: vývojárska verzia = prvý log z posledného pádu; inak text používateľa
            // (neskôr RSS, novinky, počasie — Nastavenia › Účet › Prihlasovanie)
            Rectangle {
                id: sidePanel
                visible: root.panelVisible && win.width >= 1100
                anchors { left: parent.left; top: parent.top; bottom: parent.bottom; margins: 28; bottomMargin: 72 }
                width: Math.min(520, win.width * 0.3)
                radius: 16; color: root.cGlass; border { color: root.cOutline; width: 1 }
                clip: true
                readonly property bool isLog: root.conf.panel === "log"
                Column {
                    anchors { fill: parent; margins: 20 }
                    spacing: 10
                    Text {
                        text: sidePanel.isLog ? "Posledný pád" : (root.conf.panel_title || "Správa")
                        color: root.cText; font { family: root.fDisplay; pixelSize: 20; weight: Font.DemiBold }
                    }
                    Text {
                        visible: sidePanel.isLog
                        text: root.crashLog === "" ? "Žiadny zaznamenaný pád. ☕" : "Vývojárska verzia · /var/lib/latteos/greeter/last-crash.log"
                        color: root.cDim; font { family: root.fUi; pixelSize: 12 }
                    }
                    Rectangle { width: parent.width; height: 1; color: root.cOutline }
                    Text {
                        width: parent.width
                        height: sidePanel.height - 110
                        wrapMode: sidePanel.isLog ? Text.WrapAnywhere : Text.WordWrap
                        elide: Text.ElideRight
                        text: sidePanel.isLog ? root.crashLog : root.conf.panel_text
                        color: sidePanel.isLog ? root.cDim : root.cText
                        font { family: sidePanel.isLog ? "monospace" : root.fUi; pixelSize: sidePanel.isLog ? 11 : 14 }
                        textFormat: Text.PlainText
                    }
                }
            }

            // hodiny a dátum
            Column {
                anchors.horizontalCenter: parent.horizontalCenter
                y: parent.height * 0.12
                spacing: 2
                Text {
                    id: clock
                    anchors.horizontalCenter: parent.horizontalCenter
                    color: root.cText
                    font { family: root.fDisplay; pixelSize: Math.min(win.height * 0.11, 104); weight: Font.DemiBold }
                    text: Qt.formatTime(new Date(), "HH:mm")
                }
                Text {
                    id: date
                    anchors.horizontalCenter: parent.horizontalCenter
                    color: root.cDim
                    font { family: root.fUi; pixelSize: 18; weight: Font.Medium }
                    text: Qt.locale("sk_SK").toString(new Date(), "dddd d. MMMM")
                }
                Timer {
                    interval: 10000; running: true; repeat: true
                    onTriggered: { clock.text = Qt.formatTime(new Date(), "HH:mm"); date.text = Qt.locale("sk_SK").toString(new Date(), "dddd d. MMMM"); }
                }
            }

            // karta prihlásenia
            Rectangle {
                id: card
                width: Math.min(420, win.width - 32)
                height: content.implicitHeight + 48
                anchors.centerIn: parent
                anchors.verticalCenterOffset: win.height * 0.06
                radius: 16
                color: root.cGlass
                border { color: root.cOutline; width: 1 }

                Column {
                    id: content
                    anchors { left: parent.left; right: parent.right; top: parent.top; margins: 24 }
                    spacing: 14

                    Row {
                        spacing: 12
                        Image {
                            source: "file:///usr/share/latteos/noctalia/icons/latte-cup.png"
                            width: 40; height: 40; smooth: true
                        }
                        Column {
                            anchors.verticalCenter: parent.verticalCenter
                            Text { text: "LatteOS"; color: root.cText; font { family: root.fDisplay; pixelSize: 24; weight: Font.DemiBold } }
                            Text {
                                text: root.mode === "safe" ? "Režim SAFE" : "Pripravené"
                                color: root.mode === "safe" ? root.cAccent : root.cDim
                                font { family: root.fUi; pixelSize: 12; weight: Font.Bold }
                            }
                        }
                    }

                    // posledné dva účty: klik vyberie účet a presunie kurzor do hesla
                    Row {
                        visible: root.recentUsers.length > 0
                        spacing: 8
                        Repeater {
                            model: root.recentUsers
                            Rectangle {
                                id: chip
                                required property string modelData
                                readonly property bool picked: userInput.text === modelData
                                width: (content.width - 8) / 2; height: 52; radius: 12
                                color: picked ? Qt.rgba(228 / 255, 178 / 255, 131 / 255, 0.18) : root.cField
                                border { color: picked ? root.cAccent : "transparent"; width: 1 }
                                Rectangle {
                                    id: avatar
                                    x: 10; anchors.verticalCenter: parent.verticalCenter
                                    width: 34; height: 34; radius: 17; color: root.cAccent
                                    Text { anchors.centerIn: parent; text: chip.modelData.charAt(0).toUpperCase(); color: root.cOnAccent; font { family: root.fUi; pixelSize: 16; weight: Font.ExtraBold } }
                                }
                                Column {
                                    anchors { left: avatar.right; leftMargin: 10; right: parent.right; rightMargin: 8; verticalCenter: parent.verticalCenter }
                                    Text { width: parent.width; elide: Text.ElideRight; text: root.fullNames[chip.modelData] || chip.modelData; color: root.cText; font { family: root.fUi; pixelSize: 13; weight: Font.Bold } }
                                    Text { width: parent.width; elide: Text.ElideRight; text: chip.modelData; color: root.cDim; font { family: root.fUi; pixelSize: 11 } }
                                }
                                MouseArea { anchors.fill: parent; onClicked: { userInput.text = chip.modelData; passInput.forceActiveFocus(); } }
                            }
                        }
                    }

                    // meno
                    Rectangle {
                        width: parent.width; height: 44; radius: 12; color: root.cField
                        border { color: userInput.activeFocus ? root.cAccent : "transparent"; width: 1 }
                        TextInput {
                            id: userInput
                            anchors { fill: parent; leftMargin: 14; rightMargin: 14 }
                            verticalAlignment: TextInput.AlignVCenter
                            color: root.cText; selectionColor: root.cAccent
                            font { family: root.fUi; pixelSize: 15 }
                            text: root.defaultUser()
                            KeyNavigation.tab: passInput
                            onAccepted: passInput.forceActiveFocus()
                        }
                        Text {
                            anchors { left: parent.left; leftMargin: 14; verticalCenter: parent.verticalCenter }
                            visible: userInput.text === ""; text: "Meno"; color: root.cDim
                            font { family: root.fUi; pixelSize: 15 }
                        }
                    }

                    // heslo
                    Rectangle {
                        width: parent.width; height: 44; radius: 12; color: root.cField
                        border { color: passInput.activeFocus ? root.cAccent : "transparent"; width: 1 }
                        TextInput {
                            id: passInput
                            anchors { fill: parent; leftMargin: 14; rightMargin: 14 }
                            verticalAlignment: TextInput.AlignVCenter
                            color: root.cText; selectionColor: root.cAccent
                            echoMode: TextInput.Password; passwordCharacter: "•"
                            font { family: root.fUi; pixelSize: 15 }
                            focus: true
                            enabled: !root.busy
                            KeyNavigation.tab: userInput
                            onAccepted: { root.login(userInput.text.trim(), text); text = ""; }
                            Component.onCompleted: forceActiveFocus()
                            Connections { target: root; function onFocusPassword() { passInput.forceActiveFocus(); } }
                        }
                        Text {
                            anchors { left: parent.left; leftMargin: 14; verticalCenter: parent.verticalCenter }
                            visible: passInput.text === ""; text: "Heslo"; color: root.cDim
                            font { family: root.fUi; pixelSize: 15 }
                        }
                    }

                    // relácia
                    Row {
                        spacing: 8
                        Repeater {
                            model: root.sessions
                            Rectangle {
                                required property var modelData
                                required property int index
                                width: (content.width - 8) / 2; height: 48; radius: 12
                                color: root.sessionIndex === index ? Qt.rgba(228 / 255, 178 / 255, 131 / 255, 0.18) : root.cField
                                border { color: root.sessionIndex === index ? root.cAccent : "transparent"; width: 1 }
                                Column {
                                    anchors.centerIn: parent
                                    Text { anchors.horizontalCenter: parent.horizontalCenter; text: modelData.name; color: root.cText; font { family: root.fUi; pixelSize: 13; weight: Font.Bold } }
                                    Text { anchors.horizontalCenter: parent.horizontalCenter; text: modelData.hint; color: root.cDim; font { family: root.fUi; pixelSize: 11 } }
                                }
                                MouseArea { anchors.fill: parent; onClicked: { root.sessionIndex = index; passInput.forceActiveFocus(); } }
                            }
                        }
                    }

                    // prihlásiť
                    Rectangle {
                        width: parent.width; height: 46; radius: 12
                        color: root.busy ? Qt.darker(root.cAccent, 1.4) : root.cAccent
                        Text {
                            anchors.centerIn: parent
                            text: root.busy ? "Prihlasujem…" : "Prihlásiť"
                            color: root.cOnAccent; font { family: root.fUi; pixelSize: 15; weight: Font.ExtraBold }
                        }
                        MouseArea {
                            anchors.fill: parent; enabled: !root.busy
                            onClicked: { root.login(userInput.text.trim(), passInput.text); passInput.text = ""; }
                        }
                    }

                    Text {
                        width: parent.width; wrapMode: Text.WordWrap
                        visible: root.status !== ""
                        text: root.status
                        color: root.statusError ? root.cError : root.cDim
                        font { family: root.fUi; pixelSize: 13; weight: Font.Medium }
                    }
                }
            }

            // režim a dôvod (vľavo dole), napájanie (vpravo dole)
            Text {
                anchors { left: parent.left; bottom: parent.bottom; margins: 18 }
                width: win.width * 0.5; elide: Text.ElideRight
                color: root.cDim; opacity: 0.85
                font { family: root.fUi; pixelSize: 12 }
                text: "Režim " + root.mode.toUpperCase() + " · " + root.renderer + (root.reason !== "" ? " — " + root.reason : "")
            }
            Row {
                anchors { right: parent.right; bottom: parent.bottom; margins: 14 }
                spacing: 8
                Repeater {
                    model: [ { label: "Reštartovať", proc: reboot }, { label: "Vypnúť", proc: poweroff } ]
                    Rectangle {
                        required property var modelData
                        width: lbl.implicitWidth + 28; height: 36; radius: 12
                        color: root.cGlass; border { color: root.cOutline; width: 1 }
                        Text { id: lbl; anchors.centerIn: parent; text: modelData.label; color: root.cText; font { family: root.fUi; pixelSize: 13; weight: Font.DemiBold } }
                        MouseArea { anchors.fill: parent; onClicked: modelData.proc.running = true }
                    }
                }
            }
        }
    }
}
