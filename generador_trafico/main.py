import time, requests, os, random
import numpy as np

# ============================================
# CONFIGURACIÓN DESDE VARIABLES DE ENTORNO
# ============================================
URL_CACHE = os.getenv("CACHE_URL", "http://cache_system:8000")
ZONAS = ["Z1", "Z2", "Z3", "Z4", "Z5"]
CONSULTAS = ["q1", "q2", "q3", "q4", "q5"]

# Parámetros de simulación (personalizables desde docker-compose)
DISTRIBUCION = os.getenv("DISTRIBUCION", "zipf").lower()
TOTAL_CONSULTAS = int(os.getenv("TOTAL_CONSULTAS", "6000"))
SLEEP_ENTRE_CONSULTAS = float(os.getenv("SLEEP_ENTRE_CONSULTAS", "0.01"))
CONFIDENCE_VARIATION = os.getenv("CONFIDENCE_VARIATION", "random").lower()
CONFIDENCE_FIXED = float(os.getenv("CONFIDENCE_FIXED", "0.0"))

# ============================================
# PESOS ZIPF
# ============================================
if DISTRIBUCION == "zipf":
    weights = [1/(i**1.5) for i in range(1, len(ZONAS) + 1)]
    weights = np.array(weights) / np.sum(weights)
    print(f" Distribución Zipf - Pesos: {dict(zip(ZONAS, weights.round(3)))}", flush=True)
else:
    weights = None
    print(f" Distribución Uniforme - Todas las zonas igual probabilidad", flush=True)

def esperar_sistema():
    """Espera activa hasta que el caché y el backend estén listos"""
    print(f" Verificando conexión con el ecosistema en {URL_CACHE}...", flush=True)
    intentos = 0
    while True:
        try:
            res = requests.get(f"{URL_CACHE}/consulta/q1/Z1?confidence_min=0.0", timeout=2)
            if res.status_code == 200:
                print(f" Sistema en línea (intento {intentos + 1}). Iniciando ráfaga...\n", flush=True)
                return True
        except requests.exceptions.ConnectionError:
            pass
        except Exception as e:
            print(f"  Error inesperado: {e}", flush=True)
        
        intentos += 1
        if intentos % 10 == 0:
            print(f" Aún esperando... ({intentos} intentos)", flush=True)
        time.sleep(3)

def seleccionar_zona():
    """Selecciona zona según la distribución configurada"""
    if DISTRIBUCION == "zipf":
        return np.random.choice(ZONAS, p=weights)
    else:
        return random.choice(ZONAS)

def generar_parametros():
    """Genera parámetros de consulta con MUCHA variabilidad"""
    if CONFIDENCE_VARIATION == "fixed":
        conf = CONFIDENCE_FIXED
    else:
        # 100 valores posibles (0.00 a 0.99) en vez de 10
        conf = round(random.uniform(0.0, 0.99), 2)
    
    # 10 valores de bins en vez de 3
    bins = random.choice([2, 3, 5, 7, 10, 12, 15, 20, 25, 30])
    return conf, bins

# ============================================
# BLOQUE PRINCIPAL
# ============================================
if __name__ == "__main__":
    esperar_sistema()

    print(f"  Iniciando {TOTAL_CONSULTAS} consultas ", flush=True)
    print(f"   Distribución: {DISTRIBUCION.upper()}", flush=True)
    print(f"   Variación confidence: {CONFIDENCE_VARIATION}", flush=True)
    print(f"   Sleep entre consultas: {SLEEP_ENTRE_CONSULTAS}s", flush=True)
    print("-" * 60, flush=True)

    tiempo_inicio = time.time()
    consultas_exitosas = 0
    consultas_fallidas = 0
    
    for i in range(1, TOTAL_CONSULTAS + 1):
        try:
            q = random.choice(CONSULTAS)
            z = seleccionar_zona()
            conf, bins = generar_parametros()

            if q == "q4":
                z_b = random.choice([zona for zona in ZONAS if zona != z])
                url = f"{URL_CACHE}/consulta/{q}/{z}/{z_b}?confidence_min={conf}"
            elif q == "q5":
                url = f"{URL_CACHE}/consulta/{q}/{z}?bins={bins}"
            else:
                url = f"{URL_CACHE}/consulta/{q}/{z}?confidence_min={conf}"
            
            t_inicio = time.time()
            res = requests.get(url, timeout=5)
            t_respuesta = (time.time() - t_inicio) * 1000
            
            if res.status_code == 200:
                consultas_exitosas += 1
            else:
                consultas_fallidas += 1
            
            if i % 100 == 0 or i == 1:
                print(f"[{i}/{TOTAL_CONSULTAS}] {q.upper()} en {z} | "
                      f"Conf: {conf} | HTTP {res.status_code} | "
                      f"⏱️  {t_respuesta:.0f}ms", flush=True)
            
            time.sleep(SLEEP_ENTRE_CONSULTAS)
            
        except requests.exceptions.Timeout:
            consultas_fallidas += 1
            print(f"[{i}/{TOTAL_CONSULTAS}]  TIMEOUT en {q} {z}", flush=True)
        except requests.exceptions.ConnectionError:
            consultas_fallidas += 1
            print(f"[{i}/{TOTAL_CONSULTAS}]  CONNECTION ERROR", flush=True)
            time.sleep(1)
        except Exception as e:
            consultas_fallidas += 1
            print(f"[{i}/{TOTAL_CONSULTAS}]  Error: {e}", flush=True)
            time.sleep(0.5)

    tiempo_total = time.time() - tiempo_inicio
    print("\n" + "=" * 60)
    print(" SIMULACIÓN TERMINADA")
    print("=" * 60)
    print(f" Total consultas:       {TOTAL_CONSULTAS}")
    print(f" Exitosas:              {consultas_exitosas}")
    print(f" Fallidas:              {consultas_fallidas}")
    print(f"  Tiempo total:          {tiempo_total:.2f}s")
    print(f" Throughput promedio:   {consultas_exitosas/tiempo_total:.2f} consultas/s")
    print(f" Tasa de éxito:         {(consultas_exitosas/TOTAL_CONSULTAS)*100:.1f}%")
    print("=" * 60)
    print("\n Contenedor en espera (CTRL+C para salir)...", flush=True)
    
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        print("\n Generador detenido manualmente.", flush=True)
