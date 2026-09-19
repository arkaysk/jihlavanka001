"""Čo si greeter pamätá medzi štartmi: kto sa prihlásil naposledy a do akej relácie.

Ukladá sa do domovského adresára používateľa greetd (/var/lib/greetd).
"""
import json
import os
import sys

MAX_RECENT = 6


def state_file():
    return os.environ.get("LATTEOS_GREETER_STATE") or os.path.expanduser(
        "~/.local/state/latteos/greeter.json"
    )


class State:
    def __init__(self):
        self.recent = []            # mená, naposledy prihlásený prvý
        self.sessions = {}          # meno -> názov relácie

    @classmethod
    def load(cls):
        state = cls()
        try:
            with open(state_file(), encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            return state
        except (OSError, ValueError) as err:
            print("latte-greeter: stav sa nedá prečítať: %s" % err, file=sys.stderr)
            return state
        if isinstance(data, dict):
            recent = data.get("recent")
            if isinstance(recent, list):
                state.recent = [n for n in recent if isinstance(n, str)][:MAX_RECENT]
            sessions = data.get("sessions")
            if isinstance(sessions, dict):
                state.sessions = {
                    k: v for k, v in sessions.items() if isinstance(k, str) and isinstance(v, str)
                }
        return state

    @property
    def last_user(self):
        return self.recent[0] if self.recent else None

    def record_login(self, username, session_name):
        self.recent = ([username] + [n for n in self.recent if n != username])[:MAX_RECENT]
        self.sessions[username] = session_name
        self.save()

    def save(self):
        path = state_file()
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            tmp = path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump({"recent": self.recent, "sessions": self.sessions}, f, ensure_ascii=False)
            os.replace(tmp, path)
        except OSError as err:
            # bez uloženia sa len nezapamätá poradie; prihlásenie to nesmie zrušiť
            print("latte-greeter: stav sa nedá uložiť: %s" % err, file=sys.stderr)
