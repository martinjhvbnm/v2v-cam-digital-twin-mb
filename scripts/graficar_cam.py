import csv
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# 1. Leer el CSV extraído del pcap
rows = []
with open('cam_data.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        try:
            rows.append({
                'time': float(row['time']),
                'lat': float(row['lat']) / 1e7,
                'lon': float(row['lon']) / 1e7,
            })
        except:
            continue

times = [r['time'] for r in rows]
lats  = [r['lat']  for r in rows]
lons  = [r['lon']  for r in rows]

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dl/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))

# 2. Calcular velocidad (m/s), rumbo, intervalos y aceleración
speeds_ms = [0]      # velocidad en m/s
speeds_kmh = [0]     # velocidad en km/h
headings = [0]
intervals = [0]
accels = [0]         # aceleración en m/s²

for i in range(1, len(times)):
    dt = times[i] - times[i-1]
    d = haversine(lats[i-1], lons[i-1], lats[i], lons[i])
    v_ms = d / dt if dt > 0 else 0
    speeds_ms.append(v_ms)
    speeds_kmh.append(v_ms * 3.6)

    dlat = lats[i] - lats[i-1]
    dlon = lons[i] - lons[i-1]
    headings.append(math.degrees(math.atan2(dlon, dlat)) % 360)

    intervals.append(dt * 1000)

    # Aceleración: diferencia de velocidad / tiempo
    if i >= 2 and dt > 0:
        accels.append((speeds_ms[i] - speeds_ms[i-1]) / dt)
    else:
        accels.append(0)

