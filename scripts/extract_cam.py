import subprocess, xml.etree.ElementTree as ET

PCAP = "/home/vanet/VaN3Twin/ns-3-dev/v2v-80211p-student-application-0-0.pcap"
res = subprocess.run(["tshark", "-r", PCAP, "-Y", "its", "-T", "pdml"], capture_output=True, text=True)
root = ET.fromstring(res.stdout)

filas = []
for pkt in root.findall(".//packet"):
    datos = {}
    for field in pkt.findall(".//field"):
        nombre = (field.get("name", "") + " " + field.get("showname", "")).lower()
        valor = field.get("show", "").strip()
        
        if "latitude" in nombre:
            datos["lat"] = valor
        elif "longitude" in nombre:
            datos["lon"] = valor
        elif "speedvalue" in nombre or "speed" in nombre:
            datos["speed"] = valor
        elif "headingvalue" in nombre or "heading" in nombre:
            datos["heading"] = valor
        elif "time_relative" in nombre:
            datos["time"] = valor
            
    # Solo guardamos si encontramos los 5 campos clave
    if len(datos) == 5:
        filas.append(datos)

with open("cam_data.csv", "w") as f:
    f.write("time,lat,lon,speed,heading\n")
    for d in filas:
        f.write(f"{d['time']},{d['lat']},{d['lon']},{d['speed']},{d['heading']}\n")

print(f"✅ Se extrajeron {len(filas)} CAMs.")
