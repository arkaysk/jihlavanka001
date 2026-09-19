"""Tapeta LatteOS: systémová a používateľská.

Systémová tapeta patrí k téme (data/wallpapers/, po inštalácii
/usr/local/share/latteos/wallpapers/). Používa ju prihlasovacia obrazovka,
ktorá domovské adresáre nevidí, a plocha, kým si používateľ nevyberie vlastnú.

Používateľská tapeta je súbor v priestore používateľa. Cestu k nej drží
~/.config/latteos/appearance.toml; zapisujú ju Nastavenia systému, dovtedy
príkaz latte-wallpaper. Plocha berie používateľskú tapetu a ak chýba alebo sa
nedá prečítať, systémovú.
"""
import json
import os
import sys
import tomllib

from latte_common import paths
from latte_common.volumes import CONFIG_DIR

SYSTEM_DEFAULT = "latteos-wallpaper1.jpg"
FITS = ("cover", "contain", "fill")


def appearance_file():
    return os.path.join(CONFIG_DIR, "appearance.toml")


def system_path():
    return os.path.join(paths.data_dir(), "wallpapers", SYSTEM_DEFAULT)


def load_appearance():
    """Nastavenie vzhľadu používateľa: {"wallpaper": cesta alebo None, "fit": ...}."""
    result = {"wallpaper": None, "fit": "cover"}
    try:
        with open(appearance_file(), "rb") as f:
            data = tomllib.load(f)
    except FileNotFoundError:
        return result
    except (OSError, tomllib.TOMLDecodeError) as err:
        print("latte-wallpaper: %s sa nedá prečítať: %s" % (appearance_file(), err), file=sys.stderr)
        return result
    section = data.get("wallpaper")
    if isinstance(section, dict):
        path = section.get("path")
        if isinstance(path, str) and os.path.isabs(path):
            result["wallpaper"] = path
        if section.get("fit") in FITS:
            result["fit"] = section["fit"]
    return result


def save_appearance(wallpaper=None, fit="cover"):
    """Zapíše nastavenie; wallpaper=None vráti systémovú tapetu."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    lines = ["# Vzhľad LatteOS pre tohto používateľa", ""]
    if wallpaper:
        lines += [
            "[wallpaper]",
            "path = " + json.dumps(wallpaper, ensure_ascii=False),
            "fit = " + json.dumps(fit),
            "",
        ]
    tmp = appearance_file() + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    os.replace(tmp, appearance_file())


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
