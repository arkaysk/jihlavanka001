"""Tri režimy promptu v lište: Hľadať (súbory a priečinky), Terminál (príkazy Linuxu), AI (LM Studio).

Každý režim vlastní svoje zobrazenie (view), ktoré prompt ukáže v popupe nad lištou. Zobrazenia
prežijú zatvorenie popupu, takže rozhovor s AI ani výstup terminálu sa zatvorením nestratia.
"""
import codecs
import os
import signal
import tempfile
import threading
import time

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk, Gio, GLib, Pango  # noqa: E402

from latte_common import llm, search, termrun, textmark  # noqa: E402
from latte_common import volumes as vol_mod  # noqa: E402

SEARCH_LIMIT = 100
SEARCH_MIN_CHARS = 2
SEARCH_DEBOUNCE_MS = 220
POPUP_MAX_HEIGHT = 420
HIT_ROW_HEIGHT = 56                 # výška riadka výsledku hľadania
HIT_ROWS_SHOWN = 6
TERMINAL_MAX_CHARS = 200_000
HISTORY_LIMIT = 20                  # správ AI, ktoré sa posielajú modelu


class Mode:
    """Spoločný základ. `host` je PromptSegment (show, refresh, open_files, set_entry_text...)."""
    id = ""
    icon = ""
    name = ""
    placeholder = ""

    def __init__(self, host):
        self.host = host
        self.view = self.build()

    def build(self):
        raise NotImplementedError

    def title(self):
        return self.name

    def extras(self):
        """Ďalšie tlačidlá v hlavičke popupu."""
        return []

    def changed(self, text):
        pass

    def submit(self, text):
        pass

    def key(self, keyval, state):
        """Kláves z políčka promptu; True, ak ho režim spracoval."""
        return False

    def activated(self):
        """Režim sa stal aktívnym."""

    def say(self, text):
        """Stavový riadok pod obsahom; prázdny sa nezobrazí."""
        self.status.set_text(text)
        self.status.set_visible(bool(text))


def scrolled(child, min_height=0, max_height=POPUP_MAX_HEIGHT):
    scroll = Gtk.ScrolledWindow(hexpand=True, vexpand=False)
    scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    scroll.set_propagate_natural_height(True)
    scroll.set_min_content_height(min_height)
    scroll.set_max_content_height(max_height)
    scroll.set_child(child)
    return scroll


def tool_button(icon, tip, action):
    button = Gtk.Button(icon_name=icon)
    button.add_css_class("flat")
    button.add_css_class("prompt-tool")
    button.set_tooltip_text(tip)
    button.connect("clicked", lambda _b: action())
    return button


