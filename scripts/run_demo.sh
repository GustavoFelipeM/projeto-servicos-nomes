#!/bin/bash

echo "1. Iniciando Service Registry..."
python3 src/registry/server.py &
REGISTRY_PID=$!
sleep 1

echo "2. Subindo Instancia A do Serviço (Porta 5001)..."
python3 src/service/app.py 5001 &
SERVICE1_PID=$!

echo "3. Subindo Instancia B do Serviço (Porta 5002)..."
python3 src/service/app.py 5002 &
SERVICE2_PID=$!
sleep 2

echo "4. Executando o Cliente Consumidor..."
python3 src/client/consumer.py

# Encerra os processos de fundo ao terminar
kill $REGISTRY_PID $SERVICE1_PID $SERVICE2_PID