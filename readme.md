# zipliner - Postcodes → polylines (and routes) on OpenStreetMap

zipliner reads a semicolon-separated CSV of source/destination postcodes with country codes (CH, LI, AT, DE) and builds an interactive OpenStreetMap HTML map with markers and connecting lines, or real road routes via OSRM.

## Features

- Supported countries: CH, LI, AT, DE
- Straight line (postcode centroid → centroid) or real road route (OSRM)
- Multiple rows → multiple lines/routes
- Auto-fit to all points
- Treats postcodes as strings (keeps leading zeros like `01067`)

## Prerequisites

- Python 3.9+
- pip

Python packages:

- pandas
- pgeocode
- folium
- requests (only needed when routing is enabled)

Install:

```bash
pip install -r requirements.txt
```

## CSV format (semicolon-separated)

Required columns (all as text):

| Column                | Example | Notes                         |
| --------------------- | ------- | ----------------------------- |
| `source_zip`          | `9000`  | Keep as text (e.g., `01067`)  |
| `source_country`      | `CH`    | ISO-2: `CH`, `LI`, `AT`, `DE` |
| `destination_zip`     | `9244`  |                               |
| `destination_country` | `CH`    |                               |

Example:

```csv
source_zip;source_country;destination_zip;destination_country
9000;CH;9244;CH
78462;DE;6900;AT
9490;LI;6850;AT

```

## Usage

1) Generate a map from CSV (straight lines)

```bash
python zipliner.py
```

1) Open `map.html` in your browser.

## In-file configuration

```bash
CSV_PATH = "zipliner_routes_sample_004.csv"
USE_ROUTING = False
```

### What they do

- `CSV_PATH`: Path to your semicolon-separated CSV (with the four required columns).
- `USE_ROUTING`:
    - `False` → draw straight lines between postcode centroids (offline, fastest).
    - `True` → request real road routes from OSRM (router.project-osrm.org), which:
        - requires internet access,
        - is community-run and rate-limited,
        - may occasionally return errors/timeouts for very long or unusual routes.

## Notes & limits

- Postcode geometry: Without routing, the tool connects postcode centroids, not exact street addresses.
- Routing (OSRM): Uses the public endpoint router.project-osrm.org by default (community-run, rate-limited). For production, host your own OSRM or use a managed service.
- Disambiguation: Explicit country codes resolve postcode collisions (e.g., 6900 exists in CH and AT).
- Encoding: Save the CSV as UTF-8.