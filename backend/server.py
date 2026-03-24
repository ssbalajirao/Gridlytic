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

# ── cached globals ────────────────────────────────────────────────────────────
cached_track_map = None
cached_session = None
cached_bounds = None
cached_driver_metadata = None
cached_race_start_time = None
cached_driver_telemetry = {}   # { driver_number: DataFrame with TimeDelta col }
cached_driver_laps = {}        # { driver_number: DataFrame } for lap/tyre lookup

# NEW: pre-computed position table
# Structure: { time_bucket (int seconds): [ {driver dict}, ... ] }
cached_positions = {}
precompute_complete = False     # flag so the frontend knows when it's ready

BUCKET_SIZE = 1                 # pre-compute every 1 second of race time
RACE_DURATION = 5400            # 90 min ceiling (Silverstone ~4680s, bit of headroom)

session_lock = threading.Lock()
# ─────────────────────────────────────────────────────────────────────────────


def get_track_shape_once():
    global cached_track_map

    if cached_track_map is None:
        print("[PHASE 1] Loading track geometry for the first time...")

        session = fastf1.get_session(2025, 'Silverstone', 'R')
        session.load(telemetry=True, weather=False)

        fastest_lap = session.laps.pick_fastest()
        telemetry = fastest_lap.get_telemetry().iloc[::2]

        x_min, x_max = telemetry['X'].min(), telemetry['X'].max()
        y_min, y_max = telemetry['Y'].min(), telemetry['Y'].max()

        path_parts = []
        for i, row in enumerate(telemetry.itertuples()):
            x_range = x_max - x_min
            y_range = y_max - y_min
            if x_range == 0 or y_range == 0:
                return cached_track_map

            norm_x = ((row.X - x_min) / x_range) * 1000
            norm_y = 1000 - (((row.Y - y_min) / y_range) * 1000)

            command = "M" if i == 0 else "L"
            path_parts.append(f"{command} {norm_x:.1f} {norm_y:.1f}")

        path_parts.append("Z")
        padding = 50
        cached_track_map = {
            "svgPath": " ".join(path_parts),
            "viewBox": f"{-padding} {-padding} {1000 + (padding * 2)} {1000 + (padding * 2)}",
            "bounds": {
                "x_min": float(x_min), "x_max": float(x_max),
                "y_min": float(y_min), "y_max": float(y_max)
            }
        }
        print("[PHASE 1] Track geometry ready.")

    return cached_track_map


def initialize_session():
    """Load session + telemetry for all drivers once. Subsequent calls are instant."""
    global cached_session, cached_bounds, cached_driver_metadata
    global cached_race_start_time, cached_driver_telemetry, cached_driver_laps

    with session_lock:
        if cached_session is None:
            print("[PHASE 2] Initializing session data...")
            cached_session = fastf1.get_session(2025, 'Silverstone', 'R')
            cached_session.load(telemetry=True, weather=False)

            cached_race_start_time = cached_session.laps['LapStartTime'].min()
            print(f"[PHASE 2] Race start time: {cached_race_start_time}")

            track_info = get_track_shape_once()
            cached_bounds = track_info['bounds']

            # Build driver metadata (color + full name)
            cached_driver_metadata = {}
            for _, res in cached_session.results.iterrows():
                cached_driver_metadata[str(res['DriverNumber'])] = {
                    "color": f"#{res['TeamColor']}" if not pd.isna(res['TeamColor']) else "#FFFFFF",
                    "name": res['FullName']
                }

            # Pre-load telemetry for every driver into memory right now
            # This is the slow part — we do it ONCE at startup, not per-request
            all_drivers = cached_session.results['DriverNumber'].unique()
            for driver_num in all_drivers:
                driver_number = str(driver_num)
                try:
                    driver_laps = cached_session.laps.pick_drivers(driver_number)
                    cached_driver_laps[driver_number] = driver_laps

                    try:
                        tel = driver_laps.get_telemetry()
                    except Exception:
                        # fallback: lap-by-lap
                        all_tel = []
                        for _, lap in driver_laps.iterrows():
                            try:
                                lt = lap.get_telemetry()
                                if len(lt) > 0:
                                    all_tel.append(lt)
                            except Exception:
                                continue
                        if not all_tel:
                            print(f"[PHASE 2] ⚠️  No telemetry for driver {driver_number}")
                            continue
                        tel = pd.concat(all_tel, ignore_index=True)

                    # Add TimeDelta column once here — never recomputed per request
                    tel = tel.copy()
                    tel['TimeDelta'] = (
                        tel['Time'] - cached_race_start_time
                    ).dt.total_seconds()
                    cached_driver_telemetry[driver_number] = tel
                    print(f"[PHASE 2] ✅ Loaded telemetry for driver {driver_number}: {len(tel)} points")

                except Exception as e:
                    print(f"[PHASE 2] ❌ Error loading driver {driver_number}: {e}")

            print("[PHASE 2] Session initialized successfully!")

    return cached_session, cached_bounds, cached_driver_metadata


