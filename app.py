from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route('/proxy', methods=['GET'])
@app.route('/')
def home():
    return "🚀 Flask Proxy Server is Running!"

def proxy():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "URL parameter is required"}), 400

    headers = {
        "Authorization": f"5b3ce3597851110001cf6248b0d2d44302c042159f34a1ef0a4dd629"
    }

    response = requests.get(url, headers=headers)

    return jsonify(response.json())

if __name__ == '__main__':
    app.run()
