from flask import Flask, request, jsonify
from flask_cors import CORS
import requests  # * Para enviar el mensaje al webhook de Discord

app = Flask(__name__)
CORS(app)  # habilita CORS para todos los dominios

# ! Reemplaza con tu webhook real de Discord
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1406707343542190112/zUuMvY2ZytelLwyLqq8oq_D-AHxlh4-gYR4M8nim_qxcgoZdRrG0iEKgaJ2zKoYgoYIk"

@app.route("/enviar", methods=["GET"])
def enviar():
    noti = request.args.get("noti")
    
    if noti:
        # * Enviar a Discord
        data = {"content": f"📢 Notificación recibida: {noti}"}
        try:
            r = requests.post(DISCORD_WEBHOOK_URL, json=data)
            r.raise_for_status()  # ! Valida si hubo error
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

        return jsonify({"success": True, "mensaje": f"Notificación enviada a Discord: {noti}"})
    else:
        return jsonify({"success": False, "error": "Falta parámetro 'noti'"}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
