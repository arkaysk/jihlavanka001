"""Tapeta LatteOS: systémová a používateľská.

Systémová tapeta patrí k téme (data/wallpapers/, po inštalácii
/usr/local/share/latteos/wallpapers/). Používa ju prihlasovacia obrazovka,
ktorá domovské adresáre nevidí, a plocha, kým si používateľ nevyberie vlastnú.

Používateľská tapeta je súbor v priestore používateľa. Cestu k nej drží
~/.config/latteos/appearance.toml; zapisujú ju Nastavenia systému, dovtedy
príkaz latte-wallpaper. Plocha berie používateľskú tapetu a ak chýba alebo sa
nedá prečítať, systémovú.
"""
import os
import sys

from latte_common import paths, settings
from latte_common.volumes import CONFIG_DIR

SYSTEM_DEFAULT = "latteos-wallpaper1.jpg"
FITS = ("cover", "contain", "fill")


def appearance_file():
    return os.path.join(CONFIG_DIR, "appearance.toml")


def system_path():
    return os.path.join(paths.data_dir(), "wallpapers", SYSTEM_DEFAULT)


def _store():
    """Doména „appearance“ (schéma data/settings/appearance.schema.toml) v adresári CONFIG_DIR."""
    return settings.Registry().store("appearance", directory=CONFIG_DIR)


def load_appearance():
    """Nastavenie pozadia: {"wallpaper": cesta alebo None, "fit": ...}. Neplatné hodnoty sa
    ignorujú (Store ich nahlási na stderr a použije predvolené)."""
    store = _store()
    return {"wallpaper": store.get("wallpaper.path") or None, "fit": store.get("wallpaper.fit")}


def save_appearance(wallpaper=None, fit="cover"):
    """Zapíše nastavenie; wallpaper=None vráti systémovú tapetu. Ostatné nastavenia vzhľadu
    (farby, motív, písmo) v súbore ostanú."""
    store = _store()
    if wallpaper:
        store.set_many({"wallpaper.path": wallpaper, "wallpaper.fit": fit})
    else:
        store.reset("wallpaper.path", "wallpaper.fit")


def user_path():
    """Tapeta používateľa, ak je nastavená a súbor sa dá čítať."""
    path = load_appearance()["wallpaper"]
    if path and os.path.isfile(path) and os.access(path, os.R_OK):
        return path
    return None


def desktop_path():
    """Tapeta plochy: používateľská, inak systémová."""
    return user_path() or system_path()


def desktop_fit():
    return load_appearance()["fit"]


def blurred_pixbuf(path):
    """Rozmazaná kópia tapety pre prihlasovanie (bez závislosti od PIL).

    Rozmazanie sa robí raz pri štarte a nie v CSS: filter blur() by na
    softvérovom vykresľovaní (GSK_RENDERER=cairo vo VirtualBoxe) brzdil.
    Obraz sa opakovane zmenšuje na polovicu a potom rovnako zväčšuje,
    čo dáva hladší výsledok než jeden veľký skok.
    """
    import gi
    gi.require_version("GdkPixbuf", "2.0")
    from gi.repository import GdkPixbuf

    interp = GdkPixbuf.InterpType.BILINEAR
    original = GdkPixbuf.Pixbuf.new_from_file(path)
    width, height = original.get_width(), original.get_height()
    small = original
    for _ in range(5):
        w, h = max(2, small.get_width() // 2), max(2, small.get_height() // 2)
        small = small.scale_simple(w, h, interp)
    big = small
    while big.get_width() < width:
        big = big.scale_simple(big.get_width() * 2, big.get_height() * 2, interp)
    return big.scale_simple(width, height, interp)


def _main(argv):
    usage = "použitie: latte-wallpaper set SÚBOR [cover|contain|fill] | reset | show"
    if not argv or argv[0] not in ("set", "reset", "show"):
        print(usage, file=sys.stderr)
        return 2
    if argv[0] == "show":
        print("systémová:   ", system_path())
        print("používateľská:", user_path() or "(nenastavená)")
        print("plocha:      ", desktop_path(), "(%s)" % desktop_fit())
        return 0
    if argv[0] == "reset":
        save_appearance(None)
        print("Tapeta plochy je opäť systémová.")
        return 0
    if len(argv) < 2 or (len(argv) > 2 and argv[2] not in FITS):
        print(usage, file=sys.stderr)
        return 2
    path = os.path.abspath(os.path.expanduser(argv[1]))
    import gi
    gi.require_version("GdkPixbuf", "2.0")
    from gi.repository import GdkPixbuf
    if not os.path.isfile(path) or GdkPixbuf.Pixbuf.get_file_info(path)[0] is None:
        print("latte-wallpaper: %s nie je obrázok" % path, file=sys.stderr)
        return 1
    save_appearance(path, argv[2] if len(argv) > 2 else "cover")
    print("Tapeta plochy:", path)
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
