import json
import sys
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

REGISTRY_URL = "http://127.0.0.1:8000"


class PaymentServiceHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/processar":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response = {"message": f"Pagamento processado com sucesso pelo nó na Porta {PORT}"}
            self.wfile.write(json.dumps(response).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()


def register_self(name, url):
    payload = json.dumps({"name": name, "url": url}).encode("utf-8")
    req = urllib.request.Request(
        f"{REGISTRY_URL}/register",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    try:
        urllib.request.urlopen(req)
        print(f"[SERVIÇO] Registrado com sucesso no Registry como '{name}'")
    except Exception as e:
        print(f"[SERVIÇO] Erro ao registrar no Registry: {e}")


def send_heartbeats(name, url):
    """Mantenha a instância viva no Registry enviando solicitações a cada 4 segundos."""
    while True:
        time.sleep(4)
        payload = json.dumps({"name": name, "url": url}).encode("utf-8")
        req = urllib.request.Request(
            f"{REGISTRY_URL}/heartbeat",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        try:
            urllib.request.urlopen(req)
        except Exception:
            print("[SERVIÇO] Falha ao enviar heartbeat!")


def main():
    global PORT
    PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5001
    service_name = "pagamento"
    my_url = f"http://127.0.0.1:{PORT}"

    register_self(service_name, my_url)

    threading.Thread(target=send_heartbeats, args=(service_name, my_url), daemon=True).start()

    server = HTTPServer(("127.0.0.1", PORT), PaymentServiceHandler)
    print(f"[SERVIÇO] Instância '{service_name}' ativa em {my_url}...")
    server.serve_forever()


if __name__ == "__main__":
    main()