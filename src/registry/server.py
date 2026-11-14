import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

REGISTRY = {}
LOCK = threading.Lock()
TTL_SECONDS = 10  # Tempo máximo sem heartbeat antes de desregistrar a instância


class RegistryHandler(BaseHTTPRequestHandler):
    def _send_json(self, status, data):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def _read_payload(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode("utf-8")) if body else {}
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
            return None
        return data if isinstance(data, dict) else None

    def _parse_instance(self, data):
        if not isinstance(data, dict):
            return None
        service_name = data.get("name")
        url = data.get("url")
        parsed_url = urlparse(url) if isinstance(url, str) else None
        if (
            not isinstance(service_name, str)
            or not service_name.strip()
            or not isinstance(url, str)
            or not parsed_url
            or parsed_url.scheme not in {"http", "https"}
            or not parsed_url.netloc
        ):
            return None
        return service_name.strip(), url

    def do_POST(self):
        data = self._read_payload()
        instance = self._parse_instance(data)

        # 1. Cadastro de novos serviços
        if self.path == "/register":
            if instance is None:
                return self._send_json(400, {"error": "Dados inválidos"})
            service_name, url = instance

            with LOCK:
                if service_name not in REGISTRY:
                    REGISTRY[service_name] = {}
                REGISTRY[service_name][url] = time.time()

            print(f"[REGISTRY] + Novo serviço registrado: '{service_name}' em {url}")
            return self._send_json(200, {"status": "registrado"})

        # 2. Recebimento de sinal de vida (Heartbeat)
        elif self.path == "/heartbeat":
            if instance is None:
                return self._send_json(400, {"error": "Dados inválidos"})
            service_name, url = instance
            with LOCK:
                if service_name in REGISTRY and url in REGISTRY[service_name]:
                    REGISTRY[service_name][url] = time.time()
                    print(f"[REGISTRY] Heartbeat de '{service_name}' ({url})")
                    return self._send_json(200, {"status": "ok"})
            return self._send_json(404, {"error": "Instância não encontrada"})

        # 3. Remoção explícita de uma instância em encerramento normal
        elif self.path == "/deregister":
            if instance is None:
                return self._send_json(400, {"error": "Dados inválidos"})
            service_name, url = instance
            with LOCK:
                instances = REGISTRY.get(service_name, {})
                if url not in instances:
                    return self._send_json(404, {"error": "Instância não encontrada"})
                del instances[url]
                if not instances:
                    del REGISTRY[service_name]
            print(f"[REGISTRY] - Serviço removido: '{service_name}' em {url}")
            return self._send_json(200, {"status": "removido"})

        self._send_json(404, {"error": "Rota desconhecida"})

    def do_GET(self):
        parsed = urlparse(self.path)
        # 4. Resolução de nomes (Service Discovery)
        if parsed.path == "/discover":
            query = parse_qs(parsed.query)
            service_name = query.get("name", [None])[0]

            with LOCK:
                instances = list(REGISTRY.get(service_name, {}).keys())

            print(f"[REGISTRY] ? Consulta por '{service_name}': {len(instances)} instância(s) ativa(s)")
            return self._send_json(200, {"service": service_name, "instances": instances})

        self._send_json(404, {"error": "Rota desconhecida"})


def auto_cleanup_health_check():
    """Thread de fundo para remover instâncias que sofreram crash ou queda."""
    while True:
        time.sleep(3)
        cleanup_expired_instances()


def cleanup_expired_instances(now=None):
    now = time.time() if now is None else now
    with LOCK:
        for service, instances in list(REGISTRY.items()):
            for url, last_seen in list(instances.items()):
                if now - last_seen > TTL_SECONDS:
                    print(f"[REGISTRY] REMOVENDO INSTANCIA INATIVA: {service} ({url})")
                    del REGISTRY[service][url]
            if not instances:
                del REGISTRY[service]


def main():
    threading.Thread(target=auto_cleanup_health_check, daemon=True).start()
    server = ThreadingHTTPServer(("127.0.0.1", 8000), RegistryHandler)
    print("==================================================")
    print(" [REGISTRY] Servidor rodando em http://127.0.0.1:8000")
    print("==================================================")
    server.serve_forever()


if __name__ == "__main__":
    main()