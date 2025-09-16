from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import base64

app = Flask(__name__)
CORS(app)  # habilita CORS para todos los dominios

# ========= CONFIG =========
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1406707343542190112/zUuMvY2ZytelLwyLqq8oq_D-AHxlh4-gYR4M8nim_qxcgoZdRrG0iEKgaJ2zKoYgoYIk"
URL = "https://raw.githubusercontent.com/skrifna4-lab/base/refs/heads/main/db.txt"
exel = "https://script.google.com/macros/s/AKfycbxQVjyF32GLYkBYIwI0XbIVKL4oDXZPva0gL0U_9ADKPpj_IlFhB-wEks3j0dwMioMP/exec"
# ==========================
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
   
def pufificador(texto):
    mensaje = texto.split("|")[2]
    info = mensaje.split("-")[1].strip().split("te envió un pago por")
    nombre = info[0].strip()
    monto = info[1].split(".")[0].replace("S/ ", "").strip()

    return nombre, monto

# --- Funciones auxiliares ---
def from_base64(base64_texto: str) -> str:
    """Decodifica base64 a texto normal"""
    return base64.b64decode(base64_texto.encode("utf-8")).decode("utf-8")

def buscar(plataforma):
    """Busca cuentas en la base remota"""
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

# --- RUTAS ---
#📢 Notificación recibida: |com.bcp.innovacxion.yapeapp|Confirmación de Pago - Rosa Espetia T. te envió un pago por S/ 1. El cód. de seguridad es: 313|

@app.route("/enviar", methods=["GET"])
def notificar():
    """Manda notificación a Discord"""
    noti = request.args.get("noti")
    if not noti:
        return jsonify({"success": False, "error": "Falta parámetro 'noti'"}), 400

    noti = "|com.bcp.innovacxion.yapeapp|Confirmaci de Pago - Leisel M. Dolmos A. te envi\u00f3 un pago por S/ 12. El c\u00f3d. de seguridad es: 044|"

    a = noti.split("|")
    b = a[1]
    if (b == "com.bcp.innovacxion.yapeapp"):
        nom, mon = pufificador(noti)
        subir_comentario(nom, mon)
        data = {"content": f"📢 Notificación recibida: {noti}"}
    else:
        data = {"content": f"📢 Notificación recibida: {noti}"}

    try:
        r = requests.post(DISCORD_WEBHOOK_URL, json=data)
        r.raise_for_status()
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

    return jsonify({"success": True, "mensaje": f"Notificación enviada a Discord: {noti}"})


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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
