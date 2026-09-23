"""Malý prevod markdownu z odpovede AI na značky Pango (Gtk.Label s use_markup).

Zvláda len to, čo modely bežne píšu: bloky kódu, `kód`, **tučné**, nadpisy a odrážky.
Nedokončený zápis (odpoveď sa ešte píše) ostane doslovný, značky nikdy nevyjdú nevyvážené.
"""
import re
from html import escape

_BOLD = re.compile(r"\*\*(.+?)\*\*")
_HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(.*)$")
_BULLET = re.compile(r"^(\s*)[-*+]\s+(.*)$")


def _inline(line):
    parts = line.split("`")
    if len(parts) % 2 == 0:             # nepárny počet ` : posledný je nedokončený
        parts[-2:] = ["`".join(parts[-2:])]
    out = []
    for i, part in enumerate(parts):
        text = escape(part, quote=False)
        if i % 2:
            out.append("<tt>%s</tt>" % text)
        else:
            out.append(_BOLD.sub(r"<b>\1</b>", text))
    return "".join(out)


def to_pango(text):
    out = []
    in_code = False
    for line in text.split("\n"):
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            out.append("<tt>%s</tt>" % escape(line, quote=False))
            continue
        heading = _HEADING.match(line)
        if heading:
            out.append("<b>%s</b>" % _inline(heading.group(1)))
            continue
        bullet = _BULLET.match(line)
        if bullet:
            out.append("%s• %s" % (bullet.group(1), _inline(bullet.group(2))))
            continue
        out.append(_inline(line))
    return "\n".join(out)
