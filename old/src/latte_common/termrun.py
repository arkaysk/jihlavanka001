"""Príkazy Linuxu z promptu v lište (režim Terminál).

Príkaz beží v `bash -c` bez vstupu, s výstupom do popupu. Po skončení sa zistí aktuálny
priečinok, takže `cd` platí aj pre ďalší príkaz (premenné a aliasy nie). Programy, čo
potrebujú skutočný terminál (vim, top, ssh, sudo...), sa otvoria v okne `foot`.
"""
import os
import re
import shlex
import shutil

# Znamená: spusti ho ako bash -c, vypíš stav priečinka do súboru $2.
_WRAPPER = 'eval "$1"\nrc=$?\npwd >"$2" 2>/dev/null\nexit $rc'
_TERMINAL_WRAPPER = (
    'eval "$1"\nrc=$?\n'
    'if [ $rc -ne 0 ]; then printf "\\n[kód %s] Enter zatvorí okno" "$rc"; read -r _; fi\nexit $rc'
)

_ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)|\x1b[@-Z\\-_]")

TTY_PROGRAMS = {
    "vim", "vi", "nvim", "nano", "emacs", "micro", "less", "more", "man", "top", "htop", "btop",
    "atop", "nmtui", "mc", "ranger", "tmux", "screen", "ssh", "sftp", "telnet", "sudo", "su",
    "passwd", "python", "python3", "ipython", "node", "irb", "lua", "mysql", "psql", "sqlite3",
    "watch",
}
# Interpretery a klienty: bez argumentov je to interaktívny prompt, s argumentom (skript,
# -c, dotaz) bežia normálne.
_TTY_ONLY_WITHOUT_ARGS = {"python", "python3", "node", "irb", "lua", "mysql", "psql", "sqlite3"}


def strip_ansi(text):
    return _ANSI.sub("", text).replace("\r\n", "\n").replace("\r", "\n")


def first_program(command):
    """Prvý príkaz riadku bez priradení premenných (A=1 príkaz)."""
    try:
        parts = shlex.split(command, comments=False, posix=True)
    except ValueError:
        parts = command.split()
    while parts and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", parts[0]):
        parts = parts[1:]
    if not parts:
        return "", []
    return os.path.basename(parts[0]), parts[1:]


def needs_terminal(command):
    """Potrebuje príkaz skutočný terminál (TUI, heslo, interaktívny prompt)?"""
    program, args = first_program(command)
    if program not in TTY_PROGRAMS:
        return False
    if program in _TTY_ONLY_WITHOUT_ARGS:
        return not args
    return True


def argv(command, cwd_file):
    return ["setsid", "bash", "-c", _WRAPPER, "latte", command, cwd_file]


def environment(base=None):
    env = dict(base if base is not None else os.environ)
    # LD_PRELOAD s gtk4-layer-shell patrí len lište (tools/run-shell.sh), príkazy ho dediť nemajú
    preload = [p for p in env.get("LD_PRELOAD", "").split() if "gtk4-layer-shell" not in p]
    if preload:
        env["LD_PRELOAD"] = " ".join(preload)
    else:
        env.pop("LD_PRELOAD", None)
    env.update({"TERM": "dumb", "NO_COLOR": "1", "PAGER": "cat", "GIT_PAGER": "cat",
                "SYSTEMD_PAGER": "", "MANPAGER": "cat"})
    return env


def terminal_argv(command, cwd):
    """Príkaz v okne foot, alebo None, ak foot nie je nainštalovaný."""
    if shutil.which("foot") is None:
        return None
    return ["foot", "--working-directory", cwd, "bash", "-c", _TERMINAL_WRAPPER, "latte", command]


def pretty_cwd(cwd, home=None):
    home = home or os.path.expanduser("~")
    if cwd == home:
        return "~"
    if cwd.startswith(home.rstrip("/") + "/"):
        return "~" + cwd[len(home):]
    return cwd
