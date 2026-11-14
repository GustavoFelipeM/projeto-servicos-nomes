import json
import threading
import time
import unittest
import urllib.error
import urllib.request
from unittest import mock

from src.client import consumer
from src.registry import server as registry
from src.service import app as service


class FakeResponse:
    status = 200

    def __init__(self, data=None):
        self.data = json.dumps(data or {"message": "ok"}).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return self.data


class RegistryEndpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = registry.ThreadingHTTPServer(("127.0.0.1", 0), registry.RegistryHandler)
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
        cls.registry_url = f"http://127.0.0.1:{cls.httpd.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.thread.join()

    def setUp(self):
        with registry.LOCK:
            registry.REGISTRY.clear()

    def post(self, path, payload):
        request = urllib.request.Request(
            f"{self.registry_url}{path}",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        return urllib.request.urlopen(request, timeout=1)

    def test_register_discover_heartbeat_and_deregister(self):
        payload = json.dumps({"name": "pagamento", "url": "http://127.0.0.1:5001"}).encode()
        response = self.post("/register", payload)
        self.assertEqual(response.status, 200)

        with urllib.request.urlopen(
            f"{self.registry_url}/discover?name=pagamento", timeout=1
        ) as response:
            data = json.loads(response.read())
        self.assertEqual(data["instances"], ["http://127.0.0.1:5001"])

        response = self.post("/heartbeat", payload)
        self.assertEqual(response.status, 200)
        response = self.post("/deregister", payload)
        self.assertEqual(response.status, 200)

        with urllib.request.urlopen(
            f"{self.registry_url}/discover?name=pagamento", timeout=1
        ) as response:
            self.assertEqual(json.loads(response.read())["instances"], [])

    def test_invalid_payload_returns_bad_request(self):
        with self.assertRaises(urllib.error.HTTPError) as context:
            self.post("/register", b"not-json")
        self.assertEqual(context.exception.code, 400)

        payload = json.dumps({"name": "pagamento", "url": "not-a-url"}).encode()
        with self.assertRaises(urllib.error.HTTPError) as context:
            self.post("/register", payload)
        self.assertEqual(context.exception.code, 400)

    def test_expired_instance_is_removed(self):
        with registry.LOCK:
            registry.REGISTRY["pagamento"] = {"http://127.0.0.1:5001": 0}
        registry.cleanup_expired_instances(now=registry.TTL_SECONDS + 1)
        with registry.LOCK:
            self.assertNotIn("pagamento", registry.REGISTRY)


class ClientAndServiceTests(unittest.TestCase):
    def test_heartbeat_reregisters_after_not_found(self):
        not_found = urllib.error.HTTPError(
            "http://registry/heartbeat", 404, "missing", {}, None
        )
        with mock.patch.object(service.urllib.request, "urlopen", side_effect=not_found):
            with mock.patch.object(service, "register_self") as register:
                service.send_heartbeat("pagamento", "http://127.0.0.1:5001")
        register.assert_called_once_with("pagamento", "http://127.0.0.1:5001")

    def test_client_tries_next_instance_after_failure(self):
        failed = urllib.error.URLError("instance unavailable")
        with mock.patch.object(
            consumer, "discover_service", return_value=["http://one", "http://two"]
        ), mock.patch.object(
            consumer.random, "sample", return_value=["http://one", "http://two"]
        ), mock.patch.object(
            consumer.urllib.request, "urlopen", side_effect=[failed, FakeResponse()]
        ) as urlopen:
            consumer.execute_request()
        self.assertEqual(urlopen.call_count, 2)

    def test_register_uses_timeout(self):
        with mock.patch.object(service.urllib.request, "urlopen", return_value=FakeResponse()) as urlopen:
            self.assertTrue(service.register_self("pagamento", "http://127.0.0.1:5001"))
        self.assertEqual(urlopen.call_args.kwargs["timeout"], service.HTTP_TIMEOUT)


if __name__ == "__main__":
    unittest.main()
