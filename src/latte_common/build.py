"""Označenie zostavy: dev build alebo vydanie."""
import os

NAME = "LatteOS 0.1 Jihlavanka"
# Ak tento súbor existuje, ide o vydanie. Bez neho je to dev build, v ktorom sú
# navyše vývojové voľby (vypnutie relácie do konzoly, konzola v prihlasovaní).
RELEASE_MARKER = "/etc/latteos/release"


def is_dev():
    return not os.path.exists(RELEASE_MARKER)


def label():
    return "DEV" if is_dev() else "RELEASE"
