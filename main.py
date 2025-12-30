import os
from flask import Flask, request, jsonify, Response

from flask_cors import CORS
import requests
import re
import mysql.connector
from num2words import num2words

app = Flask(__name__)
CORS(app)

# -----------------------
# CONFIGURACIÓN BASE DE DATOS
# -----------------------
DB_CONFIG = {
    "host": "144.91.102.20",
    "port": 3306,
    "user": "u1298_SpdTD27pzK",
    "password": "ujPvBqd0@p.@m+jN=PQDG9vn",
    "database": "s1298_inka_ride"
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

# -----------------------
# DISCORD Y GOOGLE SCRIPT
# -----------------------
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
URL = "https://raw.githubusercontent.com/skrifna4-lab/base/refs/heads/main/db.txt"
exel = "https://script.google.com/macros/s/AKfycbxQVjyF32GLYkBYIwI0XbIVKL4oDXZPva0gL0U_9ADKPpj_IlFhB-wEks3j0dwMioMP/exec"

def subir_comentario(nombre, monto):
    data = {"nombre": nombre, "monto": monto}
    try:
        response = requests.post(exel, data=data)
        print("Respuesta Google:", response.text)
    except Exception as e:
        print("Error al enviar:", str(e))

def pufificador(msg):
    try:
        regex = r"-\s*(.+?)\s+te envió un pago por S/\s*([\d.]+)"
        match = re.search(regex, msg, re.IGNORECASE)
        if match:
            return match.group(1).strip(), match.group(2).strip()
        simple = re.search(r"Yape\s+([A-Za-zÁÉÍÓÚÑ.\s]+)\s+([\d.]+)", msg, re.IGNORECASE)
        if simple:
            return simple.group(1).strip(), simple.group(2).strip()
        return None, None
    except:
        return None, None

def monto_a_palabras(monto_str):
    try:
        monto = float(monto_str)
        entero = int(monto)
        decimales = round((monto - entero) * 100)
        partes = []
        if entero == 0:
            partes.append("cero")
        elif entero == 1:
            partes.append("un sol")
        else:
            partes.append(f"{num2words(entero, lang='es')} soles")
        if decimales > 0:
            partes.append(f"con {num2words(decimales, lang='es')} céntimos")
        return " ".join(partes)
    except Exception as e:
        print("Error en monto_a_palabras:", e)
        return f"{monto_str} soles"

# -----------------------
# FUNCIONES DE BASE DE DATOS
# -----------------------
def registrar_pago(nombre, monto):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pagos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(255),
            monto DECIMAL(10,2),
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Evitar duplicados por nombre y monto exacto
    cursor.execute("SELECT * FROM pagos WHERE nombre=%s AND monto=%s", (nombre, monto))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return False  # Ya existe
    cursor.execute("INSERT INTO pagos (nombre, monto) VALUES (%s, %s)", (nombre, monto))
    conn.commit()
    cursor.close()
    conn.close()
    return True

def verificar_pago(nombre, monto):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pagos WHERE nombre=%s AND monto=%s", (nombre, monto))
    resultado = cursor.fetchone()
    cursor.close()
    conn.close()
    return bool(resultado)

# -----------------------
# ENDPOINT PRINCIPAL DE YAPE
# -----------------------
@app.route("/yape", methods=["GET"])
def notificar():
    noti = request.args.get("noti")
    if not noti:
        return jsonify({"success": False, "error": "Falta parámetro 'noti'"}), 400

    a = noti.split("|")
    b = a[1]

    # Mandar mensaje a Discord siempre
    data = {"content": f"📢 Notificación recibida: {noti}"}
    try:
        r = requests.post(DISCORD_WEBHOOK_URL, json=data)
        r.raise_for_status()
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

    if b == "com.bcp.innovacxion.yapeapp":
        nombre, monto = pufificador(noti)
        if nombre and monto:
            registrado = registrar_pago(nombre, monto)
            if registrado:
                subir_comentario(nombre, monto)
                texto = f"Hola, {nombre} ya pagó {monto_a_palabras(monto)}"
            else:
                texto = f"Hola, {nombre} ya había realizado este pago previamente"

            try:
                requests.get(f"https://pc.skrifna.uk/decir?text={texto}")
            except Exception as e:
                print("Error al llamar a /decir:", e)

    return jsonify({"success": True, "mensaje": "NOTI SUBIDA :v"})

# -----------------------
# ENDPOINT PARA VERIFICAR PAGO
# -----------------------
@app.route("/verificar_pago", methods=["GET"])
def verificar():
    nombre = request.args.get("nombre")
    monto = request.args.get("monto")
    if not nombre or not monto:
        return jsonify({"success": False, "error": "Faltan parámetros 'nombre' o 'monto'"}), 400

    existe = verificar_pago(nombre, monto)
    return jsonify({"success": True, "existe": existe, "mensaje": f"{nombre} {'ya pagó' if existe else 'no ha pagado'}"})

TARGET = "http://may1.soymaycol.icu:10002"

# Proxy genérico: captura cualquier ruta

@app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
def proxy(path):
    try:
        url = f"{TARGET}/{path}"

        headers = {k: v for k, v in request.headers if k.lower() != "host"}

        resp = requests.request(
            method=request.method,
            url=url,
            headers=headers,
            params=request.args,
            data=request.get_data(),
            cookies=request.cookies,
            stream=True
        )

        response = Response(resp.raw, status=resp.status_code)
        excluded_headers = ['content-encoding', 'transfer-encoding', 'connection']
        for key, value in resp.headers.items():
            if key.lower() not in excluded_headers:
                response.headers[key] = value

        return response

    except requests.exceptions.RequestException as e:
        return {"error": "No se pudo conectar al servidor", "details": str(e)}, 500

TARGET_P2 = "http://185.16.39.160:5026"
TARGET_ROOT = "https://skrifna.uk/"

# Proxy para /p2/
@app.route("/p2/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
def proxy_p2(path):
    try:
        url = f"{TARGET_P2}/{path}"
        headers = {k: v for k, v in request.headers if k.lower() != "host"}

        resp = requests.request(
            method=request.method,
            url=url,
            headers=headers,
            params=request.args,
            data=request.get_data(),
            cookies=request.cookies,
            stream=True
        )

        response = Response(resp.raw, status=resp.status_code)
        excluded_headers = ['content-encoding', 'transfer-encoding', 'connection']
        for key, value in resp.headers.items():
            if key.lower() not in excluded_headers:
                response.headers[key] = value

        return response

    except requests.exceptions.RequestException as e:
        return {"error": "No se pudo conectar al servidor P2", "details": str(e)}, 500

# Página raíz cargada directamente desde skrifna.uk
@app.route("/", methods=["GET"])
def root():
    try:
        resp = requests.get(TARGET_ROOT, stream=True)
        response = Response(resp.raw, status=resp.status_code)
        excluded_headers = ['content-encoding', 'transfer-encoding', 'connection']
        for key, value in resp.headers.items():
            if key.lower() not in excluded_headers:
                response.headers[key] = value
        return response
    except requests.exceptions.RequestException as e:
        return {"error": "No se pudo cargar la página principal", "details": str(e)}, 500

# Evitar errores con favicon
@app.route("/favicon.ico")
def favicon():
    return "", 204
# -----------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)




