import json
import os
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from latte_common import llm  # noqa: E402

MODELS = [
    {"id": "embed", "type": "embeddings", "state": "not-loaded"},
    {"id": "maly", "type": "llm", "state": "not-loaded"},
    {"id": "velky", "type": "vlm", "state": "loaded"},
]


class Handler(BaseHTTPRequestHandler):
    chunks = []
    seen = {}

    def log_message(self, *_a):
        pass

    def do_GET(self):
        if self.path == "/api/v0/models":
            self.reply(200, {"data": MODELS})
        elif self.path == "/v1/models":
            self.reply(200, {"data": [{"id": "iba-v1"}]})
        else:
            self.reply(404, {"error": "nie"})

    def do_POST(self):
        size = int(self.headers.get("Content-Length", 0))
        Handler.seen = json.loads(self.rfile.read(size))
        if Handler.seen.get("model") == "zly":
            self.reply(400, {"error": {"message": "model sa nedá načítať"}})
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        for chunk in Handler.chunks:
            self.wfile.write(b"data: " + chunk.encode("utf-8") + b"\n\n")
        self.wfile.write(b"data: [DONE]\n\n")

    def reply(self, code, body):
        data = json.dumps(body).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def delta(**kw):
    return json.dumps({"choices": [{"delta": kw}]})


class LlmTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), Handler)
        cls.base = "http://127.0.0.1:%d" % cls.server.server_port
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_list_models_reads_state_from_native_api(self):
        self.assertEqual({m["id"]: m["state"] for m in llm.list_models(self.base)},
                         {"embed": "not-loaded", "maly": "not-loaded", "velky": "loaded"})

    def test_pick_prefers_loaded_chat_model(self):
        self.assertEqual(llm.pick_model(MODELS), "velky")

    def test_pick_falls_back_to_first_chat_model_never_embeddings(self):
        models = [MODELS[0], MODELS[1]]
        self.assertEqual(llm.pick_model(models), "maly")
        with self.assertRaises(llm.LlmError):
            llm.pick_model([MODELS[0]])

    def test_pick_honours_the_configured_model_or_says_it_is_missing(self):
        self.assertEqual(llm.pick_model(MODELS, "maly"), "maly")
        with self.assertRaises(llm.LlmError):
            llm.pick_model(MODELS, "neexistuje")

    def test_unreachable_server_gives_a_readable_error(self):
        with self.assertRaises(llm.LlmError) as ctx:
            llm.list_models("http://127.0.0.1:9")
        self.assertIn("127.0.0.1:9", str(ctx.exception))

    def test_stream_yields_content_and_reasoning(self):
        Handler.chunks = [delta(reasoning_content="hm"), delta(content="Ah"), delta(content="oj")]
        stream = llm.ChatStream(self.base, "velky", [{"role": "user", "content": "čau"}])
        self.assertEqual(list(stream.events()),
                         [("reasoning", "hm"), ("content", "Ah"), ("content", "oj")])
        self.assertEqual(Handler.seen["messages"][0]["role"], "system")
        self.assertEqual(Handler.seen["messages"][-1]["content"], "čau")
        self.assertTrue(Handler.seen["stream"])

    def test_think_tags_in_content_are_split_even_across_chunks(self):
        Handler.chunks = [delta(content="<thi"), delta(content="nk>úvaha</th"),
                          delta(content="ink>odpoveď")]
        events = list(llm.ChatStream(self.base, "velky", []).events())
        text = {}
        for kind, part in events:
            text[kind] = text.get(kind, "") + part
        self.assertEqual(text, {"reasoning": "úvaha", "content": "odpoveď"})

    def test_http_error_carries_the_servers_message(self):
        with self.assertRaises(llm.LlmError) as ctx:
            list(llm.ChatStream(self.base, "zly", []).events())
        self.assertIn("model sa nedá načítať", str(ctx.exception))

    def test_cancelled_stream_stops_quietly(self):
        Handler.chunks = [delta(content="a"), delta(content="b")]
        stream = llm.ChatStream(self.base, "velky", [])
        events = stream.events()
        self.assertEqual(next(events), ("content", "a"))
        stream.cancel()
        self.assertEqual(list(events), [])


class ThinkSplitterTest(unittest.TestCase):
    def test_lone_angle_bracket_is_not_swallowed(self):
        s = llm.ThinkSplitter()
        out = s.feed("a < b") + s.flush()
        self.assertEqual("".join(t for _k, t in out), "a < b")

    def test_unfinished_tag_at_the_end_is_flushed(self):
        s = llm.ThinkSplitter()
        self.assertEqual(s.feed("ahoj <th"), [("content", "ahoj ")])
        self.assertEqual(s.flush(), [("content", "<th")])


if __name__ == "__main__":
    unittest.main()
