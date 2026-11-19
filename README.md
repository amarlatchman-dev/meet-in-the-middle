# Meet in the Middle

Find a fair meeting spot for up to 10 people. Each starting point floods outward along the real road network (OpenStreetMap), and the meeting spot is where the floods meet. Routes, travel times and Google Maps links are shown for everyone.

- Car or walking
- "Fairest" (shortest longest trip) or "Saves most travel" (lowest combined travel)
- No API keys: uses OpenStreetMap data via Overpass, Photon geocoding and CARTO tiles

Open `index.html` in a browser, or use the GitHub Pages link.

## Pre-loaded road maps

When everyone is inside the pre-built area, the app reads `data/manifest.json`, downloads only the road tiles around the group (each tile is 0.5° square, about 50 km), and runs the whole street-by-street flood in the browser, with no live servers needed. Outside that area it falls back to the free OSRM routing service.

Current coverage: **Southern Ontario**, from Windsor to Ottawa and Cornwall, north to about Muskoka (41.6–45.7°N, 83.2–74.3°W).

The `Build road maps` GitHub Action (`.github/workflows/build-maps.yml`) downloads Ontario from Geofabrik, falling back to tiled Overpass downloads if Geofabrik is unreachable. It runs `tools/build_region.py`, which writes the tiles and manifest into `data/`. It runs monthly, or on demand from the Actions tab.

Map data © OpenStreetMap contributors (ODbL).
