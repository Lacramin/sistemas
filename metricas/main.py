from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
import csv, os
from datetime import datetime

app = FastAPI()
contador_global = 0

class Metrica(BaseModel):
    evento: str
    datos: dict

ARCHIVO = "registro_metricas.csv"

if not os.path.exists(ARCHIVO):
    with open(ARCHIVO, mode="w", newline="") as f:
        csv.writer(f).writerow(["timestamp", "evento", "key", "t_res"])

@app.post("/registrar")
def registrar(m: Metrica):
    global contador_global
    ts = datetime.now().isoformat()
    k = m.datos.get("key", "")
    t = m.datos.get("t_res", "")

    with open(ARCHIVO, mode="a", newline="") as f:
        escritor = csv.writer(f)
        escritor.writerow([ts, m.evento, k, t])
        f.flush()
    
    contador_global += 1
    print(f" Métrica #{contador_global} recibida: {m.evento} | {k}", flush=True)
    
    return {"status": "ok"}

@app.get("/descargar")
def descargar_csv():
    if os.path.exists(ARCHIVO):
        return FileResponse(ARCHIVO, media_type="text/csv", filename="registro_metricas.csv")
    return {"error": "No hay datos aún"}

@app.get("/stats")
def stats():
    if not os.path.exists(ARCHIVO):
        return {"error": "No hay datos"}
    
    import pandas as pd
    df = pd.read_csv(ARCHIVO)
    hits = len(df[df['evento'] == 'hit'])
    misses = len(df[df['evento'] == 'miss'])
    errores = len(df[df['evento'] == 'error'])
    total = hits + misses
    
    return {
        "total_metricas": len(df),
        "hits": hits,
        "misses": misses,
        "errores": errores,
        "hit_rate": round(hits / total, 4) if total > 0 else 0
    }

@app.get("/reset")
def reset_metrics():
    global contador_global
    contador_global = 0
    if os.path.exists(ARCHIVO):
        os.remove(ARCHIVO)
    with open(ARCHIVO, mode="w", newline="") as f:
        csv.writer(f).writerow(["timestamp", "evento", "key", "t_res"])
    return {"status": "reset_ok"}
