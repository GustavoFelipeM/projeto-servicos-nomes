import json
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

REGISTRY_URL = "http://127.0.0.1:8000"
HTTP_TIMEOUT = 3


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
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT):
            pass
        print(f"[SERVIÇO] Registrado com sucesso no Registry como '{name}'")
        return True
    except Exception as e:
        print(f"[SERVIÇO] Erro ao registrar no Registry: {e}")
        return False


def deregister_self(name, url):
    payload = json.dumps({"name": name, "url": url}).encode("utf-8")
    req = urllib.request.Request(
        f"{REGISTRY_URL}/deregister",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT):
            pass
        print(f"[SERVIÇO] Removido do Registry: '{name}' ({url})")
    except Exception as e:
        print(f"[SERVIÇO] Erro ao remover do Registry: {e}")


def send_heartbeats(name, url):
    """Mantenha a instância viva no Registry enviando solicitações a cada 4 segundos."""
    while True:
        time.sleep(4)
        send_heartbeat(name, url)


def send_heartbeat(name, url):
    payload = json.dumps({"name": name, "url": url}).encode("utf-8")
    req = urllib.request.Request(
        f"{REGISTRY_URL}/heartbeat",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as response:
            if response.status == 404:
                register_self(name, url)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            register_self(name, url)
        else:
            print(f"[SERVIÇO] Falha ao enviar heartbeat: HTTP {error.code}")
    except Exception as error:
        print(f"[SERVIÇO] Falha ao enviar heartbeat: {error}")


def main():
    global PORT
    PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5001
    service_name = "pagamento"
    my_url = f"http://127.0.0.1:{PORT}"

    server = HTTPServer(("127.0.0.1", PORT), PaymentServiceHandler)
    register_self(service_name, my_url)
    threading.Thread(target=send_heartbeats, args=(service_name, my_url), daemon=True).start()
    print(f"[SERVIÇO] Instância '{service_name}' ativa em {my_url}...")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        deregister_self(service_name, my_url)
        server.server_close()


if __name__ == "__main__":
    main()