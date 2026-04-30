import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
from glob import glob

os.makedirs("metricas/graficos", exist_ok=True)

experimentos = []
archivos = sorted(glob("metricas/*.csv"))

for archivo in archivos:
    nombre = os.path.basename(archivo).replace(".csv", "")
    if 'registro_metricas' in nombre:
        continue
    try:
        df = pd.read_csv(archivo)
        df.columns = df.columns.str.strip()
        df['evento'] = df['evento'].astype(str).str.strip().str.upper()
        df['t_res'] = pd.to_numeric(df['t_res'], errors='coerce')
        
        hits = len(df[df['evento'] == 'HIT'])
        misses = len(df[df['evento'] == 'MISS'])
        total = hits + misses
        
        if total > 0:
            hit_rate = hits / total
            hit_times = df[df['evento'] == 'HIT']['t_res'].dropna()
            miss_times = df[df['evento'] == 'MISS']['t_res'].dropna()
            
            partes = nombre.split("_")
            distribucion = partes[0]
            politica = partes[1]
            memoria = partes[2]
            
            experimentos.append({
                "nombre": nombre,
                "distribucion": distribucion,
                "politica": politica,
                "memoria": memoria,
                "hits": hits,
                "misses": misses,
                "total": total,
                "hit_rate": hit_rate,
                "avg_hit_time": hit_times.mean() if len(hit_times) > 0 else 0,
                "avg_miss_time": miss_times.mean() if len(miss_times) > 0 else 0,
                "p95_hit": hit_times.quantile(0.95) if len(hit_times) > 0 else 0,
                "p95_miss": miss_times.quantile(0.95) if len(miss_times) > 0 else 0
            })
    except Exception as e:
        print(f" Error con {archivo}: {e}")

df_exp = pd.DataFrame(experimentos)

# Ordenar memorias correctamente
orden_memoria = ['10mb', '25mb', '50mb', '200mb', '500mb']
memoria_labels = ['10 MB', '25 MB', '50 MB', '200 MB', '500 MB']

# ============================================
# GRÁFICO 1: Hit Rate comparativo (5 barras)
# ============================================
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

for idx, dist in enumerate(['zipf', 'uniform']):
    ax = axes[idx]
    subset = df_exp[df_exp['distribucion'] == dist]
    
    x = np.arange(len(orden_memoria))
    width = 0.35
    
    lru_data = []
    lfu_data = []
    for mem in orden_memoria:
        lru_val = subset[(subset['politica'] == 'lru') & (subset['memoria'] == mem)]
        lfu_val = subset[(subset['politica'] == 'lfu') & (subset['memoria'] == mem)]
        lru_data.append(lru_val['hit_rate'].values[0] * 100 if len(lru_val) > 0 else 0)
        lfu_data.append(lfu_val['hit_rate'].values[0] * 100 if len(lfu_val) > 0 else 0)
    
    ax.bar(x - width/2, lru_data, width, label='LRU', color='#3498db')
    ax.bar(x + width/2, lfu_data, width, label='LFU', color='#e74c3c')
    
    # Agregar valores encima de las barras
    for i, (v1, v2) in enumerate(zip(lru_data, lfu_data)):
        ax.text(i - width/2, v1 + 1, f'{v1:.1f}', ha='center', fontsize=8)
        ax.text(i + width/2, v2 + 1, f'{v2:.1f}', ha='center', fontsize=8)
    
    ax.set_xlabel('Memoria')
    ax.set_ylabel('Hit Rate (%)')
    ax.set_title(f'Hit Rate - Distribución {dist.upper()}')
    ax.set_xticks(x)
    ax.set_xticklabels(memoria_labels)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    ax.set_ylim(0, 100)

plt.tight_layout()
plt.savefig('metricas/graficos/hit_rate_comparativo.png', dpi=300)
plt.close()
print("Gráfico 1: Hit Rate comparativo")

# ============================================
# GRÁFICO 2: Latencias promedio
# ============================================
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

for idx, dist in enumerate(['zipf', 'uniform']):
    for jdx, pol in enumerate(['lru', 'lfu']):
        ax = axes[idx][jdx]
        subset = df_exp[(df_exp['distribucion'] == dist) & (df_exp['politica'] == pol)]
        
        x = np.arange(len(orden_memoria))
        width = 0.35
        
        hit_times = []
        miss_times = []
        for mem in orden_memoria:
            hit_val = subset[subset['memoria'] == mem]
            hit_times.append(hit_val['avg_hit_time'].values[0] * 1000 if len(hit_val) > 0 else 0)
            miss_times.append(hit_val['avg_miss_time'].values[0] * 1000 if len(hit_val) > 0 else 0)
        
        ax.bar(x - width/2, hit_times, width, label='Hit', color='#2ecc71')
        ax.bar(x + width/2, miss_times, width, label='Miss', color='#e74c3c')
        
        ax.set_xlabel('Memoria')
        ax.set_ylabel('Latencia promedio (ms)')
        ax.set_title(f'{dist.upper()} - {pol.upper()}')
        ax.set_xticks(x)
        ax.set_xticklabels(memoria_labels)
        ax.legend()
        ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('metricas/graficos/latencia_comparativa.png', dpi=300)
