"""Úlohy na pozadí pre správcu súborov: vlákno alebo správcovský pomocník cez pkexec.

Obe úlohy majú rovnaké rozhranie: start(on_progress, on_done) a cancel(), a
všetky spätné volania idú v hlavnom vlákne GLib. Výsledok je fileops.Result.
"""
import errno
import json
import os
import threading

from gi.repository import Gio, GLib

from latte_common import fileops

HELPER = "/usr/libexec/latteos/latte-files-admin"
PKEXEC_DISMISSED = 126          # používateľ zavrel dialóg overenia


def admin_available():
    return os.access(HELPER, os.X_OK)


def _call(fn, *args):
    fn(*args)
    return False                # GLib.idle_add: nespúšťať znova


class LocalJob:
    def __init__(self, transfer):
        self.transfer = transfer

    def start(self, on_progress, on_done):
        def work():
            result = self.transfer.run(lambda p: GLib.idle_add(_call, on_progress, p))
            GLib.idle_add(_call, on_done, result)

        threading.Thread(target=work, daemon=True).start()

    def cancel(self):
        self.transfer.cancel()


def _to_result(data):
    result = fileops.Result()
    result.state = data.get("state", "error")
    result.done = data.get("done", [])
    err = data.get("error")
    result.error = tuple(err) if err else None
    return result


def _failure(path, message, state="error", code=errno.EIO):
    result = fileops.Result()
    result.state = state
    result.error = (path, code, message) if state == "error" else None
    return result


def _launch_failed(err):
    return _failure("", "Správcovský pomocník sa nespustil: " + err.message)


def _exit_result(proc, lines, path):
    """Výsledok, keď pomocník nepovedal nič zrozumiteľné (pkexec zlyhal skôr)."""
    status = proc.get_exit_status() if proc.get_if_exited() else -1
    if status == PKEXEC_DISMISSED:
        return _failure(path, "", state="cancelled")
    detail = " ".join(lines).strip()
    return _failure(path, detail or "Oprávnenie správcu sa nepodarilo získať (kód %d)." % status)


class AdminJob:
    """Prenos (kopírovanie/presun) ako root; priebeh a výsledok čítame z riadkov JSON."""

    def __init__(self, kind, sources, dest_dir, policy=fileops.KEEP_BOTH):
        self.argv = ["pkexec", HELPER, "transfer", kind, dest_dir, *sources, "--policy", policy]
        self.dest_dir = dest_dir
        self.proc = None
        self.started = False        # už prišiel prvý riadok od pomocníka (overenie prebehlo)
        self.cancelling = False
        self.final = None
        self.raw = []

    def start(self, on_progress, on_done):
        self.on_progress, self.on_done = on_progress, on_done
        try:
            self.proc = Gio.Subprocess.new(
                self.argv,
                Gio.SubprocessFlags.STDIN_PIPE
                | Gio.SubprocessFlags.STDOUT_PIPE
                | Gio.SubprocessFlags.STDERR_MERGE,
            )
        except GLib.Error as err:
            GLib.idle_add(_call, on_done, _launch_failed(err))
            return
        self.reader = Gio.DataInputStream.new(self.proc.get_stdout_pipe())
        self.reader.read_line_async(GLib.PRIORITY_DEFAULT, None, self._line)

    def _line(self, reader, task):
        try:
            line, _len = reader.read_line_finish_utf8(task)
        except GLib.Error:
            line = None
        if line is None:
            self.proc.wait_async(None, self._exited)
            return
        try:
            msg = json.loads(line)
        except ValueError:
            msg = None
        if isinstance(msg, dict) and "progress" in msg:
            self.started = True
            self.on_progress(fileops.Progress(*msg["progress"]))
        elif isinstance(msg, dict) and "result" in msg:
            self.final = msg["result"]
        else:
            self.raw.append(line)
        reader.read_line_async(GLib.PRIORITY_DEFAULT, None, self._line)

    def _exited(self, proc, task):
        try:
            proc.wait_finish(task)
        except GLib.Error:
            pass
        if self.final is not None:
            self.on_done(_to_result(self.final))
        elif self.cancelling:
            self.on_done(_failure(self.dest_dir, "", state="cancelled"))
        else:
            self.on_done(_exit_result(proc, self.raw, self.dest_dir))

    def cancel(self):
        if self.proc is None:
            return
        self.cancelling = True
        if not self.started:
            self.proc.force_exit()      # ešte čaká na overenie: zavrieť pkexec
            return
        try:
            out = self.proc.get_stdin_pipe()
            out.write_all(b"cancel\n", None)
            out.flush(None)
        except GLib.Error:
            self.proc.force_exit()


def call(args, on_result):
    """Jednorazový povel pomocníkovi (list, mkdir, rename, delete). on_result(dict)."""
    argv = ["pkexec", HELPER, *args]
    try:
        proc = Gio.Subprocess.new(
            argv,
            Gio.SubprocessFlags.STDIN_PIPE
            | Gio.SubprocessFlags.STDOUT_PIPE
            | Gio.SubprocessFlags.STDERR_MERGE,
        )
    except GLib.Error as err:
        GLib.idle_add(_call, on_result, {"state": "error", "error": ["", errno.EIO, "Správcovský pomocník sa nespustil: " + err.message]})
        return

    def finished(_proc, task):
        try:
            _ok, out, _err = proc.communicate_utf8_finish(task)
        except GLib.Error as err:
            on_result({"state": "error", "error": ["", errno.EIO, err.message]})
            return
        lines = (out or "").splitlines()
        final = None
        raw = []
        for line in lines:
            try:
                msg = json.loads(line)
            except ValueError:
                raw.append(line)
                continue
            if isinstance(msg, dict) and "result" in msg:
                final = msg["result"]
        if final is not None:
            on_result(final)
        elif proc.get_if_exited() and proc.get_exit_status() == PKEXEC_DISMISSED:
            on_result({"state": "cancelled"})
        else:
            code = proc.get_exit_status() if proc.get_if_exited() else -1
            on_result({"state": "error", "error": ["", errno.EIO,
                       " ".join(raw).strip() or "Oprávnenie správcu sa nepodarilo získať (kód %d)." % code]})

    proc.communicate_utf8_async(None, None, finished)
