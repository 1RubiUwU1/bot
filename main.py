from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # habilita CORS para todos los dominios

@app.route("/enviar", methods=["GET"])
def enviar():
    noti = request.args.get("noti")
    
    if noti:
        return jsonify({"success": True, "mensaje": f"Notificación recibida: {noti}"})
    else:
        return jsonify({"success": False, "error": "Falta parámetro 'noti'"}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
