"""Ikony na ploche (bod 2.10): obsah priečinka Plocha (~/Desktop) a Kôš.

Ikony sa plnia po stĺpcoch zhora nadol. Dvojklik otvorí: priečinok v správcovi súborov, spúšťač
(.desktop) spustí aplikáciu, ostatné súbory ich predvolená aplikácia. Zmeny v priečinku sa
prejavia hneď.
"""
import os

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio, GLib, Pango  # noqa: E402

ICON_SIZE = 48
CELL_WIDTH = 96
MARGIN = 16


def desktop_dir():
    path = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DESKTOP)
    home = os.path.expanduser("~")
    if not path or os.path.normpath(path) == home:
        return None                     # bez priečinka Plocha by ikony nahradili celý domov
    return path


def trash_dir():
    return os.path.join(GLib.get_user_data_dir(), "Trash", "files")


def trash_count():
    try:
        return len(os.listdir(trash_dir()))
    except OSError:
        return 0


class Entry:
    """Jedna ikona: názov, ikona, cesta a druh (file | dir | launcher | trash)."""

    def __init__(self, name, gicon, path, kind):
        self.name, self.gicon, self.path, self.kind = name, gicon, path, kind


def list_entries(directory):
    entries = []
    if directory and os.path.isdir(directory):
        for name in sorted(os.listdir(directory), key=lambda n: n.lower()):
            if name.startswith("."):
                continue
            path = os.path.join(directory, name)
            if os.path.isdir(path):
                entries.append(Entry(name, Gio.ThemedIcon.new("folder"), path, "dir"))
            elif name.endswith(".desktop"):
                info = Gio.DesktopAppInfo.new_from_filename(path)
                if info is not None:
                    entries.append(Entry(info.get_display_name() or name,
                                         info.get_icon() or Gio.ThemedIcon.new("application-x-executable"),
                                         path, "launcher"))
                    continue
                entries.append(Entry(name, Gio.ThemedIcon.new("text-x-generic"), path, "file"))
            else:
                content_type, _u = Gio.content_type_guess(name, None)
                entries.append(Entry(name, Gio.content_type_get_icon(content_type), path, "file"))
    full = trash_count() > 0
    entries.append(Entry("Kôš", Gio.ThemedIcon.new("user-trash-full" if full else "user-trash"),
                         trash_dir(), "trash"))
    return entries


class DesktopIcons(Gtk.FlowBox):
    def __init__(self, open_files):
        super().__init__()
        self.open_files = open_files
        self.reload_source = 0
        self.add_css_class("desktop-icons")
        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.set_max_children_per_line(30)
        self.set_homogeneous(True)
        self.set_activate_on_single_click(False)
        self.set_halign(Gtk.Align.START)
        self.set_valign(Gtk.Align.START)
        self.connect("child-activated", lambda _f, child: self.open(child.entry))

        self.monitors = []
        for path in (desktop_dir(), os.path.dirname(trash_dir())):
            if path and os.path.isdir(path):
                monitor = Gio.File.new_for_path(path).monitor_directory(Gio.FileMonitorFlags.NONE, None)
                monitor.connect("changed", lambda *_a: self.schedule())
                self.monitors.append(monitor)
        self.reload()

    def schedule(self):
        if not self.reload_source:
            self.reload_source = GLib.timeout_add(200, self.reload)

    def reload(self):
        self.reload_source = 0
        self.remove_all()
        for entry in list_entries(desktop_dir()):
            self.append(self.build(entry))
        self.unselect_all()
        return False

    def build(self, entry):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        box.set_size_request(CELL_WIDTH, -1)
        icon = Gtk.Image.new_from_gicon(entry.gicon)
        icon.set_pixel_size(ICON_SIZE)
        label = Gtk.Label(label=entry.name)
        label.set_wrap(True)
        label.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        label.set_width_chars(11)
        label.set_max_width_chars(11)
        label.set_justify(Gtk.Justification.CENTER)
        label.add_css_class("desktop-label")
        box.append(icon)
        box.append(label)
        child = Gtk.FlowBoxChild()
        child.set_child(box)
        child.entry = entry
        return child

    def open(self, entry):
        if entry.kind in ("dir", "trash"):
            os.makedirs(entry.path, exist_ok=True)
            self.open_files(entry.path)
        elif entry.kind == "launcher":
            info = Gio.DesktopAppInfo.new_from_filename(entry.path)
            try:
                info.launch([], None)
            except GLib.Error as err:
                print("latte-shell: spúšťač %s sa nespustil: %s" % (entry.path, err.message))
        else:
            try:
                Gio.AppInfo.launch_default_for_uri(Gio.File.new_for_path(entry.path).get_uri(), None)
            except GLib.Error as err:
                print("latte-shell: %s sa nedá otvoriť: %s" % (entry.path, err.message))
