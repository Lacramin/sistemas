from fastapi import FastAPI, Query
import redis, os, requests, json, time

app = FastAPI()

HOST_REDIS = os.getenv("REDIS_HOST", "redis-cache")
URL_RESPUESTAS = os.getenv("RESPUESTAS_URL", "http://generador_respuestas:8000")
URL_METRICAS = os.getenv("METRICAS_URL", "http://metricas:8000")

cliente_redis = redis.Redis(host=HOST_REDIS, port=6379, db=0, decode_responses=True)

def mandar_metrica(tipo, info):
    try:
        requests.post(f"{URL_METRICAS}/registrar", json={"evento": tipo, "datos": info}, timeout=0.2)
    except:
        pass

@app.get("/consulta/{query}/{zona_a}")
def consultar_simple(
    query: str, 
    zona_a: str, 
    confidence_min: float = Query(0.0), 
    bins: int = Query(5)
):
    t0 = time.time()
    
    if query == "q5":
        llave = f"confidence_dist:{zona_a}:bins={bins}"
    elif query == "q1":
        llave = f"count:{zona_a}:conf={confidence_min}"
    elif query == "q2":
        llave = f"area:{zona_a}:conf={confidence_min}"
    elif query == "q3":
        llave = f"density:{zona_a}:conf={confidence_min}"
    else:
        llave = f"{query}:{zona_a}:conf={confidence_min}"
    
    cached = cliente_redis.get(llave)
    if cached:
        mandar_metrica("hit", {"key": llave, "t_res": round(time.time() - t0, 6)})
        return json.loads(cached)
    
    try:
        url_backend = f"{URL_RESPUESTAS}/data/{zona_a}/{query}"
        params = {"confidence_min": confidence_min, "bins": bins}
        
        res = requests.get(url_backend, params=params, timeout=5)
        res.raise_for_status()
        data = res.json()
        
        cliente_redis.setex(llave, 60, json.dumps(data))
        mandar_metrica("miss", {"key": llave, "t_res": round(time.time() - t0, 6)})
        return data

    except Exception as e:
        mandar_metrica("error", {"key": llave, "t_res": round(time.time() - t0, 6)})
        return {"error": "backend_unreachable", "detalle": str(e)}

@app.get("/consulta/{query}/{zona_a}/{zona_b}")
def consultar_doble(
    query: str, 
    zona_a: str, 
    zona_b: str, 
    confidence_min: float = Query(0.0)
):
    t0 = time.time()
    
    llave = f"compare:density:{zona_a}:{zona_b}:conf={confidence_min}"
    
    cached = cliente_redis.get(llave)
    if cached:
        mandar_metrica("hit", {"key": llave, "t_res": round(time.time() - t0, 6)})
        return json.loads(cached)
    
    try:
        url_backend = f"{URL_RESPUESTAS}/data/{zona_a}/{query}"
        params = {"confidence_min": confidence_min, "zona_b": zona_b}
        
        res = requests.get(url_backend, params=params, timeout=5)
        data = res.json()
        
        cliente_redis.setex(llave, 60, json.dumps(data))
        mandar_metrica("miss", {"key": llave, "t_res": round(time.time() - t0, 6)})
        return data
    except Exception as e:
        mandar_metrica("error", {"key": llave, "t_res": round(time.time() - t0, 6)})
        return {"error": "caido", "detalle": str(e)}

@app.get("/health")
def health():
    try:
        cliente_redis.ping()
        return {"status": "ok", "redis": "connected"}
    except:
        return {"status": "degraded", "redis": "disconnected"}
