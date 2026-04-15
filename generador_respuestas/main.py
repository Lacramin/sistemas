from fastapi import FastAPI

app = FastAPI()

datos_zonas = {
    "Z1": [{"confianza": 0.8, "area": 120}, {"confianza": 0.4, "area": 80}],
    "Z2": [{"confianza": 0.9, "area": 200}, {"confianza": 0.6, "area": 150}],
}

@app.get("/q1/{zona}")
def q1(zona: str, conf_min: float = 0.0):
    data = datos_zonas.get(zona, [])
    total = sum(1 for d in data if d.get("confianza", 0) >= conf_min)
    return {"zona": zona, "count": total}

@app.get("/q2/{zona}")
def q2(zona: str, conf_min: float = 0.0):
    return {"msg": "q2 vacio"}

@app.get("/q3/{zona}")
def q3(zona: str, conf_min: float = 0.0):
    return {"msg": "q3 vacio"}

@app.get("/q4/{zona_a}/{zona_b}")
def q4(zona_a: str, zona_b: str, conf_min: float = 0.0):
    return {"msg": "q4 vacio"}

@app.get("/q5/{zona}")
def q5(zona: str, bins: int = 5):
    return {"msg": "q5 vacio"}
