import json
import random
import time
import urllib.request
from urllib.parse import urlencode

REGISTRY_URL = "http://127.0.0.1:8000"
HTTP_TIMEOUT = 3


def discover_service(service_name):
    """Consulta o Registry para resolver o nome lógico em instâncias de IP/Porta."""
    query = urlencode({"name": service_name})
    url = f"{REGISTRY_URL}/discover?{query}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("instances", [])
    except Exception as e:
        print(f"[CLIENTE] Erro ao conectar ao Registry: {e}")
        return []


def execute_request():
    print("\n--------------------------------------------------")
    instances = discover_service("pagamento")

    if not instances:
        print("[CLIENTE] Nenhum serviço de 'pagamento' disponível no momento!")
        return

    print(f"[CLIENTE] Instâncias encontradas: {instances}")
    # Tenta cada instância no máximo uma vez, começando por uma escolha aleatória.
    candidates = random.sample(instances, k=len(instances))
    for selected_instance in candidates:
        print(f"[CLIENTE] Instância selecionada: {selected_instance}")
        try:
            req = urllib.request.Request(f"{selected_instance}/processar")
            with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
                resultado = json.loads(resp.read().decode("utf-8"))
                print(f"[CLIENTE] Resposta recebida -> {resultado['message']}")
                return
        except Exception as error:
            print(f"[CLIENTE] Falha ao se comunicar com {selected_instance}: {error}")

    print("[CLIENTE] Nenhuma das instâncias disponíveis respondeu.")


def main():
    print("[CLIENTE] Iniciando simulação de chamadas...")
    for _ in range(5):
        execute_request()
        time.sleep(3)


if __name__ == "__main__":
    main()