# ── NEW: fast position lookup from cached telemetry ───────────────────────────
def get_position_from_cache(driver_number, target_time, bounds):
    """
    Pure in-memory lookup — no I/O, no fastf1 calls.
    Returns (x, y, speed, time_delta) or None.
    """
    tel = cached_driver_telemetry.get(driver_number)
    if tel is None or len(tel) == 0:
        return None

    closest_idx = (tel['TimeDelta'] - target_time).abs().idxmin()
    point = tel.loc[closest_idx]

    x_range = bounds['x_max'] - bounds['x_min']
    y_range = bounds['y_max'] - bounds['y_min']
    if x_range == 0 or y_range == 0:
        return None

    dot_x = ((point['X'] - bounds['x_min']) / x_range) * 1000
    dot_y = 1000 - (((point['Y'] - bounds['y_min']) / y_range) * 1000)

    return {
        "x": round(dot_x, 1),
        "y": round(dot_y, 1),
        "speed": round(float(point['Speed']), 1) if 'Speed' in point else 0,
        "time_delta": float(point['TimeDelta'])
    }


def get_tyre_and_lap(driver_number, elapsed_time):
    """Fast lookup for current lap number and tyre compound."""
    driver_laps = cached_driver_laps.get(driver_number)
    if driver_laps is None:
        return 1, 'UNKNOWN'

    current_driver_lap = 1
    try:
        base_time = driver_laps.iloc[0]['LapStartTime']
        for _, lap_row in driver_laps.iterrows():
            lap_time = (lap_row['LapStartTime'] - base_time).total_seconds()
            if lap_time <= elapsed_time:
                current_driver_lap = int(lap_row['LapNumber'])
            else:
                break

        current_lap_data = driver_laps[driver_laps['LapNumber'] == current_driver_lap]
        tire_compound = 'UNKNOWN'
        if len(current_lap_data) > 0:
            tire_compound = str(current_lap_data.iloc[0].get('Compound', 'UNKNOWN'))
    except Exception:
        tire_compound = 'UNKNOWN'

    return current_driver_lap, tire_compound


