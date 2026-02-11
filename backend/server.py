import fastf1
from flask import Flask, jsonify, request
from flask_cors import CORS
import traceback
import pandas as pd
import threading

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
cached_telemetry_ranges = {}
cached_driver_telemetry = {}
session_lock = threading.Lock()

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
            x_range = x_max - x_min
            y_range = y_max - y_min
            if x_range == 0 or y_range == 0:
                # Use default normalization or skip
                return cached_track_map

            # Then use these ranges in your calculations
            norm_x = ((row.X - x_min) / x_range) * 1000
            norm_y = 1000 - (((row.Y - y_min) / y_range) * 1000)

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

    
    return cached_track_map  


def initialize_session():
    global cached_session, cached_bounds, cached_driver_metadata
    with session_lock:
        if cached_session is None:
            print("initializing session data......")
            cached_session = fastf1.get_session(2025, 'Silverstone', 'R')
            cached_session.load(telemetry=True, weather=False)

            global cached_race_start_time
            if cached_race_start_time is None:
                cached_race_start_time = cached_session.laps['LapStartTime'].min()
                print(f"Race start time: {cached_race_start_time}")



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

# function to get driver position at a particular time 
def get_driver_position_at_time(driver_number, target_time, session, bounds):
    global cached_telemetry_ranges, cached_driver_telemetry
    
    try:
        driver_laps = session.laps.pick_drivers(driver_number)

        if len(driver_laps) == 0:
            return None
        
        # Check if we already have telemetry for this driver
        if driver_number in cached_driver_telemetry:
            driver_telemetry = cached_driver_telemetry[driver_number]
            if target_time < 5:
                print(f"    📊 Using cached telemetry for driver {driver_number}: {len(driver_telemetry)} points")
        else:
            # Try to get all telemetry at once (bulk method)
            try:
                driver_telemetry = driver_laps.get_telemetry()
                if target_time < 5:
                    print(f"    📊 Got telemetry for driver {driver_number}: {len(driver_telemetry)} points (bulk)")
            except Exception as tel_error:
                # Fallback to lap-by-lap if bulk fails
                if target_time < 5:
                    print(f"    ⚠️ Failed to get telemetry in bulk for driver {driver_number}, trying lap by lap")
                
                all_telemetry = []
                for _, lap in driver_laps.iterrows():
                    try:
                        lap_tel = lap.get_telemetry()
                        if len(lap_tel) > 0:
                            all_telemetry.append(lap_tel)
                    except Exception as lap_error:
                        continue

                if not all_telemetry:
                    if target_time < 5:
                        print(f"    ❌ No telemetry data for driver {driver_number}")
                    return None
                
                driver_telemetry = pd.concat(all_telemetry, ignore_index=True)
                if target_time < 5:
                    print(f"    📊 Got telemetry lap-by-lap for driver {driver_number}: {len(driver_telemetry)} points")
            
            # Cache the telemetry after fetching
            cached_driver_telemetry[driver_number] = driver_telemetry

        if len(driver_telemetry) == 0:
            return None
        
        # Calculate time delta from race start
        driver_telemetry = driver_telemetry.copy()
        driver_telemetry['TimeDelta'] = (
            driver_telemetry['Time'] - cached_race_start_time
        ).dt.total_seconds()

        # Cache the telemetry range for this driver
        if driver_number not in cached_telemetry_ranges:
            min_time = driver_telemetry['TimeDelta'].min()
            max_time = driver_telemetry['TimeDelta'].max()
            cached_telemetry_ranges[driver_number] = (min_time, max_time)
            print(f"📊 Driver {driver_number}: Telemetry from {min_time:.1f}s to {max_time:.1f}s")

        # Find the telemetry point closest to our target time
        closest_idx = (driver_telemetry['TimeDelta'] - target_time).abs().idxmin()
        point = driver_telemetry.loc[closest_idx]

        # Normalize coordinates to 1000x1000 grid
        x_range = bounds['x_max'] - bounds['x_min']
        y_range = bounds['y_max'] - bounds['y_min']
        
        if x_range == 0 or y_range == 0:
            return None
            
        dot_x = ((point['X'] - bounds['x_min']) / x_range) * 1000
        dot_y = 1000 - (((point['Y'] - bounds['y_min']) / y_range) * 1000)

        return {
            "x": round(dot_x, 1),
            "y": round(dot_y, 1),
            "speed": round(point['Speed'], 1) if 'Speed' in point else 0,
            "time_delta": float(point['TimeDelta'])
        }
    except Exception as e:
        if driver_number not in cached_telemetry_ranges:
            print(f"❌ Error for driver {driver_number}: {e}")
        return None

