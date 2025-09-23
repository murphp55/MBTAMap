# subway_scatter_labeled.py
# Plot MBTA subway vehicles (Red/Green[B/C/D/E]/Blue/Orange) as a lon/lat scatter.
# Labels show: "<current/next stop> → <terminal end station>".
#
# Usage:
#   pip install requests matplotlib
#   export MBTA_API_KEY="your_key"   # (optional, but recommended)
#   python subway_scatter_labeled.py

import os
import requests
import matplotlib.pyplot as plt

API = "https://api-v3.mbta.com"
API_KEY = os.getenv("MBTA_API_KEY", "")

ROUTES = ["Red", "Orange", "Blue", "Green-B", "Green-C", "Green-D", "Green-E"]

# MBTA brand colors (same green for branches), distinct markers per branch
LINE_COLOR = {
    "Red":     "#DA291C",
    "Orange":  "#ED8B00",
    "Blue":    "#003DA5",
    "Green-B": "#00843D",
    "Green-C": "#00843D",
    "Green-D": "#00843D",
    "Green-E": "#00843D",
}
MARKER = {
    "Red":     "o",
    "Orange":  "o",
    "Blue":    "o",
    "Green-B": "s",
    "Green-C": "^",
    "Green-D": "D",
    "Green-E": "P",
}

def mbta_get(path, params=None):
    headers = {}
    if API_KEY:
        headers["x-api-key"] = API_KEY
    r = requests.get(API + path, params=params or {}, headers=headers, timeout=12)
    r.raise_for_status()
    return r.json()

def fetch_vehicles_and_terminals():
    """Fetch vehicles (keep full records) and route terminals (direction_destinations)."""
    payload = mbta_get("/vehicles", {
        "include": "route",
        "filter[route]": ",".join(ROUTES),
    })
    vehicles = [v for v in payload.get("data", []) if v.get("attributes", {}).get("latitude") is not None]
    route_terminals = {}
    for inc in payload.get("included", []):
        if inc.get("type") == "route" and inc.get("id") in ROUTES:
            attrs = inc.get("attributes", {}) or {}
            route_terminals[inc["id"]] = attrs.get("direction_destinations", ["", ""])
    return vehicles, route_terminals

def fetch_stop_name(stop_id):
    """Lookup stop name by id."""
    if not stop_id:
        return None
    try:
        st = mbta_get(f"/stops/{stop_id}")
        return (st.get("data", {}).get("attributes") or {}).get("name")
    except Exception:
        return None

def fetch_next_stop_name(vehicle_obj):
    """
    Return current/next stop name for a vehicle.
    Order:
      1) vehicle's stop relationship or attributes.stop_id
      2) earliest prediction (fetch stop from include or by id)
    """
    vid = vehicle_obj.get("id")
    rel = vehicle_obj.get("relationships", {}) or {}
    veh_stop_id = ((rel.get("stop") or {}).get("data") or {}).get("id")
    if not veh_stop_id:
        veh_stop_id = (vehicle_obj.get("attributes") or {}).get("stop_id")

    # Try vehicle-linked stop first
    name = fetch_stop_name(veh_stop_id)
    if name:
        return name

    # Fall back to predictions for this vehicle
    try:
        resp = mbta_get("/predictions", {
            "filter[vehicle]": vid,
            "sort": "arrival_time,departure_time",
            "include": "stop",
            "page[limit]": 3
        })
    except requests.HTTPError:
        return None

    # Included stops map
    included_names = {}
    for inc in resp.get("included", []):
        if inc.get("type") == "stop":
            sid = inc.get("id")
            nm = (inc.get("attributes") or {}).get("name")
            if sid and nm:
                included_names[sid] = nm

    # Earliest prediction with a stop; use included or fetch by id
    for p in resp.get("data", []):
        srel = (p.get("relationships", {}) or {}).get("stop", {}) or {}
        sid = (srel.get("data") or {}).get("id")
        if not sid:
            continue
        if sid in included_names:
            return included_names[sid]
        nm = fetch_stop_name(sid)
        if nm:
            return nm

    return None

def main():
    vehicles, route_terms = fetch_vehicles_and_terminals()
    if not vehicles:
        print("No vehicle locations returned.")
        return

    # Normalize for plotting, enrich with next stop + terminal
    norm = []
    for v in vehicles:
        attrs = v.get("attributes", {}) or {}
        rel = v.get("relationships", {}) or {}
        route_id = ((rel.get("route") or {}).get("data") or {}).get("id")
        if route_id not in ROUTES:
            continue
        lat, lon = attrs.get("latitude"), attrs.get("longitude")
        if lat is None or lon is None:
            continue

        next_stop = fetch_next_stop_name(v) or "(stop unknown)"
        dir_id = attrs.get("direction_id")
        terminals = route_terms.get(route_id, ["", ""])
        terminal = terminals[dir_id] if isinstance(dir_id, int) and 0 <= dir_id < len(terminals) else "(terminal unknown)"

        norm.append({
            "route": route_id,
            "lat": lat,
            "lon": lon,
            "label": f"{next_stop} \u2192 {terminal}",  # → arrow
        })

    # Plot
    plt.figure(figsize=(7, 7))
    ax = plt.gca()
    ax.set_title("MBTA Live Vehicles — Red / Green / Blue / Orange")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_aspect("equal")
    ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.4)

    # Group by route for legend and styling
    by_route = {}
    for r in norm:
        by_route.setdefault(r["route"], []).append(r)

    for route, rows in by_route.items():
        xs = [r["lon"] for r in rows]
        ys = [r["lat"] for r in rows]
        plt.scatter(
            xs, ys,
            s=45,
            marker=MARKER.get(route, "o"),
            edgecolors="black",
            linewidths=0.4,
            alpha=0.95,
            c=LINE_COLOR.get(route, "#555555"),
            label=route
        )
        # Text labels
        for r in rows:
            ax.annotate(r["label"], (r["lon"], r["lat"]),
                        xytext=(4, 4), textcoords="offset points", fontsize=8)

    plt.legend(title="Route", loc="best", frameon=True)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
