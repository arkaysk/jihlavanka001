#!/usr/bin/env python3
"""Proces Manager/Monitor LatteOS: zivy stav, procesy a autorun."""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib, Gdk  # noqa: E402
import cairo  # noqa: E402

from latte_common import hardware_catalog, processes, system_info, theme  # noqa: E402

POLL_MS = 1000


def label(text="", css=None, xalign=0.0, hexpand=False, wrap=False):
    widget = Gtk.Label(label=text, xalign=xalign, hexpand=hexpand, ellipsize=3)
    widget.set_wrap(wrap)
    if css:
        for name in css.split():
            widget.add_css_class(name)
    return widget


class HistoryGraph(Gtk.DrawingArea):
    """Male lokalne grafy bez externej charting kniznice."""

    def __init__(self, title, color):
        super().__init__()
        self.title = title
        self.color = color
        self.values = []
        self.set_content_height(170)
        self.set_hexpand(True)
        self.set_draw_func(self.draw)

    def add(self, value):
        self.values.append(max(0.0, min(100.0, float(value))))
        del self.values[:-60]
        self.queue_draw()

    def draw(self, _area, cr, width, height):
        cr.set_source_rgba(0.08, 0.07, 0.06, 0.18)
        cr.paint()
        left, top, right, bottom = 42, 22, max(44, width - 12), max(44, height - 26)
        graph_width, graph_height = right - left, bottom - top
        cr.set_line_width(1)
        cr.set_source_rgba(0.75, 0.70, 0.64, 0.18)
        for step in range(6):
            y = top + graph_height * step / 5
            cr.move_to(left, y)
            cr.line_to(right, y)
            cr.stroke()
            cr.set_source_rgba(0.75, 0.70, 0.64, 0.75)
            cr.select_font_face("sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
            cr.set_font_size(10)
            cr.move_to(8, y + 4)
            cr.show_text(str(100 - step * 20) + "%")
            cr.set_source_rgba(0.75, 0.70, 0.64, 0.18)
        cr.set_source_rgba(*self.color, 1.0)
        cr.set_font_size(12)
        cr.move_to(left, 14)
        cr.show_text(self.title)
        if not self.values:
            return
        cr.set_line_width(2)
        for index, value in enumerate(self.values):
            x = left + graph_width * index / max(1, len(self.values) - 1)
            y = bottom - graph_height * value / 100
            if index == 0:
                cr.move_to(x, y)
            else:
                cr.line_to(x, y)
        cr.stroke()
        value = self.values[-1]
        cr.arc(right, bottom - graph_height * value / 100, 3, 0, 2 * 3.14159)
        cr.fill()


class ExpandableSection(Gtk.Box):
    """Bočna sekcia s rovnakym rozbalovacim spravanim ako Nastavenia."""

    def __init__(self, window, title, icon, pages, expanded=False):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.window = window
        self.expanded = False
        self.add_css_class("process-section")
        self.head = Gtk.Button()
        self.head.add_css_class("flat")
        self.head.add_css_class("process-section-head")
        line = Gtk.Box(spacing=10)
        line.append(Gtk.Image.new_from_icon_name(icon))
        line.append(label(title.upper(), "section-title", hexpand=True))
        self.chevron = Gtk.Image.new_from_icon_name("pan-end-symbolic")
        line.append(self.chevron)
        self.head.set_child(line)
        self.head.connect("clicked", lambda _button: self.toggle())
        self.append(self.head)
        self.list = Gtk.ListBox()
        self.list.add_css_class("process-section-pages")
        self.list.connect("row-activated", lambda _list, row: window.show_page(row.page_name))
        for page_name, page_title, page_icon in pages:
            row = Gtk.ListBoxRow()
            row.page_name = page_name
            row.set_child(self.page_row(page_title, page_icon))
            self.list.append(row)
        self.revealer = Gtk.Revealer(transition_type=Gtk.RevealerTransitionType.SLIDE_DOWN,
                                     transition_duration=180)
        self.revealer.set_child(self.list)
        self.append(self.revealer)
        self.set_expanded(expanded)

    def page_row(self, title, icon):
        line = Gtk.Box(spacing=10)
        line.append(Gtk.Image.new_from_icon_name(icon))
        line.append(label(title, "sidebar-item", hexpand=True))
        return line

    def toggle(self):
        self.set_expanded(not self.expanded)

    def set_expanded(self, expanded):
        self.expanded = expanded
        self.chevron.set_from_icon_name("pan-down-symbolic" if expanded else "pan-end-symbolic")
        self.revealer.set_reveal_child(expanded)
        if expanded:
            self.add_css_class("expanded")
        else:
            self.remove_css_class("expanded")


class Window(Gtk.ApplicationWindow):
    def __init__(self, app, advanced=False):
        super().__init__(application=app, title="Proces Manažér/Monitor")
        self.add_css_class("latte-process")
        self.set_default_size(1120, 700)
        self.advanced = advanced
        self.sampler = processes.Sampler()
        self.telemetry = system_info.TelemetrySampler()
        self.catalog = hardware_catalog.load()
        self.cpu = system_info.cpu_info()
        self.graph_source = "CPU"
        self.snapshot = None
        self.stack = Gtk.Stack(vexpand=True, hexpand=True)
        self.status = label("", "process-status")
        self.processes_list = Gtk.ListBox()
        self.processes_list.add_css_class("process-list")
        self.autorun_list = Gtk.ListBox()
        self.autorun_list.add_css_class("process-list")

        header = Gtk.HeaderBar()
        header.add_css_class("files-toolbar")
        title = label("Proces Manažér/Monitor", "toolbar-title")
        header.set_title_widget(title)
        self.mode_button = Gtk.Button(label="Advanced: maximalizovať")
        self.mode_button.add_css_class("flat")
        self.mode_button.set_tooltip_text("Maximalizovať okno pre pokročilý monitoring")
        self.mode_button.connect("clicked", self.toggle_advanced)
        header.pack_end(self.mode_button)
        self.search = Gtk.SearchEntry(placeholder_text="Hľadať názov, používateľa alebo PID")
        self.search.set_size_request(320, -1)
        self.search.connect("search-changed", self.on_search)
        header.pack_start(self.search)
        self.set_titlebar(header)

        body = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        body.add_css_class("process-body")
        body.append(self.sidebar())
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True)
        content.append(self.action_bar())
        content.append(self.stack)
        content.append(self.status)
        body.append(content)
        self.set_child(body)

        self.stack.add_titled(self.monitor_page(), "processes", "Procesy")
        self.stack.add_titled(self.performance_page(), "performance", "Výkon")
        self.stack.add_titled(self.hardware_page(), "hardware", "Hardware")
        self.stack.add_titled(self.autorun_page(), "autorun", "Autorun")
        self.stack.add_titled(self.services_page(), "services", "Služby")
        self.show_page("processes")
        self.key_controller = Gtk.EventControllerKey()
        self.key_controller.connect("key-pressed", self.on_key)
        self.add_controller(self.key_controller)
        if advanced:
            self.maximize()
            self.mode_button.set_label("Obnoviť okno")
        self.refresh()
        self.refresh_source = GLib.timeout_add(POLL_MS, self.refresh)

    def sidebar(self):
        side = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        side.add_css_class("process-sidebar")
        side.set_size_request(238, -1)
        side.append(label("Proces Manažér", "sidebar-title"))
        self.sections = []
        for title, icon, pages, expanded in (
            ("Systém", "emblem-system-symbolic",
             (("processes", "Procesy", "utilities-system-monitor-symbolic"),
              ("services", "Služby", "system-services-symbolic")), True),
            ("Výkon", "utilities-system-monitor-symbolic",
             (("performance:CPU", "Procesor", "latte-cpu-symbolic"),
              ("performance:RAM", "Pamäť", "latte-memory-symbolic"),
              ("performance:I/O", "Disky", "drive-harddisk-symbolic"),
              ("performance:Sieť", "Sieť", "network-wireless-symbolic"),
              ("performance:Grafika", "GPU", "latte-gpu-symbolic")), True),
            ("Správa", "system-run-symbolic",
             (("autorun", "Aplikácie pri spustení", "system-run-symbolic"),), False),
            ("Hardware", "computer-symbolic",
             (("hardware", "Identifikácia hardware", "computer-symbolic"),), False)):
            section = ExpandableSection(self, title, icon, pages, expanded)
            self.sections.append(section)
            side.append(section)
        side.append(Gtk.Box(vexpand=True))
        side.append(label("Aktuálny stav systému", "sidebar-foot"))
        return side

    def action_bar(self):
        bar = Gtk.Box(spacing=8)
        bar.add_css_class("process-action-bar")
        self.content_title = label("Procesy", "content-title", hexpand=True)
        bar.append(self.content_title)
        self.new_task_button = Gtk.Button(label="Spustiť novú úlohu")
        self.new_task_button.add_css_class("flat")
        self.new_task_button.connect("clicked", self.show_new_task)
        bar.append(self.new_task_button)
        self.stop_selected = Gtk.Button(label="Ukončiť úlohu")
        self.stop_selected.add_css_class("flat")
        self.stop_selected.set_sensitive(False)
        bar.append(self.stop_selected)
        return bar

    def show_page(self, name):
        if name.startswith("performance:"):
            self.select_graph_source(name.split(":", 1)[1])
            name = "performance"
        self.stack.set_visible_child_name(name)
        titles = {"processes": "Procesy", "performance": "Výkon", "hardware": "Hardware",
                  "autorun": "Aplikácie pri spustení", "services": "Služby"}
        self.content_title.set_text(titles.get(name, "Proces Manažér"))
        if name == "autorun":
            self.refresh_autorun()

    def show_new_task(self, _button):
        self.status.set_text("Spúšťanie novej úlohy bude doplnené cez aplikačný launcher.")

    def on_search(self, entry):
        self.search_term = entry.get_text().strip().lower()
        if self.snapshot is not None:
            self.rebuild_processes(self.snapshot.processes)

    def show_tab(self, index):
        name = ("processes", "autorun")[index]
        self.show_page(name)
        self.stack.set_visible_child_name(name)

    def monitor_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        page.set_margin_top(14)
        page.set_margin_start(18)
        page.set_margin_end(18)
        summary = Gtk.Grid(column_spacing=24, row_spacing=4)
        summary.add_css_class("process-summary")
        self.cpu_value = label("--", "metric-value")
        self.memory_value = label("--", "metric-value")
        self.swap_value = label("--", "metric-value")
        self.load_value = label("--", "metric-value")
        for col, (name, value) in enumerate((("CPU", self.cpu_value), ("RAM", self.memory_value),
                                              ("Swap", self.swap_value), ("Load", self.load_value))):
            summary.attach(label(name, "metric-name"), col, 0, 1, 1)
            summary.attach(value, col, 1, 1, 1)
        page.append(summary)
        catalog_source = self.catalog.source or "pribaleny fallback"
        page.append(label("Offline hardware katalog: %s" % catalog_source, "process-detail"))
        columns = Gtk.Box(spacing=8)
        columns.add_css_class("process-columns")
        for text, width in (("PID", 70), ("Proces", 220), ("Používateľ", 120), ("CPU", 90), ("RAM", 100), ("Typ", 110)):
            columns.append(label(text, "column-head", hexpand=width == 220))
        columns.append(label("Akcia", "column-head"))
        page.append(columns)
        scroll = Gtk.ScrolledWindow(vexpand=True, hexpand=True)
        scroll.set_child(self.processes_list)
        page.append(scroll)
        return page

    def performance_page(self):
        self.performance_page_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, vexpand=True)
        self.rebuild_performance_view("CPU")
        return self.performance_page_box

    def rebuild_performance_view(self, source):
        child = self.performance_page_box.get_first_child()
        while child is not None:
            next_child = child.get_next_sibling()
            self.performance_page_box.remove(child)
            child = next_child
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        page.set_margin_top(18)
        page.set_margin_start(22)
        page.set_margin_end(22)
        titles = {"CPU": ("Procesor", "Vyťaženie procesora a jeho okamžité údaje."),
                  "RAM": ("Pamäť", "Obsadená, dostupná a odkladacia pamäť."),
                  "I/O": ("Disky", "Aktivita a prenosové rýchlosti úložných zariadení."),
                  "Sieť": ("Sieť", "Prijímané a odosielané dáta podľa rozhrania."),
                  "Grafika": ("GPU", "Využitie grafického procesora a jeho senzory.")}
        title, lead = titles[source]
        page.append(label(title, "page-title"))
        page.append(label(lead, "page-lead"))
        graphs = Gtk.Box(spacing=10)
        graphs.add_css_class("performance-graphs")
        self.graphs = []
        if source == "CPU":
            self.cpu_graph = HistoryGraph("CPU utilization", (0.88, 0.48, 0.18))
            self.graphs.append((self.cpu_graph, "cpu"))
        elif source == "RAM":
            self.memory_graph = HistoryGraph("Memory usage", (0.35, 0.62, 0.78))
            self.graphs.append((self.memory_graph, "memory"))
        elif source == "I/O":
            self.disk_read_graph = HistoryGraph("Read", (0.55, 0.72, 0.28))
            self.disk_write_graph = HistoryGraph("Write", (0.88, 0.48, 0.18))
            self.graphs.extend(((self.disk_read_graph, "disk_read"), (self.disk_write_graph, "disk_write")))
        elif source == "Sieť":
            self.network_receive_graph = HistoryGraph("Receive", (0.35, 0.62, 0.78))
            self.network_send_graph = HistoryGraph("Send", (0.88, 0.32, 0.42))
            self.graphs.extend(((self.network_receive_graph, "network_receive"),
                                (self.network_send_graph, "network_send")))
        else:
            self.gpu_graph = HistoryGraph("GPU utilization", (0.62, 0.38, 0.88))
            self.graphs.append((self.gpu_graph, "gpu"))
        for graph, _metric in self.graphs:
            graphs.append(graph)
        page.append(graphs)
        self.performance_values = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.performance_values.add_css_class("telemetry-panel")
        page.append(self.performance_values)
        self.sensor_list = Gtk.ListBox()
        self.sensor_list.add_css_class("process-list")
        page.append(label("Dostupné senzory", "section-title"))
        page.append(self.sensor_list)
        self.telemetry_list = Gtk.ListBox()
        self.telemetry_list.add_css_class("process-list")
        page.append(label("Aktívne zariadenia", "section-title"))
        page.append(self.telemetry_list)
        self.performance_page_box.append(page)

    def current_graph_value(self, metric, snapshot, telemetry):
        memory_percent = 100 * snapshot.memory_used / snapshot.memory_total if snapshot.memory_total else 0
        if metric == "cpu":
            return snapshot.cpu_percent
        if metric == "memory":
            return memory_percent
        if metric == "gpu":
            return max((item["busy_percent"] for item in telemetry["gpu"]), default=0)
        if metric.startswith("disk_"):
            key = "read_bytes_sec" if metric == "disk_read" else "write_bytes_sec"
            return min(100, sum(item[key] for item in telemetry["disks"]) / (100 * 1024 * 1024) * 100)
        key = "receive_bytes_sec" if metric == "network_receive" else "send_bytes_sec"
        return min(100, sum(item[key] for item in telemetry["network"]) / (100 * 1024 * 1024) * 100)

    def select_graph_source(self, source):
        self.graph_source = source
        if hasattr(self, "performance_page_box"):
            self.rebuild_performance_view(source)
        self.status.set_text("Grafický zdroj: %s" % source)

    def hardware_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        page.set_margin_top(18)
        page.set_margin_start(22)
        page.set_margin_end(22)
        page.append(label("Hardware", "page-title"))
        page.append(label("CPU-Z a HWiNFO štýl identifikácie. Údaje sú iba na čítanie.", "page-lead"))
        grid = Gtk.Grid(column_spacing=28, row_spacing=10)
        grid.add_css_class("hardware-facts")
        facts = (("Procesor", self.cpu["model"]), ("Výrobca", self.cpu["vendor"]),
                 ("Architektúra", self.cpu["architecture"] or "Neznáma"),
                 ("Jadrá / vlákna", "%d / %d" % (self.cpu["cores"], self.cpu["threads"])),
                 ("Frekvencia", self.cpu["frequency"] + " MHz" if self.cpu["frequency"] else "Neznáma"),
                 ("Cache", self.cpu["cache"] or "Neznáma"),
                 ("PCI katalóg", self.catalog.source or "LatteOS fallback"))
        for index, (name, value) in enumerate(facts):
            row = index % 4
            col = (index // 4) * 2
            grid.attach(label(name, "fact-name"), col, row, 1, 1)
            grid.attach(label(value, "fact-value", hexpand=True), col + 1, row, 1, 1)
        page.append(grid)
        flags = " ".join(self.cpu["flags"][:18]) or "Neznáme"
        page.append(label("CPU features: " + flags, "process-detail"))
        return page

    def services_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        page.set_margin_top(18)
        page.set_margin_start(22)
        page.set_margin_end(22)
        page.append(label("Služby", "page-title"))
        page.append(label("Prehľad systemd služieb bude napojený bez preberania ich konfigurácie.", "page-lead"))
        page.append(label("Táto sekcia zatiaľ zobrazuje iba hranicu modulu: Proces Manažér monitoruje stav, App Manager a Device Manager nastavujú svoje oblasti.", "process-detail", wrap=True))
        return page

    def autorun_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        page.set_margin_top(14)
        page.set_margin_start(18)
        page.set_margin_end(18)
        page.append(label("Položky spúšťané pri štarte relácie", "page-title"))
        page.append(label("Používateľské položky je možné povoliť alebo zakázať. Systémové položky sú iba na čítanie.", "page-lead"))
        scroll = Gtk.ScrolledWindow(vexpand=True, hexpand=True)
        scroll.set_child(self.autorun_list)
        page.append(scroll)
        return page

    def refresh(self):
        self.snapshot = self.sampler.read()
        snapshot = self.snapshot
        self.cpu_value.set_text("%.1f %%" % snapshot.cpu_percent)
        self.memory_value.set_text("%s / %s" % (format_bytes(snapshot.memory_used), format_bytes(snapshot.memory_total)))
        self.swap_value.set_text("%s / %s" % (format_bytes(snapshot.swap_total - snapshot.swap_free), format_bytes(snapshot.swap_total)))
        self.load_value.set_text("%.2f  %.2f  %.2f" % snapshot.load)
        self.rebuild_processes(snapshot.processes)
        self.refresh_performance(snapshot)
        telemetry = self.refresh_telemetry()
        for graph, metric in self.graphs:
            graph.add(self.current_graph_value(metric, snapshot, telemetry))
        return True

    def refresh_performance(self, snapshot):
        if not hasattr(self, "performance_values"):
            return
        child = self.performance_values.get_first_child()
        while child is not None:
            next_child = child.get_next_sibling()
            self.performance_values.remove(child)
            child = next_child
        memory_used = "%s / %s" % (format_bytes(snapshot.memory_used), format_bytes(snapshot.memory_total))
        values = {
            "CPU": (("Utilizácia", "%.1f %%" % snapshot.cpu_percent),
                ("Load average", "%.2f  %.2f  %.2f" % snapshot.load)),
            "RAM": (("Použitá pamäť", memory_used),
                ("Swap", "%s / %s" % (format_bytes(snapshot.swap_total - snapshot.swap_free), format_bytes(snapshot.swap_total)))),
            "I/O": (), "Sieť": (), "Grafika": (),
        }
        for name, value in values[self.graph_source]:
            row = Gtk.Box(spacing=14)
            row.append(label(name, "fact-name", hexpand=True))
            row.append(label(value, "fact-value"))
            self.performance_values.append(row)
        child = self.sensor_list.get_first_child()
        while child is not None:
            next_child = child.get_next_sibling()
            self.sensor_list.remove(child)
            child = next_child
        sensors = system_info.sensors() + system_info.thermal_zones()
        if self.graph_source == "CPU":
            sensors = [sensor for sensor in sensors if sensor["kind"] == "temp" and
                       any(word in sensor["name"].lower() for word in ("cpu", "core", "package", "k10", "tctl"))]
        elif self.graph_source == "Grafika":
            sensors = [sensor for sensor in sensors if any(word in sensor["name"].lower()
                       for word in ("gpu", "edge", "junction", "video"))]
        else:
            sensors = []
        for sensor in sensors:
            row = Gtk.ListBoxRow()
            line = Gtk.Box(spacing=12)
            line.set_margin_top(6)
            line.set_margin_bottom(6)
            line.append(label(sensor["name"], "process-cell", hexpand=True))
            line.append(label("%.1f %s" % (sensor["value"], sensor["unit"]), "fact-value"))
            row.set_child(line)
            self.sensor_list.append(row)

    def refresh_telemetry(self):
        if not hasattr(self, "telemetry_list"):
            return {"disks": [], "network": [], "gpu": []}
        telemetry = self.telemetry.read()
        child = self.telemetry_list.get_first_child()
        while child is not None:
            next_child = child.get_next_sibling()
            self.telemetry_list.remove(child)
            child = next_child
        rows = []
        if self.graph_source == "I/O":
            for item in telemetry["disks"]:
                rows.append((item["name"], "disk", "R %s/s · W %s/s" %
                             (format_bytes(item["read_bytes_sec"]), format_bytes(item["write_bytes_sec"]))))
        elif self.graph_source == "Sieť":
            for item in telemetry["network"]:
                rows.append((item["name"], "network", "RX %s/s · TX %s/s" %
                             (format_bytes(item["receive_bytes_sec"]), format_bytes(item["send_bytes_sec"]))))
        elif self.graph_source == "Grafika":
            for item in telemetry["gpu"]:
                rows.append((item["name"], "GPU", "využitie %.1f %%" % item["busy_percent"]))
        for name, kind, value in rows:
            row = Gtk.ListBoxRow()
            line = Gtk.Box(spacing=12)
            line.set_margin_top(5)
            line.set_margin_bottom(5)
            line.append(label(name, "process-cell", hexpand=True))
            line.append(label(kind, "process-detail"))
            line.append(label(value, "fact-value"))
            row.set_child(line)
            self.telemetry_list.append(row)
        return telemetry

    def rebuild_processes(self, items):
        child = self.processes_list.get_first_child()
        while child is not None:
            next_child = child.get_next_sibling()
            self.processes_list.remove(child)
            child = next_child
        term = getattr(self, "search_term", "")
        visible = [item for item in items if not term or term in (item.command + " " + item.name + " " + item.user + " " + str(item.pid)).lower()]
        for item in sorted(visible, key=lambda process: (-process.cpu_percent, process.pid)):
            row = Gtk.ListBoxRow()
            line = Gtk.Box(spacing=8)
            line.set_margin_top(5)
            line.set_margin_bottom(5)
            line.append(label(str(item.pid), "process-cell"))
            name = label(item.command or item.name, "process-cell", hexpand=True)
            name.set_tooltip_text(item.executable or item.command or item.name)
            line.append(name)
            line.append(label(item.user, "process-cell"))
            line.append(label("%.1f %%" % item.cpu_percent, "process-cell"))
            line.append(label(format_bytes(item.memory_bytes), "process-cell"))
            line.append(label("Systémový" if item.is_system else "Používateľ", "process-cell"))
            stop = Gtk.Button(icon_name="process-stop-symbolic")
            stop.set_tooltip_text("Ukončiť proces")
            stop.add_css_class("flat")
            stop.connect("clicked", lambda _button, pid=item.pid: self.stop_process(pid, False))
            line.append(stop)
            if self.advanced:
                force = Gtk.Button(label="Kill")
                force.set_tooltip_text("Nútene ukončiť proces")
                force.add_css_class("destructive-action")
                force.connect("clicked", lambda _button, pid=item.pid: self.stop_process(pid, True))
                line.append(force)
            row.set_child(line)
            self.processes_list.append(row)

    def stop_process(self, pid, force):
        try:
            processes.terminate(pid, force)
            self.status.set_text("Proces %d bol odoslaný na ukončenie." % pid)
        except (OSError, PermissionError) as error:
            self.status.set_text("Proces %d sa nepodarilo ukončiť: %s" % (pid, error))

    def refresh_autorun(self):
        child = self.autorun_list.get_first_child()
        while child is not None:
            next_child = child.get_next_sibling()
            self.autorun_list.remove(child)
            child = next_child
        entries = processes.autorun_entries() + processes.systemd_autorun_entries()
        for entry in entries:
            row = Gtk.ListBoxRow()
            line = Gtk.Box(spacing=10)
            line.set_margin_top(7)
            line.set_margin_bottom(7)
            text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2, hexpand=True)
            text.append(label(entry.name, "process-cell"))
            text.append(label("%s · %s" % (entry.kind.capitalize(), entry.source), "process-detail"))
            text.append(label(entry.command, "process-command"))
            line.append(text)
            switch = Gtk.Switch(active=entry.enabled)
            switch.set_valign(Gtk.Align.CENTER)
            switch.set_sensitive(entry.writable)
            switch.connect("state-set", lambda _switch, state, e=entry: self.change_autorun(e, state))
            line.append(switch)
            row.set_child(line)
            self.autorun_list.append(row)

    def change_autorun(self, entry, enabled):
        try:
            processes.set_desktop_autorun(entry, enabled)
            self.status.set_text("Autorun: %s" % ("povolené" if enabled else "zakázané"))
        except (OSError, PermissionError, ValueError) as error:
            self.status.set_text("Autorun sa nepodarilo zmeniť: %s" % error)
            GLib.idle_add(self.refresh_autorun)
        return False

    def toggle_advanced(self, _button):
        self.advanced = not self.advanced
        if self.advanced:
            self.maximize()
            self.mode_button.set_label("Obnoviť okno")
        else:
            self.unmaximize()
            self.mode_button.set_label("Advanced: maximalizovať")
        self.refresh()

    def on_key(self, _controller, keyval, _keycode, _state):
        if keyval == Gdk.KEY_Escape and self.advanced:
            self.toggle_advanced(None)
            return True
        return False


def format_bytes(value):
    value = float(max(0, value))
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if value < 1024 or unit == "TiB":
            return "%.1f %s" % (value, unit)
        value /= 1024


class Application(Gtk.Application):
    def __init__(self, advanced=False):
        super().__init__(application_id="org.latteos.ProcessManager")
        self.advanced = advanced

    def do_activate(self):
        window = self.props.active_window
        if window is None:
            window = Window(self, self.advanced)
            theme.load(window.get_display())
        window.present()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Proces Manažér/Monitor LatteOS")
    parser.add_argument("--advanced", action="store_true", help="pokrocily rezim na celej obrazovke")
    args = parser.parse_args(argv)
    return Application(args.advanced).run([])


if __name__ == "__main__":
    sys.exit(main())
