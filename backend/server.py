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

        session = fastf1.get_session(2024, 'Monaco', 'R')
        session.load(telemetry=True, weather=False)

        # getting the fastest lap and its telemetry
        fastest_lap = session.laps.pick_fastest()
        telemetry = fastest_lap.get_telemetry()

        # getting track points
        track_points = []
        for _, row in telemetry.iloc[::20].iterrows():  
            track_points.append({
                "x": float(row['X']),
                "y": float(row['Y'])
            })
        cached_track_map = track_points
        print("[PHASE 3] Map loaded successfully!")
    
    return cached_track_map  # Fixed: return the map instead of calling function again

# creating a function to get race data
def get_f1_data():
    session = fastf1.get_session(2024, 'Monaco', 'R')
    session.load(telemetry=True, weather=False)

    result = session.results
    driversList = []

    for index, row in result.iterrows():
        driverData = {
            "id": str(row['DriverNumber']),  # Convert to string for safety
            "position": int(row['Position']) if not pd.isna(row['Position']) else 0,
            "driverName": row['FullName'],
            "teamcolor": f"#{row['TeamColor']}" if not pd.isna(row['TeamColor']) else "#FFFFFF",
            "tireCompound": "SOFT",
            "gapToLeader": str(row['Time']).split('days')[-1].strip() if str(row['Time']) != 'NaT' else "LAP",
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