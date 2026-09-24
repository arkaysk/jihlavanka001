// LatteOS — Digitálna pohoda: koľko času trávim v ktorej aplikácii (zadanie 24. 9. večer; nápad z videa
// „Hyprland as fluid as it gets“ / serpantinum — kód je vlastný). Beží skryto na pozadí:
//   každých 5 s pripočíta čas aktívnemu oknu (trieda okna), ak používateľ nie je nečinný (ext-idle-notify,
//   5 min; prehrávané video nečinnosť blokuje, takže sa ráta) a relácia nie je zamknutá,
//   raz za minútu zmeria pamäť (RSS) aktívnej aplikácie aj s podprocesmi → „obvykle v RAM“,
//   denné limity (~/.config/latteos/pohoda-limity.json: { trieda: minúty }) → oznámenie 5 min pred a pri limite.
// Dáta: ~/.local/share/latteos/pohoda/RRRR-MM-DD.json
//        { apps: { trieda: { s, title, rss, rssN, rssMax } }, hours: [24 × { trieda: s }], halves: [48 × { trieda: s }] }
// Vypnutie: ~/.config/latteos/pohoda = off. Spúšťa: latte-app pohoda (hyprland.lua). Zobrazuje: Monitor › Čas v aplikáciách.
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland

ShellRoot {
    id: ph
    readonly property string home: Quickshell.env("HOME") || "/"
    readonly property string cfg: (Quickshell.env("XDG_CONFIG_HOME") || (home + "/.config")) + "/latteos"
    readonly property string dir: (Quickshell.env("XDG_DATA_HOME") || (home + "/.local/share")) + "/latteos/pohoda"
    property string day: ""
    property var data: ({ apps: {}, hours: [] })
    property bool loaded: false
    property bool dirty: false
    property var limits: ({})
    property var warned: ({})               // trieda → "5" | "limit" (dnes už upozornené)
    property string cls: ""
    property string title: ""
    property int pid: 0
    readonly property int step: 5

    function today() { return Qt.formatDate(new Date(), "yyyy-MM-dd"); }
    function emptyDay() { const h = [], hh = []; for (let i = 0; i < 24; i++) h.push({}); for (let i = 0; i < 48; i++) hh.push({}); return { apps: {}, hours: h, halves: hh }; }

    FileView { path: ph.cfg + "/pohoda"; printErrors: false; watchChanges: true; onFileChanged: reload()
               onLoaded: if (text().trim() === "off") Qt.quit() }
    FileView {
        path: ph.cfg + "/pohoda-limity.json"; printErrors: false; watchChanges: true; onFileChanged: reload()
        onLoaded: { try { ph.limits = JSON.parse(text()) || {}; } catch (e) { ph.limits = {}; } }
        onLoadFailed: ph.limits = {}
    }
    FileView {
        id: store
        path: ph.day !== "" ? ph.dir + "/" + ph.day + ".json" : ""
        printErrors: false; atomicWrites: true
        onLoaded: { try { const d = JSON.parse(text()); if (!d.hours || d.hours.length !== 24) d.hours = ph.emptyDay().hours; if (!d.halves || d.halves.length !== 48) d.halves = ph.emptyDay().halves; ph.data = d; } catch (e) { ph.data = ph.emptyDay(); } ph.loaded = true; }
        onLoadFailed: { ph.data = ph.emptyDay(); ph.loaded = true; }
    }
    Process { id: mk; running: true; command: ["mkdir", "-p", ph.dir] }
    Component.onCompleted: day = today()

    IdleMonitor { id: idle; timeout: 300; respectInhibitors: true }

    Process {
        id: probe
        command: ["hyprctl", "-j", "activewindow"]
        stdout: StdioCollector {
            onStreamFinished: {
                let w = null;
                try { w = JSON.parse(this.text); } catch (e) {}
                ph.cls = w && w.class ? w["class"] : "";
                ph.title = w && w.title ? w.title : "";
                ph.pid = w && w.pid ? w.pid : 0;
                ph.tick();
            }
        }
    }
    Timer { interval: ph.step * 1000; repeat: true; running: ph.loaded; onTriggered: if (!probe.running) probe.running = true }

    function tick() {
        const d0 = today();
        if (d0 !== day) { flush(); day = d0; loaded = false; warned = {}; return; }     // nový deň → nový súbor
        if (idle.isIdle || cls === "" || cls === "org.quickshell" && title === "") return;
        const k = key();
        const d = data;
        const a = d.apps[k] || { s: 0, title: "", rss: 0, rssN: 0 };
        a.s += step; a.title = title;
        d.apps[k] = a;
        const now = new Date(), h = now.getHours(), hh = h * 2 + (now.getMinutes() >= 30 ? 1 : 0);
        d.hours[h][k] = (d.hours[h][k] || 0) + step;
        d.halves[hh][k] = (d.halves[hh][k] || 0) + step;
        dirty = true;
        checkLimit(k, a.s);
    }
    // aplikácie LatteOS majú všetky triedu org.quickshell → rozlíšiť podľa titulku („Súbory — LatteOS“, „x — Heidelberg“)
    function key() {
        if (cls !== "org.quickshell") return cls;
        const m = title.match(/ — (Heidelberg)$/) || title.match(/^(.*) — LatteOS$/);
        return "latte:" + (m ? m[1] : title);
    }
    function checkLimit(c, secs) {
        const lim = limits[c];
        if (!lim) return;
        const left = lim * 60 - secs;
        if (left <= 0 && warned[c] !== "limit") { warned[c] = "limit"; tell("Denný limit: " + shortName(c), "Dnes už " + lim + " min. Čas na prestávku?"); }
        else if (left > 0 && left <= 300 && !warned[c]) { warned[c] = "5"; tell("Ešte 5 minút: " + shortName(c), "Denný limit je " + lim + " min."); }
    }
    function shortName(c) { if (c.startsWith("latte:")) return c.slice(6); const e = DesktopEntries.heuristicLookup(c); return e ? e.name : c; }
    Process { id: notify }
    function tell(t, b) { notify.command = ["notify-send", "-a", "LatteOS", "-i", "preferences-desktop-screensaver", t, b]; notify.startDetached(); }

    // pamäť aktívnej aplikácie (RSS celého stromu procesov) raz za minútu
    Process {
        id: rssProc
        property string c: ""
        stdout: StdioCollector {
            onStreamFinished: {
                const kb = parseInt(this.text) || 0;
                const a = ph.data.apps[rssProc.c];
                if (!a || kb <= 0) return;
                a.rss = Math.round(((a.rss || 0) * (a.rssN || 0) + kb) / ((a.rssN || 0) + 1));   // priemer
                a.rssN = (a.rssN || 0) + 1;
                a.rssMax = Math.max(a.rssMax || 0, kb);
                ph.dirty = true;
            }
        }
    }
    Timer {
        interval: 60000; repeat: true; running: ph.loaded
        onTriggered: {
            if (!idle.isIdle && ph.pid > 0 && ph.cls !== "" && !rssProc.running) {
                rssProc.c = ph.key(); rssProc.command = ["latte-sysmon", "rss", String(ph.pid)]; rssProc.running = true;
            }
            ph.flush();
        }
    }
    function flush() { if (dirty && loaded) { store.setText(JSON.stringify(data)); dirty = false; } }
}
