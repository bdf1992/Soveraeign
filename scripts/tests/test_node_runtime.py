from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("node_runtime", ROOT / "scripts" / "node_runtime.py")
assert SPEC and SPEC.loader
node_runtime = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(node_runtime)


class NodeRuntimeTests(unittest.TestCase):
    def test_health_surface_is_explicit_and_only_three_paths(self):
        self.assertEqual(node_runtime.HEALTH_PATHS, {
            "/health/startup", "/health/ready", "/health/live"
        })

    def test_listener_backlog_is_bounded(self):
        self.assertEqual(node_runtime.BoundedHTTPServer.request_queue_size, 1)

    def test_invalid_port_refuses_before_listener_creation(self):
        self.assertEqual(node_runtime.main(["--port", "0"]), 2)
        self.assertEqual(node_runtime.main(["--port", "65536"]), 2)

    def test_real_listener_passes_health_and_refuses_unactivated_gateway(self):
        server = node_runtime.BoundedHTTPServer(("127.0.0.1", 0), node_runtime.NodeHandler)
        thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01},
                                  daemon=True)
        thread.start()
        port = server.server_address[1]
        try:
            with urlopen(f"http://127.0.0.1:{port}/health/ready", timeout=1) as response:
                self.assertEqual(response.status, 200)
                self.assertEqual(json.loads(response.read())["outcome"], "PASS")
            with self.assertRaises(HTTPError) as raised:
                urlopen(f"http://127.0.0.1:{port}/work", timeout=1)
            self.assertEqual(raised.exception.code, 503)
            self.assertEqual(json.loads(raised.exception.read())["reason"],
                             "GATEWAY_OPERATION_NOT_ACTIVATED")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=1)


if __name__ == "__main__":
    unittest.main()
