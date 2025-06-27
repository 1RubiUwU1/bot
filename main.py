from flask import Flask, request
import requests

app = Flask(__name__)

WEBHOOK_URL = "https://discord.com/api/webhooks/1387516322941894686/EwHdpFHR-qcr9yHgT4aaZu3CSs0NhH266LBAOmB8cKftB"

@app.route("/enviar", methods=["GET"])
def enviar():
    mensaje = request.args.get("mensaje", "Mensaje vacío desde GET")

    contenido = {
        "content": mensaje,
        "username": "Webhook desde GET"
    }

    resp = requests.post(WEBHOOK_URL, json=contenido)
    return "✅ Mensaje enviado a Discord via GET", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
