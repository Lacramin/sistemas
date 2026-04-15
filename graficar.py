import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('metricas/registro_50mb_lru.csv')

hits = df[df['evento'] == 'hit']['t_res']
misses = df[df['evento'] == 'miss']['t_res']

plt.figure(figsize=(8, 6))
plt.boxplot([hits, misses], labels=['Hits (Caché)', 'Misses (Backend)'])
plt.ylabel('Tiempo de respuesta (segundos)')
plt.title('Comparación de Latencia: Hits vs Misses')
plt.yscale('log') 
plt.grid(True, which="both", ls="--", alpha=0.5)
plt.savefig('grafico_latencia.png')
plt.close()

hit_rate = len(hits) / len(df) * 100
miss_rate = 100 - hit_rate

plt.figure(figsize=(6, 6))
plt.pie([hit_rate, miss_rate], labels=['Hits', 'Misses'], autopct='%1.1f%%', startangle=90, colors=['#4CAF50', '#F44336'])
plt.title(f'Tasa de Aciertos (Hit Rate Total: {hit_rate:.1f}%)')
plt.savefig('grafico_hitrate.png')
plt.close()

print("Graficos creados: grafico_latencia.png y grafico_hitrate.png")
