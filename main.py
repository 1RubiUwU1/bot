from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# 🔧 Configuración Supabase
SUPABASE_URL = "https://jpxsagtewdfgsonymkyq.supabase.co"
SUPABASE_KEY = "sb_publishable_6_SSZ04-cPNaqqyorFgxHA_qqmiaPc2"
SUPABASE_TABLE = "users"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# 🔍 Buscar por ID
@app.route("/buscar", methods=["POST"])
def buscar_usuario():
    data = request.get_json()
    user_id = data.get("id")

    if not user_id:
        return jsonify({"error": "Falta el ID"}), 400

    url = f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}?ID=eq.{user_id}"
    res = requests.get(url, headers=HEADERS)

    if res.status_code == 200 and res.json():
        return jsonify(res.json()[0]), 200
    else:
        return jsonify({"mensaje": "No encontrado"}), 404

# 🔐 Login con validación de VCM
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    user_id = data.get("id")
    clave = data.get("clave")

    if not user_id or not clave:
        return jsonify({"error": "ID y CLAVE requeridos"}), 400

    url = f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}?ID=eq.{user_id}&CLAVE=eq.{clave}"
    res = requests.get(url, headers=HEADERS)

    if res.status_code == 200 and res.json():
        usuario = res.json()[0]
        vcm = usuario.get("VCM")
        estado = "activo"

        if vcm:
            hoy = datetime.utcnow().date()
            fecha_vcm = datetime.strptime(vcm, "%Y-%m-%d").date()
            if fecha_vcm <= hoy:
                estado = "vencido"

        return jsonify({
            "user": usuario.get("USER"),
            "vcm": vcm,
            "estado": estado
        }), 200
    else:
        return jsonify({"mensaje": "Credenciales inválidas"}), 401

# ✏️ Editar la fecha VCM
@app.route("/editar_vcm", methods=["POST"])
def editar_vcm():
    data = request.get_json()
    user_id = data.get("id")
    nueva_fecha = data.get("vcm")  # formato: YYYY-MM-DD

    if not user_id or not nueva_fecha:
        return jsonify({"error": "ID y nueva fecha requeridos"}), 400

    url = f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}?ID=eq.{user_id}"
    payload = {"VCM": nueva_fecha}

    res = requests.patch(url, json=payload, headers=HEADERS)

    if res.status_code == 204:
        return jsonify({"mensaje": "VCM actualizado"}), 200
    else:
        return jsonify({"error": "Error al actualizar VCM"}), 500

# 🆕 Crear nuevo usuario
@app.route("/crear", methods=["POST"])
def crear_usuario():
    data = request.get_json()
    campos = ["ID", "USER", "VCM", "CLAVE"]

    # ! Validar que todos los campos estén presentes
    if not all(key in data for key in campos):
        return jsonify({"error": "Faltan campos requeridos"}), 400

    url = f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}"
    res = requests.post(url, json=data, headers=HEADERS)

    if res.status_code in [200, 201]:
        return jsonify({"mensaje": "Usuario creado"}), 201
    else:
        return jsonify({"error": "No se pudo crear el usuario"}), 500

# 🚀 Ejecutar el servidor
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
