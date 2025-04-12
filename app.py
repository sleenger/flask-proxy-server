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

    # Define bbox around point (5km radius approx)
    offset = 0.05
    bbox = [[lon - offset, lat - offset], [lon + offset, lat + offset]]

    url = "https://api.openrouteservice.org/pois"
    headers = {
        "Authorization": "5b3ce3597851110001cf6248b0d2d44302c042159f34a1ef0a4dd629",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    body = {
        "request": "pois",
        "geometry": {
            "bbox": bbox,
            "geojson": {
                "type": "Point",
                "coordinates": [lon, lat]
            },
            "buffer": 2000  # 2km radius
        },
        "filters": {
            "category_ids": [211, 213, 214, 216]
        }
    }

    try:
        response = requests.post(url, json=body, headers=headers)
        data = response.json()

        features = data.get("features", [])
        hospitals = []

        for feature in features:
            props = feature.get("properties", {})
            geom = feature.get("geometry", {})
            hospitals.append({
                "name": props.get("name", "Unknown"),
                "category_ids": props.get("category_ids", []),
                "coordinates": geom.get("coordinates", []),
            })

        return jsonify({
            "latitude": lat,
            "longitude": lon,
            "poi_count": len(hospitals),
            "hospitals": hospitals
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
