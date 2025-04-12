from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

@app.route('/')
def home():
    return '🚀 Flask Proxy Server is Running!'

@app.route('/proxy', methods=['GET'])
def proxy():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "URL parameter is required"}), 400
        
@app.route('/test', methods=['POST'])
def test():
    data = request.get_json()
    return jsonify({"status": "success", "received": data}), 200
    headers = {
        "Authorization": "5b3ce3597851110001cf6248b0d2d44302c042159f34a1ef0a4dd629"
    }

    response = requests.get(url, headers=headers)

    return jsonify(response.json())
@app.route('/get-speed-limit', methods=['POST'])
def get_speed_limit():
    data = request.get_json()
    lat = data.get("latitude")
    lon = data.get("longitude")

    if not lat or not lon:
        return jsonify({"error": "latitude and longitude are required"}), 400

    url = "https://api.openrouteservice.org/v2/directions/driving-car/geojson"
    headers = {
        "Authorization": "5b3ce3597851110001cf6248b0d2d44302c042159f34a1ef0a4dd629",
        "Content-Type": "application/json"
    }
    body = {
        "coordinates": [[lon, lat], [lon + 0.01, lat + 0.01]]
    }

    try:
        response = requests.post(url, json=body, headers=headers)
        data = response.json()

        # Debug: Check if features exist
        if "features" not in data or len(data["features"]) == 0:
            return jsonify({"error": "No features found in response"}), 500

        properties = data["features"][0]["properties"]
        segments = properties["segments"][0]

        # NOTE: OpenRouteService doesn't give actual speed limits here by default!
        # We’ll return segment summary for now (duration, distance)
        return jsonify({
            "latitude": lat,
            "longitude": lon,
            "summary": segments.get("summary", {}),
            "distance": segments.get("distance", "N/A"),
            "duration": segments.get("duration", "N/A")
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
if __name__ == '__main__':
    app.run(debug=True)