# ------------------------------------------------------------------ Hľadať
class SearchMode(Mode):
    id = "search"
    icon = "system-search-symbolic"
    name = "Hľadať v priečinkoch"
    placeholder = "Hľadať súbory a priečinky…"

    def build(self):
        self.generation = 0
        self.cancel = threading.Event()
        self.timer = 0
        self.query = ""
        self.count = 0
        self.searching = False
        self.volumes = []
        self.volumes_at = 0.0

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.list = Gtk.ListBox()
        self.list.add_css_class("prompt-results")
        self.list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.list.set_activate_on_single_click(True)
        self.list.connect("row-activated", lambda _l, row: self.open_hit(row.hit, False))
        self.scroll = scrolled(self.list)
        self.scroll.set_visible(False)
        box.append(self.scroll)
        self.status = Gtk.Label(xalign=0, wrap=True)
        self.status.add_css_class("prompt-status")
        box.append(self.status)
        return box

    def fit_list(self):
        """Výšku okna drží počet riadkov: okno pri streamovaní výsledkov samo nerastie spoľahlivo."""
        rows = min(self.count, HIT_ROWS_SHOWN)
        self.scroll.set_visible(rows > 0)
        self.scroll.set_min_content_height(rows * HIT_ROW_HEIGHT)

    def title(self):
        return "Hľadanie · " + self.query if self.query else self.name

    # ---------- vstup ----------
    def changed(self, text):
        if self.timer:
            GLib.source_remove(self.timer)
            self.timer = 0
        self.query = text.strip()
        self.cancel.set()
        self.generation += 1
        if len(self.query) < SEARCH_MIN_CHARS:
            self.clear()
            self.say("Aspoň %d znaky." % SEARCH_MIN_CHARS if self.query else "")
            if not self.query:
                self.host.close_popup()
            else:
                self.host.show(self)
            return
        self.host.show(self)
        self.say("Prehľadávam…")
        self.timer = GLib.timeout_add(SEARCH_DEBOUNCE_MS, self.start)

    def submit(self, text):
        row = self.list.get_selected_row()
        if row is not None:
            self.open_hit(row.hit, False)

    def key(self, keyval, state):
        if keyval in (Gdk.KEY_Down, Gdk.KEY_Up):
            rows = []
            child = self.list.get_first_child()
            while child is not None:
                rows.append(child)
                child = child.get_next_sibling()
            if not rows:
                return True
            current = self.list.get_selected_row()
            index = rows.index(current) if current in rows else -1
            index = max(0, min(len(rows) - 1, index + (1 if keyval == Gdk.KEY_Down else -1)))
            self.list.select_row(rows[index])
            GLib.idle_add(self.scroll_to, rows[index])
            return True
        return False

    def scroll_to(self, row):
        found, rect = row.compute_bounds(self.list)
        if not found:
            return False
        adj = self.scroll.get_vadjustment()
        top, bottom = rect.get_y(), rect.get_y() + rect.get_height()
        if top < adj.get_value():
            adj.set_value(top)
        elif bottom > adj.get_value() + adj.get_page_size():
            adj.set_value(bottom - adj.get_page_size())
        return False

    # ---------- hľadanie ----------
    def clear(self):
        child = self.list.get_first_child()
        while child is not None:
            self.list.remove(child)
            child = self.list.get_first_child()
        self.count = 0
        self.fit_list()

    def start(self):
        self.timer = 0
        self.cancel = threading.Event()
        self.clear()
        self.searching = True
        threading.Thread(target=self.work, args=(self.generation, self.query, self.cancel),
                         daemon=True).start()
        return False

    def known_volumes(self):
        if time.monotonic() - self.volumes_at > 30:
            self.volumes = vol_mod.list_volumes()
            self.volumes_at = time.monotonic()
        return self.volumes

    def work(self, generation, query, cancel):
        volumes = self.known_volumes()
        roots = search.search_roots(volumes, os.path.expanduser("~"))
        batch, last, total = [], time.monotonic(), 0
        for hit in search.find(roots, query, SEARCH_LIMIT, cancel.is_set):
            batch.append((hit, search.display_path(volumes, os.path.dirname(hit.path))))
            total += 1
            if len(batch) >= 8 or time.monotonic() - last > 0.15:
                GLib.idle_add(self.add_hits, generation, batch)
                batch, last = [], time.monotonic()
        if batch:
            GLib.idle_add(self.add_hits, generation, batch)
        if not cancel.is_set():
            GLib.idle_add(self.finished, generation, total, roots)

    def add_hits(self, generation, batch):
        if generation != self.generation:
            return False
        for hit, where in batch:
            row = self.build_row(hit, where)
            self.list.append(row)
            self.count += 1
        self.fit_list()
        if self.list.get_selected_row() is None:
            self.list.select_row(self.list.get_row_at_index(0))
        self.say("Prehľadávam… %d nájdených" % self.count)
        return False

    def finished(self, generation, total, roots):
        if generation != self.generation:
            return False
        self.searching = False
        if total == 0:
            self.say("Nič sa nenašlo (hľadá sa v %d miestach, skryté položky sa preskakujú)."
                                 % len(roots))
        elif total >= SEARCH_LIMIT:
            self.say("Prvých %d výsledkov, spresni hľadanie." % total)
        else:
            self.say("%d výsledkov" % total)
        return False

    def build_row(self, hit, where):
        row = Gtk.ListBoxRow()
        row.hit = hit
        box = Gtk.Box(spacing=10)
        box.add_css_class("prompt-hit")
        if hit.is_dir:
            icon = Gtk.Image.new_from_icon_name("folder")
        else:
            content_type, _u = Gio.content_type_guess(hit.name, None)
            icon = Gtk.Image.new_from_gicon(Gio.content_type_get_icon(content_type))
        icon.set_pixel_size(24)
        box.append(icon)
        text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True)
        name = Gtk.Label(label=hit.name, xalign=0)
        name.set_ellipsize(Pango.EllipsizeMode.END)
        where_label = Gtk.Label(label=where, xalign=0)
        where_label.add_css_class("dim")
        where_label.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
        text.append(name)
        text.append(where_label)
        box.append(text)
        reveal = tool_button("folder-open-symbolic", "Ukázať v priečinku",
                             lambda h=hit: self.open_hit(h, True))
        reveal.set_valign(Gtk.Align.CENTER)
        box.append(reveal)
        row.set_child(box)
        return row

    def open_hit(self, hit, reveal):
        """Priečinok alebo „ukázať v priečinku“ otvorí správcu súborov, súbor jeho predvolená aplikácia."""
        if hit.is_dir or reveal:
            self.host.open_files(hit.path if hit.is_dir and not reveal else os.path.dirname(hit.path))
        else:
            try:
                Gio.AppInfo.launch_default_for_uri(Gio.File.new_for_path(hit.path).get_uri(), None)
            except GLib.Error as err:
                self.say("Súbor sa nedá otvoriť: %s" % err.message)
                return
        self.host.close_popup()


