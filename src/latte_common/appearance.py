"""Vzhľad LatteOS: motívy, tokeny a ich preklad do jazyka jednotlivých vrstiev (docs/nastavenia.md).

Zdroj pravdy sú nastavenia domény „appearance“ (settings.py) a balík motívu data/themes/<id>/theme.toml.
Z nich vzniknú tokeny (resolve) a z tokenov výstupy pre vrstvy:

    vlastné komponenty  CSS premenné (css_variables)          – vynútené
    kompozitor          themerc-override pre labwc            – vynútené
    portál              org.freedesktop.appearance, ...       – vynútené (služba latte-appearance)
    GTK4 a libadwaita   gtk.css (spravovaný blok)             – zosúladené
    GTK 3 a 4           settings.ini (len naše kľúče)         – zosúladené

Modul nepozná GTK ani D-Bus: vracia text a hodnoty, zapisuje len súbory (apply), ktoré vie aj skontrolovať
(check). Tým sa dá celý preklad testovať bez obrazovky.
"""
import os
import re
import tomllib
from dataclasses import dataclass, field

from latte_common import paths, settings

DEFAULT_THEME = "latte"
DEFAULT_TITLEBAR = 46
ROLE_COLORS = ("fg", "fg-dim", "accent", "on-accent", "danger", "base", "terminal", "terminal-text", "corner-right")
TINT_KEYS = ("t1", "t2", "t3", "t4", "line-soft", "line", "outline", "outline-strong", "accent")
PANELS = ("bar", "side", "list", "detail", "popup", "segment", "tabs")
SHAPES = ("s", "m", "l", "xl", "xxl")
SCHEMES = ("dark", "light")
BUTTON_LAYOUT = {
    "all": ":minimize,maximize,close",
    "minimize-close": ":minimize,close",
    "close": ":close",
}
HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
DARK_TEXT, LIGHT_TEXT = "#1A1410", "#FFFFFF"        # text na vlastnej farbe zvýraznenia


class ThemeError(ValueError):
    """Motív je poškodený alebo neúplný."""


# ---------------------------------------------------------------- farby
def parse_hex(color):
    if not isinstance(color, str) or not HEX_RE.match(color):
        raise ThemeError("neplatná farba %r (očakáva sa #rrggbb)" % (color,))
    return tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))


def to_hex(rgb):
    return "#%02X%02X%02X" % tuple(max(0, min(255, round(c))) for c in rgb)


