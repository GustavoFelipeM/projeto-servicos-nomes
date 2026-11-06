import json
import random
import time
import urllib.request

REGISTRY_URL = "http://127.0.0.1:8000"


def discover_service(service_name):
    """Consulta o Registry para resolver o nome lógico em instâncias de IP/Porta."""
    url = f"{REGISTRY_URL}/discover?name={service_name}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as resp:
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

    # Balanceamento de Carga no Lado do Cliente (Client-Side Load Balancing)
    selected_instance = random.choice(instances)
    print(f"[CLIENTE] Instâncias encontradas: {instances}")
    print(f"[CLIENTE] Instância selecionada: {selected_instance}")

    try:
        req = urllib.request.Request(f"{selected_instance}/processar")
        with urllib.request.urlopen(req) as resp:
            resultado = json.loads(resp.read().decode("utf-8"))
            print(f"[CLIENTE] Resposta recebida -> {resultado['message']}")
    except Exception as e:
        print(f"[CLIENTE] Falha ao se comunicar com {selected_instance}: {e}")


def main():
    print("[CLIENTE] Iniciando simulação de chamadas...")
    for _ in range(5):
        execute_request()
        time.sleep(3)


if __name__ == "__main__":
    main()