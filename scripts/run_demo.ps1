# Garante que o script rode a partir da raiz do projeto
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location "$ScriptDir\.."

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "   Iniciando Demonstração de Service Discovery   " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 1. Inicia o Service Registry em segundo plano
Write-Host "[1/4] Subindo Service Registry (Porta 8000)..."
$registry = Start-Process python -ArgumentList "-m src.registry.server" -PassThru -NoNewWindow
Start-Sleep -Seconds 2

# 2. Subindo Instâncias do Microserviço em segundo plano
Write-Host "[2/4] Subindo Instância A de 'pagamento' (Porta 5001)..."
$service1 = Start-Process python -ArgumentList "-m src.service.app 5001" -PassThru -NoNewWindow

Write-Host "[3/4] Subindo Instância B de 'pagamento' (Porta 5002)..."
$service2 = Start-Process python -ArgumentList "-m src.service.app 5002" -PassThru -NoNewWindow
Start-Sleep -Seconds 2

# 3. Executa o Cliente Consumidor na janela atual
Write-Host "[4/4] Executando simulação do Cliente Consumidor..."
python -m src.client.consumer

# 4. Encerra os processos que ficaram rodando em segundo plano
Write-Host ""
Write-Host "Finalizando servidores de segundo plano..." -ForegroundColor Yellow
Stop-Process -Id $registry.Id -Force -ErrorAction SilentlyContinue
Stop-Process -Id $service1.Id -Force -ErrorAction SilentlyContinue
Stop-Process -Id $service2.Id -Force -ErrorAction SilentlyContinue

Write-Host "Demonstração concluída!" -ForegroundColor Green