from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import re
from num2words import num2words  # Para convertir números a palabras

app = Flask(__name__)
CORS(app)  # Habilita CORS para todos los dominios

# ========= CONFIG =========
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
URL = "https://raw.githubusercontent.com/skrifna4-lab/base/refs/heads/main/db.txt"
exel = "https://script.google.com/macros/s/AKfycbxQVjyF32GLYkBYIwI0XbIVKL4oDXZPva0gL0U_9ADKPpj_IlFhB-wEks3j0dwMioMP/exec"
# ==========================

# -----------------------
# Función para subir comentario a Google Script
# -----------------------
def subir_comentario(nombre, monto):
    data = {
        'nombre': nombre,
        'monto': monto,
    }
    try:
        response = requests.post(exel, data=data)
        print("Respuesta Google:", response.text)  # debería mostrar {"success": true}
    except Exception as e:
        print("Error al enviar:", str(e))

# -----------------------
# Función para purificar mensaje Yape
# -----------------------
def pufificador(msg):
    try:
        # Caso estilo YapeApp oficial
        regex = r"-\s*(.+?)\s+te envió un pago por S/\s*([\d.]+)"
        match = re.search(regex, msg, re.IGNORECASE)
        if match:
            nombre = match.group(1).strip()
            monto = match.group(2).strip()
            return nombre, monto

        # Caso simple: "Yape Juan 20"
        simple = re.search(r"Yape\s+([A-Za-zÁÉÍÓÚÑ.\s]+)\s+([\d.]+)", msg, re.IGNORECASE)
        if simple:
            nombre = simple.group(1).strip()
            monto = simple.group(2).strip()
            return nombre, monto

        # Si no coincide con ninguno
        return None, None
    except:
        return None, None

# -----------------------
# Convierte el monto a palabras
# -----------------------
def monto_a_palabras(monto_str):
    """Convierte el monto a palabras: 1->'un sol', 6->'seis soles', etc."""
    try:
        monto = float(monto_str)
        entero = int(monto)
        if entero == 1:
            return "un sol"
        else:
            return f"{num2words(entero, lang='es')} soles"
    except:
        return f"{monto_str} soles"

# -----------------------
# Endpoint principal de Yape
# -----------------------
@app.route("/yape", methods=["GET"])
def notificar():
    """Manda notificación a Discord y llama a /decir si pufificador es exitoso"""
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

    # Si es Yape
    if b == "com.bcp.innovacxion.yapeapp":
        nombre, monto = pufificador(noti)
        if nombre and monto:
            # Subir comentario a Google
            subir_comentario(nombre, monto)

            # Convertir monto a palabras
            monto_palabras = monto_a_palabras(monto)
            texto = f"hola te informo que {nombre} te yapeó {monto_palabras}"

            # Llamar a la API de lectura /decir
            try:
                requests.get(f"https://pc.skrifna.uk/decir?text={texto}")
            except Exception as e:
                print("Error al llamar a /decir:", e)

    return jsonify({"success": True, "mensaje": "NOTI SUBIDA :v"})

# -----------------------
# Función auxiliar: decodifica base64
# -----------------------
import base64
def from_base64(base64_texto: str) -> str:
    return base64.b64decode(base64_texto.encode("utf-8")).decode("utf-8")

# -----------------------
# Función auxiliar: busca cuentas en base remota
# -----------------------
def buscar(plataforma):
    resp = requests.get(URL)
    resultados = []

    for linea in resp.text.splitlines():
        lns = linea.split("|")
        if len(lns) < 3:
            continue  

        try:
            pl = from_base64(lns[0])
            us = from_base64(lns[1])
            cr = from_base64(lns[2])
        except Exception:
            continue  

        if plataforma.lower() == pl.lower():
            if us and cr:
                resultados.append({
                    "plataforma": pl,
                    "usuario": us,
                    "contraseña": cr
                })

    return resultados

# -----------------------
# Endpoint para buscar cuentas
# -----------------------
@app.route("/cuentas", methods=["GET"])
def cuentas():
    """Busca cuentas de la plataforma solicitada"""
    plataforma = request.args.get("plataforma")
    if not plataforma:
        return jsonify({"error": "Falta parámetro 'plataforma'"}), 400

    resultados = buscar(plataforma)
    return jsonify({
        "plataforma": plataforma,
        "total": len(resultados),
        "resultados": resultados
    })

# -----------------------
# Inicia el servidor
# -----------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