def luminance(rgb):
    def lin(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def readable_on(background, dark=DARK_TEXT, light=LIGHT_TEXT):
    """Text (tmavý alebo svetlý), ktorý je na danej farbe lepšie čitateľný."""
    bg = parse_hex(background)
    return dark if contrast(bg, parse_hex(dark)) >= contrast(bg, parse_hex(light)) else light


def mix(a, b, t):
    """a * (1 - t) + b * t, po zložkách."""
    return tuple(x * (1 - t) + y * t for x, y in zip(a, b))


def _num(value):
    return ("%.2f" % value).rstrip("0").rstrip(".") or "0"


def rgba(rgb, alpha):
    return "rgba(%d,%d,%d,%s)" % (*(round(c) for c in rgb), _num(alpha))


def hex8(rgb, alpha):
    """#rrggbbaa (formát farieb v témach labwc)."""
    return "%s%02X" % (to_hex(rgb), round(max(0.0, min(1.0, alpha)) * 255))


# ---------------------------------------------------------------- motívy
@dataclass
class Variant:
    colors: dict
    tint_base: tuple
    tint: dict
    panels: dict                # meno -> (r, g, b, alpha)


@dataclass
class Theme:
    id: str
    name: str
    description: str
    shape: dict                 # s, m, l, xl, xxl v pixeloch
    variants: dict              # "dark" / "light" -> Variant
    path: str = ""


def theme_dirs():
    data_home = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    return [os.path.join(paths.data_dir(), "themes"), os.path.join(data_home, "latteos", "themes")]


def parse_theme(data, source="<motív>", expect_id=None):
    def need(cond, why):
        if not cond:
            raise ThemeError("%s: %s" % (source, why))

    meta = data.get("theme")
    need(isinstance(meta, dict) and isinstance(meta.get("id"), str) and meta.get("name"), "chýba [theme] s id a name")
    need(re.match(r"^[a-z][a-z0-9-]*$", meta["id"]), "neplatné id motívu")
    need(expect_id is None or meta["id"] == expect_id, "id %r nesedí s adresárom %r" % (meta["id"], expect_id))
    shape = data.get("shape") or {}
    need(all(isinstance(shape.get(k), int) and shape[k] >= 0 for k in SHAPES), "[shape] musí mať celé čísla %s" % ", ".join(SHAPES))

    variants = {}
    for scheme in SCHEMES:
        section = data.get(scheme)
        if section is None:
            continue
        colors = section.get("colors") or {}
        need(all(k in colors for k in ROLE_COLORS), "[%s.colors] musí mať %s" % (scheme, ", ".join(ROLE_COLORS)))
        for role in ROLE_COLORS:
            parse_hex(colors[role])
        tint = section.get("tint") or {}
        need(all(k in tint for k in TINT_KEYS) and "base" in tint, "[%s.tint] musí mať base a %s" % (scheme, ", ".join(TINT_KEYS)))
        for k in TINT_KEYS:
            need(isinstance(tint[k], (int, float)) and 0 <= tint[k] <= 1, "[%s.tint] %s: očakáva sa 0 až 1" % (scheme, k))
        panels = {}
        for name in PANELS:
            raw = (section.get("panels") or {}).get(name)
            need(isinstance(raw, list) and len(raw) == 4 and all(isinstance(x, (int, float)) for x in raw)
                 and all(0 <= c <= 255 for c in raw[:3]) and 0 <= raw[3] <= 1,
                 "[%s.panels] %s: očakáva sa [r, g, b, priehľadnosť]" % (scheme, name))
            panels[name] = (raw[0], raw[1], raw[2], float(raw[3]))
        variants[scheme] = Variant(
            colors={k: colors[k].upper() for k in ROLE_COLORS}, tint_base=parse_hex(tint["base"]),
            tint={k: float(tint[k]) for k in TINT_KEYS}, panels=panels)
    need(variants, "motív nemá variant [dark] ani [light]")
    return Theme(id=meta["id"], name=meta["name"], description=meta.get("description", ""),
                 shape={k: shape[k] for k in SHAPES}, variants=variants, path=source)


def _read_theme(directory, theme_id):
    path = os.path.join(directory, theme_id, "theme.toml")
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
    except FileNotFoundError:
        return None
    except (OSError, tomllib.TOMLDecodeError) as err:
        raise ThemeError("%s: %s" % (path, err)) from None
    return parse_theme(data, path, expect_id=theme_id)


def load_theme(theme_id, directories=None):
    for directory in (directories if directories is not None else reversed(theme_dirs())):
        theme = _read_theme(directory, theme_id)
        if theme is not None:
            return theme
    raise ThemeError("motív %r sa nenašiel" % theme_id)


def list_themes(directories=None):
    """Nainštalované motívy; poškodené sa preskočia (chyba ide do zoznamu problémov)."""
    found, problems = {}, []
    for directory in (directories if directories is not None else theme_dirs()):
        try:
            names = sorted(os.listdir(directory))
        except OSError:
            continue
        for name in names:
            try:
                theme = _read_theme(directory, name)
            except ThemeError as err:
                problems.append(str(err))
                continue
            if theme is not None:
                found[theme.id] = theme         # používateľský motív prekryje systémový
    return list(found.values()), problems


# ---------------------------------------------------------------- tokeny
@dataclass
class Tokens:
    theme_id: str
    scheme: str                 # účinný režim: dark | light
    colors: dict                # rola -> #RRGGBB (po úprave akcentu a kontrastu)
    tint_base: tuple
    tint: dict
    panels: dict
    radii: dict                 # s, m, l, xl, xxl v px
    accent: str
    font_family: str
    font_scale: float
    buttons: str
    contrast: str
    transparency: bool
    corners: str
    titlebar: int = 46          # výška záhlavia okien v px (jeden parameter pre všetky vrstvy)
    problems: list = field(default_factory=list)
    variants: dict = field(default_factory=dict)    # režim -> Tokens tohto motívu (pre gtk.css s @media)

    @property
    def accent_rgb(self):
        return parse_hex(self.accent)


def _build(theme, scheme, values):
    """Tokeny motívu pre jeden režim s použitými voľbami (akcent, priehľadnosť, kontrast, rohy)."""
    variant = theme.variants[scheme]
    colors = dict(variant.colors)
    tint = dict(variant.tint)
    panels = dict(variant.panels)
    accent = values.get("color.accent") or colors["accent"]
    if accent != colors["accent"]:
        colors["accent"] = accent.upper()
        colors["on-accent"] = readable_on(accent, DARK_TEXT if scheme == "light" else variant.colors["on-accent"])
    if values.get("accessibility.contrast") == "high":
        colors["fg-dim"] = colors["fg"]
        for k in ("line-soft", "line", "outline", "outline-strong"):
            tint[k] = min(0.6, tint[k] * 2)
        tint["accent"] = max(tint["accent"], 0.5)
    if values.get("color.transparency") is False or values.get("accessibility.contrast") == "high":
        panels = {name: (r, g, b, 1.0) for name, (r, g, b, _a) in panels.items()}
    corners = values.get("shape.corners", "round")
    return Tokens(
        theme_id=theme.id, scheme=scheme, colors=colors, tint_base=variant.tint_base, tint=tint, panels=panels,
        radii={k: (0 if corners == "square" else v) for k, v in theme.shape.items()}, accent=colors["accent"],
        font_family=values.get("font.family", ""), font_scale=float(values.get("font.scale", 1.0)),
        buttons=values.get("window.buttons", "all"), contrast=values.get("accessibility.contrast", "normal"),
        transparency=values.get("color.transparency", True) is not False, corners=corners,
        titlebar=int(values.get("window.titlebar", DEFAULT_TITLEBAR)))


def resolve(values, directories=None):
    """Z hodnôt domény appearance (Store.values()) a motívu vyrobí tokeny. Nikdy nevyhodí chybu kvôli
    zlému motívu: použije predvolený a dôvod zapíše do Tokens.problems (bez tichej degradácie).
    Tokens.variants obsahuje tokeny všetkých režimov motívu (gtk.css ich prepína cez @media)."""
    problems = []
    wanted = values.get("theme.id", DEFAULT_THEME)
    try:
        theme = load_theme(wanted, directories)
    except ThemeError as err:
        problems.append("%s; použije sa %s" % (err, DEFAULT_THEME))
        theme = load_theme(DEFAULT_THEME, directories)

    scheme = values.get("color.scheme", "dark")
    if scheme not in theme.variants:
        other = next(iter(theme.variants))
        problems.append("motív %s nemá %s variant; použije sa %s" % (theme.id, scheme, other))
        scheme = other
    tokens = _build(theme, scheme, values)
    tokens.problems = problems
    tokens.variants = {name: (tokens if name == scheme else _build(theme, name, values)) for name in theme.variants}
    return tokens


def current_tokens(store=None, directories=None):
    """Tokeny podľa nastavení tohto používateľa (a problémy zo súboru nastavení)."""
    store = store or settings.Registry().store("appearance")
    tokens = resolve(store.values(), directories)
    tokens.problems = list(store.problems) + tokens.problems
    return tokens


# ---------------------------------------------------------------- vlastné komponenty
def latte_vars(t):
    """Premenné --latte-* pre latte.css (názvy sú historické: cream = text, caramel = akcent)."""
    c = t.colors
    out = {
        "--latte-cream": c["fg"], "--latte-cream-dim": c["fg-dim"], "--latte-caramel": c["accent"],
        "--latte-espresso": c["on-accent"], "--latte-danger": c["danger"], "--latte-night": c["base"],
        "--latte-terminal": c["terminal"], "--latte-terminal-text": c["terminal-text"],
        "--latte-corner-right": c["corner-right"],
    }
    for name in ("t1", "t2", "t3", "t4"):
        out["--latte-tint-%s" % name[1]] = rgba(t.tint_base, t.tint[name])
    for name in ("line-soft", "line", "outline", "outline-strong"):
        out["--latte-%s" % name] = rgba(t.tint_base, t.tint[name])
    out["--latte-accent-tint"] = rgba(t.accent_rgb, t.tint["accent"])
    for name, (r, g, b, a) in t.panels.items():
        out["--latte-panel-%s" % name] = rgba((r, g, b), a)
    for name, px in t.radii.items():
        out["--latte-radius-%s" % ("2xl" if name == "xxl" else name)] = "%dpx" % px
    out["--latte-titlebar-height"] = "%dpx" % t.titlebar
    return out


def css_variables(t):
    body = "\n".join("    %s: %s;" % (k, v) for k, v in latte_vars(t).items())
    return ":root {\n%s\n}\n" % body


# ---------------------------------------------------------------- GTK4 a libadwaita
def _adwaita_rows(t):
    c = t.colors
    fg = parse_hex(c["fg"])
    lst = t.panels["list"]
    popup = mix(t.panels["popup"][:3], fg, 0.06)
    accent_text = to_hex(mix(t.accent_rgb, fg, 0.15))
    return {
        "--accent-bg-color": c["accent"], "--accent-color": accent_text, "--accent-fg-color": c["on-accent"],
        "--window-bg-color": rgba(lst[:3], lst[3]), "--window-fg-color": c["fg"],
        "--view-bg-color": rgba(t.panels["detail"][:3], t.panels["detail"][3]), "--view-fg-color": c["fg"],
        "--headerbar-bg-color": rgba(t.panels["bar"][:3], t.panels["bar"][3]), "--headerbar-fg-color": c["fg"],
        "--headerbar-border-color": rgba(t.tint_base, t.tint["line"]),
        "--headerbar-backdrop-color": rgba(t.panels["side"][:3], max(t.panels["side"][3], 0.85)),
        "--headerbar-shade-color": "rgba(0,0,0,0.25)",
        "--sidebar-bg-color": rgba(t.panels["side"][:3], t.panels["side"][3]), "--sidebar-fg-color": c["fg"],
        "--sidebar-backdrop-color": rgba(t.panels["side"][:3], t.panels["side"][3]),
        "--card-bg-color": rgba(t.tint_base, t.tint["t1"]), "--card-fg-color": c["fg"],
        "--popover-bg-color": to_hex(popup), "--popover-fg-color": c["fg"],
        "--dialog-bg-color": to_hex(popup), "--dialog-fg-color": c["fg"],
    }


def _root_block(rows, indent=""):
    body = "\n".join("%s    %s: %s;" % (indent, k, v) for k, v in rows.items())
    return "%s:root {\n%s\n%s}\n" % (indent, body, indent)


def gtk4_css(t):
    """Farby libadwaita (od 1.6 sú to CSS premenné). Funkcie a ikony aplikácií ostávajú.

    gtk.css sa v bežiacej aplikácii nenačíta znova, preto obsahuje oba režimy a vyberá cez
    @media (prefers-color-scheme: dark), ktorý sa riadi portálom: prepnutie režimu sa prejaví hneď."""
    variants = t.variants or {t.scheme: t}
    controls = titlebar_css(t) + window_controls_css(t)
    if len(variants) == 1:
        return _root_block(_adwaita_rows(next(iter(variants.values())))) + controls
    base = variants.get("light") or next(iter(variants.values()))
    dark = variants.get("dark")
    return (_root_block(_adwaita_rows(base)) + "@media (prefers-color-scheme: dark) {\n"
            + _root_block(_adwaita_rows(dark), "  ") + "}\n" + controls)


def gtk_ini(t):
    """Kľúče settings.ini, ktoré LatteOS vlastní (hodnota None = kľúč odstrániť)."""
    return {
        "gtk-application-prefer-dark-theme": "true" if t.scheme == "dark" else "false",
        "gtk-decoration-layout": BUTTON_LAYOUT[t.buttons],
        "gtk-font-name": "%s 11" % t.font_family if t.font_family else None,
        "gtk-xft-dpi": str(round(96 * 1024 * t.font_scale)) if abs(t.font_scale - 1.0) > 1e-9 else None,
    }


# ---------------------------------------------------------------- kompozitor (labwc)
def labwc_theme(t):
    """themerc-override pre labwc: rámy okien bez vlastného pruhu, menu a prepínač okien."""
    c = t.colors
    fg, dim = parse_hex(c["fg"]), parse_hex(c["fg-dim"])
    tb = t.tint_base
    bar, popup = t.panels["bar"], t.panels["popup"]
    inactive_alpha = bar[3] * 0.85
    rows = [
        ("border.width", "1"), ("padding.width", "0"), ("window.titlebar.padding.height", str(max(0, (t.titlebar - BUTTON_HEIGHT) // 2))),
        ("window.active.border.color", hex8(tb, t.tint["outline"])),
        ("window.inactive.border.color", hex8(tb, t.tint["line-soft"])),
        ("window.active.title.bg.color", hex8(bar[:3], bar[3])),
        ("window.inactive.title.bg.color", hex8(bar[:3], inactive_alpha)),
        ("window.active.label.text.color", to_hex(fg)), ("window.inactive.label.text.color", to_hex(dim)),
        ("window.label.text.justify", "center"),
        ("window.button.width", str(BUTTON_WIDTH)), ("window.button.height", str(BUTTON_HEIGHT)),
        ("window.button.spacing", str(BUTTON_SPACING)),
        ("window.button.hover.bg.color", hex8(fg, BUTTON_HOVER)),
        ("window.button.hover.bg.corner-radius", str(t.radii["m"])),
        ("window.active.button.unpressed.image.color", to_hex(fg)),
        ("window.inactive.button.unpressed.image.color", to_hex(dim)),
        ("menu.border.width", "1"), ("menu.border.color", hex8(tb, t.tint["outline"])),
        ("menu.items.bg.color", hex8(popup[:3], popup[3])), ("menu.items.text.color", to_hex(fg)),
        ("menu.items.active.bg.color", hex8(t.accent_rgb, t.tint["accent"])), ("menu.items.active.text.color", to_hex(fg)),
        ("menu.separator.color", hex8(tb, t.tint["line"])),
        ("menu.title.bg.color", hex8(bar[:3], bar[3])), ("menu.title.text.color", to_hex(dim)),
        ("osd.bg.color", hex8(popup[:3], popup[3])), ("osd.border.color", hex8(tb, t.tint["outline"])),
        ("osd.border.width", "1"), ("osd.label.text.color", to_hex(fg)),
        ("osd.window-switcher.style-classic.item.active.bg.color", hex8(t.accent_rgb, t.tint["accent"])),
        ("osd.window-switcher.style-thumbnail.item.active.bg.color", hex8(t.accent_rgb, t.tint["accent"])),
    ]
    head = "# GENEROVANÉ latte-appearance (motív %s, %s). Ručné zmeny sa prepíšu; nastavuje sa v Nastaveniach." % (
        t.theme_id, t.scheme)
    return head + "\n" + "\n".join("%s: %s" % row for row in rows) + "\n"


# ---------------------------------------------------------------- tlačidlá okien
# Jeden vzhľad tlačidiel minimalizovať/maximalizovať/zavrieť pre všetky okná: v GTK4 a libadwaite ho robí CSS,
# v rámoch, ktoré kreslí labwc, ikony SVG (rovnaké tvary ako symbolické ikony Adwaita) a hover z themerc.
# Rozmer 30x24, medzera 4 a hover so zaoblením "m" sú spoločné pre obe cesty.
LABWC_THEME = "LatteOS"
BUTTON_WIDTH, BUTTON_HEIGHT, BUTTON_SPACING = 30, 24, 4
BUTTON_HOVER, BUTTON_PRESS = 0.12, 0.2      # sila podkladu z farby textu; rovnaká v každom režime a vrstve
GLYPHS = {                      # cesty z Adwaita window-*-symbolic.svg, plátno 16x16
    "close": "m 4 4 h 1 h 0.03125 c 0.253906 0.011719 0.511719 0.128906 0.6875 0.3125 l 2.28125 2.28125 l 2.3125 -2.28125 "
             "c 0.265625 -0.230469 0.445312 -0.304688 0.6875 -0.3125 h 1 v 1 c 0 0.285156 -0.035156 0.550781 -0.25 0.75 "
             "l -2.28125 2.28125 l 2.25 2.25 c 0.1875 0.1875 0.28125 0.453125 0.28125 0.71875 v 1 h -1 "
             "c -0.265625 0 -0.53125 -0.09375 -0.71875 -0.28125 l -2.28125 -2.28125 l -2.28125 2.28125 "
             "c -0.1875 0.1875 -0.453125 0.28125 -0.71875 0.28125 h -1 v -1 c 0 -0.265625 0.09375 -0.53125 0.28125 -0.71875 "
             "l 2.28125 -2.25 l -2.28125 -2.28125 c -0.210938 -0.195312 -0.304688 -0.46875 -0.28125 -0.75 z m 0 0",
    "iconify": "m 4 10.007812 h 8 v 1.988282 h -8 z m 0 0",
    "max": "m 3.988281 3.992188 v 8.011718 h 8.011719 v -8.011718 z m 2 2 h 4.011719 v 4.011718 h -4.011719 z m 0 0",
    "max_toggled": "m 4.988281 4.992188 v 6.011718 h 6.011719 v -6.011718 z m 2 2 h 2.011719 v 2.011718 h -2.011719 z m 0 0",
}
BUTTON_KINDS = ("close", "iconify", "max", "max_toggled")


def window_controls_css(t):
    """Tlačidlá okien pre GTK4 a libadwaitu: bez kruhu, plochý symbol, pri prejdení myšou zaoblený podklad.

    Podklad je farba textu hlavičky (currentColor), preto CSS nezávisí od režimu a gtk.css sa pri jeho prepnutí nemení."""
    def shade(strength):
        return "color-mix(in srgb, currentColor %d%%, transparent)" % round(strength * 100)

    # libadwaita kreslí kruh na obrázku vnútri tlačidla (windowcontrols > button > image), preto ho treba zrušiť tam
    return """windowcontrols {
    border-spacing: 0;
}
windowcontrols > button {
    min-width: %(w)dpx;
    min-height: %(h)dpx;
    margin: 0 %(gap)dpx;
    padding: 0;
    border-radius: %(radius)dpx;
    background: none;
    box-shadow: none;
    -gtk-icon-shadow: none;
}
windowcontrols > button > image {
    background: none;
    box-shadow: none;
    padding: 0;
    border-radius: 0;
}
windowcontrols > button:hover {
    background: %(hover)s;
}
windowcontrols > button:active {
    background: %(press)s;
}
""" % {"w": BUTTON_WIDTH, "h": BUTTON_HEIGHT, "gap": BUTTON_SPACING // 2, "radius": t.radii["m"],
       "hover": shade(BUTTON_HOVER), "press": shade(BUTTON_PRESS)}


# Hlavička v libadwaita aplikáciách: samotný headerbar má presne min-height (zmerané na AdwToolbarView + AdwHeaderBar).
# Keď je v hornej lište aj ďalší prvok so zbaleným odstupom (.collapse-spacing, napr. lišta kariet v Textovom editore),
# pribudne pod headerbar okolo 5 px, ktoré sa odpočítajú. Pod 46 px sa nedá zísť: tlačidlá záhlavia majú 34 px a výplň 12 px.
COLLAPSED_SPACING_EXTRA = 5
MIN_TITLEBAR = 46


def titlebar_css(t):
    """Výška záhlavia každého headerbaru (aj plochého v obsahu libadwaita aplikácií): jeden parameter pre všetky okná.

    Rám od labwc má rovnakú výšku z themerc (window.titlebar.padding.height + výška tlačidla). Vlastné komponenty
    LatteOS majú na hlavičke triedu latte-titlebar: výšku im dáva latte.css (gtk.css má vyššiu prioritu než téma
    aplikácie, bez tohto vylúčenia by im vnútil hodnotu určenú pre libadwaitu)."""
    height = max(t.titlebar, MIN_TITLEBAR)
    return ("headerbar:not(.latte-titlebar) {\n    min-height: %dpx;\n}\n"
            "toolbarview > .top-bar .collapse-spacing headerbar:not(.latte-titlebar) {\n    min-height: %dpx;\n}\n"
            % (height, height - COLLAPSED_SPACING_EXTRA))


def labwc_buttons(t):
    """{názov súboru: SVG} ikon tlačidiel rámu okna pre tému labwc LatteOS (aktívne aj neaktívne okno)."""
    out = {}
    for state, color in (("active", t.colors["fg"]), ("inactive", t.colors["fg-dim"])):
        for kind in BUTTON_KINDS:
            out["%s-%s.svg" % (kind, state)] = (
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="-7 -4 %d %d">\n'
                '  <path d="%s" fill="%s"/>\n</svg>\n' % (BUTTON_WIDTH, BUTTON_HEIGHT, BUTTON_WIDTH, BUTTON_HEIGHT,
                                                          GLYPHS[kind], color))
    return out


# ---------------------------------------------------------------- portál
def portal_values(t):
    """Hodnoty pre org.freedesktop.impl.portal.Settings: {menný priestor: {kľúč: (signatúra, hodnota)}}."""
    r, g, b = (x / 255 for x in t.accent_rgb)
    interface = {
        "color-scheme": ("s", "prefer-dark" if t.scheme == "dark" else "prefer-light"),
        "text-scaling-factor": ("d", t.font_scale),
    }
    if t.font_family:
        interface["font-name"] = ("s", "%s 11" % t.font_family)
    return {
        "org.freedesktop.appearance": {
            "color-scheme": ("u", 1 if t.scheme == "dark" else 2),
            "accent-color": ("(ddd)", (r, g, b)),
            "contrast": ("u", 1 if t.contrast == "high" else 0),
        },
        "org.gnome.desktop.interface": interface,
        "org.gnome.desktop.wm.preferences": {"button-layout": ("s", BUTTON_LAYOUT[t.buttons])},
    }


# ---------------------------------------------------------------- spravované súbory
BLOCK_BEGIN = "/* >>> LatteOS: spravuje latte-appearance, zmeny v tomto bloku sa prepíšu */"
BLOCK_END = "/* <<< LatteOS */"


def find_block(text):
    """Text spravovaného bloku (bez značiek) alebo None."""
    m = re.search(re.escape(BLOCK_BEGIN) + r"\n(.*?)" + re.escape(BLOCK_END), text, re.S)
    return m.group(1) if m else None


def strip_block(text):
    out = re.sub(r"\n?" + re.escape(BLOCK_BEGIN) + r"\n.*?" + re.escape(BLOCK_END) + r"\n?", "\n", text, flags=re.S)
    return out.strip("\n") + "\n" if out.strip() else ""


def merge_block(text, block):
    """Vloží (alebo nahradí) spravovaný blok; zvyšok súboru používateľa nechá bez zmeny."""
    rest = strip_block(text)
    return (rest + "\n" if rest else "") + "%s\n%s%s\n" % (BLOCK_BEGIN, block, BLOCK_END)


def parse_ini(text):
    """{oddiel: {kľúč: hodnota}} pre jednoduchý ini súbor (komentáre a prázdne riadky sa preskočia)."""
    data, section = {}, None
    for line in text.splitlines():
        line = line.strip()
        if not line or line[0] in "#;":
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1]
            data.setdefault(section, {})
        elif "=" in line and section is not None:
            key, value = line.split("=", 1)
            data[section][key.strip()] = value.strip()
    return data


def merge_ini(text, values, section="Settings"):
    """Nastaví len uvedené kľúče v [section]; ostatné riadky a komentáre ostanú. None kľúč odstráni."""
    lines = text.splitlines()
    start = end = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == "[%s]" % section:
            start = i
        elif start is not None and end is None and stripped.startswith("[") and stripped.endswith("]"):
            end = i
    if start is None:
        lines += ([""] if lines and lines[-1].strip() else []) + ["[%s]" % section]
        start, end = len(lines) - 1, len(lines)
    elif end is None:
        end = len(lines)

    body = lines[start + 1:end]
    for key, value in values.items():
        pattern = re.compile(r"^\s*%s\s*=" % re.escape(key))
        idx = next((i for i, l in enumerate(body) if pattern.match(l)), None)
        if value is None:
            if idx is not None:
                del body[idx]
        elif idx is not None:
            body[idx] = "%s=%s" % (key, value)
        else:
            last = max((i for i, l in enumerate(body) if l.strip()), default=-1)
            body.insert(last + 1, "%s=%s" % (key, value))
    lines[start + 1:end] = body
    return "\n".join(lines).rstrip("\n") + "\n"


# ---------------------------------------------------------------- plán a vynucovanie
@dataclass
class Dirs:
    config_home: str
    labwc: str
    data_home: str = None       # tu leží téma labwc s ikonami tlačidiel okien (data_home/themes/LatteOS/labwc)

    def __post_init__(self):
        if self.data_home is None:
            self.data_home = os.path.join(os.path.dirname(os.path.normpath(self.config_home)), "data")

    @property
    def labwc_theme(self):
        return os.path.join(self.data_home, "themes", LABWC_THEME, "labwc")

    @classmethod
    def default(cls):
        home = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
        data = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
        return cls(config_home=home, labwc=os.path.join(home, "labwc"), data_home=data)


@dataclass
class Action:
    adapter: str
    path: str
    kind: str                   # block | ini | file
    payload: object             # text bloku | {kľúč: hodnota} | celý text súboru

    def expected(self, current):
        """Obsah súboru po použití tejto akcie na súčasný obsah."""
        if self.kind == "block":
            return merge_block(current, self.payload)
        if self.kind == "ini":
            return merge_ini(current, self.payload)
        return self.payload


@dataclass
class Adapter:
    name: str
    level: str                  # enforced | aligned | recommended | planned
    title: str
    covers: str


ADAPTERS = [
    Adapter("latte", "enforced", "Vlastné komponenty", "lišta, správca súborov, prihlásenie, dialógy"),
    Adapter("compositor", "enforced", "Kompozitor (labwc)", "rámy okien bez vlastného pruhu, menu, prepínač okien"),
    Adapter("portal", "enforced", "Portál", "farebný režim, akcent, kontrast, písmo, tlačidlá okien: GTK4, libadwaita, Flatpak"),
    Adapter("gtk4", "aligned", "GTK4 a libadwaita", "farby cez gtk.css"),
    Adapter("gtk-settings", "aligned", "GTK 3 a 4", "settings.ini: tmavý režim, písmo, tlačidlá okien"),
    Adapter("gtk3", "planned", "GTK 3", "farby cez gtk.css (bez libadwaita premenných)"),
    Adapter("qt", "planned", "Qt", "platformová téma a farebná paleta"),
    Adapter("firefox", "planned", "Firefox", "politiky a motív"),
    Adapter("chromium", "planned", "Chromium a Electron", "príznaky a farebný režim z portálu"),
    Adapter("wine", "planned", "Wine", "farby v registri"),
]


def plan(t, dirs=None):
    dirs = dirs or Dirs.default()
    ini = gtk_ini(t)
    return [
        Action("gtk4", os.path.join(dirs.config_home, "gtk-4.0", "gtk.css"), "block", gtk4_css(t)),
        Action("gtk-settings", os.path.join(dirs.config_home, "gtk-4.0", "settings.ini"), "ini", ini),
        Action("gtk-settings", os.path.join(dirs.config_home, "gtk-3.0", "settings.ini"), "ini", ini),
        Action("compositor", os.path.join(dirs.labwc, "themerc-override"), "file", labwc_theme(t)),
        Action("compositor", os.path.join(dirs.labwc_theme, "themerc"), "file",
               "# Téma LatteOS: farby sú v themerc-override, tu sú len ikony tlačidiel (generuje latte-appearance).\n"),
    ] + [Action("compositor", os.path.join(dirs.labwc_theme, name), "file", svg)
         for name, svg in sorted(labwc_buttons(t).items())]


def _read(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def check(actions):
    """[(adapter, cesta, stav)]: ok = súbor zodpovedá nastaveniam, missing = chýba, drift = niekto ho zmenil."""
    out = []
    for action in actions:
        current = _read(action.path)
        if not os.path.exists(action.path):
            state = "missing"
        elif action.expected(current) == current:
            state = "ok"
        else:
            state = "drift"
        out.append((action.adapter, action.path, state))
    return out


def apply(actions):
    """Zapíše, čo sa líši; vráti zoznam zmenených ciest. Zápis je atomický (premenovanie) a idempotentný."""
    changed = []
    for action in actions:
        current = _read(action.path)
        wanted = action.expected(current)
        if os.path.exists(action.path) and wanted == current:
            continue
        directory = os.path.dirname(action.path)            # môže byť symlink (napr. ~/.config/labwc)
        os.makedirs(directory, exist_ok=True)
        tmp = os.path.join(directory, "." + os.path.basename(action.path) + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(wanted)
        os.replace(tmp, action.path)
        changed.append(action.path)
    return changed


def _ini_empty(text):
    """Súbor už neobsahuje nič okrem prázdnych riadkov a hlavičiek oddielov."""
    return all(not l.strip() or (l.strip().startswith("[") and l.strip().endswith("]")) for l in text.splitlines())


def release(actions):
    """Odstráni všetko, čo LatteOS spravuje (bloky, kľúče settings.ini, generované súbory). Vráti zmenené cesty."""
    changed = []
    for action in actions:
        if not os.path.exists(action.path):
            continue
        current = _read(action.path)
        if action.kind == "block":
            new = strip_block(current)
        elif action.kind == "ini":
            new = merge_ini(current, {k: None for k in action.payload})
        else:
            new = None
        if new is None:
            os.unlink(action.path)
        elif new == current:
            continue
        elif not new.strip() or (action.kind == "ini" and _ini_empty(new)):
            os.unlink(action.path)
        else:
            with open(action.path, "w", encoding="utf-8") as f:
                f.write(new)
        changed.append(action.path)
    return changed
