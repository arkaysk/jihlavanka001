"""Zive udaje procesov, systemu a autorun poloziek pre Proces Manager/Monitor.

Modul necita nastavenia aplikacii ani nekonfiguruje hardware. Cita aktualny stav z
/proc a autorun zdrojov, aby ho mohlo pouzit GUI, CLI aj externe telemetry vystupy.
"""
import configparser
import os
import pwd
import signal
import subprocess
import time
from dataclasses import dataclass, field


@dataclass
class Process:
    pid: int
    ppid: int
    name: str
    state: str
    uid: int
    user: str
    kind: str
    cpu_percent: float = 0.0
    memory_bytes: int = 0
    command: str = ""
    executable: str = ""
    start_time: int = 0
    cpu_ticks: int = 0

    @property
    def is_system(self):
        return self.kind == "system"


@dataclass
class SystemSnapshot:
    processes: list = field(default_factory=list)
    memory_total: int = 0
    memory_available: int = 0
    swap_total: int = 0
    swap_free: int = 0
    uptime: float = 0.0
    load: tuple = (0.0, 0.0, 0.0)
    cpu_percent: float = 0.0

    @property
    def memory_used(self):
        return max(0, self.memory_total - self.memory_available)


@dataclass
class AutorunEntry:
    ident: str
    name: str
    source: str
    command: str
    kind: str
    enabled: bool = True
    writable: bool = False
    detail: str = ""


def _read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as stream:
            return stream.read()
    except OSError:
        return ""


def _user(uid):
    try:
        return pwd.getpwuid(uid).pw_name
    except (KeyError, TypeError):
        return str(uid)


def _status(path):
    values = {}
    for line in _read(path).splitlines():
        key, sep, value = line.partition(":")
        if sep:
            values[key] = value.strip()
    return values


def _bytes(value):
    parts = value.split()
    if not parts:
        return 0
    try:
        number = int(parts[0])
    except ValueError:
        return 0
    return number * (1024 if len(parts) > 1 and parts[1].lower() == "kb" else 1)


def _stat(stat_text):
    """Vrati meno, stav, rodica, cpu ticks a start tick z /proc/PID/stat."""
    left = stat_text.find("(")
    right = stat_text.rfind(")")
    if left < 0 or right <= left:
        raise ValueError("neplatny /proc stat")
    name = stat_text[left + 1:right]
    fields = stat_text[right + 2:].split()
    if len(fields) < 20:
        raise ValueError("neuplny /proc stat")
    return name, fields[0], int(fields[1]), int(fields[10]) + int(fields[11]), int(fields[18])


def _command(proc_dir, name):
    raw = _read(os.path.join(proc_dir, "cmdline"))
    if raw:
        return raw.replace("\0", " ").strip()
    return name


def read_processes(root="/proc", current_uid=None):
    """Nacita procesy bez prav administratora; proces, ktory medzitym skonci, preskoci."""
    current_uid = os.getuid() if current_uid is None else current_uid
    processes = []
    try:
        names = os.listdir(root)
    except OSError:
        return processes
    for entry in names:
        if not entry.isdigit():
            continue
        proc_dir = os.path.join(root, entry)
        try:
            pid = int(entry)
            stat = _stat(_read(os.path.join(proc_dir, "stat")))
            status = _status(os.path.join(proc_dir, "status"))
            uid = int(status.get("Uid", "-1").split()[0])
            memory = _bytes(status.get("VmRSS", "0"))
            user = _user(uid)
            kind = "user" if uid == current_uid else "system" if uid == 0 else "other"
            try:
                executable = os.readlink(os.path.join(proc_dir, "exe"))
            except OSError:
                executable = ""
            processes.append(Process(pid, stat[2], stat[0], stat[1], uid, user, kind,
                                     memory_bytes=memory, command=_command(proc_dir, stat[0]),
                                     executable=executable, start_time=stat[4], cpu_ticks=stat[3]))
        except (OSError, ValueError, IndexError):
            continue
    return sorted(processes, key=lambda item: item.pid)


def _cpu_ticks(root):
    line = next((x for x in _read(os.path.join(root, "stat")).splitlines() if x.startswith("cpu ")), "")
    values = line.split()[1:]
    try:
        numbers = [int(value) for value in values]
    except ValueError:
        return 0, 0
    return sum(numbers), numbers[3] if len(numbers) > 3 else 0


def _meminfo(root):
    values = {}
    for line in _read(os.path.join(root, "meminfo")).splitlines():
        key, sep, value = line.partition(":")
        if sep:
            values[key] = _bytes(value)
    total = values.get("MemTotal", 0)
    available = values.get("MemAvailable", values.get("MemFree", 0))
    return total, available, values.get("SwapTotal", 0), values.get("SwapFree", 0)


