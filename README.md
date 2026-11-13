# V2V CAM Exchange & Digital Twin (Gemelo Digital)

Repositorio de la práctica **Redes Vehiculares y Heterogéneas** — Universidad de Cuenca.
Implementación del estándar **ETSI EN 302 637-2** (CAM) sobre `ns-3` + `SUMO`, y reconstrucción de trayectorias (Gemelo Digital) a partir de archivos `.pcap`.

## Características
1. **Reglas ETSI 1-10 Hz**: Disparadores de Velocidad, Rumbo, Posición y Reloj.
2. **Digital Twin (Gemelo Digital)**: Reconstrucción de la trayectoria de 2 vehículos a partir de los CAMs extraídos de un `.pcap`.
3. **Interpolación Lineal**: Suavizado del movimiento entre CAMs discretos.
4. **Estela Visual (POIs)**: Rastro de puntos que evidencia la interpolación.

## Requisitos
- SUMO 1.12 (`sumo`, `sumo-gui`, `traci`, `sumolib`)
- Python 3.8+
- `tshark` (Wireshark CLI)
- Librerías: `matplotlib`, `numpy`, `pyproj`

## Estructura
- `scripts/replay_2vehiculos_estela.py` -> Script principal del Gemelo Digital (con interpolación y estela).
- `scripts/extract_cam.py` -> Extrae lat/lon de los `.pcap` a `.csv` usando `tshark`.
- `scripts/graficar_cam.py` -> Genera las gráficas de velocidad, rumbo, aceleración y frecuencia.
- `data/` -> Coordenadas extraídas de los CAMs.
- `sumo/` -> Red del Centro Histórico de Cuenca y archivos de configuración.
- `images/` -> Gráficas generadas.

## Ejecución
1. Extraer datos del pcap (si no tienes los CSV):
   `python3 scripts/extract_cam.py`
2. Ejecutar el Gemelo Digital con interpolación:
   `python3 scripts/replay_2vehiculos_estela.py`
3. Generar gráficas:
   `python3 scripts/graficar_cam.py`

## Autor
**Martín Bravo