plt.close()
print("Gráfico 2: Latencia comparativa")

# ============================================
# GRÁFICO 3: Tabla resumen
# ============================================
fig, ax = plt.subplots(figsize=(16, 10))
ax.axis('tight')
ax.axis('off')

tabla_data = []
for _, row in df_exp.iterrows():
    tabla_data.append([
        row['nombre'],
        f"{row['total']}",
        f"{row['hit_rate']*100:.1f}%",
        f"{row['avg_hit_time']*1000:.2f} ms",
        f"{row['avg_miss_time']*1000:.2f} ms",
        f"{row['p95_hit']*1000:.2f} ms"
    ])

columnas = ['Experimento', 'Total', 'Hit Rate', 'Lat. Hit Avg', 'Lat. Miss Avg', 'P95 Hit']
table = ax.table(cellText=tabla_data, colLabels=columnas, 
                 cellLoc='center', loc='center',
                 colWidths=[0.22, 0.08, 0.10, 0.14, 0.14, 0.14])
table.auto_set_font_size(False)
table.set_fontsize(8)
table.scale(1.2, 1.6)

plt.title('Resumen de Experimentos - Tarea 1 Sistemas Distribuidos', fontsize=14, pad=20)
plt.tight_layout()
plt.savefig('metricas/graficos/tabla_resumen.png', dpi=300, bbox_inches='tight')
plt.close()
print("Gráfico 3: Tabla resumen")

# ============================================
# EXPORTAR CSV
# ============================================
df_exp.to_csv('metricas/resumen_experimentos.csv', index=False)
print(" CSV resumen exportado: metricas/resumen_experimentos.csv")

# ============================================
# RESUMEN EN CONSOLA
# ============================================
print("\n" + "=" * 80)
print("RESUMEN DE LOS 20 EXPERIMENTOS")
print("=" * 80)
print(f"\n{'Experimento':30s} | {'Hit Rate':>8s} | {'Hits':>6s} | {'Misses':>6s} | {'Total':>6s}")
print("-" * 70)
for _, row in df_exp.iterrows():
    print(f"{row['nombre']:30s} | {row['hit_rate']*100:7.1f}% | {row['hits']:5d} | {row['misses']:5d} | {row['total']:5d}")

print("\n" + "=" * 80)
print("TOP 5 MEJORES HIT RATES")
print("=" * 80)
top5 = df_exp.nlargest(5, 'hit_rate')[['nombre', 'hit_rate', 'avg_hit_time']]
for _, row in top5.iterrows():
    print(f"  {row['nombre']:30s} | {row['hit_rate']*100:.1f}% | Hit: {row['avg_hit_time']*1000:.2f} ms")

print("\n TOP 5 PEORES HIT RATES")
print("=" * 80)
bottom5 = df_exp.nsmallest(5, 'hit_rate')[['nombre', 'hit_rate', 'avg_hit_time']]
for _, row in bottom5.iterrows():
    print(f"  {row['nombre']:30s} | {row['hit_rate']*100:.1f}% | Hit: {row['avg_hit_time']*1000:.2f} ms")

print("\n COMPARACIÓN ZIPF vs UNIFORM:")
zipf_avg = df_exp[df_exp['distribucion'] == 'zipf']['hit_rate'].mean() * 100
uniform_avg = df_exp[df_exp['distribucion'] == 'uniform']['hit_rate'].mean() * 100
print(f"  Zipf promedio:    {zipf_avg:.1f}%")
print(f"  Uniform promedio: {uniform_avg:.1f}%")
print(f"  Diferencia:       {zipf_avg - uniform_avg:.1f} puntos")

print("\n COMPARACIÓN LRU vs LFU:")
lru_avg = df_exp[df_exp['politica'] == 'lru']['hit_rate'].mean() * 100
lfu_avg = df_exp[df_exp['politica'] == 'lfu']['hit_rate'].mean() * 100
print(f"  LRU promedio: {lru_avg:.1f}%")
print(f"  LFU promedio: {lfu_avg:.1f}%")
print(f"  Diferencia:   {lfu_avg - lru_avg:.1f} puntos")
