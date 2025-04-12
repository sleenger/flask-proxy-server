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

    try:
        headers = {
            "Authorization": "5b3ce3597851110001cf6248b0d2d44302c042159f34a1ef0a4dd629"
        }

        response = requests.get(url, headers=headers)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
@app.route('/test', methods=['POST'])
def test():
    data = request.get_json()
    return jsonify({"status": "success", "received": data}), 200

    
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
    latitude = data.get("latitude")
    longitude = data.get("longitude")

    if not latitude or not longitude:
        return jsonify({"error": "latitude and longitude are required"}), 400

    headers = {
        'Authorization': "5b3ce3597851110001cf6248b0d2d44302c042159f34a1ef0a4dd629",
        'Content-Type': 'application/json'
    }

    payload = {
        "request": "pois",
        "geometry": {
            "geojson": {
                "type": "Point",
                "coordinates": [longitude, latitude]
            },
            "buffer": 2500
        },
        "filters": {
            "category_ids": [202, 206]
        }
    }

    try:
        response = requests.post(
            "https://api.openrouteservice.org/pois",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        pois = response.json().get("features", [])
    except Exception as e:
        return jsonify({"error": f"ORS API failed: {str(e)}"}), 500

    hospitals = []

    for feature in pois:
        props = feature.get("properties", {})
        tags = props.get("osm_tags", {})
        coords = feature.get("geometry", {}).get("coordinates", [])
        category_ids = props.get("category_ids", [])

        if 202 in category_ids or 206 in category_ids:
            hospitals.append({
                "name": tags.get("name", "Unknown"),
                "lat": coords[1],
                "lon": coords[0],
                "distance": props.get("distance", -1),
                "address": tags.get("addr:full") or tags.get("addr:street") or tags.get("addr:housename") or "Not Available",
                "phone": tags.get("phone") or tags.get("contact:phone") or "Not Available"
            })

    hospitals.sort(key=lambda x: x["distance"] if x["distance"] != -1 else 999999)
    nearest = hospitals[0] if hospitals else None

    lcd_text = (
        f"Nearest Hospital:\n{nearest['name']}\n"
        f"{int(nearest['distance'])}m away\n{nearest['address']}"
    ) if nearest else "No nearby hospital found"

    return jsonify({
        "hospitals": hospitals,
        "nearest_hospital_lcd": lcd_text
    })

if __name__ == '__main__':
    app.run(debug=True)
