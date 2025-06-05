from flask import Flask, request, jsonify
import json

app = Flask(__name__)
archivo_url = 'url_ngrok.json'

@app.route('/actualizar_url', methods=['POST'])
def actualizar_url():
    data = request.get_json()
    url = data.get("url")
    if not url:
        return jsonify({"error": "Falta el campo 'url'"}), 400
    
    with open(archivo_url, 'w') as f:
        json.dump({"url": url}, f)
    return jsonify({"mensaje": "URL actualizada correctamente"}), 200

@app.route('/obtener_url', methods=['GET'])
def obtener_url():
    try:
        with open(archivo_url, 'r') as f:
            data = json.load(f)
        return jsonify(data), 200
    except FileNotFoundError:
        return jsonify({"error": "URL no encontrada"}), 404

if __name__ == '__main__':
    app.run(port=5001)
