import fastf1
from flask import Flask, jsonify
from flask_cors import CORS # 1. Import CORS

# 2. Initialize the Flask App
app = Flask(__name__)

# 3. Initialize CORS: Allow requests from all origins (for development only)
# This prevents the browser from blocking your React app's requests
CORS(app) 

# preload the cache data from fast f1
fastf1.Cache.enable_cache('./fastf1_cache');


# creating a function to get race data
def get_f1_data():
    session = fastf1.get_session(2024, 'Monaco', 'R')
    session.load(telemetry=False, weather=False)

    result  = session.results
    driversList = []

    for index, row in result.iterrows():
        driverData = {
            "id": row['DriverNumber'],
            "position": row['Position'],
            "driverName": row['FullName'],
            "teamcolor": f"#{row['TeamColor']}",
            "tireCompound": "SOFT",
            "gapToLeader": str(row['Time']).split('days')[-1].strip() if str(row['Time']) != 'NaT' else "LAP",
            "lapPercentage": 0.0
        }
        driversList.append(driverData)
    return driversList


    # Example function to fetch some F1 data using fastf1
    # This is just a placeholder; you can expand it as needed
# 4. Define the API Endpoint
# Route: /api/test
@app.route('/api/test', methods=['GET'])




def raceData():
    try:
        data = get_f1_data()
        return jsonify({
            "status": "success",
            "session": {
                "currentLap": 78,
                "totalLaps": 78,
                "flagStatus": "GREEN", # Static for now
                "trackName": "Monaco"
            },
            "drivers": data
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500 
    

# 5. Run the application
if __name__ == '__main__':
    # Flask runs on http://127.0.0.1:5000 by default
    # debug=True automatically reloads the server on code changes
    app.run(debug=True, port=5000)