"""Manažér času: popup nad segmentom času s tromi stránkami (bod 2.6).

Čas (pásma), Oznámenia (zoznam z modelu oznámení, Nerušiť) a Kalendár.
"""
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib  # noqa: E402

from latte_common import clock  # noqa: E402
from latte_shell.popup import HoverPopup  # noqa: E402
from latte_shell.toasts import build_card  # noqa: E402

WIDTH = 440
PAGE_HEIGHT = 380
PAGES = (("zones", "Čas"), ("notifications", "Oznámenia"), ("calendar", "Kalendár"))


def clear_children(box):
    child = box.get_first_child()
    while child is not None:
        box.remove(child)
        child = box.get_first_child()


class TimeMenu(HoverPopup):
    def __init__(self, app, left, bottom, on_closed, center, service, page):
        super().__init__(app, left, bottom, "latte-time-menu", on_closed)
        self.center = center
        self.service = service
        self.tick_source = 0
        self.tabs = {}

        panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        panel.add_css_class("time-menu")
        panel.set_size_request(WIDTH, -1)
        panel.set_hexpand(False)

        bar = Gtk.Box(spacing=2)
        bar.add_css_class("tabs")
        for name, title in PAGES:
            button = Gtk.Button(label=title)
            button.add_css_class("tab")
            button.set_hexpand(True)
            button.connect("clicked", lambda _b, n=name: self.show_page(n))
            bar.append(button)
            self.tabs[name] = button
        panel.append(bar)

        self.stack = Gtk.Stack()
        self.stack.set_size_request(-1, PAGE_HEIGHT)
        self.stack.add_named(self.build_zones(), "zones")
        self.stack.add_named(self.build_notifications(), "notifications")
        self.stack.add_named(self.build_calendar(), "calendar")
        panel.append(self.stack)
        self.set_panel(panel)

        center.subscribe(self.refresh_notifications)
        self.tick_source = GLib.timeout_add_seconds(10, self.tick)
        self.show_page(page)

    # ---------- spoločné ----------
    def show_page(self, name):
        self.page = name
        self.stack.set_visible_child_name(name)
        for key, button in self.tabs.items():
            (button.add_css_class if key == name else button.remove_css_class)("active")
        if name == "zones":
            self.refresh_zones()
        elif name == "notifications":
            self.refresh_notifications()

    def holding(self):
        return self.zone_entry.has_focus() or self.zone_entry.get_text() != ""

    def tick(self):
        if self.page == "zones":
            self.refresh_zones()
        elif self.page == "notifications":
            self.refresh_notifications()
        return True

    def close_menu(self):
        self.center.unsubscribe(self.refresh_notifications)
        if self.tick_source:
            GLib.source_remove(self.tick_source)
            self.tick_source = 0
        super().close_menu()

    # ---------- Čas ----------
    def build_zones(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        page.add_css_class("time-page")
        self.local_time = Gtk.Label(xalign=0)
        self.local_time.add_css_class("time-big")
        self.local_place = Gtk.Label(xalign=0)
        self.local_place.add_css_class("dim")
        page.append(self.local_time)
        page.append(self.local_place)

        self.zone_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        scroll = Gtk.ScrolledWindow(vexpand=True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_child(self.zone_list)
        page.append(scroll)

        add = Gtk.Box(spacing=6)
        self.zone_entry = Gtk.Entry(hexpand=True, placeholder_text="Pridať pásmo, napr. Europe/Paris")
        self.zone_entry.add_css_class("time-entry")
        self.zone_entry.connect("activate", lambda _e: self.add_zone())
        button = Gtk.Button(label="Pridať")
        button.add_css_class("toast-action")
        button.connect("clicked", lambda _b: self.add_zone())
        add.append(self.zone_entry)
        add.append(button)
        page.append(add)
        self.zone_message = Gtk.Label(xalign=0, wrap=True)
        self.zone_message.set_max_width_chars(48)
        self.zone_message.add_css_class("system-message")
        self.zone_message.set_visible(False)
        page.append(self.zone_message)
        return page

    def refresh_zones(self):
        now = clock.utc_now()
        local = now.astimezone()
        self.local_time.set_text(local.strftime("%H:%M"))
        name = clock.local_zone_name()
        self.local_place.set_text("%s · %s" % (clock.city(name) if name else "Miestny čas",
                                              local.strftime("%-d. %-m. %Y")))
        clear_children(self.zone_list)
        zones = clock.load_zones()
        if not zones:
            empty = Gtk.Label(label="Žiadne ďalšie pásma. Pridaj ich nižšie.", xalign=0)
            empty.add_css_class("dim")
            self.zone_list.append(empty)
        for zone in zones:
            city, time_text, day, diff = clock.zone_row(now, zone)
            row = Gtk.Box(spacing=10)
            row.add_css_class("zone-row")
            names = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True)
            names.append(Gtk.Label(label=city, xalign=0))
            note = Gtk.Label(label="%s · %s" % (day, diff), xalign=0)
            note.add_css_class("dim")
            names.append(note)
            row.append(names)
            value = Gtk.Label(label=time_text)
            value.add_css_class("zone-time")
            row.append(value)
            remove = Gtk.Button(icon_name="window-close-symbolic")
            remove.add_css_class("flat")
            remove.add_css_class("prompt-tool")
            remove.set_tooltip_text("Odstrániť pásmo")
            remove.set_valign(Gtk.Align.CENTER)
            remove.connect("clicked", lambda _b, z=zone: self.remove_zone(z))
            row.append(remove)
            self.zone_list.append(row)

    def add_zone(self):
        error = clock.add_zone(self.zone_entry.get_text())
        self.zone_message.set_text(error or "")
        self.zone_message.set_visible(bool(error))
        if error is None:
            self.zone_entry.set_text("")
            self.refresh_zones()

    def remove_zone(self, zone):
        clock.remove_zone(zone)
        self.refresh_zones()

    # ---------- Oznámenia ----------
    def build_notifications(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        page.add_css_class("time-page")
        head = Gtk.Box(spacing=8)
        dnd = Gtk.Label(label="Nerušiť", xalign=0, hexpand=True)
        self.dnd_switch = Gtk.Switch(active=self.center.dnd, valign=Gtk.Align.CENTER)
        self.dnd_switch.connect("state-set", self.on_dnd)
        clear = Gtk.Button(label="Vymazať všetko")
        clear.add_css_class("toast-action")
        clear.connect("clicked", lambda _b: self.center.clear())
        head.append(dnd)
        head.append(self.dnd_switch)
        head.append(clear)
        page.append(head)

        self.note_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        scroll = Gtk.ScrolledWindow(vexpand=True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_child(self.note_list)
        page.append(scroll)

        self.problem = Gtk.Label(xalign=0, wrap=True)
        self.problem.set_max_width_chars(48)
        self.problem.add_css_class("system-message")
        page.append(self.problem)
        return page

    def on_dnd(self, _switch, state):
        self.center.set_dnd(state)
        return False

    def refresh_notifications(self):
        self.dnd_switch.set_active(self.center.dnd)
        problem = self.service.problem if self.service is not None else ""
        self.problem.set_text(problem)
        self.problem.set_visible(bool(problem))
        clear_children(self.note_list)
        if not self.center.items:
            empty = Gtk.Label(label="Žiadne oznámenia.", xalign=0)
            empty.add_css_class("dim")
            self.note_list.append(empty)
        for note in self.center.items:
            self.note_list.append(build_card(
                note,
                lambda key, n=note: self.center.invoke(n.id, key) if any(k == key for k, _l in n.actions)
                else self.center.close(n.id),
                lambda n=note: self.center.close(n.id),
                show_time=True,
            ))

    # ---------- Kalendár ----------
    def build_calendar(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        page.add_css_class("time-page")
        self.calendar = Gtk.Calendar()
        self.calendar.set_show_week_numbers(True)
        self.calendar.set_vexpand(True)
        page.append(self.calendar)
        today = Gtk.Button(label="Dnes")
        today.add_css_class("toast-action")
        today.connect("clicked", lambda _b: self.calendar.set_date(GLib.DateTime.new_now_local()))
        page.append(today)
        return page
