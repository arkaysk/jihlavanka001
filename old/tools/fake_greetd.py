#!/usr/bin/env python3
"""Simulovaný greetd na skúšanie latte-greeter bez inštalácie a bez reštartu.

    python3 tools/fake_greetd.py /cesta/k/socketu

Účty: "test" s heslom "kava", "guest" bez hesla; každé iné meno pri prihlásení zlyhá
po výzve na heslo (ako v PAM). Spustenú reláciu iba vypíše.
"""
import json
import os
import socket
import struct
import sys
import threading

ACCOUNTS = {"test": "kava", "guest": None}


def read_exact(conn, count):
    data = b""
    while len(data) < count:
        chunk = conn.recv(count - len(data))
        if not chunk:
            raise EOFError
        data += chunk
    return data


def send(conn, message):
    payload = json.dumps(message).encode()
    conn.sendall(struct.pack("=I", len(payload)) + payload)


class Session:
    def __init__(self):
        self.user = None
        self.authed = False
        self.wants_password = False


def handle(conn, log, delay=0.0):
    session = None
    try:
        while True:
            (length,) = struct.unpack("=I", read_exact(conn, 4))
            msg = json.loads(read_exact(conn, length))
            kind = msg.get("type")
            log.append(msg)
            if kind == "create_session":
                session = Session()
                session.user = msg["username"]
                if session.user in ACCOUNTS and ACCOUNTS[session.user] is None:
                    session.authed = True
                    send(conn, {"type": "success"})
                else:
                    session.wants_password = True
                    send(conn, {"type": "auth_message", "auth_message_type": "secret",
                                "auth_message": "Password: "})
            elif kind == "post_auth_message_response" and session and session.wants_password:
                session.wants_password = False
                if ACCOUNTS.get(session.user) == msg.get("response") and msg.get("response"):
                    session.authed = True
                    send(conn, {"type": "success"})
                else:
                    session = None
                    send(conn, {"type": "error", "error_type": "auth_error",
                                "description": "Authentication failed"})
            elif kind == "start_session" and session and session.authed:
                print("start_session:", msg["cmd"], flush=True)
                send(conn, {"type": "success"})
            elif kind == "cancel_session":
                session = None
                send(conn, {"type": "success"})
            else:
                send(conn, {"type": "error", "error_type": "error",
                            "description": "neočakávaná správa: %s" % kind})
    except (EOFError, OSError):
        pass
    finally:
        conn.close()


class FakeGreetd:
    """Server v samostatnom vlákne; log drží všetky prijaté správy (pre testy)."""

    def __init__(self, path):
        self.path = path
        self.log = []
        if os.path.exists(path):
            os.unlink(path)
        self.server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server.bind(path)
        self.server.listen(4)
        self.thread = threading.Thread(target=self.serve, daemon=True)
        self.thread.start()

    def serve(self):
        while True:
            try:
                conn, _ = self.server.accept()
            except OSError:
                return
            threading.Thread(target=handle, args=(conn, self.log), daemon=True).start()

    def close(self):
        self.server.close()
        if os.path.exists(self.path):
            os.unlink(self.path)


if __name__ == "__main__":
    fake = FakeGreetd(sys.argv[1])
    print("fake greetd na", sys.argv[1], "(test/kava, guest bez hesla)", flush=True)
    fake.thread.join()
