# mbta_sim.py
import os, sys, time, json, requests
API = "https://api-v3.mbta.com"
API_KEY = os.getenv("MBTA_API_KEY", "")

# ---- 1) Define a simple station→pixel mapping for the Red Line (example order) ----
# Replace with your real map order; add more stops as needed.
RED_STOPS = [
    ("place-alfcl", 0),   # Alewife
    ("place-davis", 2),   # Davis
    ("place-portr", 4),   # Porter
    ("place-harsq", 6),   # Harvard
    ("place-cntsq", 8),   # Central
    ("place-knncl", 10),  # Kendall/MIT
    ("place-pktrm", 12),  # Park St (Red)
    ("place-dwnxg", 14),  # Downtown Crossing (Red)
    ("place-sstat", 16),  # South Station
]
STOP_TO_PIXEL = dict(RED_STOPS)

def mbta_get(path, params=None):
    headers = {}
    if API_KEY:
        headers["x-api-key"] = API_KEY
    resp = requests.get(API + path, params=params or {}, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()

def bucket_eta(seconds):
    # example color buckets (R,G,B) for ETA
    # <2 min bright green, 2-5 min cyan, 5-10 min blue, >10 dim
    if seconds is None:       return (3, 3, 3)
    if seconds < 120:         return (0, 255, 64)
    if seconds < 300:         return (0, 180, 255)
    if seconds < 600:         return (0, 90, 255)
    return (10, 10, 40)

def build_prediction_colors():
    # /predictions filtered to Red Line; include stops for joining
    # See MBTA Swagger for fields, includes, filters: /docs/swagger. :contentReference[oaicite:3]{index=3}
    params = {
        "filter[route]": "Red",
        "include": "stop",
        "sort": "stop_sequence"  # useful ordering when present
    }
    data = mbta_get("/predictions", params)

    # Build lookup for stop arrival times (soonest per stop)
    stop_eta = {k: None for k in STOP_TO_PIXEL}
    included_stops = {inc["id"]: inc for inc in data.get("included", []) if inc.get("type") == "stop"}

    for p in data.get("data", []):
        rels = p.get("relationships", {})
        stop_id = (rels.get("stop") or {}).get("data", {}).get("id")
        attrs = p.get("attributes", {})
        # arrival/departure times are ISO; use 'arrival_time' then 'departure_time'
        t = attrs.get("arrival_time") or attrs.get("departure_time")
        if not stop_id or stop_id not in stop_eta or not t:
            continue
        # Convert ISO time to seconds-from-now
        from datetime import datetime, timezone
        try:
            eta_sec = int(datetime.fromisoformat(t.replace("Z","+00:00")).timestamp() - datetime.now(timezone.utc).timestamp())
        except Exception:
            eta_sec = None
        # Keep soonest ETA per stop
        current = stop_eta.get(stop_id)
        if eta_sec is not None and (current is None or eta_sec < current):
            stop_eta[stop_id] = eta_sec

    # Turn ETAs into per-pixel colors
    frame = {}
    for stop_id, eta in stop_eta.items():
        pix = STOP_TO_PIXEL[stop_id]
        frame[pix] = bucket_eta(eta)
    return frame

def place_vehicle_dots(frame):
    # /vehicles for the Red Line: gives you active trains, crowding status, etc. :contentReference[oaicite:4]{index=4}
    params = {"filter[route]": "Red"}
    data = mbta_get("/vehicles", params)
    # Simple demo: hash vehicle id into the mapped pixel range
    # (Later, replace with interpolation along stop indices using next_stop_sequence.)
    import zlib
    pix_indices = sorted(STOP_TO_PIXEL.values())
    if not pix_indices:
        return frame
    lo, hi = min(pix_indices), max(pix_indices)
    span = max(1, hi - lo + 1)

    for v in data.get("data", []):
        vid = v.get("id", "veh")
        px = lo + (zlib.crc32(vid.encode()) % span)
        frame[px] = (255, 0, 0)  # red dot for train
    return frame

def ascii_preview(frame):
    # Render a quick ASCII bar from pixel 0..max
    max_i = max(frame.keys()) if frame else 0
    s = []
    for i in range(max_i + 1):
        if i in frame:
            r,g,b = frame[i]
            s.append("●" if r>200 else "•" if sum((r,g,b))>20 else "·")
        else:
            s.append(" ")
    return "".join(s)

if __name__ == "__main__":
    try:
        frame = build_prediction_colors()
        frame = place_vehicle_dots(frame)
        print("Frame (pixel_index -> [R,G,B]):")
        print(json.dumps({str(k): v for k, v in sorted(frame.items())}, indent=2))
        print("\nASCII preview:")
        print(ascii_preview(frame))
    except requests.HTTPError as e:
        print("HTTP error:", e, file=sys.stderr)
    except Exception as e:
        print("Error:", e, file=sys.stderr)
