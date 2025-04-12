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

        if "features" not in data or len(data["features"]) == 0:
            return jsonify({"error": "No features found in response"}), 500

        properties = data["features"][0]["properties"]
        segments = properties["segments"][0]

        distance = segments.get("distance", 0)
        duration = segments.get("duration", 0)

        # Estimate speed limit in km/h
        speed_limit = round((distance / duration) * 3.6, 1) if duration > 0 else "N/A"

        return jsonify({
            "latitude": lat,
            "longitude": lon,
            "distance": distance,
            "duration": duration,
            "estimated_speed_limit": speed_limit
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
@app.route('/get-poi', methods=['POST'])
def get_poi():
    data = request.get_json()
    lat = data.get("latitude")
    lon = data.get("longitude")

    if not lat or not lon:
        return jsonify({"error": "latitude and longitude are required"}), 400

    url = "https://api.openrouteservice.org/pois"
    headers = {
        "Authorization": "5b3ce3597851110001cf6248b0d2d44302c042159f34a1ef0a4dd629",
        "Content-Type": "application/json"
    }

    body = {
        "request": "pois",
        "geometry": {
            "bbox": [[lon - 0.01, lat - 0.01], [lon + 0.01, lat + 0.01]],
            "geojson": {
                "type": "Point",
                "coordinates": [lon, lat]
            },
            "buffer": 2000  # meters radius
        },
        "filters": {
            "categories": [ 211 ]  # Category for "Health" / hospitals
        }
    }

    try:
        response = requests.post(url, json=body, headers=headers)
        data = response.json()

        features = data.get("features", [])
        results = []

        for feature in features:
            name = feature["properties"].get("name", "Unknown")
            dist = feature["properties"].get("distance", "N/A")
            category = feature["properties"].get("category_ids", [])
            results.append({
                "name": name,
                "distance": dist,
                "categories": category
            })

        return jsonify({
            "latitude": lat,
            "longitude": lon,
            "poi_count": len(results),
            "hospitals": results
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
