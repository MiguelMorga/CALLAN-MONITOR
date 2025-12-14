# ======================================
# IMPORTS
# ======================================
from datetime import datetime
import os
import time
import re
import json
import paramiko
from dotenv import load_dotenv

# CARGA DE CREDENCIALES

load_dotenv()

SSH_USERNAME = os.getenv("SSH_USERNAME")
SSH_PASSWORD = os.getenv("SSH_PASSWORD")


# ======================================
# CDU JSON (IPs)
# ======================================
with open("callans.json", "r") as f:
    data = json.load(f)

ips_asignadas = {int(k): v for k, v in data["callans"].items()}


# ======================================
# ESPERA DE PROMPT SSH
# ======================================
def esperar_prompt(canal, texto_esperado, timeout=30):
    salida = ""
    canal.settimeout(timeout)
    tiempo_inicio = time.time()

    while True:
        if time.time() - tiempo_inicio > timeout:
            raise TimeoutError(f"Timeout esperando: {texto_esperado}")

        if canal.recv_ready():
            salida += canal.recv(1024).decode("utf-8", errors="ignore")
            if texto_esperado in salida:
                return salida

        time.sleep(0.1)


# ======================================
# comando show cdu health 
# ======================================
def extraer_detalle_warning(salida_warning):
    lineas = salida_warning.splitlines()
    detalle = []
    exclude_phrases = ["show cdu health", "RScmCli#", "Completion Code: Success"]

    for linea in lineas:
        linea_strip = linea.strip()
        if not linea_strip or linea_strip in exclude_phrases:
            continue
        if linea_strip.endswith(":"):
            continue
        detalle.append(linea_strip)

    return detalle


# ======================================
# Temperaturas y Health Status
# ======================================
def obtener_temperaturas_callan(ip, numero_callan):
    temperaturas = {}
    detalle_warning = []

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        print(f"Conectando a CALLAN {numero_callan}")
        ssh.connect(ip, username=SSH_USERNAME, password=SSH_PASSWORD)
        canal = ssh.invoke_shell()

        esperar_prompt(canal, "RScmCli#", 30)

        canal.send("show cdu health\n")
        salida = esperar_prompt(canal, "RScmCli#", 10)

        if "Health: OK" in salida:
            estado_salud = "OK"
        else:
            estado_salud = "Warning"
            detalle_warning = extraer_detalle_warning(salida)

        canal.send("start cdu serial session\n")
        esperar_prompt(canal, "HRU {admin}>", 30)

        canal.send("sensor show 3001 4\n")
        salida = esperar_prompt(canal, "Degrees", 10)
        match = re.search(r"(\d+(?:\.\d+)?)\s+Degrees", salida)
        temperaturas["supply"] = float(match.group(1)) if match else "No encontrado"

        canal.send("sensor show 3001 55\n")
        salida = esperar_prompt(canal, "Degrees", 10)
        match = re.search(r"(\d+(?:\.\d+)?)\s+Degrees", salida)
        temperaturas["aire"] = float(match.group(1)) if match else "No encontrado"

        ssh.close()

    except Exception as e:
        print(f"Error conectando o ejecutando comandos en IP {ip}: {e}")
        temperaturas = None
        estado_salud = "No evaluado"

    return temperaturas, estado_salud, detalle_warning


# ======================================
# Genera log txt
# ======================================
def guardar_resultados_txt(resultados, estados_salud, detalles_warning):
    ahora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    user_home = os.path.expanduser("~")
    escritorio = (
        os.path.join(user_home, "Escritorio")
        if os.path.exists(os.path.join(user_home, "Escritorio"))
        else os.path.join(user_home, "Desktop")
    )

    carpeta_resultados = os.path.join(escritorio, "Diagnostico Callans", ahora)
    os.makedirs(carpeta_resultados, exist_ok=True)

    archivo_txt = os.path.join(
        carpeta_resultados, f"temperaturas_callan_{ahora}.txt"
    )

    with open(archivo_txt, "w") as f:
        f.write("Resultados de temperaturas por Callan:\n\n")

        f.write("Temperatura supply\n")
        f.write("\t".join([f"CLLN{i}" for i in range(1, 13)]) + "\n")
        f.write("\t".join(
            str(resultados[i]["supply"]) if resultados[i] else "No encontrado"
            for i in range(1, 13)
        ) + "\n\n")

        f.write("Temperatura aire\n")
        f.write("\t".join([f"CLLN{i}" for i in range(1, 13)]) + "\n")
        f.write("\t".join(
            str(resultados[i]["aire"]) if resultados[i] else "No encontrado"
            for i in range(1, 13)
        ) + "\n\n")

        f.write("Estado de salud\n\n")
        for i in range(1, 13):
            f.write(f"Callan {i}: {estados_salud.get(i, 'No evaluado')}\n\n")
            if estados_salud.get(i) == "Warning":
                for linea in detalles_warning.get(i, []):
                    f.write(f"  {linea}\n")
                f.write("\n")

    print(f"Log guardado en:\n{archivo_txt}")


# ======================================
# Main
# ======================================
if __name__ == "__main__":
    resultados = {}
    estados_salud = {}
    detalles_warning = {}

    for i in range(1, 13):
        ip = ips_asignadas[i]
        resultado, estado, detalle = obtener_temperaturas_callan(ip, i)
        resultados[i] = resultado
        estados_salud[i] = estado
        if estado == "Warning":
            detalles_warning[i] = detalle

    guardar_resultados_txt(resultados, estados_salud, detalles_warning)

    input("\nPresiona Enter para salir...")
