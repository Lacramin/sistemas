import time, requests, os, random
import numpy as np

URL_CACHE = os.getenv("CACHE_URL", "http://localhost:8003")
zonas = ["Z1", "Z2", "Z3", "Z4", "Z5"]
consultas = ["q1", "q2", "q3", "q5"]

DISTRIBUCION = "zipf" 

# Pre-calculamos pesos Zipf para 5 elementos (a=1.5)
# Esto asegura que Z1 > Z2 > Z3 > Z4 > Z5 estrictamente
weights = [1/(i**1.5) for i in range(1, 6)]
weights /= np.sum(weights) 

time.sleep(5)

while True:
    try:
        q = random.choice(consultas)
        
        if DISTRIBUCION == "zipf":
            z = np.random.choice(zonas, p=weights)
        else:
            z = random.choice(zonas)
            
        url = f"{URL_CACHE}/consulta/{q}/{z}"
        res = requests.get(url)
        
        print(f"[{DISTRIBUCION.upper()}] -> {q.upper()}:{z} | HTTP {res.status_code}")
        time.sleep(0.5)
    except Exception:
        time.sleep(2)
