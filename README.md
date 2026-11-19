# Meet in the Middle

Find a fair meeting spot for up to 10 people. Each starting point floods outward along the real road network (OpenStreetMap), and the meeting spot is where the floods meet. Routes, travel times and Google Maps links are shown for everyone.

- Car or walking
- "Fairest" (shortest longest trip) or "Saves most travel" (lowest combined travel)
- No API keys: uses OpenStreetMap data via Overpass, Photon geocoding and CARTO tiles

Open `index.html` in a browser, or use the GitHub Pages link.

## Pre-loaded road maps

When everyone is inside a pre-built region, the app loads `data/<region>.bin` once and runs the whole street-by-street flood in the browser, with no live servers needed. Outside those regions it falls back to the free OSRM routing service.

Current regions:
- **Greater Toronto Area**: Niagara to Oshawa, north to about Newmarket and Uxbridge

The `Build road maps` GitHub Action (`.github/workflows/build-maps.yml`) downloads Ontario from Geofabrik, cuts out the region, and runs `tools/build_region.py`. It runs monthly, or on demand from the Actions tab. To add a region, add a build step to the workflow and an entry to `REGIONS` in `index.html`.

Map data © OpenStreetMap contributors (ODbL).
