# plot_mbta_stations_subway.py
# Plot ALL station locations for MBTA subway lines: Red, Green (B/C/D/E), Blue, Orange.
#
# Usage:
#   pip install requests matplotlib
#   export MBTA_API_KEY="your_key"   # optional but recommended
#   python plot_mbta_stations_subway.py
#
# Notes:
# - This makes 1 API call per route to /stops.
# - Toggle LABELS to show/hide station name labels.

import os
import requests
import matplotlib.pyplot as plt

API = "https://api-v3.mbta.com"
API_KEY = os.getenv("MBTA_API_KEY", "")

ROUTES = ["Red", "Orange", "Blue", "Green-B", "Green-C", "Green-D", "Green-E"]
LABELS = False  # set True to annotate station names

# MBTA brand colors (hex). Green branches share the same green.
LINE_COLOR = {
    "Red":     "#DA291C",
    "Orange":  "#ED8B00",
    "Blue":    "#003DA5",
    "Green-B": "#00843D",
    "Green-C": "#00843D",
    "Green-D": "#00843D",
    "Green-E": "#00843D",
}

# Distinct markers for Green branches so the legend is useful
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

def fetch_stops_for_route(route_id):
    """
    Fetch all stops for a given route_id (e.g., 'Red', 'Green-B', etc.).
    Returns a list of dicts: {id, name, lat, lon}
    """
    payload = mbta_get("/stops", {"filter[route]": route_id, "page[limit]": 200})
    stops = []
    for s in payload.get("data", []):
        attrs = s.get("attributes", {}) or {}
        lat, lon = attrs.get("latitude"), attrs.get("longitude")
        if lat is None or lon is None:
            continue
        stops.append({
            "id": s.get("id"),
            "name": attrs.get("name"),
            "lat": lat,
            "lon": lon,
        })
    # Deduplicate by stop id (some endpoints can return duplicates)
    uniq = {}
    for st in stops:
        uniq[st["id"]] = st
    return list(uniq.values())

def main():
    # Gather stops grouped by route
    by_route = {}
    for rid in ROUTES:
        by_route[rid] = fetch_stops_for_route(rid)

    # Plot
    plt.figure(figsize=(7.5, 7))
    ax = plt.gca()
    ax.set_title("MBTA Subway Stations — Red / Green (B/C/D/E) / Blue / Orange")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_aspect("equal")
    ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.4)

    # Keep overall bounds to autoscale nicely
    all_lons, all_lats = [], []

    for rid, stops in by_route.items():
        xs = [s["lon"] for s in stops]
        ys = [s["lat"] for s in stops]
        all_lons.extend(xs)
        all_lats.extend(ys)

        plt.scatter(
            xs, ys,
            s=28,
            marker=MARKER.get(rid, "o"),
            edgecolors="black",
            linewidths=0.3,
            alpha=0.95,
            c=LINE_COLOR.get(rid, "#555555"),
            label=rid
        )

        if LABELS:
            for s in stops:
                ax.annotate(
                    s["name"],
                    (s["lon"], s["lat"]),
                    xytext=(3, 3),
                    textcoords="offset points",
                    fontsize=7
                )

    if all_lons and all_lats:
        ax.set_xlim(min(all_lons) - 0.02, max(all_lons) + 0.02)
        ax.set_ylim(min(all_lats) - 0.02, max(all_lats) + 0.02)

    plt.legend(title="Route", loc="best", frameon=True, fontsize=8)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
