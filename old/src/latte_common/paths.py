"""Kde leží dátové súbory LatteOS (téma, tapety)."""
import os

# Sem ich kopíruje tools/install-greeter.sh. Prihlasovacia obrazovka beží ako
# používateľ greetd a domovské adresáre nevidí, preto nemôže čítať z repozitára.
SYSTEM_SHARE = "/usr/local/share/latteos"


def data_dir():
    """LATTEOS_DATA, inak data/ v repozitári (vývoj), inak SYSTEM_SHARE."""
    env = os.environ.get("LATTEOS_DATA")
    if env:
        return env
    repo = os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data")
    )
    if os.path.isdir(os.path.join(repo, "styles")):
        return repo
    return SYSTEM_SHARE
