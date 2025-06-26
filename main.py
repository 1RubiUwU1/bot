from flask import Flask, request
import requests
import os

app = Flask(__name__)

WEBHOOK_URL = "https://discord.com/api/webhooks/1387516322941894686/EwHdpFHRis-BkgFLh7f9tHUBUB3REd_-qcr9yHgT4aaZu3CSs0NhH266LBAOmB8cKftB"  # ← cambia esto con tu webhook real

@app.route("/enviar", methods=["GET"])
def enviar():
    mensaje = request.args.get("mensaje", "Mensaje vacío")
    contenido = {
        "content": mensaje,
        "username": "Webhook desde Flask"
    }

    try:
        resp = requests.post(WEBHOOK_URL, json=contenido)
        if resp.status_code == 204:
            print("✅ Mensaje enviado correctamente a Discord.")
            return "Mensaje enviado correctamente a Discord.", 200
        else:
            print(f"❌ Error al enviar mensaje. Código: {resp.status_code}")
            print(resp.text)
            return f"Error al enviar mensaje a Discord: {resp.status_code}", 500
    except Exception as e:
        print("❌ Excepción:", str(e))
        return "Excepción al enviar mensaje a Discord.", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
