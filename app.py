from flask import Flask, request, jsonify
import os
import requests
from arduino_cloud import ArduinoCloudManager

app = Flask(__name__)

cloud = ArduinoCloudManager(
    DEVICE_ID="eb98aa4d-d5a6-4a70-ae83-b17caa3a9b45",
    client_id="eb98aa4d-d5a6-4a70-ae83-b17caa3a9b45",
    SECRET_KEY="0uLCbI77!WwbZ?cHd?Sm6A0qC"
)
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

@app.route('/get-poi', methods=['POST'])
def get_poi():
    try:
        data = request.get_json()
        lat = data.get('latitude')
        lon = data.get('longitude')

        headers = {
            'Authorization': '5b3ce3597851110001cf6248b0d2d44302c042159f34a1ef0a4dd629',
            'Content-Type': 'application/json'
        }

        # Step 1: Get POIs
        query = {
            "request": "pois",
            "geometry": {
                "geojson": {
                    "type": "Point",
                    "coordinates": [lon, lat]
                },
                "buffer": 2000
            },
            "filters": {
                "category_ids": [206, 202]  # 206 = hospital, 202 = clinic
            }
        }

        ors_url = "https://api.openrouteservice.org/pois"
        response = requests.post(ors_url, headers=headers, json=query)

        pois = response.json().get("features", []) if response.status_code == 200 else []
        hospitals = []

        # Step 2: Collect potential hospital POIs
        for poi in pois:
            props = poi.get("properties", {})
            category_ids = props.get("category_ids", [])
            if "206" in category_ids or "202" in category_ids:
                hospitals.append({
                    "name": props.get("osm_tags", {}).get("name", "Unknown"),
                    "lat": poi.get("geometry", {}).get("coordinates", [])[1],
                    "lon": poi.get("geometry", {}).get("coordinates", [])[0],
                })

        # Step 3: Limit to top 10 by straight-line distance (just for speed)
        hospitals = sorted(hospitals, key=lambda x: ((x['lat'] - lat)**2 + (x['lon'] - lon)**2))[:10]

        # Step 4: Calculate road distance for each hospital
        for hospital in hospitals:
            directions_url = "https://api.openrouteservice.org/v2/directions/driving-car"
            coords = [[lon, lat], [hospital["lon"], hospital["lat"]]]
            body = {"coordinates": coords}

            dir_res = requests.post(directions_url, headers=headers, json=body)
            if dir_res.status_code == 200:
                dist = dir_res.json()['routes'][0]['summary']['distance']
                hospital["distance"] = round(dist, 2)  # in meters
            else:
                hospital["distance"] = float('inf')  # fallback if error

        # Step 5: Sort by actual road distance
        hospitals_sorted = sorted(hospitals, key=lambda x: x['distance'])

        return jsonify({
            "latitude": lat,
            "longitude": lon,
            "poi_count": len(hospitals_sorted),
            "hospitals": hospitals_sorted
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
def estimate_fallback_speed(road_type):
    if road_type in ["residential", "living_street", "service"]:
        return 30
    elif road_type in ["tertiary", "tertiary_link"]:
        return 40
    elif road_type in ["secondary", "secondary_link"]:
        return 50
    elif road_type in ["primary", "primary_link"]:
        return 60
    elif road_type in ["motorway", "motorway_link"]:
        return 80
    else:
        return 35  # default fallback


def get_osm_speed_limit(lat, lon):
    overpass_url = "https://overpass-api.de/api/interpreter"
    query = f"""
    [out:json][timeout:25];
    way(around:100, {lat}, {lon})["highway"];
    out tags;
    """
    try:
        response = requests.post(overpass_url, data=query)
        data = response.json()
        for element in data["elements"]:
            tags = element.get("tags", {})
            if "maxspeed" in tags:
                return float(tags["maxspeed"]), tags.get("highway", "")
        # No maxspeed but road_type found
        if data["elements"]:
            return None, data["elements"][0]["tags"].get("highway", "")
    except Exception as e:
        print("Overpass API error:", e)
    return None, None


def get_ors_estimated_speed(lat, lon):
    try:
        url = "https://api.openrouteservice.org/v2/directions/driving-car"
        headers = {
            "Authorization": "5b3ce3597851110001cf6248b0d2d44302c042159f34a1ef0a4dd629",
            "Content-Type": "application/json"
        }
        body = {
            "coordinates": [[lon, lat], [lon + 0.001, lat + 0.001]]
        }
        res = requests.post(url, headers=headers, json=body)
        data = res.json()
        summary = data["features"][0]["properties"]["summary"]
        distance = summary["distance"] / 1000
        duration = summary["duration"] / 3600
        speed = distance / duration
        return round(speed, 1)
    except Exception as e:
        print("ORS speed fallback error:", e)
        return None


@app.route('/get-smart-speed-limit', methods=['POST'])
def get_smart_speed_limit():
    content = request.get_json()
    lat = content.get("latitude")
    lon = content.get("longitude")

    if lat is None or lon is None:
        return jsonify({"error": "latitude and longitude are required"}), 400

    speed_limit, road_type = get_osm_speed_limit(lat, lon)

    if speed_limit:
        source = "overpass"
    else:
        speed_limit = get_ors_estimated_speed(lat, lon)
        source = "ors"
        if speed_limit is None and road_type:
            speed_limit = estimate_fallback_speed(road_type)
            source = f"fallback ({road_type})"
        elif speed_limit is None:
            speed_limit = 35
            source = "default fallback"

    return jsonify({
        "latitude": lat,
        "longitude": lon,
        "estimated_speed_limit": speed_limit,
        "source": source
    })

if __name__ == '__main__':
    app.run(debug=True)
