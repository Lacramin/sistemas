import pandas as pd
import matplotlib.pyplot as plt
import requests
import os

# Configuración
CASO = os.getenv("CASO", "zipf_lru_50mb")
URL_METRICAS = os.getenv("URL_METRICAS", "http://localhost:8001")
ARCHIVO_CSV = f"metricas/{CASO}.csv"

# Intentar descargar el CSV desde el servicio de métricas
try:
    print(f" Descargando métricas desde {URL_METRICAS}/descargar...")
    response = requests.get(f"{URL_METRICAS}/descargar", timeout=5)
    if response.status_code == 200:
        os.makedirs("metricas", exist_ok=True)
        with open(ARCHIVO_CSV, "wb") as f:
            f.write(response.content)
        print(f" CSV guardado como {ARCHIVO_CSV}")
    else:
        print(f" No se pudo descargar el CSV. Usando archivo local si existe.")
except Exception as e:
    print(f" Error al descargar: {e}. Usando archivo local si existe.")

# Procesar y graficar
try:
    df = pd.read_csv(ARCHIVO_CSV)
    df.columns = df.columns.str.strip()
    df['evento'] = df['evento'].astype(str).str.strip().str.upper()
    df['t_res'] = pd.to_numeric(df['t_res'], errors='coerce')
    df['t_res'] = df['t_res'].replace(0.0, 0.000001)

    hits = df[df['evento'] == 'HIT']['t_res'].dropna()
    misses = df[df['evento'] == 'MISS']['t_res'].dropna()

    if hits.empty and misses.empty:
        print(f" El archivo {CASO}.csv no tiene datos válidos.")
    else:
        # --- 1. Gráfico Circular (Donut Chart) ---
        plt.figure(figsize=(7, 7))
        hit_count = len(hits)
        miss_count = len(misses)
        total = hit_count + miss_count
        
        labels = ['Hits', 'Misses']
        sizes = [hit_count, miss_count]
        colors = ['#2ecc71', '#e74c3c']
        explode = (0.05, 0)

        plt.pie(sizes, explode=explode, labels=labels, colors=colors,
                autopct='%1.1f%%', shadow=True, startangle=140, 
                pctdistance=0.85, textprops={'fontsize': 12, 'weight': 'bold'})

        centro = plt.Circle((0,0), 0.70, fc='white')
        fig = plt.gcf()
        fig.gca().add_artist(centro)

        plt.title(f'Análisis de Tráfico: {CASO}\n(Total Consultas: {total})', fontsize=14, pad=20)
        plt.axis('equal') 
        plt.tight_layout()
        os.makedirs("metricas", exist_ok=True)
        plt.savefig(f'metricas/grafico_circular_{CASO}.png', dpi=300)
        plt.close()
        print(f" Gráfico circular guardado: metricas/grafico_circular_{CASO}.png")

        # --- 2. Boxplot de Latencia ---
        plt.figure(figsize=(8, 6))
        plt.boxplot([hits, misses], labels=['Hits (Caché)', 'Misses (Backend)'], 
                    patch_artist=True, boxprops=dict(facecolor='#3498db', color='black'))
        plt.ylabel('Tiempo de respuesta (segundos)')
        plt.title(f'Distribución de Latencia ({CASO})')
        plt.yscale('log')
        plt.grid(True, ls="--", alpha=0.6)
        plt.savefig(f'metricas/grafico_latencia_{CASO}.png', dpi=300)
        plt.close()
        print(f" Gráfico de latencia guardado: metricas/grafico_latencia_{CASO}.png")

except Exception as e:
    print(f" Error al procesar el archivo: {e}")
