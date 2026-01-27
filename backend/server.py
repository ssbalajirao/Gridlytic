import fastf1
from flask import Flask, jsonify, request
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
cached_session = None
cached_bounds = None
cached_driver_metadata = None
cached_race_start_time = None


def get_track_shape_once():
    global cached_track_map

    if cached_track_map is None:
        print("[PHASE 3] Loading  Geometry for the first time...")

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
            norm_y = 1000 - (((row.Y - y_min)/(y_max - y_min)) * 1000)

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


def initialize_session():
    global cached_session, cached_bounds, cached_driver_metadata
    if cached_session is None:
        print("initializing session data......")
        cached_session = fastf1.get_session(2025, 'Silverstone', 'R')
        cached_session.load(telemetry=True, weather=False)

        global cached_race_start_time
        if cached_race_start_time is None:
            cached_race_start_time = cached_session.laps['LapStartTime'].min()



        # getting bounds
        track_info = get_track_shape_once()
        cached_bounds = track_info['bounds']

        cached_driver_metadata = {}
        for _, res in cached_session.results.iterrows():
            cached_driver_metadata[str(res['DriverNumber'])] = {
                "color": f"#{res['TeamColor']}" if not pd.isna(res['TeamColor']) else "#FFFFFF",
                "name": res['FullName']
            }
        print("Session initialized successfully!")
    return cached_session, cached_bounds, cached_driver_metadata

# function to get driver position at a pertivular time 


def get_driver_position_at_time(driver_number, target_time):
    session, bounds, driver_metadata = initialize_session()

    try:
        driver_laps = session.laps.pick_drivers(driver_number)

        if len(driver_laps) == 0:
            return None
        

        telemetry  = driver_laps.get_telemetry()

        if len(telemetry) == 0:
            return None
    # Calculate time delta from race start

        telemetry = telemetry.copy()
        telemetry['TimeDelta'] = (
            telemetry['Time'] - cached_race_start_time
        ).dt.total_seconds()

    # Find the telemetry point closest to our target time
        closest_idx = (telemetry['TimeDelta'] - target_time).abs().idxmin()
        point = telemetry.loc[closest_idx]

    # Normalize coordinates to 1000x1000 grid (same as track outline)
        dot_x = ((point['X'] - bounds['x_min']) / (bounds['x_max'] - bounds['x_min'])) * 1000
        dot_y = 1000 - (((point['Y'] - bounds['y_min']) / (bounds['y_max'] - bounds['y_min'])) * 1000)

        return {
            "x":round(dot_x, 1),
            "y":round(dot_y, 1),
            "speed": round(point['Speed'], 1) if 'Speed' in point else 0,
            "time_delta":float(point['TimeDelta'])
        }
    except Exception as e:
        print(f"Error getting position for driver {driver_number} at time {target_time}: {e}")
        return None



# creating a function to get race data
def get_f1_data():

    # getting cached data from the other two functions

    session, bounds, driver_metadata = initialize_session()

    



    # result = session.results

    target_lap = 1
    race_laps = session.laps.pick_laps(target_lap)
    driversList = []
    for index, row in race_laps.iterrows():
        # 1. Standardize the driver number variable name
        driver_number = str(row['DriverNumber'])
        # 2. Set default values outside the try block to avoid UnboundLocalError
        dot_x, dot_y = 0, 0
        team_color = "#FFFFFF"
        full_name = row.get('Driver', 'Unknown')
        try:
            driver_lap = session.laps.pick_drivers(driver_number).pick_laps(target_lap)
            
            if len(driver_lap) > 0:
                # ← CHANGE: Get starting position instead of ending position
                raw_telemetry = driver_lap.get_telemetry().iloc[0]  # First point instead of last
                
                # Scale coordinates
                dot_x = ((raw_telemetry['X'] - bounds['x_min']) / (bounds['x_max'] - bounds['x_min'])) * 1000
                dot_y = 1000 - (((raw_telemetry['Y'] - bounds['y_min']) / (bounds['y_max'] - bounds['y_min'])) * 1000)
            

            team_color = driver_metadata.get(driver_number, {}).get("color", "#FFFFFF")
            full_name = driver_metadata.get(driver_number, {}).get("name", row.get('Driver', 'Unknown'))
            
        except Exception as e:
            print(f"Warning: Could not get position for driver {driver_number}: {e}")
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
            "driverName": full_name,
            "teamcolor": team_color,
            "tireCompound": str(row.get('Compound', 'SOFT')),
            "gapToLeader": clean_gap,
            "lapPercentage": 0.0,
            "x":round(dot_x, 1), #sending normalised x and y to front end 
            "y":round(dot_y, 1)
        }
        driversList.append(driverData)
    return driversList


@app.route('/app/race/Live', methods=['GET'])
def get_live_positions():
    try:
        elapsed_time = float(request.args.get('elapsed', 0))

        session, bounds, driver_metadata = initialize_session()


        avg_lap_time = 90
        current_lap = min(int(elapsed_time / avg_lap_time) + 1, 52)  # Silverstone has ~52 laps

        # fetching all the drivers from the session 
        drivers_List = []
        all_drivers = session.results['DriverNumber'].unique()

        # looping thriugh each driver position at a given time

        for driver_num in all_drivers:
            driver_number = str(driver_num)

            position_data = get_driver_position_at_time(driver_number, elapsed_time)

            if position_data:
                team_color = driver_metadata.get(driver_number, {}).get("color", "#FFFFFF")
                full_name = driver_metadata.get(driver_number, {}).get("name", f"Driver {driver_number}")

                # trying to get current lap info and tire compound

                try:
                    driver_laps = session.laps.pick_drivers(driver_number)
                    current_driver_lap = 1

                    for _, lap_row in driver_laps.iterrows():
                        lap_time = (lap_row['LapStartTime'] - driver_laps.iloc[0]['LapStartTime']).total_seconds()
                        if lap_time <= elapsed_time:
                            current_driver_lap = int(lap_row['LapNumber'])
                        else:
                            break

                    # getting tyre compound of the current lap 
                    current_lap_data = driver_laps[driver_laps['LapNumber'] == current_driver_lap]
                    tire_compound = 'UNKOWN'
                    if len(current_lap_data) > 0:
                        tire_compound = str(current_lap_data.iloc[0].get('Compound','UNKNOWN'))
                except:
                    tire_compound = 'UNKNOWN'
                    current_driver_lap = current_lap
                
                # Driver data object

                drivers_List.append({
                    "id": driver_number,
                    "driverName": full_name,
                    "teamcolor": team_color,
                    "tireCompound": tire_compound,
                    "x": position_data['x'],  # ← Normalized coordinates for SVG
                    "y": position_data['y'],
                    "speed": position_data.get('speed', 0),
                    "currentLap": current_driver_lap
                })
        
        drivers_List.sort(key=lambda d: d.get('speed', 0), reverse=True)

        for idx, driver in enumerate(drivers_List):
            driver['position'] = idx + 1
            driver['gapToLeader'] = f"+{idx * 0.5:.1f}s" if idx > 0 else "LAP"
        
        return jsonify({
            "status": "success",
            "currentLap": current_lap,
            "elapsedTime": elapsed_time,
            "drivers": drivers_List
        })
    except Exception as e:
        print("ERROR in live endpoint:")
        print(traceback.format_exc())
        return jsonify({"status": "error", "message": str(e)}), 500






# =======================================================================================================#
# Define the API Endpoint this will get test data 
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
                "currentLap": 1,
                "totalLaps": 52,
                "flagStatus": "GREEN",
                "trackName": "Silverstone"
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