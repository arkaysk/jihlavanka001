"""Klient protokolu greetd (JSON cez unixový socket $GREETD_SOCK).

Správa je 4 bajty dĺžky v poradí bajtov stroja a potom JSON. Beh prihlásenia
riadi LoginFlow: preloží odpovede greetd na jednoduché výsledky (Outcome),
takže rozhranie nemusí poznať protokol.
Volania blokujú (PAM pri zlom hesle chvíľu čaká), rozhranie ich preto
spúšťa vo vlákne.
"""
import json
import os
import socket
import struct
import threading
from dataclasses import dataclass, field


class GreetdError(Exception):
    pass


class Client:
    def __init__(self, path=None):
        self.path = path or os.environ.get("GREETD_SOCK")
        self.sock = None

    def _connect(self):
        if not self.path:
            raise GreetdError("GREETD_SOCK nie je nastavený: greeter nebeží pod greetd")
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            sock.connect(self.path)
        except OSError as err:
            sock.close()
            raise GreetdError("greetd sa nedá kontaktovať: %s" % err) from err
        self.sock = sock

    def close(self):
        if self.sock is not None:
            self.sock.close()
            self.sock = None

    def _read(self, count):
        data = b""
        while len(data) < count:
            chunk = self.sock.recv(count - len(data))
            if not chunk:
                raise GreetdError("greetd zavrel spojenie")
            data += chunk
        return data

    def request(self, message):
        if self.sock is None:
            self._connect()
        payload = json.dumps(message).encode()
        try:
            self.sock.sendall(struct.pack("=I", len(payload)) + payload)
            (length,) = struct.unpack("=I", self._read(4))
            if length > 1 << 20:
                raise GreetdError("neplatná odpoveď greetd")
            return json.loads(self._read(length))
        except (OSError, ValueError, GreetdError) as err:
            self.close()                # ďalšie volanie sa pripojí znova
            if isinstance(err, GreetdError):
                raise
            raise GreetdError("chyba komunikácie s greetd: %s" % err) from err


@dataclass
class Outcome:
    """Výsledok kroku prihlásenia.

    kind: "success" (overené), "prompt" (čaká odpoveď), "error".
    notes: informačné správy od PAM, ktoré prišli cestou (napr. "Účet vyprší").
    """
    kind: str
    text: str = ""
    secret: bool = True
    auth_error: bool = False
    notes: list = field(default_factory=list)


class LoginFlow:
    """Jedno prihlasovanie: begin -> (answer)* -> start. Volania sú serializované."""

    def __init__(self, client=None):
        self.client = client or Client()
        self.lock = threading.Lock()
        self.active = False           # v greetd je otvorená relácia, ktorú treba zrušiť

    def begin(self, username):
        with self.lock:
            self._cancel()
            self.active = True
            return self._outcome(self.client.request({"type": "create_session", "username": username}))

    def answer(self, text):
        with self.lock:
            return self._outcome(
                self.client.request({"type": "post_auth_message_response", "response": text})
            )

    def start(self, cmd, env=None):
        with self.lock:
            reply = self.client.request({"type": "start_session", "cmd": cmd, "env": env or []})
            if reply.get("type") == "success":
                self.active = False
                return Outcome("success")
            return self._error(reply)

    def cancel(self):
        with self.lock:
            self._cancel()

    def _cancel(self):
        if not self.active:
            return
        self.active = False
        try:
            self.client.request({"type": "cancel_session"})
        except GreetdError:
            pass

    def _error(self, reply):
        self._cancel()
        return Outcome(
            "error",
            reply.get("description", "Neznáma chyba"),
            auth_error=reply.get("error_type") == "auth_error",
        )

    def _outcome(self, reply):
        notes = []
        while reply.get("type") == "auth_message":
            kind = reply.get("auth_message_type")
            text = reply.get("auth_message", "")
            if kind in ("visible", "secret"):
                return Outcome("prompt", text, secret=kind == "secret", notes=notes)
            notes.append(text)          # info/error: len sa zobrazí, PAM čaká na potvrdenie
            reply = self.client.request({"type": "post_auth_message_response", "response": None})
        if reply.get("type") == "success":
            return Outcome("success", notes=notes)
        outcome = self._error(reply)
        outcome.notes = notes
        return outcome
