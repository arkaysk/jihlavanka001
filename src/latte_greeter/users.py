"""Zoznam používateľov pre prihlasovaciu obrazovku.

Greeter beží ako používateľ greetd a domovské adresáre nevidí, preto sa fotka
berie z /var/lib/AccountsService/icons (kam ju dáva Nastavenie používateľov)
a inak sa ukážu iniciálky.
"""
import os
import pwd
from dataclasses import dataclass

MIN_UID = 1000
MAX_UID = 60000
ICONS_DIR = "/var/lib/AccountsService/icons"
NOT_LOGIN_SHELLS = ("nologin", "false", "sync", "halt", "shutdown")


@dataclass
class User:
    name: str
    real_name: str
    uid: int
    avatar: str = None

    @property
    def title(self):
        return self.real_name or self.name


def _can_login(entry):
    return (
        MIN_UID <= entry.pw_uid < MAX_UID
        and os.path.basename(entry.pw_shell) not in NOT_LOGIN_SHELLS
        and entry.pw_name != "nobody"
    )


def list_users(recent=(), entries=None, icons_dir=ICONS_DIR):
    """Používatelia, ktorí sa môžu prihlásiť: naposledy prihlásení hore, ostatní abecedne."""
    users = []
    for entry in entries if entries is not None else pwd.getpwall():
        if not _can_login(entry):
            continue
        icon = os.path.join(icons_dir, entry.pw_name)
        users.append(
            User(
                name=entry.pw_name,
                real_name=entry.pw_gecos.split(",")[0].strip(),
                uid=entry.pw_uid,
                avatar=icon if os.access(icon, os.R_OK) and os.path.isfile(icon) else None,
            )
        )
    rank = {name: i for i, name in enumerate(recent)}
    users.sort(key=lambda u: (rank.get(u.name, len(rank)), u.title.lower()))
    return users
