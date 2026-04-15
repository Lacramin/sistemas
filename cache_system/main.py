from fastapi import FastAPI
import redis, os, requests, json, time

app = FastAPI()

HOST_REDIS = os.getenv("REDIS_HOST", "localhost")
URL_RESPUESTAS = os.getenv("RESPUESTAS_URL", "http://localhost:8002")
URL_METRICAS = os.getenv("METRICAS_URL", "http://localhost:8001")

cliente_redis = redis.Redis(host=HOST_REDIS, port=6379, db=0, decode_responses=True)

def mandar_metrica(tipo, info):
    try:
        requests.post(f"{URL_METRICAS}/registrar", json={"evento": tipo, "datos": info})
    except:
        pass

@app.get("/consulta/{query}/{params}")
def consultar(query: str, params: str):
    t0 = time.time()
    llave = f"{query}:{params}"
    
    cached = cliente_redis.get(llave)
    
    if cached:
        mandar_metrica("hit", {"key": llave, "t_res": time.time() - t0})
        return json.loads(cached)
    
    try:
        res = requests.get(f"{URL_RESPUESTAS}/{query}/{params}")
        data = res.json()
    except Exception as e:
        return {"error": "caido", "detalle": str(e)}
    
    cliente_redis.setex(llave, 60, json.dumps(data))
    mandar_metrica("miss", {"key": llave, "t_res": time.time() - t0})
    
    return data
