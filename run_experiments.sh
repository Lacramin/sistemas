#!/bin/bash

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  AUTOMATIZACIÓN DE 20 EXPERIMENTOS     ${NC}"
echo -e "${GREEN}========================================${NC}"

run_experiment() {
    local DIST=$1
    local POLICY=$2
    local MEMORY=$3
    local CASO="${DIST}_${POLICY#allkeys-}_${MEMORY}"
    
    echo -e "\n${YELLOW}========================================${NC}"
    echo -e "${YELLOW}  EXPERIMENTO: ${CASO}${NC}"
    echo -e "${YELLOW}========================================${NC}"
    
    echo " Deteniendo servicios anteriores..."
    docker compose -f docker-compose-temp.yml down -v 2>/dev/null
    docker compose down -v 2>/dev/null
    
    echo "  Configurando: ${DIST}, ${POLICY}, ${MEMORY}..."
    
    cat > docker-compose-temp.yml << EOF
services:
  redis-cache:
    image: redis:alpine
    ports:
      - "6379:6379"
    command: redis-server --maxmemory ${MEMORY} --maxmemory-policy ${POLICY}
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  metricas:
    build: ./metricas
    ports:
      - "8001:8000"
    volumes:
      - ./metricas:/app

  generador_respuestas:
    build: ./generador_respuestas
    ports:
      - "8002:8000"

  cache_system:
    build: ./cache_system
    ports:
      - "8003:8000"
    depends_on:
      redis-cache:
        condition: service_healthy
      generador_respuestas:
        condition: service_started
      metricas:
        condition: service_started
    environment:
      - REDIS_HOST=redis-cache
      - RESPUESTAS_URL=http://generador_respuestas:8000
      - METRICAS_URL=http://metricas:8000

  generador_trafico:
    build: ./generador_trafico
    depends_on:
      - cache_system
    environment:
      - CACHE_URL=http://cache_system:8000
      - DISTRIBUCION=${DIST}
      - TOTAL_CONSULTAS=6000
      - SLEEP_ENTRE_CONSULTAS=0.01
      - CONFIDENCE_VARIATION=random
EOF

    echo " Levantando servicios..."
    docker compose -f docker-compose-temp.yml up -d redis-cache metricas generador_respuestas cache_system
    
    echo "Esperando a que los servicios estén listos..."
    sleep 15
    
    echo " Reseteando métricas..."
    python3 -c "import requests; requests.get('http://localhost:8001/reset')" 2>/dev/null || true
    
    echo "Iniciando generador de tráfico..."
    docker compose -f docker-compose-temp.yml up generador_trafico &
    TRAFFIC_PID=$!
    
    echo "Esperando 6000 consultas (~90 segundos)..."
    sleep 90
    
    echo "Deteniendo generador..."
    docker compose -f docker-compose-temp.yml stop generador_trafico 2>/dev/null
    kill $TRAFFIC_PID 2>/dev/null
    sleep 3
    
    echo "Descargando métricas..."
    mkdir -p metricas
    python3 -c "
import requests
r = requests.get('http://localhost:8001/descargar')
if r.status_code == 200:
    with open('metricas/${CASO}.csv', 'wb') as f:
        f.write(r.content)
    print('OK')
else:
    print('ERROR:', r.status_code)
"
    
    if [ -f "metricas/${CASO}.csv" ] && [ -s "metricas/${CASO}.csv" ]; then
        LINEAS=$(wc -l < "metricas/${CASO}.csv")
        echo -e "${GREEN} Archivo guardado: metricas/${CASO}.csv (${LINEAS} líneas)${NC}"
    else
        echo -e "${RED} Error: El archivo está vacío o no existe${NC}"
    fi
    
    echo " Estadísticas rápidas:"
    python3 -c "import requests; print(requests.get('http://localhost:8001/stats').json())" 2>/dev/null || echo "Servicio no disponible"
    
    echo " Limpiando para siguiente experimento..."
    docker compose -f docker-compose-temp.yml down -v 2>/dev/null
    rm -f docker-compose-temp.yml
    sleep 5
}

echo -e "\n${GREEN} INICIANDO LOTES DE EXPERIMENTOS${NC}\n"

# --- ZIPF + LRU ---
for MEM in 10mb 25mb 50mb 200mb 500mb; do
    run_experiment "zipf" "allkeys-lru" $MEM
done

# --- ZIPF + LFU ---
for MEM in 10mb 25mb 50mb 200mb 500mb; do
    run_experiment "zipf" "allkeys-lfu" $MEM
done

# --- UNIFORM + LRU ---
for MEM in 10mb 25mb 50mb 200mb 500mb; do
    run_experiment "uniform" "allkeys-lru" $MEM
done

# --- UNIFORM + LFU ---
for MEM in 10mb 25mb 50mb 200mb 500mb; do
    run_experiment "uniform" "allkeys-lfu" $MEM
done

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  ¡20 EXPERIMENTOS COMPLETADOS!      ${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\nArchivos generados en ./metricas/:"
ls -lh metricas/*.csv 2>/dev/null || echo "No se encontraron archivos CSV"
