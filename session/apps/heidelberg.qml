// LatteOS — Heidelberg, editor dokumentov (old/IDEAS.md: „originálny LatteOS editor dokumentov“).
// txt, md, html s náhľadom vedľa editora, formátovanie tlačidlami (Markdown), Ctrl+S uloží, Ctrl+N nový.
// docx, odt, rtf, epub cez pandoc: otvoria sa ako Markdown, uložia späť do pôvodného formátu (originál
// sa pri prvom uložení zazálohuje ako „súbor~“); Export do DOCX/ODT/EPUB/HTML.
// Spúšťa sa: latte-app heidelberg [súbor]
import QtQuick
import Quickshell
import Quickshell.Io
import "common"

ShellRoot {
    id: app
    LatteTheme { id: theme }

    readonly property string home: Quickshell.env("HOME") || "/"
    readonly property string docsDir: home + "/Dokumenty"
    readonly property string recentFile: (Quickshell.env("XDG_STATE_HOME") || (home + "/.local/state")) + "/latteos/heidelberg-recent.json"
    property string path: (Quickshell.env("LATTE_APP_ARGS") || "").trim().replace(/^file:\/\//, "")
    property string savedText: ""
    property bool dirty: editor.text !== savedText
    property string status: ""
    property var recent: []
    property var docs: []
    property bool preview: true
    readonly property string ext: (path.match(/\.([^./]+)$/) || [, "md"])[1].toLowerCase()
    readonly property bool isDoc: ["docx", "odt", "rtf", "epub", "doc"].indexOf(ext) >= 0   // cez pandoc
    readonly property string kind: isDoc ? "md" : (ext === "html" || ext === "htm" ? "html" : (ext === "md" || ext === "markdown" ? "md" : "txt"))
    property bool hasPandoc: true
    property bool backedUp: false
    readonly property int words: editor.text.trim() === "" ? 0 : editor.text.trim().split(/\s+/).length

    Process { id: pandocCheck; running: true; command: ["sh", "-c", "command -v pandoc"]; onExited: (code) => app.hasPandoc = code === 0 }
    // dokumenty (docx, odt…) → Markdown na úpravu
    Process {
        id: docLoad
        stdout: StdioCollector {
            onStreamFinished: { editor.text = this.text; app.savedText = editor.text; app.status = "Otvorené cez pandoc (formátovanie zjednodušené na Markdown)"; app.remember(app.path); }
        }
        onExited: (code) => { if (code !== 0) app.status = "Dokument sa nepodarilo otvoriť (pandoc, kód " + code + ")"; }
    }
    function loadDoc() {
        if (!hasPandoc) { status = "Na " + ext.toUpperCase() + " treba pandoc — tlačidlo Doinštalovať hore"; editor.text = ""; savedText = ""; return; }
        docLoad.command = ["pandoc", path, "-t", "markdown-raw_html-native_divs-native_spans-header_attributes-bracketed_spans", "--wrap=none"];
        docLoad.running = true;
    }
    Timer { id: pandocWait; interval: 300; onTriggered: app.loadDoc() }     // počkať na kontrolu pandocu
    FileView { id: tmpMd; path: (Quickshell.env("XDG_RUNTIME_DIR") || "/tmp") + "/heidelberg-" + Qt.md5(app.path || "novy") + ".md"; printErrors: false; atomicWrites: true }
    Process { id: docSave; onExited: (code) => app.status = code === 0 ? "Uložené · " + Qt.formatTime(new Date(), "HH:mm") : "Uloženie zlyhalo (pandoc, kód " + code + ")" }
    function exportAs(fmt) {
        if (!hasPandoc) { status = "Export potrebuje pandoc — Doinštalovať"; return; }
        const baseName = path ? path.replace(/\.[^./]+$/, "") : docsDir + "/Dokument " + Qt.formatDateTime(new Date(), "yyyy-MM-dd HH-mm");
        const out = baseName + "." + fmt;
        tmpMd.setText(editor.text);
        docSave.command = ["pandoc", "-f", kind === "html" ? "html" : "markdown", tmpMd.path, "-s", "-o", out];
        docSave.running = true;
        status = "Exportujem do " + out.split("/").pop() + "…";
    }
    FileView {
        id: doc
        path: app.isDoc ? "" : app.path
        printErrors: false
        blockLoading: true
        onLoaded: { editor.text = text(); app.savedText = editor.text; app.status = "Otvorené"; app.remember(app.path); }
        onLoadFailed: { if (app.path !== "") { editor.text = ""; app.savedText = ""; app.status = "Nový súbor"; } }
    }
    FileView {
        id: recentView
        path: app.recentFile; printErrors: false
        onLoaded: { try { app.recent = JSON.parse(text()); } catch (e) { app.recent = []; } }
    }
    function remember(p) {
        if (!p) return;
        recent = [p].concat(recent.filter(x => x !== p)).slice(0, 8);
        recentView.setText(JSON.stringify(recent));
    }
    Process {
        id: docsProc; running: true
        command: ["sh", "-c", "mkdir -p \"$1\"; ls -t \"$1\"/*.md \"$1\"/*.txt \"$1\"/*.html \"$1\"/*.docx \"$1\"/*.odt 2>/dev/null | head -20", "sh", app.docsDir]
        stdout: StdioCollector { onStreamFinished: app.docs = this.text.split("\n").filter(l => l !== "") }
    }

    function open(p) {
        if (dirty && !confirmDiscard) { confirmDiscard = true; pendingOpen = p; status = "Neuložené zmeny! Klikni znova pre zahodenie, alebo Ctrl+S."; return; }
        confirmDiscard = false;
        path = p; backedUp = false;
        if (isDoc) loadDoc(); else doc.reload();
    }
    property bool confirmDiscard: false
    property string pendingOpen: ""
    function save() {
        if (path === "") {
            path = docsDir + "/Dokument " + Qt.formatDateTime(new Date(), "yyyy-MM-dd HH-mm") + ".md";
        }
        if (isDoc) {
            if (!hasPandoc) { status = "Uloženie do " + ext.toUpperCase() + " potrebuje pandoc"; return; }
            tmpMd.setText(editor.text);
            const backup = backedUp ? "" : "cp -n -- \"$3\" \"$3~\" 2>/dev/null; ";
            docSave.command = ["sh", "-c", backup + "pandoc -f markdown \"$1\" -o \"$2\"", "sh", tmpMd.path, path, path];
            docSave.running = true; backedUp = true; savedText = editor.text;
            remember(path); return;
        }
        doc.setText(editor.text);
        savedText = editor.text;
        status = "Uložené · " + Qt.formatTime(new Date(), "HH:mm");
        remember(path);
        docsProc.running = true;
    }
    function newDoc() {
        if (dirty && !confirmDiscard) { confirmDiscard = true; pendingOpen = ""; status = "Neuložené zmeny! Ctrl+N znova pre zahodenie."; return; }
        confirmDiscard = false;
        path = ""; editor.text = ""; savedText = ""; status = "Nový dokument (Markdown)";
    }
    // formátovanie: obalí výber značkami Markdownu (alebo HTML)
    function wrap(a, b) {
        const s = editor.selectionStart, e = editor.selectionEnd, t = editor.selectedText || "text";
        editor.remove(s, e); editor.insert(s, a + t + b);
        editor.select(s + a.length, s + a.length + t.length); editor.forceActiveFocus();
    }
    function linePrefix(p) {
        const pos = editor.cursorPosition, txt = editor.text;
        const start = txt.lastIndexOf("\n", pos - 1) + 1;
        editor.insert(start, p); editor.forceActiveFocus();
    }
    function fmt(what) {
        const html = kind === "html";
        if (what === "b") wrap(html ? "<b>" : "**", html ? "</b>" : "**");
        else if (what === "i") wrap(html ? "<i>" : "*", html ? "</i>" : "*");
        else if (what === "h") html ? wrap("<h2>", "</h2>") : linePrefix("## ");
        else if (what === "l") html ? wrap("<li>", "</li>") : linePrefix("- ");
        else if (what === "q") html ? wrap("<blockquote>", "</blockquote>") : linePrefix("> ");
        else if (what === "c") wrap("`", "`");
        else if (what === "a") wrap(html ? "<a href=\"https://\">" : "[", html ? "</a>" : "](https://)");
    }

    FloatingWindow {
        title: (app.path ? app.path.split("/").pop() : "Nový dokument") + (app.dirty ? " •" : "") + " — Heidelberg"
        implicitWidth: 1280; implicitHeight: 800
        color: theme.surface

        Item {
            id: root
            anchors.fill: parent
            Shortcut { sequence: "Ctrl+S"; onActivated: app.save() }
            Shortcut { sequence: "Ctrl+N"; onActivated: app.newDoc() }
            Shortcut { sequence: "Ctrl+B"; onActivated: app.fmt("b") }
            Shortcut { sequence: "Ctrl+I"; onActivated: app.fmt("i") }
            Shortcut { sequence: "Ctrl+P"; onActivated: app.preview = !app.preview }

            SideBar {
                id: side
                theme: theme
                anchors { left: parent.left; top: parent.top; bottom: parent.bottom }
                heading: "Heidelberg"; headingGlyph: "file-text"
                current: "doc:" + app.path
                model: [
                    { title: "Dokument", items: [{ key: "new", glyph: "plus", label: "Nový dokument", sub: "Ctrl+N · Markdown" }] },
                    { title: "Nedávne", items: app.recent.map(p => ({ key: "doc:" + p, glyph: "file-text", label: p.split("/").pop(), sub: p.substring(0, p.lastIndexOf("/")).replace(app.home, "~") })) },
                    { title: "Dokumenty", items: app.docs.map(p => ({ key: "doc:" + p, glyph: "file-text", label: p.split("/").pop() })) }
                ]
                onActivated: (it) => { if (it.key === "new") app.newDoc(); else app.open(it.key.slice(4)); }
            }

            HeaderBar {
                id: header
                theme: theme
                appId: "latteos-heidelberg"
                anchors { left: side.right; right: parent.right; top: parent.top }
                title: (app.path ? app.path.split("/").pop() : "Nový dokument") + (app.dirty ? "  •  neuložené" : "")
                netVisible: false
                searchPlaceholder: "Hľadať v texte"
                onSearchChanged: (t) => { const i = t ? editor.text.toLowerCase().indexOf(t.toLowerCase()) : -1; if (i >= 0) { editor.select(i, i + t.length); } }
                onCloseRequested: Qt.quit()
                IconButton { theme: theme; glyph: "device-floppy"; tip: "Uložiť (Ctrl+S)"; onClicked: app.save() }
                IconButton { theme: theme; glyph: "eye"; checked: app.preview; tip: "Náhľad (Ctrl+P)"; onClicked: app.preview = !app.preview }
            }

            // panel formátovania
            Row {
                id: tools
                anchors { left: side.right; top: header.bottom; leftMargin: 16; topMargin: 10 }
                spacing: 6
                component Fmt: Rectangle {
                    id: fb
                    property string label; property string what; property string tip
                    width: Math.max(34, ft.implicitWidth + 18); height: 32; radius: 8
                    color: fm.containsMouse ? theme.hover : theme.field
                    Text { id: ft; anchors.centerIn: parent; text: fb.label; color: theme.fg; font { family: theme.fontUi; pixelSize: 13; weight: Font.Bold; italic: fb.what === "i" } }
                    MouseArea { id: fm; anchors.fill: parent; hoverEnabled: true; onClicked: app.fmt(fb.what) }
                }
                Fmt { label: "B"; what: "b" }
                Fmt { label: "I"; what: "i" }
                Fmt { label: "Nadpis"; what: "h" }
                Fmt { label: "• Zoznam"; what: "l" }
                Fmt { label: "❝ Citát"; what: "q" }
                Fmt { label: "</> Kód"; what: "c" }
                Fmt { label: "Odkaz"; what: "a" }
                Item { width: 18; height: 1 }
                component Exp: Rectangle {
                    id: eb
                    property string label; property string fmt
                    width: et.implicitWidth + 18; height: 32; radius: 8
                    color: em2.containsMouse ? theme.hover : "transparent"; border { color: theme.line; width: 1 }
                    Text { id: et; anchors.centerIn: parent; text: eb.label; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12; weight: Font.Bold } }
                    MouseArea { id: em2; anchors.fill: parent; hoverEnabled: true; onClicked: app.exportAs(eb.fmt) }
                }
                Text { anchors.verticalCenter: parent.verticalCenter; text: "Export:"; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 } }
                Exp { label: "DOCX"; fmt: "docx" }
                Exp { label: "ODT"; fmt: "odt" }
                Exp { label: "EPUB"; fmt: "epub" }
                Exp { label: "HTML"; fmt: "html" }
                Rectangle {
                    visible: !app.hasPandoc
                    width: pt2.implicitWidth + 18; height: 32; radius: 8; color: theme.primary
                    Text { id: pt2; anchors.centerIn: parent; text: "Doinštalovať dokumenty (pandoc)"; color: theme.fgOnPrimary; font { family: theme.fontUi; pixelSize: 12; weight: Font.Bold } }
                    MouseArea { anchors.fill: parent; onClicked: { inst.command = ["foot", "-e", "sh", "-c", "sudo dnf install pandoc-cli; read -p 'Enter zavrie okno…' x"]; inst.running = true; } }
                    Process { id: inst; onExited: pandocCheck.running = true }
                }
            }

            Row {
                anchors { left: side.right; right: parent.right; top: tools.bottom; bottom: statusBar.top; margins: 16; topMargin: 10 }
                spacing: 14
                // editor
                Rectangle {
                    width: app.preview ? (parent.width - 14) / 2 : parent.width; height: parent.height
                    radius: 12; color: theme.field
                    Flickable {
                        id: flick
                        anchors { fill: parent; margins: 14 }
                        contentHeight: editor.implicitHeight; clip: true
                        TextEdit {
                            id: editor
                            width: flick.width
                            wrapMode: TextEdit.Wrap; selectByMouse: true; focus: true
                            color: theme.fg; selectionColor: theme.primary; selectedTextColor: theme.fgOnPrimary
                            font { family: app.kind === "txt" ? theme.fontUi : theme.fontMono; pixelSize: 14 }
                            onCursorRectangleChanged: {
                                if (cursorRectangle.y < flick.contentY) flick.contentY = cursorRectangle.y;
                                else if (cursorRectangle.y + cursorRectangle.height > flick.contentY + flick.height) flick.contentY = cursorRectangle.y + cursorRectangle.height - flick.height;
                            }
                        }
                        Text { visible: editor.text === ""; text: "Píš… (Markdown: # nadpis, **tučné**, *kurzíva*, - zoznam)"; color: theme.fgDim; font { family: theme.fontUi; pixelSize: 14 } }
                    }
                }
                // náhľad
                Rectangle {
                    visible: app.preview
                    width: (parent.width - 14) / 2; height: parent.height
                    radius: 12; color: Qt.rgba(0, 0, 0, theme.mode === "dark" ? 0.12 : 0.03); border { color: theme.line; width: 1 }
                    Flickable {
                        anchors { fill: parent; margins: 20 }
                        contentHeight: rendered.implicitHeight; clip: true
                        Text {
                            id: rendered
                            width: parent.width; wrapMode: Text.Wrap
                            textFormat: app.kind === "html" ? Text.RichText : (app.kind === "md" ? Text.MarkdownText : Text.PlainText)
                            text: editor.text; color: theme.fg; linkColor: theme.primary
                            font { family: app.kind === "txt" ? theme.fontMono : theme.fontUi; pixelSize: 15 }
                            onLinkActivated: (l) => Qt.openUrlExternally(l)
                        }
                    }
                }
            }

            Rectangle {
                id: statusBar
                anchors { left: side.right; right: parent.right; bottom: parent.bottom }
                height: 30; color: "transparent"
                Rectangle { width: parent.width; height: 1; color: theme.line }
                Text {
                    x: 14; anchors.verticalCenter: parent.verticalCenter
                    text: app.words + " slov · " + editor.text.length + " znakov · " + (app.isDoc ? app.ext.toUpperCase() + " (upravuje sa ako Markdown)" : ({ md: "Markdown", html: "HTML", txt: "text" })[app.kind]) + (app.status ? "   ·   " + app.status : "")
                    color: theme.fgDim; font { family: theme.fontUi; pixelSize: 12 }
                }
                Text {
                    anchors { right: parent.right; rightMargin: 14; verticalCenter: parent.verticalCenter }
                    text: "Ctrl+S uložiť · Ctrl+N nový · Ctrl+B/I tučné/kurzíva · Ctrl+P náhľad"
                    color: theme.fgDim; opacity: 0.8; font { family: theme.fontUi; pixelSize: 11 }
                }
            }
        }
    }
    Component.onCompleted: {
        if (isDoc) { pandocWait.start(); return; }
        if (path === "") { editor.text = "# Vitaj v Heidelbergu\n\nToto je **editor dokumentov LatteOS**. Píš vľavo, vpravo vidíš výsledok.\n\n- Markdown aj HTML\n- Ctrl+S uloží do *Dokumenty*\n\n> Názov Gutenberg je obsadený, preto Heidelberg.\n"; savedText = editor.text; status = "Ukážka (neuloží sa, kým nestlačíš Ctrl+S)"; }
    }
}
