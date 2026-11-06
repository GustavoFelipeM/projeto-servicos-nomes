import json
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
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

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        data = json.loads(body.decode("utf-8")) if body else {}

        # 1. Cadastro de novos serviços
        if self.path == "/register":
            service_name = data.get("name")
            url = data.get("url")
            if not service_name or not url:
                return self._send_json(400, {"error": "Dados inválidos"})

            with LOCK:
                if service_name not in REGISTRY:
                    REGISTRY[service_name] = {}
                REGISTRY[service_name][url] = time.time()

            print(f"[REGISTRY] + Novo serviço registrado: '{service_name}' em {url}")
            return self._send_json(200, {"status": "registrado"})

        # 2. Recebimento de sinal de vida (Heartbeat)
        elif self.path == "/heartbeat":
            service_name = data.get("name")
            url = data.get("url")
            with LOCK:
                if service_name in REGISTRY and url in REGISTRY[service_name]:
                    REGISTRY[service_name][url] = time.time()
                    print(f"[REGISTRY] Heartbeat de '{service_name}' ({url})")
                    return self._send_json(200, {"status": "ok"})
            return self._send_json(404, {"error": "Instância não encontrada"})

        self._send_json(404, {"error": "Rota desconhecida"})

    def do_GET(self):
        parsed = urlparse(self.path)
        # 3. Resolução de nomes (Service Discovery)
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
        now = time.time()
        with LOCK:
            for service, instances in list(REGISTRY.items()):
                for url, last_seen in list(instances.items()):
                    if now - last_seen > TTL_SECONDS:
                        print(f"[REGISTRY] ✖ REMOVENDO INSTÂNCIA INATIVA: {service} ({url})")
                        del REGISTRY[service][url]


def main():
    threading.Thread(target=auto_cleanup_health_check, daemon=True).start()
    server = HTTPServer(("127.0.0.1", 8000), RegistryHandler)
    print("==================================================")
    print(" [REGISTRY] Servidor rodando em http://127.0.0.1:8000")
    print("==================================================")
    server.serve_forever()


if __name__ == "__main__":
    main()