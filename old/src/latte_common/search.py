"""Hľadanie súborov a priečinkov podľa názvu (prompt v lište, režim Hľadať).

Prechádza sa do šírky, takže plytké zhody prídu prvé. Skryté položky (názov od bodky)
sa preskakujú, rovnako ako v správcovi súborov. Veľkosť písmen a diakritika nerozhoduje.
"""
import os
import unicodedata
from collections import deque, namedtuple

Hit = namedtuple("Hit", "path name is_dir")

SKIP_DIRS = {"node_modules", "__pycache__"}


def fold(text):
    """Malé písmená bez diakritiky: „Žltá“ sa nájde ako „zlta“."""
    decomposed = unicodedata.normalize("NFD", text.casefold())
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def words(query):
    return [w for w in fold(query).split() if w]


def dedupe_roots(roots):
    """Existujúce priečinky bez duplicít a bez tých, čo ležia v inom z koreňov."""
    real = []
    for root in roots:
        if root and os.path.isdir(root):
            path = os.path.realpath(root)
            if path not in real:
                real.append(path)
    return [r for r in real
            if not any(o != r and r.startswith(o.rstrip("/") + "/") for o in real)]


def search_roots(volumes, home):
    """Kde sa hľadá: domovský priečinok a pripojené zväzky s dátami.
    Systémový zväzok sa neprehľadáva celý, je v ňom len to, čo ukazuje správca súborov."""
    roots = [home]
    roots += [v.path for v in volumes if v.mounted and v.role != "system"]
    return dedupe_roots(roots)


def find(roots, query, limit=100, cancelled=None):
    """Generátor zhôd (Hit). Skončí po `limit` zhodách, prehľadaní všetkého alebo zrušení."""
    needles = words(query)
    if not needles:
        return
    found = 0
    queue = deque(roots)
    while queue:
        if cancelled is not None and cancelled():
            return
        directory = queue.popleft()
        try:
            with os.scandir(directory) as it:
                entries = list(it)
        except OSError:
            continue                    # bez práva alebo zmizol: nie je čo hlásiť po jednom
        entries.sort(key=lambda e: e.name.lower())
        for entry in entries:
            if entry.name.startswith("."):
                continue
            try:
                is_dir = entry.is_dir(follow_symlinks=False)
            except OSError:
                is_dir = False
            name = fold(entry.name)
            if all(w in name for w in needles):
                yield Hit(entry.path, entry.name, is_dir)
                found += 1
                if found >= limit:
                    return
            if is_dir and entry.name not in SKIP_DIRS:
                queue.append(entry.path)


def display_path(volumes, path):
    """Cesta tak, ako ju ukazuje drobčeková navigácia správcu súborov: zväzok a cesta v ňom
    (Device1 › home › user › Dokumenty). Mimo zväzkov sa vráti cesta tak, ako je."""
    from latte_common import volumes as vol_mod

    found = vol_mod.locate(volumes, path)
    if found is None:
        return path
    volume, _root = found
    rest = path[len(volume.path.rstrip("/")):]
    return (volume.name + rest).replace("/", " › ")