# ------------------------------------------------------------------ Terminál
class TerminalMode(Mode):
    id = "terminal"
    icon = "utilities-terminal-symbolic"
    name = "Terminál"
    placeholder = "Príkaz Linuxu…"

    def build(self):
        self.cwd = os.path.expanduser("~")
        self.proc = None
        self.cancel = None
        self.history = []
        self.history_at = None
        self.last_command = ""

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.text = Gtk.TextView()
        self.text.add_css_class("prompt-terminal")
        self.text.set_editable(False)
        self.text.set_cursor_visible(False)
        self.text.set_monospace(True)
        self.text.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.text.set_left_margin(12)
        self.text.set_right_margin(12)
        self.text.set_top_margin(8)
        self.text.set_bottom_margin(8)
        self.buffer = self.text.get_buffer()
        self.buffer.create_tag("cmd", foreground="#D9913B", weight=700)
        self.buffer.create_tag("err", foreground="#E8846B")
        self.buffer.create_tag("dim", foreground="#CDBFAF")
        self.end_mark = self.buffer.create_mark("end", self.buffer.get_end_iter(), False)
        self.scroll = scrolled(self.text, min_height=180)
        box.append(self.scroll)
        self.status = Gtk.Label(xalign=0)
        self.status.add_css_class("prompt-status")
        box.append(self.status)

        self.stop_button = tool_button("media-playback-stop-symbolic", "Zastaviť príkaz (Ctrl+C)", self.interrupt)
        self.stop_button.set_visible(False)
        self.buttons = [
            self.stop_button,
            tool_button("utilities-terminal-symbolic", "Spustiť posledný príkaz v okne terminálu",
                        self.repeat_in_terminal),
            tool_button("edit-clear-symbolic", "Vymazať výstup", self.clear),
        ]
        self.write("Príkazy Linuxu bežia v %s. Programy, čo potrebujú terminál (vim, top, ssh, sudo…), "
                   "sa otvoria vo vlastnom okne.\n" % termrun.pretty_cwd(self.cwd), "dim")
        return box

    def title(self):
        return "Terminál · " + termrun.pretty_cwd(self.cwd)

    def extras(self):
        return self.buttons

    def activated(self):
        self.host.set_prefix(self.prefix())

    def prefix(self):
        return os.path.basename(self.cwd.rstrip("/")) or "/"

    # ---------- výstup ----------
    def write(self, text, tag=None):
        end = self.buffer.get_end_iter()
        if tag:
            self.buffer.insert_with_tags_by_name(end, text, tag)
        else:
            self.buffer.insert(end, text)
        if self.buffer.get_char_count() > TERMINAL_MAX_CHARS:
            start = self.buffer.get_start_iter()
            cut = self.buffer.get_iter_at_offset(TERMINAL_MAX_CHARS // 4)
            self.buffer.delete(start, cut)
        self.buffer.move_mark(self.end_mark, self.buffer.get_end_iter())
        self.text.scroll_mark_onscreen(self.end_mark)

    def clear(self):
        self.buffer.set_text("")

    # ---------- vstup ----------
    def key(self, keyval, state):
        if keyval in (Gdk.KEY_Up, Gdk.KEY_Down) and self.history:
            last = len(self.history)
            at = last if self.history_at is None else self.history_at
            at = max(0, at - 1) if keyval == Gdk.KEY_Up else min(last, at + 1)
            self.history_at = at
            self.host.set_entry_text(self.history[at] if at < last else "")
            return True
        if keyval in (Gdk.KEY_c, Gdk.KEY_C) and state & Gdk.ModifierType.CONTROL_MASK and self.proc:
            self.interrupt()
            return True
        return False

    def submit(self, text):
        command = text.strip()
        if not command:
            return
        if self.proc is not None:
            self.say("Príkaz ešte beží (Ctrl+C ho zastaví).")
            self.host.show(self)
            return
        self.say("")
        self.host.show(self)
        self.history.append(command)
        self.history_at = None
        self.last_command = command
        self.host.set_entry_text("")
        self.write("%s $ %s\n" % (termrun.pretty_cwd(self.cwd), command), "cmd")
        if termrun.needs_terminal(command):
            self.run_in_terminal(command)
        else:
            self.run(command)

    def run(self, command):
        fd, cwd_file = tempfile.mkstemp(prefix="latte-cwd-", dir=os.environ.get("XDG_RUNTIME_DIR"))
        os.close(fd)
        launcher = Gio.SubprocessLauncher.new(
            Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_MERGE)
        launcher.set_cwd(self.cwd)
        launcher.set_environ(["%s=%s" % item for item in termrun.environment().items()])
        try:
            proc = launcher.spawnv(termrun.argv(command, cwd_file))
        except GLib.Error as err:
            os.unlink(cwd_file)
            self.write("Príkaz sa nepodarilo spustiť: %s\n" % err.message, "err")
            return
        self.proc = proc
        self.cancel = Gio.Cancellable()
        self.cwd_file = cwd_file
        self.read_done = False
        self.exited = False
        self.decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        self.stop_button.set_visible(True)
        self.say("Beží…")
        proc.get_stdout_pipe().read_bytes_async(65536, GLib.PRIORITY_DEFAULT, self.cancel,
                                                self.on_read, proc)
        proc.wait_async(None, self.on_exit, proc)

    def on_read(self, stream, result, proc):
        if proc is not self.proc:
            return
        try:
            data = stream.read_bytes_finish(result).get_data()
        except GLib.Error:
            data = b""                                  # zrušené alebo rúra sa zavrela
        if data:
            self.write(termrun.strip_ansi(self.decoder.decode(data)))
            stream.read_bytes_async(65536, GLib.PRIORITY_DEFAULT, self.cancel, self.on_read, proc)
            return
        self.read_done = True
        self.maybe_finish(proc)

    def on_exit(self, proc, result, _data):
        if proc is not self.proc:
            return
        try:
            proc.wait_finish(result)
        except GLib.Error:
            pass
        self.exited = True
        if self.read_done:
            self.maybe_finish(proc)
        else:
            # proces na pozadí (príkaz &) môže držať rúru otvorenú: čakať len chvíľu
            GLib.timeout_add(200, self.maybe_finish, proc, True)

    def maybe_finish(self, proc, force=False):
        if proc is not self.proc or not self.exited or not (self.read_done or force):
            return False
        self.cancel.cancel()
        self.proc = None
        self.stop_button.set_visible(False)
        tail = self.decoder.decode(b"", final=True)
        if tail:
            self.write(termrun.strip_ansi(tail))
        try:
            with open(self.cwd_file, encoding="utf-8") as f:
                new = f.read().strip()
            if new and os.path.isdir(new) and new != self.cwd:
                self.cwd = new
        except OSError:
            pass
        finally:
            try:
                os.unlink(self.cwd_file)
            except OSError:
                pass
        code = proc.get_exit_status() if proc.get_if_exited() else -1
        if proc.get_if_signaled():
            self.write("[zastavené signálom %d]\n" % proc.get_term_sig(), "dim")
        elif code != 0:
            self.write("[kód %d]\n" % code, "err")
        self.say("")
        self.host.set_prefix(self.prefix())
        self.host.refresh()
        return False

    def interrupt(self):
        proc = self.proc
        if proc is None:
            return
        try:
            os.killpg(int(proc.get_identifier()), signal.SIGINT)
        except (OSError, TypeError, ValueError):
            proc.send_signal(signal.SIGINT)

    # ---------- programy s terminálom ----------
    def run_in_terminal(self, command):
        argv = termrun.terminal_argv(command, self.cwd)
        if argv is None:
            self.write("„%s“ potrebuje terminál a foot nie je nainštalovaný (dnf install foot).\n"
                       % command, "err")
            return
        launcher = Gio.SubprocessLauncher.new(Gio.SubprocessFlags.NONE)
        launcher.set_environ(["%s=%s" % item for item in termrun.environment().items()])
        try:
            launcher.spawnv(argv)
        except GLib.Error as err:
            self.write("Okno terminálu sa nepodarilo otvoriť: %s\n" % err.message, "err")
            return
        self.write("Spustené v okne terminálu.\n", "dim")

    def repeat_in_terminal(self):
        if self.last_command:
            self.run_in_terminal(self.last_command)


# ------------------------------------------------------------------ AI
class Turn:
    """Jedna odpoveď AI: text, ktorý sa dopisuje, a jej zdroj."""

    def __init__(self, bubble):
        self.bubble = bubble
        self.text = ""
        self.reasoning = ""
        self.stream = None
        self.cancelled = False
        self.orphan = False             # rozhovor sa medzitým vymazal
        self.failed = False
        self.dirty = False


class AiMode(Mode):
    id = "ai"
    icon = "latte-ai-symbolic"
    name = "AI"
    placeholder = "Opýtaj sa AI…"

    def build(self):
        self.messages = []
        self.turn = None
        self.model = ""
        self.render_timer = 0
        self.base = llm.settings()[0]

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.chat = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.chat.add_css_class("ai-chat")
        self.empty = Gtk.Label(xalign=0, wrap=True)
        self.empty.add_css_class("dim")
        self.chat.append(self.empty)
        self.scroll = scrolled(self.chat, min_height=220)
        box.append(self.scroll)
        self.status = Gtk.Label(xalign=0, wrap=True)
        self.status.add_css_class("prompt-status")
        box.append(self.status)
        self.update_empty()

        self.stop_button = tool_button("media-playback-stop-symbolic", "Zastaviť odpoveď (Ctrl+C)", self.stop)
        self.stop_button.set_visible(False)
        self.buttons = [self.stop_button,
                        tool_button("list-add-symbolic", "Nový rozhovor", self.reset)]
        return box

    def title(self):
        return "AI · " + self.model if self.model else "AI · " + self.base.split("//")[-1]

    def extras(self):
        return self.buttons

    def update_empty(self):
        self.empty.set_text("Opýtaj sa AI. Beží lokálne v LM Studiu (%s), otázky neopúšťajú tvoju sieť."
                            % self.base.split("//")[-1])
        self.empty.set_visible(not self.messages and self.turn is None)

    # ---------- rozhovor ----------
    def bubble(self, role):
        label = Gtk.Label(xalign=0, wrap=True, selectable=True, use_markup=True)
        label.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        label.set_max_width_chars(80)
        label.add_css_class("ai-msg")
        label.add_css_class(role)
        return label

    def add_bubble(self, role, text):
        label = self.bubble(role)
        label.set_markup(textmark.to_pango(text) if role == "assistant" else GLib.markup_escape_text(text))
        self.chat.append(label)
        return label

    def submit(self, text):
        text = text.strip()
        if not text:
            return
        self.host.show(self)
        if self.turn is not None:
            self.say("AI ešte odpovedá (Ctrl+C ju zastaví).")
            return
        self.host.set_entry_text("")
        self.say("")
        self.messages.append({"role": "user", "content": text})
        self.add_bubble("user", text)
        bubble = self.add_bubble("assistant", "")
        bubble.set_markup("<i>Čakám na odpoveď…</i>")
        self.turn = Turn(bubble)
        self.update_empty()
        self.stop_button.set_visible(True)
        base, wanted = llm.settings()
        self.base = base
        threading.Thread(target=self.work, args=(self.turn, base, wanted, list(self.messages[-HISTORY_LIMIT:])),
                         daemon=True).start()
        self.scroll_down()

    def work(self, turn, base, wanted, messages):
        try:
            model = llm.pick_model(llm.list_models(base), wanted)
            GLib.idle_add(self.set_model, model)
            turn.stream = llm.ChatStream(base, model, messages)
            for kind, part in turn.stream.events():
                if turn.cancelled:
                    break
                GLib.idle_add(self.on_chunk, turn, kind, part)
        except llm.LlmError as err:
            GLib.idle_add(self.on_error, turn, str(err))
        except Exception as err:            # vlákno nesmie skončiť potichu, rozhranie by čakalo donekonečna
            GLib.idle_add(self.on_error, turn, "AI zlyhala: %s" % err)
        GLib.idle_add(self.on_done, turn)

    def set_model(self, model):
        self.model = model
        self.host.refresh()
        return False

    def on_chunk(self, turn, kind, part):
        if kind == "reasoning":
            turn.reasoning += part
        else:
            turn.text += part
        turn.dirty = True
        if not self.render_timer:
            self.render_timer = GLib.timeout_add(60, self.render, turn)
        return False

    def render(self, turn):
        self.render_timer = 0
        if not turn.dirty:
            return False
        turn.dirty = False
        if turn.text:
            turn.bubble.set_markup(textmark.to_pango(turn.text.strip()))
        elif turn.reasoning:
            turn.bubble.set_markup("<i>Premýšľam… (%d znakov úvahy)</i>" % len(turn.reasoning))
        self.scroll_down()
        return False

    def on_error(self, turn, message):
        turn.failed = True
        turn.bubble.remove_css_class("assistant")
        turn.bubble.add_css_class("error")
        turn.bubble.set_text(message)
        return False

    def on_done(self, turn):
        if turn.orphan:
            return False
        if self.render_timer:
            GLib.source_remove(self.render_timer)
            self.render_timer = 0
        turn.dirty = True
        if not turn.failed:
            self.render(turn)
        if self.turn is turn:
            self.turn = None
        self.stop_button.set_visible(False)
        if turn.failed or (turn.cancelled and not turn.text.strip()):
            self.drop_last_user_message()
        elif turn.text.strip():
            if turn.cancelled:
                turn.bubble.set_markup(textmark.to_pango(turn.text.strip()) + "\n<i>(zastavené)</i>")
            self.messages.append({"role": "assistant", "content": turn.text.strip()})
        elif not turn.cancelled:
            turn.bubble.set_markup("<i>AI nič neodpovedala.</i>")
            self.drop_last_user_message()
        self.host.refresh()
        return False

    def drop_last_user_message(self):
        if self.messages and self.messages[-1]["role"] == "user":
            self.messages.pop()

    def scroll_down(self):
        adj = self.scroll.get_vadjustment()

        def to_end():
            adj.set_value(adj.get_upper())
            return False

        GLib.idle_add(to_end)

    def key(self, keyval, state):
        if keyval in (Gdk.KEY_c, Gdk.KEY_C) and state & Gdk.ModifierType.CONTROL_MASK and self.turn:
            self.stop()
            return True
        return False

    def stop(self):
        turn = self.turn
        if turn is not None:
            turn.cancelled = True
            if turn.stream is not None:
                turn.stream.cancel()

    def reset(self):
        if self.turn is not None:
            self.turn.orphan = True
        self.stop()
        self.messages.clear()
        if self.render_timer:
            GLib.source_remove(self.render_timer)
            self.render_timer = 0
        self.stop_button.set_visible(False)
        child = self.chat.get_first_child()
        while child is not None:
            nxt = child.get_next_sibling()
            if child is not self.empty:
                self.chat.remove(child)
            child = nxt
        self.turn = None
        self.say("")
        self.update_empty()
        self.host.refresh()


MODE_CLASSES = (SearchMode, TerminalMode, AiMode)
