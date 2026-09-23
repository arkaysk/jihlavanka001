"""Model oznámení (bod 2.7): čo sa ukazuje ako bublina a čo ostáva v zozname pod zvončekom.

Bez GTK a bez D-Bus, aby sa dal skúšať. Bublina po vypršaní zmizne, ale oznámenie ostane v
zozname, kým ho používateľ nezavrie (rovnako ako v bežných prostrediach). Dočasné (transient)
oznámenia v zozname nezostávajú. Režim Nerušiť bubliny nezobrazí, len ich uloží; kritické
oznámenia sa zobrazia vždy.
"""
import time
from dataclasses import dataclass, field

URGENCY_LOW, URGENCY_NORMAL, URGENCY_CRITICAL = 0, 1, 2
DEFAULT_TIMEOUT_MS = 6000
HISTORY_LIMIT = 50

# dôvody zatvorenia podľa špecifikácie org.freedesktop.Notifications
CLOSED_EXPIRED, CLOSED_DISMISSED, CLOSED_BY_CALL, CLOSED_UNDEFINED = 1, 2, 3, 4


@dataclass
class Notification:
    id: int
    app_name: str
    app_icon: str
    summary: str
    body: str
    actions: list                       # [(kľúč, text)]
    urgency: int = URGENCY_NORMAL
    timeout_ms: int = DEFAULT_TIMEOUT_MS  # 0 = neprestane sa ukazovať
    transient: bool = False
    time: float = field(default_factory=time.time)
    popup: bool = True                  # ukazuje sa ako bublina


class Center:
    """Zoznam oznámení. Zmeny hlásia funkcie on_popup(n), on_popup_close(id), on_closed(id, dôvod),
    on_action(id, kľúč); na zmenu zoznamu sa dá prihlásiť cez subscribe()."""

    def __init__(self):
        self.items = []
        self.next_id = 1
        self.dnd = False
        self.listeners = []
        self.on_popup = lambda n: None
        self.on_popup_close = lambda nid: None
        self.on_closed = lambda nid, reason: None
        self.on_action = lambda nid, key: None

    def subscribe(self, listener):
        self.listeners.append(listener)

    def unsubscribe(self, listener):
        if listener in self.listeners:
            self.listeners.remove(listener)

    def on_change(self):
        for listener in list(self.listeners):
            listener()

    # ---------- príjem ----------
    def notify(self, app_name, replaces_id, app_icon, summary, body, actions, hints, expire_timeout):
        pairs = list(zip(actions[0::2], actions[1::2]))         # kľúč, text, kľúč, text...
        urgency = hints.get("urgency", URGENCY_NORMAL)
        if not isinstance(urgency, int) or not 0 <= urgency <= 2:
            urgency = URGENCY_NORMAL
        if expire_timeout < 0:
            timeout = DEFAULT_TIMEOUT_MS
        else:
            timeout = expire_timeout
        if urgency == URGENCY_CRITICAL:
            timeout = 0                                         # kritické zmizne, až keď ho zavrie človek
        existing = self.find(replaces_id) if replaces_id else None
        if existing is not None:
            nid = existing.id
            self.items.remove(existing)
        else:
            nid = self.next_id
            self.next_id += 1
        note = Notification(nid, app_name, app_icon, summary, body, pairs, urgency, timeout,
                            bool(hints.get("transient", False)))
        note.popup = not self.dnd or urgency == URGENCY_CRITICAL
        self.items.insert(0, note)
        while len(self.items) > HISTORY_LIMIT:
            old = self.items.pop()
            self.on_popup_close(old.id)
            self.on_closed(old.id, CLOSED_UNDEFINED)
        if note.popup:
            self.on_popup(note)
        else:
            self.on_popup_close(nid)
        self.on_change()
        return nid

    def find(self, nid):
        return next((n for n in self.items if n.id == nid), None)

    # ---------- zatvorenie ----------
    def popup_expired(self, nid):
        """Bublina vypršala: zmizne, oznámenie ostane v zozname (dočasné sa zahodí)."""
        note = self.find(nid)
        if note is None or not note.popup:
            return
        note.popup = False
        self.on_popup_close(nid)
        if note.transient:
            self.items.remove(note)
        self.on_closed(nid, CLOSED_EXPIRED)
        self.on_change()

    def close(self, nid, reason=CLOSED_DISMISSED):
        """Odstráni oznámenie úplne (zavrel ho človek alebo aplikácia)."""
        note = self.find(nid)
        if note is None:
            return False
        self.items.remove(note)
        self.on_popup_close(nid)
        self.on_closed(nid, reason)
        self.on_change()
        return True

    def clear(self):
        for note in list(self.items):
            self.close(note.id)

    def invoke(self, nid, key):
        """Človek zvolil akciu: aplikácia sa dozvie a oznámenie sa zatvorí."""
        if self.find(nid) is None:
            return
        self.on_action(nid, key)
        self.close(nid)

    # ---------- Nerušiť ----------
    def set_dnd(self, on):
        self.dnd = bool(on)
        if self.dnd:
            for note in self.items:
                if note.popup and note.urgency != URGENCY_CRITICAL:
                    note.popup = False
                    self.on_popup_close(note.id)
        self.on_change()

    @property
    def count(self):
        return len(self.items)
