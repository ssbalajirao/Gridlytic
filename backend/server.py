import fastf1
from flask import Flask, jsonify
from flask_cors import CORS
import traceback
import pandas as pd

# Initialize the Flask App
app = Flask(__name__)

# Initialize CORS: Allow requests from all origins (for development only)
CORS(app) 

# preload the cache data from fast f1
fastf1.Cache.enable_cache('./fastf1_cache')

# creating a function to get track shape by fetching fastest lap
cached_track_map = None

def get_track_shape_once():
    global cached_track_map

    if cached_track_map is None:
        print("[PHASE 3] Loading Monaco Geometry for the first time...")

        session = fastf1.get_session(2025, 'Silverstone', 'R')
        session.load(telemetry=True, weather=False)

        # getting the fastest lap and its telemetry to get the outline of the map
        fastest_lap = session.laps.pick_fastest()
        telemetry = fastest_lap.get_telemetry().iloc[::2]

        # finding bound to determine track outlines
        x_min, x_max = telemetry['X'].min(), telemetry['X'].max()
        y_min, y_max = telemetry['Y'].min(), telemetry['Y'].max()
        # getting track points


        # Calculation of point to make grid

        path_parts = []

        for i, row in enumerate(telemetry.itertuples()):
            norm_x = ((row.X - x_min) / (x_max - x_min)) * 1000
            norm_y = ((row.Y - y_min)/(y_max - y_min)) * 1000

            # Path building
            command = "M" if i == 0 else "L"
            path_parts.append(f"{command} {norm_x:.1f} {norm_y:.1f}")

        path_parts.append("Z")
        padding = 50
        cached_track_map = {
            "svgPath":" ".join(path_parts),
            "viewBox":f"{-padding} {-padding} {1000 + (padding * 2)} {1000 + (padding * 2)}",
            "bounds": {
                "x_min": float(x_min), "x_max": float(x_max),
                "y_min": float(y_min), "y_max": float(y_max)
            }
        }
        print("Geometry engine is ready")

    
    return cached_track_map  # Fixed: return the map instead of calling function again

# creating a function to get race data
def get_f1_data():
    session = fastf1.get_session(2025, 'Silverstone', 'R')
    session.load(telemetry=True, weather=False)

    result = session.results
    driversList = []

    for index, row in result.iterrows():
        gap_str = str(row['Time'])

            # 2. APPLY THE CLEANING LOGIC HERE
        if gap_str == 'NaT' or 'days' not in gap_str:
            clean_gap = "LAP"
        else:
                # Trims "0 days 00:00:15.554000" to "00:00:15"
            clean_gap = gap_str.split('days')[-1].split('.')[0].strip()
        driverData = {
            "id": str(row['DriverNumber']),  # Convert to string for safety
            "position": int(row['Position']) if not pd.isna(row['Position']) else 0,
            "driverName": row['FullName'],
            "teamcolor": f"#{row['TeamColor']}" if not pd.isna(row['TeamColor']) else "#FFFFFF",
            "tireCompound": "SOFT",
            "gapToLeader": clean_gap,
            "lapPercentage": 0.0
        }
        driversList.append(driverData)
    return driversList

# Define the API Endpoint
@app.route('/api/test', methods=['GET'])
def raceData():
    try:
        print("Fetching F1 data...")
        data = get_f1_data()
        print(f"Got {len(data)} drivers")
        
        # getting race track data 
        print("Fetching track map...")
        race_track = get_track_shape_once()  # Fixed: actually call the function
        print(f"Got track map with {len(race_track) if race_track else 0} points")
        
        return jsonify({
            "status": "success",
            "session": {
                "currentLap": 78,
                "totalLaps": 78,
                "flagStatus": "GREEN",
                "trackName": "Monaco"
            },
            "drivers": data,
            "track_map": race_track
        })
    except Exception as e:
        print("ERROR occurred:")
        print(traceback.format_exc())
        return jsonify({"status": "error", "message": str(e)}), 500 


# 5. Run the application
if __name__ == '__main__':
    # Flask runs on http://127.0.0.1:5000 by default
    # debug=True automatically reloads the server on code changes
    app.run(debug=True, port=5000)