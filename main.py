import os
import sqlite3 # Importamos SQLite
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import re
from num2words import num2words # Para convertir números a palabras

# Usamos la hora para marcar el registro del pago
from datetime import datetime

app = Flask(__name__)
CORS(app) # Habilita CORS para todos los dominios

# ========= CONFIG =========
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
URL = "https://raw.githubusercontent.com/skrifna4-lab/base/refs/heads/main/db.txt"
exel = "https://script.google.com/macros/s/AKfycbxQVjyF32GLYkBYIwI0XbIVKL4oDXZPva0gL0U_9ADKPpj_IlFhB-wEks3j0dwMioMP/exec"
PAGOS_DB = "pagos.db" # Nombre del archivo de la base de datos de pagos
# ==========================

# -----------------------
# Función para inicializar la base de datos de pagos
# -----------------------
def init_db():
    conn = sqlite3.connect(PAGOS_DB)
    cursor = conn.cursor()
    # Creamos la tabla 'pagos' si no existe
    # El campo 'id' será el identificador único
    # El campo 'nombre' será el nombre del pagador (como llega de Yape)
    # El campo 'monto' será el monto del pago
    # El campo 'fecha' será la marca de tiempo del registro
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pagos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            monto REAL NOT NULL,
            fecha TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# -----------------------
# Función para registrar un pago en la base de datos
# -----------------------
def registrar_pago(nombre, monto):
    try:
        conn = sqlite3.connect(PAGOS_DB)
        cursor = conn.cursor()
        # Insertamos el nuevo pago con la fecha actual
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO pagos (nombre, monto, fecha) VALUES (?, ?, ?)",
            (nombre, float(monto), fecha_actual)
        )
        conn.commit()
        conn.close()
        print(f"Pago registrado en {PAGOS_DB}: {nombre} - S/ {monto}")
        return True
    except Exception as e:
        print(f"Error al registrar pago en DB: {e}")
        return False

# -----------------------
# Función para verificar si un pago existe en la base de datos
# -----------------------
def verificar_pago_db(nombre, monto):
    """Busca en la DB si existe un pago con ese nombre y monto."""
    try:
        conn = sqlite3.connect(PAGOS_DB)
        cursor = conn.cursor()
        
        # Utilizamos parámetros en la consulta para evitar inyección SQL
        # Buscamos un pago que coincida exactamente con el nombre y el monto
        cursor.execute(
            "SELECT * FROM pagos WHERE nombre = ? AND monto = ?",
            (nombre, float(monto))
        )
        
        resultado = cursor.fetchone()
        conn.close()
        
        # Devuelve True si encontró un registro, False si no
        return resultado is not None
    except Exception as e:
        print(f"Error al verificar pago en DB: {e}")
        return False


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
        print("Respuesta Google:", response.text) # debería mostrar {"success": true}
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
def monto_a_palabras(monto_str):
    """Convierte un monto tipo '12.50' a palabras: 'doce soles con cincuenta céntimos'"""
    try:
        monto = float(monto_str)
        entero = int(monto)
        decimales = round((monto - entero) * 100) # parte decimal como entero (0-99)

        partes = []

        # Parte entera
        if entero == 0:
            partes.append("cero")
        elif entero == 1:
            partes.append("un sol")
        else:
            partes.append(f"{num2words(entero, lang='es')} soles")

        # Parte decimal
        if decimales > 0:
            partes.append(f"con {num2words(decimales, lang='es')} céntimos")

        return " ".join(partes)
    except Exception as e:
        print("Error en monto_a_palabras:", e)
        return f"{monto_str} soles"

# -----------------------
# Endpoint principal de Yape
# -----------------------
@app.route("/yape", methods=["GET"])
def notificar():
    """Manda notificación a Discord, registra el pago y llama a /decir si pufificador es exitoso"""
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
        # Si falla Discord, seguimos con la lógica de Yape
        print(f"Advertencia: Error al enviar a Discord: {e}")

    # Si es Yape
    if b == "com.bcp.innovacxion.yapeapp":
        nombre, monto = pufificador(noti)
        if nombre and monto:
            # 1. Registrar pago en pagos.db
            registrar_pago(nombre, monto)
            
            # 2. Subir comentario a Google
            subir_comentario(nombre, monto)

            # 3. Notificación de voz
            monto_palabras = monto_a_palabras(monto)
            texto = f"hola te informo que {nombre} te yapeó {monto_palabras}"

            try:
                # Llamar a la API de lectura /decir
                requests.get(f"https://pc.skrifna.uk/decir?text={texto}")
            except Exception as e:
                print("Error al llamar a /decir:", e)

    return jsonify({"success": True, "mensaje": "NOTI SUBIDA :v"})


# -----------------------
# NUEVO ENDPOINT: Verificar si un pago existe
# -----------------------
@app.route("/verificar_pago", methods=["GET"])
def verificar_pago():
    """Verifica si un pago con un nombre y monto específicos ya existe en la DB."""
    nombre = request.args.get("nombre")
    monto = request.args.get("monto")
    
    if not nombre or not monto:
        return jsonify({
            "success": False, 
            "error": "Faltan parámetros: 'nombre' o 'monto'"
        }), 400

    # Limpiamos el nombre por si hay espacios extra
    nombre = nombre.strip()
    
    # Intentamos convertir el monto a número para asegurar la verificación
    try:
        float(monto)
    except ValueError:
        return jsonify({
            "success": False, 
            "error": "El 'monto' debe ser un número válido"
        }), 400
        
    # Verificar en la base de datos
    existe = verificar_pago_db(nombre, monto)
    
    if existe:
        # Pagar ya existe
        # Llamar a la API de lectura /decir con la confirmación
        texto_confirmacion = f"Pago de {nombre} por {monto_a_palabras(monto)} ya se encuentra registrado. Ya pagó."
        try:
            requests.get(f"https://pc.skrifna.uk/decir?text={texto_confirmacion}")
        except Exception as e:
            print("Error al llamar a /decir para confirmación:", e)

        return jsonify({
            "success": True,
            "existe": True,
            "mensaje": f"P ya pagó. Pago de {nombre} por S/ {monto} ya registrado."
        })
    else:
        # Pago no existe
        return jsonify({
            "success": True,
            "existe": False,
            "mensaje": f"Pago de {nombre} por S/ {monto} NO encontrado."
        })


# -----------------------
# Función auxiliar: decodifica base64 (Mantenidas de tu código original)
# -----------------------
import base64
def from_base64(base64_texto: str) -> str:
    return base64.b64decode(base64_texto.encode("utf-8")).decode("utf-8")

# -----------------------
# Función auxiliar: busca cuentas en base remota (Mantenidas de tu código original)
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
# Endpoint para buscar cuentas (Mantenidas de tu código original)
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
    init_db() # Inicializa la base de datos de pagos al iniciar
    app.run(host="0.0.0.0", port=8080)
