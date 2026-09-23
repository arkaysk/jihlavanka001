"""Služba latte-appearance: vynucuje vzhľad (súbory, kompozitor) a obsluhuje portál.

Pri štarte zapíše všetky vrstvy podľa nastavení. Potom sleduje ~/.config/latteos/appearance.toml
(zmena v Nastaveniach) aj súbory, ktoré spravuje (gtk.css, settings.ini, themerc-override), a keď sa
niekto od nastavenia odchýli, vráti ich späť. Kompozitor sa načíta znova (labwc -r), len ak sa jeho
téma naozaj zmenila.
"""
import os
import subprocess
import sys

from gi.repository import GLib

from latte_common import appearance, settings
from latte_appearance import portal


def log(*parts):
    print("latte-appearance:", *parts, file=sys.stderr, flush=True)


def reload_labwc():
    """labwc -r pošle SIGHUP labwc podľa LABWC_PID (autostart ho odovzdáva do user managera)."""
    pid = os.environ.get("LABWC_PID")
    if not pid or not os.path.exists("/proc/%s" % pid):
        log("labwc sa nenačíta znova: LABWC_PID chýba alebo labwc nebeží")
        return False
    try:
        subprocess.run(["labwc", "-r"], check=True, timeout=5, capture_output=True)
        return True
    except (subprocess.SubprocessError, OSError) as err:
        log("labwc -r zlyhalo:", err)
        return False


class Service:
    def __init__(self, dirs=None, reload=reload_labwc, store=None, directories=None):
        self.registry = settings.Registry()
        self.store = store or self.registry.store("appearance")
        self.dirs = dirs or appearance.Dirs.default()
        self.reload = reload
        self.directories = directories
        self.tokens = None
        self.portal = portal.PortalBackend(self.portal_values)
        self.monitors = []

    def compute(self):
        self.store.reload()
        self.tokens = appearance.resolve(self.store.values(), self.directories)
        self.tokens.problems = list(self.store.problems) + self.tokens.problems
        return self.tokens

    def portal_values(self):
        return appearance.portal_values(self.tokens or self.compute())

    def enforce(self):
        """Zapíše vrstvy, ktoré sa líšia od nastavení. Vráti zmenené cesty."""
        tokens = self.tokens or self.compute()
        for problem in tokens.problems:
            log("problém:", problem)
        actions = appearance.plan(tokens, self.dirs)
        changed = appearance.apply(actions)
        for path in changed:
            log("zapísané:", path)
        compositor = {a.path for a in actions if a.adapter == "compositor"}
        if compositor & set(changed):
            self.reload()
        return changed

    def on_change(self):
        self.compute()
        changed = self.enforce()
        sent = self.portal.refresh()
        log("nastavenia sa zmenili: %d súborov, %d hodnôt portálu" % (len(changed), sent))

    def on_drift(self):
        """Niekto zmenil spravovaný súbor: ak sa líši od nastavení, vráti sa späť."""
        changed = self.enforce()
        if changed:
            log("vynútené znova (súbor zmenený mimo Nastavení):", ", ".join(changed))

    def start(self):
        self.compute()
        self.enforce()
        self.portal.start()
        self.monitors.append(settings.watch([settings.Registry().domain("appearance").file], self.on_change))
        by_directory = {}
        for action in appearance.plan(self.tokens, self.dirs):
            by_directory.setdefault(os.path.dirname(action.path), []).append(os.path.basename(action.path))
        for directory, names in by_directory.items():
            try:
                self.monitors.append(settings.watch(names, self.on_drift, directory=directory))
            except (OSError, GLib.Error) as err:
                log("súbory v %s sa nesledujú: %s" % (directory, err))

    def run(self):
        self.start()
        log("beží (motív %s, %s)" % (self.tokens.theme_id, self.tokens.scheme))
        GLib.MainLoop().run()
