# pip install pgeocode folium pandas requests
import pandas as pd
import pgeocode
import folium
import requests
import colorsys

CSV_PATH = "src/zipliner_routes_sample_004.csv"
USE_ROUTING = False  # True = Routes (OSRM), False = as the crow flies

COUNTRIES = {"CH", "LI", "AT", "DE"}
nomi = {cc: pgeocode.Nominatim(cc) for cc in COUNTRIES}

df = pd.read_csv(CSV_PATH, sep=';', dtype=str).fillna("")

# Check columns
required_cols = {"source_zip","source_country","destination_zip","destination_country"}
missing = required_cols - set(df.columns)
if missing:
    raise ValueError(f"Missing columns in CSV: {', '.join(sorted(missing))}")

def norm_country(c):
    c = (c or "").strip().upper()
    if c not in COUNTRIES:
        raise ValueError(f"Invalid country code: {c!r} (expected: {', '.join(sorted(COUNTRIES))})")
    return c

def zip_to_latlon(plz, country):
    z = (plz or "").strip()
    if not z:
        raise ValueError("Empty ZIP in CSV")
    cc = norm_country(country)
    r = nomi[cc].query_postal_code(z)
    if pd.isna(r.latitude) or pd.isna(r.longitude):
        raise ValueError(f"ZIP {z} in {cc} not found!")
    return float(r.latitude), float(r.longitude), r.place_name, cc

def osrm_route(latlon1, latlon2, attempts=3, timeout=20):
    (lat1, lon1), (lat2, lon2) = latlon1, latlon2
    url = (
        "https://router.project-osrm.org/route/v1/driving/"
        f"{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"
    )
    last_err = None
    for _ in range(attempts):
        try:
            resp = requests.get(url, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            routes = data.get("routes", [])
            if not routes:
                raise ValueError("No route returned by OSRM")
            coords = routes[0]["geometry"]["coordinates"]  # [lon, lat]
            return [[lat, lon] for lon, lat in coords]
        except Exception as e:
            last_err = e
            # retry
            continue
    raise RuntimeError(f"OSRM failed after {attempts} attempts: {last_err}")

def random_color_palette(n):
    palette = []
    for i in range(n):
        # Evenly distribute hues for higher difference
        h = i / n
        rgb = colorsys.hsv_to_rgb(h, 0.7, 0.75)
        palette.append('#' + ''.join(f'{int(c*255):02x}' for c in rgb))
    return palette

# Create map
m = folium.Map(location=[47.3, 9.1], zoom_start=7, tiles="OpenStreetMap")
palette = random_color_palette(len(df))
all_points = []
failures = []

for idx, row in df.iterrows():
    rownum = idx + 2  # header is row 1
    s_zip = row["source_zip"]
    s_ctry = row["source_country"]
    d_zip = row["destination_zip"]
    d_ctry = row["destination_country"]

    try:
        lat1, lon1, name1, c1 = zip_to_latlon(s_zip, s_ctry)
        lat2, lon2, name2, c2 = zip_to_latlon(d_zip, d_ctry)

        folium.Marker([lat1, lon1], tooltip=f"{s_zip} {c1} – {name1}").add_to(m)
        folium.Marker([lat2, lon2], tooltip=f"{d_zip} {c2} – {name2}").add_to(m)

        if USE_ROUTING:
            line = osrm_route((lat1, lon1), (lat2, lon2))
        else:
            line = [[lat1, lon1], [lat2, lon2]]

        color = palette[idx % len(palette)]
        folium.PolyLine(
            line,
            weight=4,
            tooltip=f"{s_zip} {c1} → {d_zip} {c2}",
            color=color
        ).add_to(m)

        all_points.extend([[lat1, lon1], [lat2, lon2]])
        
        print(f"Row {rownum}: {s_zip} {c1} → {d_zip} {c2} OK")

    except Exception as e:
        failures.append({
            "row_number": rownum,
            "source_zip": s_zip,
            "source_country": s_ctry,
            "destination_zip": d_zip,
            "destination_country": d_ctry,
            "error": str(e)
        })
        continue

if all_points:
    m.fit_bounds(all_points, padding=(30, 30))
m.save("map.html")

if failures:
    print(f"\nCompleted with warnings: {len(failures)} row(s) failed, {len(df) - len(failures)} succeeded.")
    pd.DataFrame(failures).to_csv("zipliner_failures.csv", index=False, sep=';')
    print("Details written to 'zipliner_failures.csv'.")
else:
    print(f"\nAll good: processed {len(df)} row(s) successfully.")

print("Done! Open 'map.html' in your browser.")