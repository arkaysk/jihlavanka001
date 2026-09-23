"""Klient lokálneho LM Studia (OpenAI-kompatibilné API) pre AI v prompte lišty.

Adresu a model nastavuje ~/.config/latteos/prompt.toml (ai_url, ai_model). Bez modelu sa vezme
ten, čo je v LM Studiu načítaný. Používa sa len štandardná knižnica; volania blokujú,
preto ich komponenty spúšťajú vo vlákne.
"""
import json
import urllib.error
import urllib.request

from latte_common import prefs

DEFAULT_URL = "http://192.168.56.1:1234"
CHAT_TYPES = ("llm", "vlm")
SYSTEM_PROMPT = (
    "Si asistent v prostredí LatteOS. Odpovedaj stručne a vecne, v jazyku, v ktorom sa ťa "
    "používateľ pýta (predvolene po slovensky)."
)


class LlmError(Exception):
    """Chyba zrozumiteľná pre používateľa (text ide priamo do rozhrania)."""


def settings():
    """(adresa servera bez lomky na konci, požadovaný model alebo "")."""
    values = prefs.load("prompt")
    return values.get("ai_url", DEFAULT_URL).rstrip("/"), values.get("ai_model", "")


def _open(request, timeout):
    try:
        return urllib.request.urlopen(request, timeout=timeout)
    except urllib.error.HTTPError as err:
        detail = ""
        try:
            body = json.loads(err.read().decode("utf-8", "replace"))
            error = body.get("error", "") if isinstance(body, dict) else ""
            detail = error.get("message", "") if isinstance(error, dict) else str(error)
        except (ValueError, OSError):
            pass
        finally:
            err.close()
        raise LlmError("LM Studio odpovedal chybou %d%s" % (err.code, ": " + detail if detail else ""))
    except (urllib.error.URLError, OSError, ValueError) as err:
        reason = getattr(err, "reason", err)
        raise LlmError("LM Studio na %s neodpovedá (%s). Beží tam server?"
                       % (request.full_url.split("/api/")[0].split("/v1/")[0], reason))


def _get_json(url, timeout=5):
    with _open(urllib.request.Request(url), timeout) as resp:
        try:
            return json.loads(resp.read().decode("utf-8"))
        except ValueError:
            raise LlmError("LM Studio poslal neplatnú odpoveď (%s)" % url)


def list_models(base):
    """Zoznam modelov ako slovníky s kľúčmi id, type, state. Najprv natívne API LM Studia
    (pozná stav načítania), inak štandardné /v1/models."""
    try:
        data = _get_json(base + "/api/v0/models").get("data", [])
    except LlmError:
        data = _get_json(base + "/v1/models").get("data", [])
    return [{"id": m["id"], "type": m.get("type", "llm"), "state": m.get("state", "")}
            for m in data if isinstance(m, dict) and m.get("id")]


def pick_model(models, wanted=""):
    """Model podľa nastavenia, inak načítaný, inak prvý, čo vie chatovať (nie embeddings)."""
    if wanted:
        if any(m["id"] == wanted for m in models):
            return wanted
        raise LlmError("Model „%s“ z prompt.toml LM Studio nemá" % wanted)
    chat = [m for m in models if m["type"] in CHAT_TYPES]
    for m in chat:
        if m["state"] == "loaded":
            return m["id"]
    if chat:
        return chat[0]["id"]
    raise LlmError("LM Studio nemá žiadny jazykový model")


class ThinkSplitter:
    """Oddelí <think>…</think> od odpovede, aj keď sa značka rozdelí medzi dva kúsky."""

    def __init__(self):
        self.thinking = False
        self.pending = ""

    def feed(self, text):
        out = []
        buffer = self.pending + text
        self.pending = ""
        while buffer:
            tag = "</think>" if self.thinking else "<think>"
            at = buffer.find(tag)
            if at >= 0:
                if at:
                    out.append(("reasoning" if self.thinking else "content", buffer[:at]))
                buffer = buffer[at + len(tag):]
                self.thinking = not self.thinking
                continue
            keep = 0                    # koniec kúska môže byť začiatok značky
            for n in range(min(len(tag) - 1, len(buffer)), 0, -1):
                if tag.startswith(buffer[-n:]):
                    keep = n
                    break
            emit, self.pending = buffer[:len(buffer) - keep], buffer[len(buffer) - keep:]
            if emit:
                out.append(("reasoning" if self.thinking else "content", emit))
            break
        return out

    def flush(self):
        rest, self.pending = self.pending, ""
        return [("reasoning" if self.thinking else "content", rest)] if rest else []


class ChatStream:
    """Jedna odpoveď streamom. events() vydáva ("reasoning"|"content", text);
    cancel() sa dá volať z iného vlákna a preruší čakanie na server."""

    def __init__(self, base, model, messages, timeout=600):
        self.base, self.model, self.messages, self.timeout = base, model, messages, timeout
        self.response = None
        self.cancelled = False

    def cancel(self):
        self.cancelled = True
        response = self.response
        if response is not None:
            try:
                response.close()
            except OSError:
                pass

    def events(self):
        body = json.dumps({
            "model": self.model,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + self.messages,
            "stream": True,
        }).encode("utf-8")
        request = urllib.request.Request(
            self.base + "/v1/chat/completions", data=body,
            headers={"Content-Type": "application/json"})
        splitter = ThinkSplitter()
        self.response = _open(request, self.timeout)
        try:
            for raw in self.response:
                if self.cancelled:
                    return
                line = raw.decode("utf-8", "replace").strip()
                if not line.startswith("data:"):
                    continue
                payload = line[5:].strip()
                if payload == "[DONE]":
                    break
                try:
                    choice = json.loads(payload)["choices"][0]
                except (ValueError, KeyError, IndexError, TypeError):
                    continue
                delta = choice.get("delta") or {}
                if delta.get("reasoning_content"):
                    yield "reasoning", delta["reasoning_content"]
                if delta.get("content"):
                    yield from splitter.feed(delta["content"])
            yield from splitter.flush()
        except (OSError, ValueError) as err:
            if not self.cancelled:
                raise LlmError("Spojenie s LM Studiom sa prerušilo: %s" % err)
        finally:
            self.cancel()
