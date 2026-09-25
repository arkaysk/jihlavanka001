// LatteOS — Správca zariadení (Device Manager). Podľa old/docs/nastavenia.md („Správca zdrojov“):
// zariadenia ako dlaždice (veľká ikona v zaoblenom štvorci, názov, stav) po skupinách; ukazuje zariadenia,
// nie ich obsah. Obrazovky: rozlíšenie a mierka s potvrdením do 15 s, inak sa zmena vráti (Enter = ponechať,
// Esc = vrátiť). Backend: latte-devices. Spúšťa sa: latte-app zariadenia [skupina|siete]
// Stav každého zariadenia (funguje / chýba firmvér / chýba balík / treba cudzí repozitár / nepodporované) a súhrn hore.
// Spolupráca aplikácií LatteOS: opravu urobí App Manager (Inštalátor, Aktualizácie › Ovládače), živé hodnoty a to,
// kto práve používa kameru/mikrofón/GPU, dodá Monitor (latte-sysmon senzory, sukromie). Záložka Siete: pripojenia, Wi-Fi, VPN.
import QtQuick
import Quickshell
import Quickshell.Io
import "common"

ShellRoot {
    id: app
    LatteTheme { id: theme }

    property string group: (Quickshell.env("LATTE_APP_ARGS") || "").trim() || "vsetko"
    property var groups: []
    property var problems: []
    property var faults: []
    property string summary: ""
    property var nets: ({ connections: [], wifi: [], addresses: [] })
    property var live: []                 // hodnoty z Monitora pre vybrané zariadenie
    property var uses: []                 // [ [mic|camera, aplikácia] ]
    Process { id: netProc; command: ["latte-devices", "siete"]
              stdout: StdioCollector { onStreamFinished: { try { app.nets = JSON.parse(this.text); } catch (e) {} } } }
    Timer { interval: 5000; repeat: true; running: app.group === "siete"; triggeredOnStart: true; onTriggered: if (!netProc.running) netProc.running = true }
    Process { id: liveProc; command: ["latte-sysmon", "senzory"]
              stdout: StdioCollector { onStreamFinished: {
                  let g = []; try { g = JSON.parse(this.text); } catch (e) {}
                  const pre = app.sel && app.sel.item.sensorPrefix ? app.sel.item.sensorPrefix : "";
                  const out = [];
                  for (const grp of g) for (const it of grp.items) if (pre && it.id.startsWith(pre)) out.push(it);
                  if (app.sel && app.sel.group === "pocitac" && /Core|Ryzen|CPU|Intel|AMD/i.test(app.sel.item.name)) for (const grp of g) if (grp.name.startsWith("Procesor")) for (const it of grp.items.slice(0, 6)) out.push(it);
                  app.live = out; } } }
    Process { id: useProc; command: ["latte-sysmon", "sukromie"]
              stdout: StdioCollector { onStreamFinished: app.uses = this.text.split("\n").filter(l => l).map(l => l.split("\t")) } }
    Timer { interval: 2000; repeat: true; running: !!app.sel; triggeredOnStart: true
            onTriggered: { if (!liveProc.running && (app.sel.item.sensorPrefix || app.sel.group === "pocitac")) liveProc.running = true;
                           if (!useProc.running && (app.sel.group === "kamery" || app.sel.group === "zvuk")) useProc.running = true; } }
    function fix(f) {                     // oprava cez App Manager (tímová práca aplikácií)
        if (f.packages && f.packages.length && !f.repo) run(["latte-app", "instalator", "--nazov=Ovládač_" + f.name.replace(/[^\w]+/g, "_").slice(0, 30), "install"].concat(f.packages), "App Manager inštaluje " + f.packages.join(", "));
        else run(["latte-app", "aplikacie", "aktualizacie"], "App Manager › Ovládače a firmvér");
    }
    property var sel: null            // { group, item }
    property string status: ""
    // obrazovka: skúšaný režim a odpočet
    property string pickMode: ""
    property real pickScale: 1
    property int countdown: 0
    property var trial: null          // { connector, mode, scale }
    property var audio: ({ sinks: [], sources: [], apps: [] })
    Process {
        id: audioProc; command: ["latte-devices", "audio"]
        stdout: StdioCollector { onStreamFinished: { try { app.audio = JSON.parse(this.text); } catch (e) {} } }
    }
    Timer { interval: 3000; repeat: true; running: !!app.sel && app.sel.group === "zvuk"; triggeredOnStart: true; onTriggered: audioProc.running = true }
    function audioCmd(args) { runner.command = ["latte-devices", "audio"].concat(args); runner.running = true; audioLater.restart(); }
    Timer { id: audioLater; interval: 300; onTriggered: audioProc.running = true }

    function count(n) { return n + (n === 1 ? " zariadenie" : (n >= 2 && n <= 4 ? " zariadenia" : " zariadení")); }
    readonly property var shownGroups: group === "vsetko" ? groups.filter(g => g.items.length > 0) : groups.filter(g => g.key === group)

    Process {
        id: listProc; running: true
        command: ["latte-devices", "list"]
        stdout: StdioCollector { onStreamFinished: { try { const d = JSON.parse(this.text); app.groups = d.groups; app.problems = d.problems; app.faults = d.faults || []; app.summary = d.summary || ""; app.refreshSel();
                                                                   if (!app.sel && app.group !== "vsetko") { const g = d.groups.find(x => x.key === app.group); if (g && g.items.length) app.pick(g, g.items[0]); } } catch (e) {} } }
    }
    Timer { interval: 10000; repeat: true; running: app.countdown === 0; onTriggered: listProc.running = true }
    function refreshSel() {
        if (!sel) return;
        const g = groups.find(x => x.key === sel.group);
        const it = g ? g.items.find(i => i.name === sel.item.name) : null;
        if (it) sel = { group: sel.group, item: it };
    }
    // pravý klik na zariadenie: akcie podľa skupiny + kopírovať informácie
    function deviceMenu(g, it, x, y) {
        const det = it.details || {};
        const info = it.name + "\n" + it.sub + Object.keys(det).map(k => "\n" + k + ": " + det[k]).join("");
        const items = [{ glyph: "info-circle", label: "Podrobnosti", action: () => app.pick(g, it) }];
        if (g.key === "disky" || g.key === "usb") {
            const dev = det["zariadenie"] || "";
            if (dev) {
                items.push({ glyph: "folder", label: "Otvoriť v Súboroch", action: () => app.run(["sh", "-c", 'm=$(lsblk -nro MOUNTPOINT "$1" | grep -m1 .); [ -n "$m" ] && exec latte-app subory "$m"; notify-send -a LatteOS "Disk nie je pripojený" "$1"', "sh", dev]) });
                if (g.key === "usb" || /usb/i.test(det["pripojenie"] || ""))
                    items.push({ glyph: "usb", label: "Bezpečne odobrať", action: () => app.run(["sh", "-c", 'for p in $(lsblk -nro PATH "$1" | tail -n +2) "$1"; do udisksctl unmount -b "$p" 2>/dev/null; done; udisksctl power-off -b "$1" && notify-send -a LatteOS "Môžeš odpojiť" "$2"', "sh", dev, it.name], "Odoberám " + it.name) });
            }
        }
        if (g.key === "siet") {
            const ifc = (it.name.match(/·\s*(\S+)$/) || [])[1] || "";
            if (ifc) {
                const on = (det["stav"] || "") === "connected";
                items.push({ glyph: on ? "world-off" : "world", label: on ? "Odpojiť" : "Pripojiť", action: () => app.run(["nmcli", "device", on ? "disconnect" : "connect", ifc], (on ? "Odpájam " : "Pripájam ") + ifc) });
            }
            items.push({ glyph: "settings", label: "Nastavenia siete", action: () => app.run(["latte-app", "nastavenia", "siet"]) });
        }
        if (g.key === "napajanie" && it.name === "Profil výkonu") {
            items.push({ separator: true });
            for (const pr of [["power-saver", "Úsporný"], ["balanced", "Vyvážený"], ["performance", "Výkonný"]])
                items.push({ glyph: "bolt", label: "Profil: " + pr[1], hint: it.sub === pr[1] ? "✓" : "", action: () => app.run(["powerprofilesctl", "set", pr[0]], "Profil výkonu: " + pr[1]) });
        }
        if (g.key === "grafika" || g.key === "pocitac") items.push({ glyph: "cpu", label: "Hardvér v Monitore", action: () => app.run(["latte-app", "monitor", "hardver"]) });
        if (g.key === "obrazovky") items.push({ glyph: "device-desktop", label: "Rozlíšenie a mierka", action: () => app.pick(g, it) });
        if (g.key === "vstup") items.push({ glyph: "keyboard", label: "Klávesnica a skratky", action: () => app.run(["latte-app", "nastavenia", "klavesnica"]) });
        items.push({ separator: true });
        items.push({ glyph: "clipboard", label: "Kopírovať informácie", action: () => app.run(["wl-copy", "--", info], "Skopírované: " + it.name) });
        ctx.open(x, y, items, it.name);
    }
    function pick(g, it) {
        sel = { group: g.key, item: it };
        if (g.key === "obrazovky" && it.mode) { pickMode = it.mode; pickScale = it.scale; }
    }

    Process { id: runner; onExited: listProc.running = true }
    Timer { id: netLater; interval: 1500; onTriggered: netProc.running = true }
    property string wifiSsid: ""
    property bool wifiSecure: false
    Process { id: wifiProc; stdinEnabled: true; onExited: (c) => { app.status = c === 0 ? "Pripojené: " + app.wifiSsid : "Pripojenie zlyhalo (heslo?)"; app.wifiSsid = ""; netLater.restart(); } }
    function wifiConnect(pw) { wifiProc.stdinEnabled = true; wifiProc.command = ["latte-devices", "wifi", wifiSsid]; wifiProc.running = true; wifiProc.write(pw + "\n"); wifiProc.stdinEnabled = false; status = "Pripájam " + wifiSsid + "…"; }
    function run(cmd, msg) { runner.command = cmd; runner.running = true; if (msg) app.status = msg; }

    // 15 s na potvrdenie, potom návrat (aj pri zatvorení okna)
    function tryDisplay() {
        const it = sel.item;
        trial = { connector: it.connector, mode: pickMode, scale: pickScale, before: it.mode, beforeScale: it.scale };
        run(["latte-devices", "display", "try", it.connector, pickMode, String(pickScale)], "Skúšam " + pickMode + " · mierka " + pickScale);
        countdown = 15; tick.start();
    }
    function keep() {
        if (!trial) return;
        tick.stop(); countdown = 0;
        run(["latte-devices", "display", "keep", trial.connector, trial.mode, String(trial.scale)], "Uložené: " + trial.mode + " · mierka " + trial.scale);
        trial = null;
    }
    function revert() {
        if (!trial) return;
        tick.stop(); countdown = 0;
        run(["latte-devices", "display", "try", trial.connector, trial.before, String(trial.beforeScale)], "Vrátené na " + trial.before);
        trial = null;
    }
    Timer { id: tick; interval: 1000; repeat: true; onTriggered: { app.countdown--; if (app.countdown <= 0) app.revert(); } }

    FloatingWindow {

        onClosed: Qt.quit()              // zavretie z kompozitora (✕ v titulku, Super+Q) ukončí aj proces
        id: win
        title: "Správca zariadení — LatteOS"
        implicitWidth: 1220; implicitHeight: 780
        color: theme.surface
        onVisibleChanged: if (!visible) app.revert()

        Item {
            id: root
            anchors.fill: parent
            focus: true
            Keys.onReturnPressed: app.keep()
            Keys.onEscapePressed: app.revert()

            SideBar {
                id: side
                theme: theme
                anchors { left: parent.left; top: parent.top; bottom: parent.bottom }
                heading: "Zariadenia"; headingGlyph: "cpu"
                current: app.group
                model: [
                    { title: "Prehľad", items: [{ key: "vsetko", glyph: "layout-grid", label: "Všetky zariadenia", sub: app.faults.length ? "⚠ " + app.summary : app.count(app.groups.reduce((n, g) => n + g.items.length, 0)) },
                                                { key: "siete", glyph: "network", label: "Siete", sub: "pripojenia, Wi-Fi, VPN" }] },
                    { title: "Skupiny", items: app.groups.map(g => ({ key: g.key, glyph: g.glyph, label: g.title, sub: g.items.length ? app.count(g.items.length) : "nič nepripojené", dim: g.items.length === 0 })) }
                ]
                onActivated: (it) => app.group = it.key
            }

            HeaderBar {
                id: header
                theme: theme
                anchors { left: side.right; right: parent.right; top: parent.top }
                title: app.group === "vsetko" ? "Všetky zariadenia" : (app.group === "siete" ? "Siete" : ((app.groups.find(g => g.key === app.group) || {}).title || ""))
                searchPlaceholder: "Hľadať zariadenie"
                netVisible: false
                onCloseRequested: { app.revert(); Qt.quit(); }
            }

            Flickable {
                id: content
                ScrollHint { flick: content; colors: theme }
                anchors { left: side.right; top: header.bottom; bottom: parent.bottom; right: detail.left; margins: 20 }
                contentHeight: col.implicitHeight + 20; clip: true
                Column {
                    id: col
                    width: content.width; spacing: 16
                    // súhrn (stará verzia: „Všetky zariadenia pracujú normálne“)
                    Rectangle {
                        visible: app.group === "vsetko" && app.summary !== ""
                        width: col.width; height: sumCol.implicitHeight + 24; radius: 14
                        color: app.faults.length ? Qt.rgba(theme.error.r, theme.error.g, theme.error.b, 0.1) : Qt.rgba(0.44, 0.7, 0.45, 0.12)
                        border { color: app.faults.length ? theme.error : "#6FB36F"; width: 1 }
                        Column {
                            id: sumCol; x: 14; y: 12; width: parent.width - 28; spacing: 8
                            Row { spacing: 8
                                  Glyph { name: app.faults.length ? "alert-triangle" : "check"; size: 18; color: app.faults.length ? theme.error : "#6FB36F"; anchors.verticalCenter: parent.verticalCenter }
                                  Text { text: app.summary; color: theme.fg; font { family: theme.fontUi; pixelSize: 15; weight: Font.Bold } } }
                            Repeater {
                                model: app.faults
                                Row {
                                    required property var modelData
                                    width: sumCol.width; spacing: 10
                                    Column { width: parent.width - 150; spacing: 1
                                             Text { width: parent.width; elide: Text.ElideRight; text: modelData.name + " · " + modelData.stateTitle; color: theme.fg; font { family: theme.fontUi; pixelSize: 12; weight: Font.DemiBold } }
                                             Text { width: parent.width; wrapMode: Text.WordWrap; text: modelData.reason; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 11 } } }
                                    Rectangle { width: 140; height: 30; radius: 9; color: theme.primary; anchors.verticalCenter: parent.verticalCenter
                                                Text { anchors.centerIn: parent; text: modelData.packages.length && !modelData.repo ? "Doinštalovať" : "App Manager"; color: theme.fgOnPrimary; font { family: theme.fontUi; pixelSize: 12; weight: Font.Bold } }
                                                MouseArea { anchors.fill: parent; onClicked: app.fix(modelData) } }
                                }
                            }
                        }
                    }
                    // ── záložka Siete ──
                    Column {
                        visible: app.group === "siete"
                        width: col.width; spacing: 8
                        Text { text: "ULOŽENÉ PRIPOJENIA"; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12; weight: Font.Bold; letterSpacing: 0.8 } }
                        Repeater {
                            model: app.nets.connections
                            Rectangle {
                                required property var modelData
                                width: col.width; height: 52; radius: 12; color: nm.containsMouse ? theme.hover : theme.field
                                border { color: modelData.active ? theme.primary : "transparent"; width: 1 }
                                Glyph { x: 14; anchors.verticalCenter: parent.verticalCenter; name: modelData.vpn ? "lock" : (modelData.type === "Wi-Fi" ? "wifi" : "network"); size: 20; color: modelData.active ? theme.primary : theme.fgDim }
                                Column { x: 46; anchors.verticalCenter: parent.verticalCenter
                                         Text { text: modelData.name; color: theme.fg; font { family: theme.fontUi; pixelSize: 13; weight: Font.Bold } }
                                         Text { text: modelData.type + (modelData.device ? " · " + modelData.device : "") + (modelData.active ? " · pripojené" : "") + (modelData.auto ? " · automaticky" : ""); color: theme.fgDim; font { family: theme.fontUi; pixelSize: 11 } } }
                                MouseArea { id: nm; anchors.fill: parent; hoverEnabled: true; acceptedButtons: Qt.LeftButton | Qt.RightButton
                                            onClicked: (m) => { const q = mapToItem(null, m.x, m.y), c = modelData;
                                                ctx.open(q.x, q.y, [
                                                    { glyph: c.active ? "world-off" : "world", label: c.active ? "Odpojiť" : "Pripojiť", action: () => { app.run(["latte-devices", "siet", c.active ? "odpoj" : "pripoj", c.name], (c.active ? "Odpájam " : "Pripájam ") + c.name); netLater.restart(); } },
                                                    { glyph: "settings", label: "Upraviť (nmtui)", action: () => app.run(["foot", "-e", "nmtui", "edit", c.name]) },
                                                    { separator: true },
                                                    { glyph: "trash", label: "Zabudnúť pripojenie", danger: true, action: () => { app.run(["latte-devices", "siet", "zabudni", c.name], "Zabudnuté: " + c.name); netLater.restart(); } }
                                                ], c.name); } }
                            }
                        }
                        Text { text: "WI-FI V OKOLÍ"; topPadding: 8; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12; weight: Font.Bold; letterSpacing: 0.8 } }
                        Text { visible: app.nets.wifi.length === 0; text: "Žiadna Wi-Fi karta alebo sieť v dosahu."; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 } }
                        Repeater {
                            model: app.nets.wifi
                            Rectangle {
                                required property var modelData
                                width: col.width; height: 40; radius: 10; color: wm.containsMouse ? theme.hover : theme.field
                                Text { x: 14; anchors.verticalCenter: parent.verticalCenter; text: (modelData.inUse ? "● " : "") + modelData.ssid; color: theme.fg; font { family: theme.fontUi; pixelSize: 13; weight: modelData.inUse ? Font.Bold : Font.Normal } }
                                Text { anchors { right: parent.right; rightMargin: 14; verticalCenter: parent.verticalCenter } text: (modelData.security ? "🔒 " : "") + modelData.signal + " %"; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 } }
                                MouseArea { id: wm; anchors.fill: parent; hoverEnabled: true; onClicked: { app.wifiSsid = modelData.ssid; app.wifiSecure = !!modelData.security; wifiPw.text = ""; if (!app.wifiSecure) app.wifiConnect(""); else wifiPw.forceActiveFocus(); } }
                            }
                        }
                        Rectangle {
                            visible: app.wifiSsid !== "" && app.wifiSecure
                            width: col.width; height: 44; radius: 10; color: theme.field; border { color: theme.primary; width: 1 }
                            Text { id: wlab; x: 12; anchors.verticalCenter: parent.verticalCenter; text: "Heslo pre " + app.wifiSsid + ":"; color: theme.fg; font { family: theme.fontUi; pixelSize: 12 } }
                            TextInput { id: wifiPw; anchors { left: wlab.right; leftMargin: 10; right: parent.right; rightMargin: 12; verticalCenter: parent.verticalCenter }
                                        echoMode: TextInput.Password; passwordCharacter: "•"; color: theme.fg; font { family: theme.fontUi; pixelSize: 13 }
                                        Keys.onReturnPressed: (ev) => { ev.accepted = true; app.wifiConnect(text); text = ""; }
                                        Keys.onEscapePressed: (ev) => { ev.accepted = true; app.wifiSsid = ""; } }
                        }
                        Text { text: "ADRESY: " + (app.nets.addresses.join(" · ") || "žiadne"); topPadding: 8; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 } }
                        Row { spacing: 8
                              Rectangle { width: vpnl.implicitWidth + 24; height: 32; radius: 9; color: vpm.containsMouse ? theme.hover : theme.field
                                          Text { id: vpnl; anchors.centerIn: parent; text: "Pridať VPN / pripojenie (nmtui)"; color: theme.fg; font { family: theme.fontUi; pixelSize: 12; weight: Font.Bold } }
                                          MouseArea { id: vpm; anchors.fill: parent; hoverEnabled: true; onClicked: app.run(["foot", "-e", "nmtui", "connect"]) } }
                              Rectangle { width: nsl.implicitWidth + 24; height: 32; radius: 9; color: nsm.containsMouse ? theme.hover : theme.field
                                          Text { id: nsl; anchors.centerIn: parent; text: "Nastavenia siete"; color: theme.fg; font { family: theme.fontUi; pixelSize: 12; weight: Font.Bold } }
                                          MouseArea { id: nsm; anchors.fill: parent; hoverEnabled: true; onClicked: app.run(["latte-app", "nastavenia", "siet"]) } } }
                    }
                    Repeater {
                        model: app.group === "siete" ? [] : app.shownGroups
                        Column {
                            id: grp
                            required property var modelData
                            width: col.width; spacing: 8
                            Text { text: grp.modelData.title.toUpperCase(); color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12; weight: Font.Bold; letterSpacing: 0.8 } }
                            Text { visible: grp.modelData.items.length === 0; text: "Nič nepripojené."; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 13 } }
                            Flow {
                                width: parent.width; spacing: 10
                                Repeater {
                                    model: grp.modelData.items
                                    Rectangle {
                                        id: tile
                                        required property var modelData
                                        readonly property bool picked: !!app.sel && app.sel.group === grp.modelData.key && app.sel.item.name === modelData.name
                                        width: (col.width - 10) / 2; height: 76; radius: 14
                                        color: picked ? Qt.rgba(theme.primary.r, theme.primary.g, theme.primary.b, 0.16) : (tm.containsMouse ? theme.hover : theme.field)
                                        border { color: picked ? theme.primary : "transparent"; width: 1.5 }
                                        Rectangle {   // veľká ikona v zaoblenom štvorci
                                            id: ico
                                            x: 12; anchors.verticalCenter: parent.verticalCenter
                                            width: 52; height: 52; radius: 14
                                            color: Qt.rgba(theme.primary.r, theme.primary.g, theme.primary.b, 0.14)
                                            Glyph { anchors.centerIn: parent; name: grp.modelData.glyph; size: 26; color: theme.primary }
                                        }
                                        Column {
                                            anchors { left: ico.right; leftMargin: 12; right: parent.right; rightMargin: 12; verticalCenter: parent.verticalCenter }
                                            spacing: 3
                                            Text { width: parent.width; elide: Text.ElideRight; text: tile.modelData.name; color: theme.fg; font { family: theme.fontUi; pixelSize: 14; weight: Font.Bold } }
                                            Text {
                                                width: parent.width; elide: Text.ElideRight
                                                text: (tile.modelData.state && tile.modelData.state !== "ok" && tile.modelData.state !== "off" ? "⚠ " + tile.modelData.stateTitle + " · " : ({ ok: "● ", warn: "! ", off: "○ " })[tile.modelData.status]) + tile.modelData.sub
                                                color: tile.modelData.status === "warn" ? theme.error : theme.fgDim
                                                font { family: theme.fontUi; pixelSize: 12 }
                                            }
                                        }
                                        MouseArea { id: tm; anchors.fill: parent; hoverEnabled: true; acceptedButtons: Qt.LeftButton | Qt.RightButton
                                                    onClicked: (m) => { app.pick(grp.modelData, tile.modelData); if (m.button === Qt.RightButton) { const q = mapToItem(null, m.x, m.y); app.deviceMenu(grp.modelData, tile.modelData, q.x, q.y); } }
                                                    onDoubleClicked: app.pick(grp.modelData, tile.modelData) }
                                    }
                                }
                            }
                        }
                    }
                    Text { visible: app.problems.length > 0; width: parent.width; wrapMode: Text.WordWrap; text: "! " + app.problems.join(" · "); color: theme.error; font { family: theme.fontUi; pixelSize: 12 } }
                }
            }

            // detail / nastavenia vybraného zariadenia
            Rectangle {
                id: detail
                anchors { right: parent.right; top: header.bottom; bottom: parent.bottom; margins: 14 }
                width: 320; radius: theme.radius
                color: Qt.rgba(0, 0, 0, theme.mode === "dark" ? 0.16 : 0.04); border { color: theme.line; width: 1 }
                Flickable {
                    id: rolovanie2
                    ScrollHint { flick: rolovanie2; colors: theme }
                    anchors { fill: parent; margins: 16 }
                    contentHeight: dcol.implicitHeight; clip: true
                    Column {
                        id: dcol
                        width: parent.width; spacing: 10
                        readonly property var it: app.sel ? app.sel.item : null
                        readonly property string g: app.sel ? app.sel.group : ""
                        Text { width: parent.width; wrapMode: Text.WordWrap; text: parent.it ? parent.it.name : "Vyber zariadenie"
                               color: theme.fg; font { family: theme.fontDisplay; pixelSize: 19; weight: Font.DemiBold } }
                        Text { width: parent.width; wrapMode: Text.WordWrap; text: parent.it ? parent.it.sub : "Klikni na dlaždicu. Zariadenie je vždy v jednej skupine podľa toho, čo robí."
                               color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 } }
                        Rectangle {        // stav zariadenia + oprava cez App Manager
                            visible: !!dcol.it && !!dcol.it.state
                            readonly property bool bad: !!dcol.it && dcol.it.state !== "ok" && dcol.it.state !== "off"
                            width: parent.width; height: stc.implicitHeight + 20; radius: 10
                            color: bad ? Qt.rgba(theme.error.r, theme.error.g, theme.error.b, 0.1) : theme.field
                            Column { id: stc; x: 10; y: 10; width: parent.width - 20; spacing: 6
                                Text { text: (parent.parent.bad ? "⚠ " : "● ") + (dcol.it ? dcol.it.stateTitle : ""); color: parent.parent.bad ? theme.error : theme.primary; font { family: theme.fontUi; pixelSize: 13; weight: Font.Bold } }
                                Text { visible: !!dcol.it && dcol.it.reason !== ""; width: parent.width; wrapMode: Text.WordWrap; text: dcol.it ? dcol.it.reason : ""; color: theme.fg; font { family: theme.fontUi; pixelSize: 12 } }
                                Rectangle { visible: parent.parent.bad || (!!dcol.it && dcol.it.reason.indexOf("RPM Fusion") >= 0); width: parent.width; height: 32; radius: 9; color: theme.primary
                                            Text { anchors.centerIn: parent; text: dcol.it && dcol.it.packages.length && !dcol.it.repo ? "Doinštalovať " + dcol.it.packages.join(", ") : "Riešiť v App Manageri › Ovládače"; color: theme.fgOnPrimary; font { family: theme.fontUi; pixelSize: 12; weight: Font.Bold } }
                                            MouseArea { anchors.fill: parent; onClicked: app.fix(dcol.it) } }
                            }
                        }
                        Column {           // živé hodnoty z Monitora
                            visible: app.live.length > 0
                            width: parent.width; spacing: 4
                            Text { text: "TERAZ (z Monitora)"; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 10; weight: Font.Bold; letterSpacing: 0.6 } }
                            Repeater { model: app.live.slice(0, 8)
                                Row { required property var modelData; width: dcol.width
                                      Text { width: parent.width - 90; elide: Text.ElideRight; text: modelData.label; color: theme.fg; font { family: theme.fontUi; pixelSize: 12 } }
                                      Text { width: 90; horizontalAlignment: Text.AlignRight; text: String(modelData.value).replace(".", ",") + " " + modelData.unit; color: theme.primary; font { family: theme.fontMono; pixelSize: 12; weight: Font.Bold } } } }
                        }
                        Text {             // kto práve používa kameru / mikrofón (Monitor)
                            visible: (dcol.g === "kamery" || dcol.g === "zvuk") && app.uses.length > 0
                            width: parent.width; wrapMode: Text.WordWrap; color: theme.error; font { family: theme.fontUi; pixelSize: 12; weight: Font.Bold }
                            text: app.uses.filter(u => (dcol.g === "kamery") === (u[0] === "camera")).map(u => "Práve používa: " + u[1]).join("\n")
                        }
                        Repeater {
                            model: parent.it ? Object.keys(parent.it.details) : []
                            Column {
                                required property string modelData
                                width: dcol.width; spacing: 1
                                Text { text: modelData.toUpperCase(); color: theme.fgDim; font { family: theme.fontUi; pixelSize: 10; weight: Font.Bold; letterSpacing: 0.6 } }
                                Text { width: parent.width; wrapMode: Text.WrapAnywhere; text: String(dcol.it.details[modelData]); color: theme.fg; font { family: theme.fontUi; pixelSize: 12 } }
                            }
                        }

                        // ── obrazovka: rozlíšenie a mierka ──
                        Column {
                            visible: dcol.g === "obrazovky" && !!dcol.it && !!dcol.it.modes
                            width: parent.width; spacing: 8
                            Text { text: "ROZLÍŠENIE"; topPadding: 6; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 11; weight: Font.Bold; letterSpacing: 0.6 } }
                            Flow {
                                width: parent.width; spacing: 6
                                Repeater {
                                    model: dcol.it && dcol.it.modes ? dcol.it.modes.slice(0, 12) : []
                                    Rectangle {
                                        required property string modelData
                                        readonly property bool on: app.pickMode === modelData
                                        width: mt.implicitWidth + 16; height: 28; radius: 8
                                        color: on ? Qt.rgba(theme.primary.r, theme.primary.g, theme.primary.b, 0.2) : theme.field
                                        border { color: on ? theme.primary : "transparent"; width: 1 }
                                        Text { id: mt; anchors.centerIn: parent; text: modelData.replace("x", " × ").replace("@", " · ") + " Hz"; color: theme.fg; font { family: theme.fontUi; pixelSize: 11 } }
                                        MouseArea { anchors.fill: parent; onClicked: app.pickMode = parent.modelData }
                                    }
                                }
                            }
                            Text { text: "MIERKA"; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 11; weight: Font.Bold; letterSpacing: 0.6 } }
                            Row {
                                spacing: 6
                                Repeater {
                                    // iba mierky s celočíselnou logickou veľkosťou (inak ich Hyprland odmietne a nechá 1)
                                    model: {
                                        const r = app.pickMode.match(/^(\d+)x(\d+)/);
                                        const w = r ? parseInt(r[1]) : 0, h = r ? parseInt(r[2]) : 0;
                                        return [1, 1.25, 1.5, 1.75, 2].filter(sc => sc === 1 || (Number.isInteger(w / sc) && Number.isInteger(h / sc)));
                                    }
                                    Rectangle {
                                        required property real modelData
                                        readonly property bool on: Math.abs(app.pickScale - modelData) < 0.01
                                        width: 50; height: 28; radius: 8
                                        color: on ? Qt.rgba(theme.primary.r, theme.primary.g, theme.primary.b, 0.2) : theme.field
                                        border { color: on ? theme.primary : "transparent"; width: 1 }
                                        Text { anchors.centerIn: parent; text: (modelData * 100) + " %"; color: theme.fg; font { family: theme.fontUi; pixelSize: 11 } }
                                        MouseArea { anchors.fill: parent; onClicked: app.pickScale = parent.modelData }
                                    }
                                }
                            }
                            Rectangle {
                                readonly property bool changed: !!dcol.it && (app.pickMode !== dcol.it.mode || Math.abs(app.pickScale - dcol.it.scale) > 0.01)
                                visible: app.countdown === 0
                                width: parent.width; height: 38; radius: 10
                                color: changed ? theme.primary : theme.field
                                Text { anchors.centerIn: parent; text: "Použiť"; font { family: theme.fontUi; pixelSize: 13; weight: Font.Bold }
                                       color: parent.changed ? theme.fgOnPrimary : theme.fgDim }
                                MouseArea { anchors.fill: parent; onClicked: if (parent.changed) app.tryDisplay() }
                            }
                            // potvrdenie do 15 s
                            Rectangle {
                                visible: app.countdown > 0
                                width: parent.width; height: cc.implicitHeight + 24; radius: 12; color: theme.field; border { color: theme.primary; width: 1.5 }
                                Column {
                                    id: cc
                                    x: 12; y: 12; width: parent.width - 24; spacing: 8
                                    Text { width: parent.width; wrapMode: Text.WordWrap; text: "Ponechať toto nastavenie? Návrat o " + app.countdown + " s."; color: theme.fg; font { family: theme.fontUi; pixelSize: 13; weight: Font.Bold } }
                                    Row {
                                        spacing: 8
                                        Rectangle { width: 110; height: 34; radius: 10; color: theme.primary
                                                    Text { anchors.centerIn: parent; text: "Ponechať (Enter)"; color: theme.fgOnPrimary; font { family: theme.fontUi; pixelSize: 12; weight: Font.Bold } }
                                                    MouseArea { anchors.fill: parent; onClicked: app.keep() } }
                                        Rectangle { width: 100; height: 34; radius: 10; color: theme.surface; border { color: theme.line; width: 1 }
                                                    Text { anchors.centerIn: parent; text: "Vrátiť (Esc)"; color: theme.fg; font { family: theme.fontUi; pixelSize: 12; weight: Font.Bold } }
                                                    MouseArea { anchors.fill: parent; onClicked: app.revert() } }
                                    }
                                }
                            }
                        }

                        // ── odkazy na nástroje podľa skupiny ──
                        component Link: Rectangle {
                            id: lk
                            property string glyph; property string label
                            signal clicked()
                            width: dcol.width; height: 36; radius: 10
                            color: lm.containsMouse ? theme.hover : theme.field
                            Row { x: 12; anchors.verticalCenter: parent.verticalCenter; spacing: 10
                                  Glyph { name: lk.glyph; size: 16; color: theme.fg }
                                  Text { text: lk.label; color: theme.fg; font { family: theme.fontUi; pixelSize: 13; weight: Font.DemiBold } } }
                            MouseArea { id: lm; anchors.fill: parent; hoverEnabled: true; onClicked: lk.clicked() }
                        }
                        Link { visible: dcol.g === "siet"; glyph: "wifi"; label: "Pripojenia (nmtui)"; onClicked: app.run(["foot", "-e", "nmtui"]) }
                        // ── zvuk: výstupy, vstupy, aplikácie ──
                        component B: Rectangle {
                            id: bb; property string t; signal hit()
                            width: 32; height: 32; radius: 8; color: bm.containsMouse ? theme.hover : theme.field
                            Text { anchors.centerIn: parent; text: bb.t; color: theme.fg; font { family: theme.fontUi; pixelSize: 14; weight: Font.Bold } }
                            MouseArea { id: bm; anchors.fill: parent; hoverEnabled: true; onClicked: bb.hit() }
                        }
                        component Vol: Row {
                            id: vr
                            property string label; property int value; property bool muted; property bool picked; property string kind; property string target
                            signal pick()
                            spacing: 6; width: dcol.width
                            Rectangle {
                                width: dcol.width - 110; height: 32; radius: 8
                                color: vr.picked ? Qt.rgba(theme.primary.r, theme.primary.g, theme.primary.b, 0.18) : theme.field
                                border { color: vr.picked ? theme.primary : "transparent"; width: 1 }
                                Text { x: 10; width: parent.width - 20; anchors.verticalCenter: parent.verticalCenter; elide: Text.ElideRight
                                       text: (vr.picked ? "● " : "") + vr.label + "  ·  " + (vr.muted ? "stlmené" : vr.value + " %"); color: theme.fg; font { family: theme.fontUi; pixelSize: 12 } }
                                MouseArea { anchors.fill: parent; onClicked: vr.pick() }
                            }
                            B { visible: vr.kind !== "source"; t: "−"; onHit: app.audioCmd(["volume", vr.kind, vr.target, String(Math.max(0, vr.value - 10))]) }
                            B { visible: vr.kind !== "source"; t: "+"; onHit: app.audioCmd(["volume", vr.kind, vr.target, String(Math.min(150, vr.value + 10))]) }
                            B { visible: vr.kind !== "source"; t: vr.muted ? "🔇" : "🔈"; onHit: app.audioCmd(["mute", vr.kind, vr.target]) }
                        }
                        Column {
                            visible: dcol.g === "zvuk"
                            width: parent.width; spacing: 6
                            Text { text: "VÝSTUP (klik = predvolený)"; topPadding: 6; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 11; weight: Font.Bold; letterSpacing: 0.6 } }
                            Repeater { model: app.audio.sinks
                                Vol { required property var modelData; label: modelData.desc; value: modelData.volume; muted: modelData.mute; picked: modelData.default
                                      kind: "sink"; target: modelData.name; onPick: app.audioCmd(["default", "sink", modelData.name]) } }
                            Text { text: "VSTUP (mikrofón)"; topPadding: 4; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 11; weight: Font.Bold; letterSpacing: 0.6 } }
                            Repeater { model: app.audio.sources
                                Vol { required property var modelData; label: modelData.desc; value: modelData.volume; muted: modelData.mute; picked: modelData.default
                                      kind: "source"; target: modelData.name; onPick: app.audioCmd(["default", "source", modelData.name]) } }
                            Text { text: "APLIKÁCIE"; topPadding: 4; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 11; weight: Font.Bold; letterSpacing: 0.6 } }
                            Text { visible: app.audio.apps.length === 0; text: "Žiadna aplikácia teraz nehrá."; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 } }
                            Repeater { model: app.audio.apps
                                Vol { required property var modelData; label: modelData.name; value: modelData.volume; muted: modelData.mute; picked: false
                                      kind: "app"; target: modelData.id } }
                        }
                        Link { visible: dcol.g === "bluetooth"; glyph: "bluetooth"; label: "Bluetooth v riadiacom centre"; onClicked: app.run(["noctalia", "msg", "panel-open", "control-center", "bluetooth"]) }
                        Link { visible: dcol.g === "disky"; glyph: "folder"; label: "Otvoriť v Súboroch"; onClicked: app.run(["latte-app", "subory"]) }
                        Link { visible: dcol.g === "grafika"; glyph: "bolt"; label: "Stupeň výkonu (Nastavenia)"; onClicked: app.run(["latte-app", "nastavenia", "vykon"]) }
                        Link { visible: dcol.g === "napajanie"; glyph: "battery"; label: "Profil výkonu v Zariadeniach na lište"; onClicked: app.run(["noctalia", "msg", "panel-toggle", "latteos/devices:panel"]) }
                        Link { visible: dcol.g === "pocitac"; glyph: "activity"; label: "Živý stav v Monitore"; onClicked: app.run(["latte-app", "monitor"]) }
                        Link { visible: !!dcol.it && !!dcol.it.sensorPrefix || dcol.g === "pocitac"; glyph: "activity"; label: "Senzory v Monitore"; onClicked: app.run(["latte-app", "monitor", "senzory"]) }
                        Link { visible: dcol.g === "grafika" || dcol.g === "siet" || dcol.g === "ostatne"; glyph: "download"; label: "Ovládače a firmvér (App Manager)"; onClicked: app.run(["latte-app", "aplikacie", "aktualizacie"]) }
                        Link { visible: dcol.g === "kamery" || dcol.g === "zvuk"; glyph: "shield"; label: "Kto smie mikrofón a kameru (App Manager)"; onClicked: app.run(["latte-app", "aplikacie", "opravnenia"]) }
                        Link { visible: dcol.g === "tlac"; glyph: "printer"; label: "Tlačiarne (CUPS)"; onClicked: app.run(["xdg-open", "http://localhost:631/printers"]) }
                        Text { width: parent.width; wrapMode: Text.WordWrap; text: app.status; color: theme.primary; font { family: theme.fontUi; pixelSize: 12 } }
                    }
                }
            }
            ContextMenu { id: ctx; theme: theme }
        }
    }
}