# ── NEW: background pre-computation ──────────────────────────────────────────
def precompute_all_positions():
    """
    Runs in a background thread after startup.
    Walks through the entire race second-by-second and stores results
    in cached_positions so /api/race/live is just a dict lookup.
    """
    global cached_positions, precompute_complete

    print("[PHASE 3] Starting background pre-computation of all positions...")
    session, bounds, driver_metadata = initialize_session()
    all_drivers = list(session.results['DriverNumber'].unique())

    for t in range(0, RACE_DURATION, BUCKET_SIZE):
        bucket_drivers = []

        for driver_num in all_drivers:
            driver_number = str(driver_num)
            pos = get_position_from_cache(driver_number, t, bounds)
            if pos is None:
                continue

            team_color = driver_metadata.get(driver_number, {}).get("color", "#FFFFFF")
            full_name = driver_metadata.get(driver_number, {}).get("name", f"Driver {driver_number}")
            current_lap, tire_compound = get_tyre_and_lap(driver_number, t)

            bucket_drivers.append({
                "id": driver_number,
                "driverName": full_name,
                "teamcolor": team_color,
                "tireCompound": tire_compound,
                "x": pos['x'],
                "y": pos['y'],
                "speed": pos['speed'],
                "time_delta": pos['time_delta'],
                "currentLap": current_lap
            })

        # Sort by time_delta (race order) and assign positions + gaps
        if bucket_drivers:
            bucket_drivers.sort(key=lambda d: d['time_delta'])
            leader_time = bucket_drivers[0]['time_delta']
            for idx, driver in enumerate(bucket_drivers):
                driver['position'] = idx + 1
                if idx == 0:
                    driver['gapToLeader'] = "LEAD"
                else:
                    gap_seconds = driver['time_delta'] - leader_time
                    if gap_seconds < 60:
                        driver['gapToLeader'] = f"+{gap_seconds:.1f}s"
                    else:
                        minutes = int(gap_seconds // 60)
                        seconds = gap_seconds % 60
                        driver['gapToLeader'] = f"+{minutes}:{seconds:05.2f}"

        cached_positions[t] = bucket_drivers

        if t % 300 == 0:
            print(f"[PHASE 3] Pre-computed up to {t}s / {RACE_DURATION}s ({int(t/RACE_DURATION*100)}%)")

    precompute_complete = True
    print("[PHASE 3] ✅ Pre-computation complete! All race positions are ready.")
# ─────────────────────────────────────────────────────────────────────────────


@app.route('/api/race/live', methods=['GET'])
def get_live_positions():
    """
    Now just a dictionary lookup — responds in < 1ms once pre-computation is done.
    Falls back to live computation if pre-computation hasn't reached this time yet.
    """
    try:
        elapsed_time = float(request.args.get('elapsed', 0))

        # Snap to nearest bucket
        bucket = int(round(elapsed_time / BUCKET_SIZE) * BUCKET_SIZE)
        bucket = max(0, min(bucket, RACE_DURATION - 1))

        # Fast path: pre-computed data is available
        if bucket in cached_positions:
            drivers_list = cached_positions[bucket]
            current_lap = drivers_list[0]['currentLap'] if drivers_list else 1
            return jsonify({
                "status": "success",
                "currentLap": current_lap,
                "elapsedTime": elapsed_time,
                "drivers": drivers_list,
                "source": "precomputed"   # handy for debugging
            })

        # Slow fallback: pre-computation hasn't reached this time yet
        # (only happens in the first few minutes after server start)
        print(f"[LIVE FALLBACK] Pre-computation not ready for t={elapsed_time:.1f}s, computing live...")
        session, bounds, driver_metadata = initialize_session()
        all_drivers = session.results['DriverNumber'].unique()
        drivers_list = []

        for driver_num in all_drivers:
            driver_number = str(driver_num)
            pos = get_position_from_cache(driver_number, elapsed_time, bounds)
            if pos is None:
                continue

            team_color = driver_metadata.get(driver_number, {}).get("color", "#FFFFFF")
            full_name = driver_metadata.get(driver_number, {}).get("name", f"Driver {driver_number}")
            current_lap, tire_compound = get_tyre_and_lap(driver_number, elapsed_time)

            drivers_list.append({
                "id": driver_number,
                "driverName": full_name,
                "teamcolor": team_color,
                "tireCompound": tire_compound,
                "x": pos['x'],
                "y": pos['y'],
                "speed": pos['speed'],
                "time_delta": pos['time_delta'],
                "currentLap": current_lap
            })

        if drivers_list:
            drivers_list.sort(key=lambda d: d['time_delta'])
            leader_time = drivers_list[0]['time_delta']
            for idx, driver in enumerate(drivers_list):
                driver['position'] = idx + 1
                if idx == 0:
                    driver['gapToLeader'] = "LEAD"
                else:
                    gap_seconds = driver['time_delta'] - leader_time
                    if gap_seconds < 60:
                        driver['gapToLeader'] = f"+{gap_seconds:.1f}s"
                    else:
                        minutes = int(gap_seconds // 60)
                        seconds = gap_seconds % 60
                        driver['gapToLeader'] = f"+{minutes}:{seconds:05.2f}"

        current_lap = drivers_list[0]['currentLap'] if drivers_list else 1
        return jsonify({
            "status": "success",
            "currentLap": current_lap,
            "elapsedTime": elapsed_time,
            "drivers": drivers_list,
            "source": "live"
        })

    except Exception as e:
        print("ERROR in live endpoint:")
        print(traceback.format_exc())
        return jsonify({"status": "error", "message": str(e)}), 500


# NEW: endpoint so the frontend can check pre-computation progress
@app.route('/api/status', methods=['GET'])
def get_status():
    total_buckets = RACE_DURATION // BUCKET_SIZE
    computed_buckets = len(cached_positions)
    return jsonify({
        "status": "success",
        "precompute_complete": precompute_complete,
        "progress_percent": round((computed_buckets / total_buckets) * 100, 1),
        "computed_seconds": computed_buckets * BUCKET_SIZE,
        "total_seconds": RACE_DURATION
    })


@app.route('/api/test', methods=['GET'])
def raceData():
    try:
        print("Fetching F1 data...")
        session, bounds, driver_metadata = initialize_session()

        # Build initial driver list from lap 1 positions (same as before)
        target_lap = 1
        race_laps = session.laps[session.laps['LapNumber'] == target_lap]
        driversList = []

        for index, row in race_laps.iterrows():
            driver_number = str(row['DriverNumber'])
            dot_x, dot_y = 0, 0
            team_color = "#FFFFFF"
            full_name = driver_metadata.get(driver_number, {}).get("name", "Unknown")

            try:
                driver_laps = session.laps.pick_drivers(driver_number)
                driver_lap = driver_laps[driver_laps['LapNumber'] == target_lap]

                if len(driver_lap) > 0:
                    raw_telemetry = driver_lap.iloc[0].get_telemetry()
                    if len(raw_telemetry) > 0:
                        first_point = raw_telemetry.iloc[0]
                        dot_x = ((first_point['X'] - bounds['x_min']) / (bounds['x_max'] - bounds['x_min'])) * 1000
                        dot_y = 1000 - (((first_point['Y'] - bounds['y_min']) / (bounds['y_max'] - bounds['y_min'])) * 1000)

                team_color = driver_metadata.get(driver_number, {}).get("color", "#FFFFFF")

            except Exception as e:
                print(f"Warning: Could not get position for driver {driver_number}: {e}")

            gap_str = str(row['Time'])
            if gap_str == 'NaT' or 'days' not in gap_str:
                clean_gap = "LAP"
            else:
                clean_gap = gap_str.split('days')[-1].split('.')[0].strip()

            driversList.append({
                "id": driver_number,
                "position": int(row['Position']) if not pd.isna(row['Position']) else 0,
                "driverName": full_name,
                "teamcolor": team_color,
                "tireCompound": str(row.get('Compound', 'SOFT')),
                "gapToLeader": clean_gap,
                "lapPercentage": 0.0,
                "x": round(dot_x, 1),
                "y": round(dot_y, 1)
            })

        race_track = get_track_shape_once()

        return jsonify({
            "status": "success",
            "session": {
                "currentLap": 1,
                "totalLaps": 52,
                "flagStatus": "GREEN",
                "trackName": "Silverstone"
            },
            "drivers": driversList,
            "track_map": race_track
        })
    except Exception as e:
        print("ERROR occurred:")
        print(traceback.format_exc())
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    # Kick off background pre-computation in a separate thread
    # The server starts immediately and serves requests while this runs
    precompute_thread = threading.Thread(target=precompute_all_positions, daemon=True)
    precompute_thread.start()

    # NOTE: debug=True causes Flask to reload which kills the background thread.
    # Use debug=False while testing the animation, or use use_reloader=False.
    app.run(debug=False, port=5000)