# creating a function to get race data
def get_f1_data():
    # getting cached data from the other two functions
    session, bounds, driver_metadata = initialize_session()

    target_lap = 1
    race_laps = session.laps[session.laps['LapNumber'] == target_lap]
    driversList = []
    for index, row in race_laps.iterrows():
        # 1. Standardize the driver number variable name
        driver_number = str(row['DriverNumber'])
        # 2. Set default values outside the try block to avoid UnboundLocalError
        dot_x, dot_y = 0, 0
        team_color = "#FFFFFF"
        full_name = row.get('Driver', 'Unknown')
        try:
            driver_laps = session.laps.pick_drivers(driver_number)
            driver_lap = driver_laps[driver_laps['LapNumber'] == target_lap]
            
            if len(driver_lap) > 0:
                # ← CHANGE: Get starting position instead of ending position
                raw_telemetry = driver_lap.iloc[0].get_telemetry()  # First point instead of last
                if len(raw_telemetry) > 0:
                    # getting first point of starting session
                    first_point = raw_telemetry.iloc[0]
                    # Scale coordinates
                    dot_x = ((first_point['X'] - bounds['x_min']) / (bounds['x_max'] - bounds['x_min'])) * 1000
                    dot_y = 1000 - (((first_point['Y'] - bounds['y_min']) / (bounds['y_max'] - bounds['y_min'])) * 1000)
            

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


@app.route('/api/race/live', methods=['GET'])
def get_live_positions():
    try:
        elapsed_time = float(request.args.get('elapsed', 0))
        if elapsed_time < 5:
            print(f"\n📡 /api/race/live @ {elapsed_time:.2f}s")

        session, bounds, driver_metadata = initialize_session()

        # fetching all the drivers from the session 
        drivers_List = []
        all_drivers = session.results['DriverNumber'].unique()
        print(f"Processing {len(all_drivers)} drivers: {list(all_drivers)}")

        # looping through each driver position at a given time
        for driver_num in all_drivers:
            driver_number = str(driver_num)

            if elapsed_time < 5:
                print(f"🔍 Processing driver {driver_number}...")

            position_data = get_driver_position_at_time(driver_number, elapsed_time, session, bounds)
            if position_data and elapsed_time < 5:
                print(f"   ✅ Driver {driver_number}: Got position data")
            elif elapsed_time < 5:
                print(f"   ❌ Driver {driver_number}: No position data (returned None)")

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
                    tire_compound = 'UNKNOWN'
                    if len(current_lap_data) > 0:
                        tire_compound = str(current_lap_data.iloc[0].get('Compound','UNKNOWN'))
                except Exception as e:
                    tire_compound = 'UNKNOWN'
                    current_driver_lap = 1
                
                # Driver data object
                drivers_List.append({
                    "id": driver_number,
                    "driverName": full_name,
                    "teamcolor": team_color,
                    "tireCompound": tire_compound,
                    "x": position_data['x'],  # ← Normalized coordinates for SVG
                    "y": position_data['y'],
                    "speed": position_data.get('speed', 0),
                    "time_delta": position_data.get('time_delta', float('inf')),
                    "currentLap": current_driver_lap
                })
        
        if drivers_List:
            drivers_List.sort(key=lambda d: d.get('time_delta', 0))
            leader_time = drivers_List[0].get('time_delta', 0) if drivers_List else 0
            for idx, driver in enumerate(drivers_List):
                driver['position'] = idx + 1

                if idx == 0:
                    driver['gapToLeader'] = "LAP"  
                else:
                    gap_seconds = driver.get('time_delta', 0) - leader_time
                    if gap_seconds <60:
                        driver['gapToLeader'] = f"+{gap_seconds:.1f}s"
                    else:
                        minutes = int(gap_seconds // 60)
                        seconds = gap_seconds % 60
                        driver['gapToLeader'] = f"+{minutes}:{seconds:05.2f}"
        else:
            print("⚠️ No drivers have position data!")
        
        current_lap =1
        if drivers_List:
            current_lap = drivers_List[0].get('currentLap',1)
        
            print(f"✅ Returning {len(drivers_List)} drivers out of {len(all_drivers)} total")
            if drivers_List and elapsed_time < 5:
                print(f"   🏁 Leader: {drivers_List[0]['driverName']} - Lap {drivers_List[0]['currentLap']}, Position: x={drivers_List[0]['x']:.1f}, y={drivers_List[0]['y']:.1f}")

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