# Suavizar aceleración con una ventana móvil de 3 puntos (para ver la tendencia)
def suavizar(datos, ventana=3):
    resultado = []
    for i in range(len(datos)):
        inicio = max(0, i - ventana//2)
        fin = min(len(datos), i + ventana//2 + 1)
        resultado.append(np.mean(datos[inicio:fin]))
    return resultado

accels_suave = suavizar(accels, ventana=3)

# 3. Crear las 5 gráficas en layout 3x2
fig, axes = plt.subplots(3, 2, figsize=(16, 14))

# --- 1. Recorrido ---
ax1 = axes[0, 0]
sc = ax1.scatter(lons, lats, c=speeds_kmh, cmap='jet', s=70, edgecolors='black', linewidths=0.5, zorder=5)
ax1.plot(lons, lats, 'k--', alpha=0.4, linewidth=1)
ax1.scatter([lons[0]], [lats[0]], c='lime', s=300, marker='*', zorder=10, edgecolors='black', label='Inicio')
ax1.scatter([lons[-1]], [lats[-1]], c='red', s=200, marker='X', zorder=10, edgecolors='black', label='Fin')
plt.colorbar(sc, ax=ax1, label='Velocidad (km/h)')
ax1.set_xlabel('Longitud (°)')
ax1.set_ylabel('Latitud (°)')
ax1.set_title('1. Recorrido del vehículo (color = velocidad)')
ax1.legend(loc='best')
ax1.grid(True, alpha=0.3)
ax1.set_aspect('equal', adjustable='datalim')

# --- 2. Velocidad vs tiempo ---
ax2 = axes[0, 1]
ax2.plot(times, speeds_kmh, 'o-', color='blue', markersize=6, linewidth=1.5)
ax2.fill_between(times, speeds_kmh, alpha=0.2, color='blue')
ax2.set_xlabel('Tiempo (s)')
ax2.set_ylabel('Velocidad (km/h)')
ax2.set_title('2. Velocidad del vehículo')
ax2.grid(True, alpha=0.3)

# --- 3. Rumbo vs tiempo ---
ax3 = axes[1, 0]
ax3.plot(times, headings, 'o-', color='purple', markersize=6, linewidth=1.5)
ax3.set_xlabel('Tiempo (s)')
ax3.set_ylabel('Rumbo (°)\n[0=N, 90=E, 180=S, 270=W]')
ax3.set_title('3. Rumbo del vehículo')
ax3.set_ylim(-10, 370)
ax3.set_yticks([0, 90, 180, 270, 360])
ax3.grid(True, alpha=0.3)

# --- 4. Aceleración vs tiempo ---
ax4 = axes[1, 1]
ax4.plot(times, accels_suave, '-', color='darkgreen', linewidth=2, label='Aceleración (suavizada)')
ax4.plot(times, accels, 'o', color='green', markersize=4, alpha=0.4, label='Aceleración (cruda)')
ax4.axhline(y=0, color='black', linestyle='-', linewidth=1)
ax4.axhline(y=0.5,  color='orange', linestyle='--', alpha=0.6, label='Umbral ETSI +0.5 m/s')
ax4.axhline(y=-0.5, color='orange', linestyle='--', alpha=0.6, label='Umbral ETSI -0.5 m/s')
ax4.set_xlabel('Tiempo (s)')
ax4.set_ylabel('Aceleración (m/s²)')
ax4.set_title('4. Aceleración del vehículo (+ acelera, − frena)')
ax4.legend(loc='best', fontsize=8)
ax4.grid(True, alpha=0.3)

# --- 5. Intervalos entre CAMs ---
ax5 = axes[2, 0]
ax5.plot(times[1:], intervals[1:], 'o-', color='darkred', markersize=6, linewidth=1.5)
ax5.axhline(y=100,  color='red', linestyle='--', alpha=0.7, label='Mín: 100 ms (10 Hz)')
ax5.axhline(y=1000, color='red', linestyle='--', alpha=0.7, label='Máx: 1000 ms (1 Hz)')
ax5.set_xlabel('Tiempo (s)')
ax5.set_ylabel('Intervalo entre CAMs (ms)')
ax5.set_title('5. Frecuencia de envío de CAM (rango ETSI 1-10 Hz)')
ax5.legend(loc='upper right')
ax5.grid(True, alpha=0.3)
ax5.set_ylim(0, 1100)

# --- 6. Panel de estadísticas (texto) ---
ax6 = axes[2, 1]
ax6.axis('off')
dist_total = sum(haversine(lats[i], lons[i], lats[i+1], lons[i+1]) for i in range(len(lats)-1))
stats_text = (
    f"📊 RESUMEN DEL VEHÍCULO 1\n"
    f"{'=' * 40}\n\n"
    f"Total CAMs capturados: {len(times)}\n"
    f"Duración: {times[-1] - times[0]:.2f} s\n"
    f"Distancia: {dist_total:.1f} m\n\n"
    f"VELOCIDAD\n"
    f"  Mínima:    {min(speeds_kmh[1:]):.1f} km/h\n"
    f"  Máxima:    {max(speeds_kmh):.1f} km/h\n"
    f"  Promedio:  {np.mean(speeds_kmh[1:]):.1f} km/h\n\n"
    f"ACELERACIÓN\n"
    f"  Máx (+):   {max(accels):.2f} m/s²\n"
    f"  Mín (−):   {min(accels):.2f} m/s²\n"
    f"  Cambios >0.5 m/s: {sum(1 for a in accels if abs(a) > 0.5)} veces\n\n"
    f"FRECUENCIA\n"
    f"  Mín:       {min(intervals[1:]):.0f} ms ({1000/min(intervals[1:]):.2f} Hz)\n"
    f"  Máx:       {max(intervals[1:]):.0f} ms ({1000/max(intervals[1:]):.2f} Hz)\n"
    f"  Promedio:  {np.mean(intervals[1:]):.0f} ms ({1000/np.mean(intervals[1:]):.2f} Hz)\n"
)
ax6.text(0.05, 0.95, stats_text, transform=ax6.transAxes,
         fontsize=11, verticalalignment='top', family='monospace',
         bbox=dict(boxstyle='round', facecolor='lightyellow', edgecolor='gray'))

plt.suptitle(f'Análisis completo del vehículo 1 — {len(times)} CAMs capturados en el .pcap',
             fontsize=15, fontweight='bold')
plt.tight_layout()
plt.savefig('graficas_vehiculo.png', dpi=120, bbox_inches='tight')
print("✅ Gráfica guardada: graficas_vehiculo.png")

# 4. Estadísticas por consola
print("\n📊 ESTADÍSTICAS DEL VEHÍCULO 1")
print("=" * 50)
print(f"Total CAMs capturados: {len(times)}")
print(f"Duración total: {times[-1] - times[0]:.2f} s")
print(f"Distancia recorrida: {dist_total:.1f} m")
print(f"\nVelocidad mínima:    {min(speeds_kmh[1:]):.1f} km/h")
print(f"Velocidad máxima:    {max(speeds_kmh):.1f} km/h")
print(f"Velocidad promedio:  {np.mean(speeds_kmh[1:]):.1f} km/h")
print(f"\nAceleración máxima (+): {max(accels):.2f} m/s²")
print(f"Aceleración mínima (−): {min(accels):.2f} m/s²")
print(f"Cambios de velocidad > 0.5 m/s: {sum(1 for a in accels if abs(a) > 0.5)} veces")
print(f"\nIntervalo mínimo:    {min(intervals[1:]):.0f} ms → {1000/min(intervals[1:]):.2f} Hz")
print(f"Intervalo máximo:    {max(intervals[1:]):.0f} ms → {1000/max(intervals[1:]):.2f} Hz")
print(f"Intervalo promedio:  {np.mean(intervals[1:]):.0f} ms → {1000/np.mean(intervals[1:]):.2f} Hz")
