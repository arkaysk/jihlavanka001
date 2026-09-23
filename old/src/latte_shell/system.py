"""Akcie systémového manažéra: odhlásenie, vypnutie relácie a reštart (bod 2.5).

Odhlásenie a vypnutie končia reláciu, líšia sa tým, kam sa používateľ dostane:
- odhlásiť: labwc skončí čisto, latteos-session upratá a používateľ sa vráti na
  prihlasovaciu obrazovku (aj keď sa LatteOS spustil ručne z konzoly, ktorú otvoril greetd);
- vypnúť: relácia aj grafika skončia a ostane textová konzola servera
  (multi-user.target). Bez greetd (relácia spustená ručne z konzoly) je to to isté
  ako odhlásiť, lebo konzola je tam už teraz.
Tie dve spúšťa session/latteos-logout ako samostatnú user službu, lebo lišta skončí spolu
s reláciou a poradie krokov musí prežiť.
Reštart je jednoduché `systemctl reboot` (logind, bez hesla pre aktívnu lokálnu reláciu); ostatné
prihlásené účty logind zahlási sám, chyba sa ukáže v popupe.
"""
import os
import shutil
import subprocess
from dataclasses import dataclass

HELPER = "latteos-logout"
# Pravidlo, ktoré dovolí prepnúť do konzoly bez hesla (dáva ho tools/install-greeter.sh).
# Oprávnenie sa vopred nedá overiť (pkcheck s detailmi smie len root), preto sa kontroluje súbor.
CONSOLE_RULE = "/etc/polkit-1/rules.d/51-latteos-dev.rules"


@dataclass
class Action:
    id: str
    label: str
    hint: str
    confirm: bool = False       # prvý klik len vyžiada potvrdenie


ACTIONS = [
    Action("console", "Vypnúť", "relácia → konzola"),
    Action("reboot", "Reštartovať", "počítač", confirm=True),
    Action("logout", "Odhlásiť", "do prihlásenia"),
]


def greetd_active():
    try:
        return subprocess.run(
            ["systemctl", "is-active", "--quiet", "greetd"], timeout=5
        ).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def console_permitted(rule_file=None):
    return os.path.isfile(rule_file or CONSOLE_RULE)


def helper_path():
    """Nainštalovaný pomocník, inak ten z repozitára (vývoj)."""
    found = shutil.which(HELPER)
    if found:
        return found
    return os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "session", HELPER)
    )


def command(action_id, greetd=None):
    """Príkaz pre akciu. greetd=None znamená zistiť, či beží."""
    if action_id not in ("logout", "console", "reboot"):
        raise ValueError("neznáma akcia: %s" % action_id)
    if action_id == "reboot":
        return ["systemctl", "reboot"]
    if action_id == "console":
        if greetd is None:
            greetd = greetd_active()
    else:
        greetd = False
    argv = [
        # --unit: dvojklik nespustí pomocníka dvakrát; --setenv bez hodnoty odovzdá
        # aktuálnu hodnotu z lišty (manager ju po skončení relácie zabudne)
        "systemd-run", "--user", "--collect", "--quiet", "--no-block",
        "--unit=" + HELPER, "--setenv=LABWC_PID", "--setenv=XDG_SESSION_ID",
        helper_path(),
    ]
    if greetd:
        argv.append("--console")
    return argv


def unavailable_reason(argv, environ=None):
    """Prečo sa príkaz nedá spustiť (text pre používateľa), alebo None."""
    environ = os.environ if environ is None else environ
    if os.path.basename(argv[0]) == "systemd-run":
        if not environ.get("LABWC_PID"):
            # labwc --exit zisťuje bežiaci kompozitor z LABWC_PID; do user služieb ho
            # odovzdáva session/labwc/autostart, takže chýba len v relácii spustenej pred touto zmenou.
            return "chýba LABWC_PID, prihlás sa znova"
        if not os.access(argv[-1] if argv[-1] != "--console" else argv[-2], os.X_OK):
            return "chýba pomocník %s" % HELPER
    return None