class Sampler:
    """Vzorka systemu s CPU percentami medzi dvoma citaniami."""

    def __init__(self, root="/proc", clock=time.monotonic, cpu_count=None):
        self.root = root
        self.clock = clock
        self.cpu_count = cpu_count or (os.cpu_count() or 1)
        self.previous = None

    def read(self):
        now = self.clock()
        total_ticks, idle_ticks = _cpu_ticks(self.root)
        processes = read_processes(self.root)
        current = {item.pid: (item, item.start_time) for item in processes}
        cpu_percent = 0.0
        if self.previous is not None:
            old_time, old_total, old_idle, old_proc = self.previous
            elapsed_ticks = total_ticks - old_total
            if elapsed_ticks > 0:
                cpu_percent = max(0.0, min(100.0, 100.0 * (elapsed_ticks - (idle_ticks - old_idle)) / elapsed_ticks))
                for item in processes:
                    old = old_proc.get(item.pid)
                    if old and old[1] == item.start_time:
                        item.cpu_percent = max(0.0, 100.0 * (item.cpu_ticks - old[0]) / elapsed_ticks * self.cpu_count)
        self.previous = (now, total_ticks, idle_ticks,
                         {pid: (item.cpu_ticks, item.start_time) for pid, (item, _start) in current.items()})
        total, available, swap_total, swap_free = _meminfo(self.root)
        try:
            uptime = float(_read(os.path.join(self.root, "uptime")).split()[0])
        except (ValueError, IndexError):
            uptime = 0.0
        try:
            load = tuple(float(value) for value in _read(os.path.join(self.root, "loadavg")).split()[:3])
        except (ValueError, IndexError):
            load = (0.0, 0.0, 0.0)
        return SystemSnapshot(processes, total, available, swap_total, swap_free, uptime, load, cpu_percent)


def terminate(pid, force=False):
    """Ukonci proces pouzivatela; PID 1 a vlastny proces su chranene."""
    if pid <= 1 or pid == os.getpid():
        raise PermissionError("tento proces nie je mozne ukoncit")
    os.kill(pid, signal.SIGKILL if force else signal.SIGTERM)


def _desktop_paths(home=None, system_dir="/etc/xdg/autostart"):
    home = home or os.path.expanduser("~")
    return [os.path.join(home, ".config", "autostart"), system_dir]


def autorun_entries(home=None, system_dir="/etc/xdg/autostart"):
    """Najde XDG autostart polozky; systemd jednotky doplni, ak su dostupne."""
    entries = []
    for directory in _desktop_paths(home, system_dir):
        try:
            names = sorted(name for name in os.listdir(directory) if name.endswith(".desktop"))
        except OSError:
            continue
        for name in names:
            path = os.path.join(directory, name)
            parser = configparser.RawConfigParser(interpolation=None)
            parser.optionxform = str
            try:
                parser.read(path, encoding="utf-8")
                section = "Desktop Entry"
                if not parser.has_section(section) or parser.get(section, "Type", fallback="Application") != "Application":
                    continue
                enabled = parser.get(section, "Hidden", fallback="false").lower() != "true"
                kind = "user" if directory != system_dir else "system"
                entries.append(AutorunEntry("desktop:" + path, parser.get(section, "Name", fallback=name), path,
                                           parser.get(section, "Exec", fallback=""), kind, enabled,
                                           kind == "user", "XDG autostart"))
            except (configparser.Error, OSError):
                continue
    return sorted(entries, key=lambda item: (item.kind, item.name.lower()))


def set_desktop_autorun(entry, enabled):
    if entry.kind != "user" or not entry.writable:
        raise PermissionError("systemovu autorun polozku nemoze menit bezpecne tento modul")
    parser = configparser.RawConfigParser(interpolation=None)
    parser.optionxform = str
    parser.read(entry.source, encoding="utf-8")
    if not parser.has_section("Desktop Entry"):
        raise ValueError("neplatny desktop subor")
    parser.set("Desktop Entry", "Hidden", "false" if enabled else "true")
    with open(entry.source, "w", encoding="utf-8") as stream:
        parser.write(stream, space_around_delimiters=False)


def systemd_autorun_entries(home=None):
    """Volitelny doplnok: vrati uzivatelske jednotky bez spustenia systemctl."""
    home = home or os.path.expanduser("~")
    directories = [os.path.join(home, ".config", "systemd", "user"), "/etc/systemd/user"]
    found = []
    for directory in directories:
        try:
            names = sorted(name for name in os.listdir(directory) if name.endswith((".service", ".timer", ".socket")))
        except OSError:
            continue
        for name in names:
            path = os.path.join(directory, name)
            kind = "user" if directory.startswith(home) else "system"
            found.append(AutorunEntry("systemd:" + path, name, path, "systemctl --user %s" % name,
                                      kind, True, kind == "user", "systemd user unit"))
    return found
