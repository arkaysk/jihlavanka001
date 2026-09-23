"""Miesta v súkromnom priestore používateľa: Kôš ako zložka v domovskom priestore.

Kôš podľa špecifikácie freedesktop leží v ~/.local/share/Trash/files (a metadáta v .../info). Technická
cesta sa používateľovi neukazuje: v Správcovi súborov je Kôš zložka „Kôš“ v jeho súkromnom priestore
(System › home › meno › Kôš). Skutočné umiestnenie sa nemení, aby s ním fungovali aj ostatné aplikácie
a `Gio.File.trash`. Každý používateľ má svoj Kôš vo svojom domove (0700), takže ho iný účet nevidí.
"""
import os

TRASH_NAME = "Kôš"


def home():
    return os.path.expanduser("~")


def data_home():
    return os.environ.get("XDG_DATA_HOME") or os.path.join(home(), ".local", "share")


def trash_root():
    return os.path.join(data_home(), "Trash")


def trash_files():
    """Zložka, v ktorej sú vyhodené súbory; toto je „Kôš“, ktorý vidí používateľ."""
    return os.path.join(trash_root(), "files")


def ensure_trash():
    """Vytvorí Kôš používateľa (files a info, mód 0700), ak ešte nie je. Vráti None, alebo text chyby."""
    try:
        for sub in ("files", "info"):
            os.makedirs(os.path.join(trash_root(), sub), mode=0o700, exist_ok=True)
        os.chmod(trash_root(), 0o700)
    except OSError as err:
        return "Kôš sa nepodarilo pripraviť: %s" % (err.strerror or err)
    return None


def count_trashed(path=None):
    try:
        return len(os.listdir(path or trash_files()))
    except OSError:
        return 0


def in_trash(path):
    base = trash_files()
    return path == base or path.startswith(base + os.sep)


def parts(base, path):
    """[(názov, skutočná cesta)] od `base` (bez neho) po `path`.

    Technická cesta ku Košu (.local/share/Trash/files) sa zloží do jednej zložky „Kôš“.
    """
    rel = os.path.relpath(path, base)
    if rel == ".":
        return []
    out, current = [], base
    for part in rel.split(os.sep):
        current = os.path.join(current, part)
        out.append((part, current))
    trash = trash_files()
    if not in_trash(path) or not (trash == base or trash.startswith(home() + os.sep)):
        return out
    chain, current = [], home()
    for part in os.path.relpath(trash, home()).split(os.sep):
        current = os.path.join(current, part)
        chain.append(current)
    for i in range(len(out) - len(chain) + 1):
        if [real for _n, real in out[i:i + len(chain)]] == chain:
            out[i:i + len(chain)] = [(TRASH_NAME, trash)]
            break
    return out


def title(path):
    """Názov zobrazenej zložky (v záhlaví okna)."""
    if path == trash_files():
        return TRASH_NAME
    return os.path.basename(path) or path


def parent(path):
    """Nadradená zložka pre „..“: z Koša do domova (Kôš je zložka v ňom), inak obyčajne o úroveň vyššie."""
    if path == trash_files():
        return home()
    return os.path.dirname(path)
