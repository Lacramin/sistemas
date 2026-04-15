from fastapi import FastAPI

from pydantic import BaseModel

import csv, os

from datetime import datetime


app = FastAPI()


class Metrica(BaseModel):

    evento: str

    datos: dict


# Registro CSV 

ARCHIVO = "registro_metricas.csv"


if not os.path.exists(ARCHIVO):

    with open(ARCHIVO, mode="w", newline="") as f:

        csv.writer(f).writerow(["timestamp", "evento", "key", "t_res"])


@app.post("/registrar")

def registrar(m: Metrica):

    ts = datetime.now().isoformat()

    k = m.datos.get("key", "")

    t = m.datos.get("t_res", "")


    with open(ARCHIVO, mode="a", newline="") as f:

        csv.writer(f).writerow([ts, m.evento, k, t])


    # Log consola

    print(f"[{m.evento.upper()}] {m.datos}")

    return {"status": "ok"}
