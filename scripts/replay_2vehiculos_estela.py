import traci
import csv
import math
import time
import sumolib

# 1. Cargar red
net = sumolib.net.readNet('mi_mapa.net.xml')

# 2. Config SUMO (pasos de 0.05s para movimiento fluido)
cfg = """<configuration>
  <input><net-file value="mi_mapa.net.xml"/></input>
  <time><begin value="0"/><end value="40"/><step-length value="0.05"/></time>
</configuration>"""
with open("replay.sumo.cfg", "w") as f:
    f.write(cfg)

# 3. Leer CAMs y convertir a coordenadas X/Y
def leer_csv(archivo):
    rows = []
    with open(archivo, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            lat = float(row['lat']) / 1e7
            lon = float(row['lon']) / 1e7
            x, y = net.convertLonLat2XY(lon, lat)
            rows.append({"t": float(row['time']), "x": x, "y": y})
    return rows

veh1 = leer_csv("cam_veh1.csv")
veh2 = leer_csv("cam_veh2.csv")
print(f"📦 veh1: {len(veh1)} CAMs, veh2: {len(veh2)} CAMs")

# 4. Iniciar SUMO-GUI
print("🎬 Abriendo SUMO-GUI...")
traci.start(["sumo-gui", "-c", "replay.sumo.cfg", "--start", "--delay", "15"])

# Configurar vista
view_id = traci.gui.getIDList()[0]
traci.gui.setSchema(view_id, "real world")
traci.gui.setZoom(view_id, 2000)

# Crear tipo de vehículo grande para que se vea bien
traci.vehicletype.copy("DEFAULT_VEHTYPE", "veh_grande")
traci.vehicletype.setLength("veh_grande", 6.0)
traci.vehicletype.setWidth("veh_grande", 2.5)

# 5. Crear vehículos sin ruta (para posicionamiento libre)
traci.vehicle.add("veh1_rojo", "", typeID="veh_grande", depart=0)
traci.vehicle.setColor("veh1_rojo", (255, 0, 0, 255))
traci.vehicle.add("veh2_azul", "", typeID="veh_grande", depart=0)
traci.vehicle.setColor("veh2_azul", (0, 100, 255, 255))

for v in ["veh1_rojo", "veh2_azul"]:
    traci.vehicle.setSpeedMode(v, 0)
    traci.vehicle.setLaneChangeMode(v, 0)

# 6. Función de interpolación lineal
def interpolar(datos, t_actual):
    idx = 0
    for i in range(len(datos)-1):
        if datos[i]["t"] <= t_actual <= datos[i+1]["t"]:
            idx = i
            break
    p0 = datos[idx]
    p1 = datos[min(idx+1, len(datos)-1)]
    
    dt = p1["t"] - p0["t"]
    if dt <= 0:
        return p0["x"], p0["y"], 0, 0
    
    # Interpolación matemática
    frac = max(0, min(1, (t_actual - p0["t"]) / dt))
    x = p0["x"] + (p1["x"] - p0["x"]) * frac
    y = p0["y"] + (p1["y"] - p0["y"]) * frac
    
    # Calcular ángulo y velocidad
    dx = p1["x"] - p0["x"]
    dy = p1["y"] - p0["y"]
    dist = math.hypot(dx, dy)
    speed = dist / dt
    angle = (90 - math.degrees(math.atan2(dy, dx))) % 360
    return x, y, angle, speed

# 7. Bucle principal con interpolación y estela
print("=" * 70)
print("🎬 INTERPOLACIÓN + ESTELA DE PUNTOS")
print("=" * 70)

t_max = max(veh1[-1]["t"], veh2[-1]["t"])
t = 0
contador_estela = 0

# Colores de la estela (RGBA: Rojo, Verde, Azul, Alpha/Transparencia)
COLOR_ESTELA_V1 = (255, 0, 0, 120)    # Rojo semitransparente
COLOR_ESTELA_V2 = (0, 100, 255, 120)  # Azul semitransparente
TAMANO_POI = 3.0                       # Tamaño del punto en metros

while t < t_max:
    traci.simulationStep()
    t = traci.simulation.getTime()

    # Interpolar veh1
    x1, y1, a1, s1 = interpolar(veh1, t)
    traci.vehicle.moveToXY("veh1_rojo", "", -1, x1, y1, a1, keepRoute=2)
    traci.vehicle.setSpeed("veh1_rojo", s1)

    # Interpolar veh2
    x2, y2, a2, s2 = interpolar(veh2, t)
    traci.vehicle.moveToXY("veh2_azul", "", -1, x2, y2, a2, keepRoute=2)
    traci.vehicle.setSpeed("veh2_azul", s2)

    # 👈 ESTELA: Agregar un punto cada 0.2 segundos (cada 4 pasos de 0.05s)
    contador_estela += 1
    if contador_estela % 4 == 0: 
        poi_id_v1 = f"estela_v1_{contador_estela}"
        poi_id_v2 = f"estela_v2_{contador_estela}"
        
        # Punto para veh1 (Rojo)
        traci.poi.add(poi_id_v1, x1, y1, COLOR_ESTELA_V1, poiType="estela")
        traci.poi.setWidth(poi_id_v1, TAMANO_POI)
        traci.poi.setHeight(poi_id_v1, TAMANO_POI)
        
        # Punto para veh2 (Azul)
        traci.poi.add(poi_id_v2, x2, y2, COLOR_ESTELA_V2, poiType="estela")
        traci.poi.setWidth(poi_id_v2, TAMANO_POI)
        traci.poi.setHeight(poi_id_v2, TAMANO_POI)

    time.sleep(0.01)

traci.close()
print("\n✅ Reproducción interpolada con estela terminada.")
print(f"   Puntos de estela dibujados: ~{contador_estela // 4} por vehículo")
