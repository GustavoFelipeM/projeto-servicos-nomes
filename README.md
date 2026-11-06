# Serviço de Nomes e Descoberta de Serviços (Service Discovery)

Projeto prático em Python puro demonstrando os conceitos de **Service Registry**, **Health Checking (Heartbeats)** e **Client-Side Discovery** em Sistemas Distribuídos.


## Arquitetura do Sistema

```text
               +-----------------------+
               |  src.registry.server  |
               |  (Servidor de Nomes)  |
               +-----------+-----------+
                           ^
             (1) /register | (3) /discover?name=pagamento
             (2) /heartbeat|
       +-------------------+-------------------+
       |                                       |
+------+---------------+               +-------+---------------+
|    src.service.app   | <--- (4) GET -|  src.client.consumer  |
|(Instância de Serviço)|     /processar|  (Cliente Consumidor) |
+----------------------+               +-----------------------+

```


## Estrutura de Módulos

* `src/registry/server.py`: Servidor de registro e gerenciamento do ciclo de vida das instâncias.
* `src/service/app.py`: Aplicação backend com auto-registro e atualização contínua de heartbeat.
* `src/client/consumer.py`: Cliente consumidor com resolução dinâmica de endereços e balanceamento de carga.
* `scripts/run_demo.sh`: Script de automação para Linux / WSL / macOS.
* `scripts/run_demo.ps1`: Script de automação para Windows (PowerShell).


## Como Executar no Linux / WSL / macOS

### Opção 1: Execução Automatizada (Recomendado)

A partir do diretório raiz do projeto:

```bash
chmod +x scripts/run_demo.sh
./scripts/run_demo.sh
```

### Opção 2: Execução Manual (Multi-Terminal)

Abra 4 terminais no diretório raiz do projeto:

1. **Terminal 1 (Registry):**
```bash
python3 -m src.registry.server
```


2. **Terminal 2 (Serviço - Instância A):**
```bash
python3 -m src.service.app 5001
```


3. **Terminal 3 (Serviço - Instância B):**
```bash
python3 -m src.service.app 5002
```


4. **Terminal 4 (Cliente):**
```bash
python3 -m src.client.consumer
```



## Como Executar no Windows (PowerShell / CMD)

### Opção 1: Execução Automatizada via PowerShell

1. Abra o **PowerShell** no diretório raiz do projeto.
2. (Opcional) Caso a execução de scripts esteja bloqueada no Windows, rode uma vez:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
```


3. Execute o script de automação:
```powershell
.\scripts\run_demo.ps1
```



### Opção 2: Execução Manual (Multi-Janela no Windows)

Abra 4 janelas do **Prompt de Comando (`cmd`)** ou **PowerShell** no diretório raiz:

1. **Janela 1 (Registry):**
```cmd
python -m src.registry.server
```


2. **Janela 2 (Serviço - Instância A):**
```cmd
python -m src.service.app 5001
```


3. **Janela 3 (Serviço - Instância B):**
```cmd
python -m src.service.app 5002
```


4. **Janela 4 (Cliente):**
```cmd
python -m src.client.consumer
```