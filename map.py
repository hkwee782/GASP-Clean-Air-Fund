# Neha Map - best one so far

"""
Grant Allocation Map Explorer
==================
• Filters by Category, Year, Location
• Click a project → map shows boundary polygon, multi-polygon, street line, or pin
• Boundaries fetched automatically from OpenStreetMap (cached to disk)
"""

import plotly.express as px
import json, os, time
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, State, callback_context
from dash.dependencies import ALL
import geopandas as gpd
import osmnx as ox
from geopy.geocoders import Nominatim
import re

# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────
EXCEL_FILE  = "FinalSheet.xlsx"
CACHE_FILE  = "geo_cache.json"
SEARCH_AREA = "Allegheny County, Pennsylvania, USA"

# ─────────────────────────────────────────
# GEOMETRY CACHE
# ─────────────────────────────────────────
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE) as f:
        geo_cache = json.load(f)
else:
    geo_cache = {}

def save_cache():
    with open(CACHE_FILE, "w") as f:
        json.dump(geo_cache, f)

def purge_stale_cache():
    """
    Delete any geo_cache entries for boundary-type locations that were wrongly
    saved as a single pin marker (result of the old if/elif bug).
    Runs automatically at startup so stale entries are re-fetched correctly.
    """
    stale = [
        k for k, v in list(geo_cache.items())
        if LOCATION_OVERRIDES.get(k, {}).get("type") == "boundary"
        and len(v.get("traces", [])) == 1
        and v["traces"][0].get("mode") == "markers"
    ]
    if stale:
        for k in stale:
            print(f"[cache] Purging stale boundary pin → will re-fetch polygon for: {k!r}")
            del geo_cache[k]
        save_cache()
        print(f"[cache] Purged {len(stale)} stale entries. Delete geo_cache.json manually if problems persist.")
    else:
        print("[cache] No stale boundary entries found.")

# ─────────────────────────────────────────
# LOCATION OVERRIDES
# type "point"    → geocode address to a single pin
# type "street"   → geocode address and draw a short line symbol
# type "boundary" → force OSMnx to fetch a real polygon boundary
# ─────────────────────────────────────────
LOCATION_OVERRIDES = {
    # ── Specific buildings / addresses → pin ──
    # NOTE: Replace the Kamin address below with the real address if this is wrong
    "Kamin Science Center": {
        "type": "point",
        "query": "1 Allegheny Ave, Pittsburgh, PA 15212"
    },
    "Allegheny County Parks Department": {
        "type": "point",
        "query": "542 Forbes Ave, Pittsburgh, PA 15219"
    },
    "CCAC Allegheny Campus": {
        "type": "point",
        "query": "808 Ridge Ave, Pittsburgh, PA 15212"
    },
    "CCAC North Campus": {
        "type": "point",
        "query": "8701 Perry Hwy, Pittsburgh, PA 15237"
    },
    "CCAC Boyce Campus": {
        "type": "point",
        "query": "595 Beatty Rd, Monroeville, PA 15146"
    },
    "CCAC South Campus": {
        "type": "point",
        "query": "1750 Clairton Rd, West Mifflin, PA 15122"
    },
    
    # ── Street → line symbol ──
    "Corrigan Dr. in South Park": {
        "type": "street",
        "query": "Corrigan Drive, South Park Township, Allegheny County, Pennsylvania, USA"
    },

    # ── Force real polygon boundaries ──
    "Allegheny County": {
        "type": "boundary",
        "query": "Allegheny County, Pennsylvania, USA"
    },
    "Pittsburgh": {
        "type": "boundary",
        "query": "Pittsburgh, Allegheny County, Pennsylvania, USA"
    },
    "Swissvale Borough": {
        "type": "boundary",
        "query": "Swissvale, Allegheny County, Pennsylvania, USA"
    },
    "Etna Borough": {
        "type": "boundary",
        "query": "Etna, Allegheny County, Pennsylvania, USA"
    },
    "West Mifflin Borough": {
        "type": "boundary",
        "query": "West Mifflin, Allegheny County, Pennsylvania, USA"
    },
    "Wilkinsburg Borough": {
        "type": "boundary",
        "query": "Wilkinsburg, Allegheny County, Pennsylvania, USA"
    },
    "Brackenridge Borough": {
        "type": "boundary",
        "query": "Brackenridge, Allegheny County, Pennsylvania, USA"
    },
    "Pitcairn Borough": {
        "type": "boundary",
        "query": "Pitcairn, Allegheny County, Pennsylvania, USA"
    },
    "Munhall Borough": {
        "type": "boundary",
        "query": "Munhall, Allegheny County, Pennsylvania, USA"
    },
    "Sharpsburg Borough": {
        "type": "boundary",
        "query": "Sharpsburg, Allegheny County, Pennsylvania, USA"
    },
    "Braddock Borough": {
        "type": "boundary",
        "query": "Braddock, Allegheny County, Pennsylvania, USA"
    },
    "North Braddock Borough": {
        "type": "boundary",
        "query": "North Braddock, Allegheny County, Pennsylvania, USA"
    },
    "Rankin Borough": {
        "type": "boundary",
        "query": "Rankin, Allegheny County, Pennsylvania, USA"
    },
    "East Pittsburgh Borough": {
        "type": "boundary",
        "query": "East Pittsburgh, Allegheny County, Pennsylvania, USA"
    },
    "Carnegie Borough": {
        "type": "boundary",
        "query": "Carnegie, Allegheny County, Pennsylvania, USA"
    },
    "Churchill Borough": {
        "type": "boundary",
        "query": "Churchill, Allegheny County, Pennsylvania, USA"
    },
    "Lawrenceville": {
        "type": "boundary",
        "query": "Lawrenceville, Pittsburgh, Pennsylvania, USA"
    },
    "Chateau": {
        "type": "boundary",
        "query": "Chateau, Pittsburgh, Pennsylvania, USA"
    },
    "Neville Island": {
        "type": "boundary",
        "query": "Neville Island, Allegheny County, Pennsylvania, USA"
    },
    "Monongahela River Valley": {
        "type": "coords",
        "lat": 40.25,
        "lon": -79.95
    },    
    "Northgate School District": {
        "type": "point",
        "query": "Northgate Senior High School, 589, Union Avenue, Ross Township, Allegheny County, Pennsylvania, 15202, United States"
    },
    "Bethel Park School District": {
        "type": "boundary",
        "query": "Bethel Park, Allegheny County, Pennsylvania, USA"
    },
    "McKeesport Area School District": {
        "type": "boundary",
        "query": "McKeesport, Allegheny County, Pennsylvania, USA"
    },
    "West Mifflin Area School District": {
        "type": "boundary",
        "query": "West Mifflin, Allegheny County, Pennsylvania, USA"
    },
    "Woodland Hills School District": {
        "type": "boundary",
        "query": "Woodland Hills, Allegheny County, Pennsylvania, USA"
    },
    "South Fayette School District": {
        "type": "boundary",
        "query": "South Fayette Township, Allegheny County, Pennsylvania, USA"
    },
}

# ─────────────────────────────────────────
# GEOMETRY HELPERS
# ─────────────────────────────────────────
# Purge any bad cache entries saved by the old buggy code before doing anything else
purge_stale_cache()

geolocator = Nominatim(user_agent="grant_map_explorer_v3")

def fetch_osm_polygon(query: str):
    """
    Fetch a real polygon boundary from OSM.
    Rejects Point results — only returns Polygon / MultiPolygon.
    """
    attempts = [
        query,
        f"{query}, {SEARCH_AREA}",
        f"{query}, Pennsylvania, USA",
    ]
    for attempt in attempts:
        for which_result in range(1, 4):
            try:
                gdf = ox.geocode_to_gdf(attempt, which_result=which_result)
                if gdf is not None and not gdf.empty:
                    geom = gdf.geometry.iloc[0]
                    if geom.geom_type in ("Polygon", "MultiPolygon"):
                        return gdf
            except Exception:
                continue
        time.sleep(0.2)
    return None

def geocode_point(query: str):
    """Returns (lat, lon) tuple or None."""
    try:
        loc = geolocator.geocode(query, timeout=10)
        if loc:
            return (loc.latitude, loc.longitude)
    except Exception:
        pass
    return None

def geometry_to_traces(geom, name: str, color: str):
    """Recursively convert a shapely geometry to Plotly Scattermapbox traces."""
    traces = []
    gtype = geom.geom_type

    if gtype == "Polygon":
        lons, lats = geom.exterior.xy
        #fill_color = color + "30"  # hex + 30 ≈ 18% opacity fill
        
        traces.append(go.Scattermapbox(
            lon=list(lons),
            lat=list(lats),
            mode="lines",
            fill="toself",
            #fillcolor=fill_color,
            fillcolor="rgba(0,0,255,0.08)", #light transparent fill
            #line=dict(color=color, width=2.5),
            line=dict(color="#0066ff", width=4),
            name=name,
            hoverinfo="name",
        ))

    elif gtype == "MultiPolygon":
        for poly in geom.geoms:
            traces += geometry_to_traces(poly, name, color)

    elif gtype in ("LineString", "MultiLineString"):
        geoms = [geom] if gtype == "LineString" else list(geom.geoms)
        for line in geoms:
            lons, lats = line.xy
            traces.append(go.Scattermapbox(
                lon=list(lons),
                lat=list(lats),
                mode="lines",
                line=dict(color=color, width=4),
                name=name,
                hoverinfo="name",
            ))

    elif gtype == "Point":
        traces.append(go.Scattermapbox(
            lon=[geom.x],
            lat=[geom.y],
            mode="markers",
            marker=dict(size=16, color=color),
            name=name,
            hoverinfo="name",
        ))

    elif gtype == "GeometryCollection":
        for g in geom.geoms:
            traces += geometry_to_traces(g, name, color)

    return traces

def gdf_to_traces(gdf, name: str, color: str):
    traces = []
    for geom in gdf.geometry:
        traces += geometry_to_traces(geom, name, color)
    return traces

# ─────────────────────────────────────────
# MAIN RESOLVER
# ─────────────────────────────────────────
COLORS = ["#e63946", "#457b9d", "#2a9d8f", "#e9c46a", "#f4a261", "#6a4c93", "#06d6a0"]

def resolve_location(raw_location: str):
    """
    Resolve a raw Location string to Plotly traces + map center.
    Handles comma-separated multi-locations. Results cached to disk.
    """
    if raw_location in geo_cache:
        return _rebuild_from_cache(raw_location)

    parts = [p.strip() for p in raw_location.split(",") if p.strip()]

    all_traces = []
    all_centers = []

    for i, part in enumerate(parts):
        color = COLORS[i % len(COLORS)]
        traces, center = _resolve_single(part, color)
        all_traces += traces
        if center:
            all_centers.append(center)

    geo_cache[raw_location] = _serialize(all_traces, all_centers)
    save_cache()

    return all_traces, _mean_center(all_centers)

def _resolve_single(part: str, color: str):
    """Resolve one location name. Returns (traces, center) or ([], None)."""
    override = LOCATION_OVERRIDES.get(part)

    # ── Hardcoded coordinates (no pin shown) ──
    if override and override["type"] == "coords":
        pt = (override["lat"], override["lon"])
        return [], pt  # empty traces = no pin, but center is still set

    # ── Explicit point override ──
    if override and override["type"] == "point":
        pt = geocode_point(override["query"])
        if pt:
            traces = [go.Scattermapbox(
                lon=[pt[1]], lat=[pt[0]],
                mode="markers",
                marker=dict(size=16, color=color),
                name=part, hoverinfo="name",
            )]
            return traces, pt
        return [], None

    # ── Explicit STREET override ──
    elif override and override["type"] == "street":
        try:
            street_full_query = override["query"]
            parts_split = [p.strip() for p in street_full_query.split(",")]
            street_name = parts_split[0]       # "Corrigan Drive"
            place_name  = ", ".join(parts_split[1:])  # "South Park Township, ..."
    
            G = ox.graph_from_place(place_name, network_type="drive")
            edges = ox.graph_to_gdfs(G, nodes=False, edges=True)
    
            # handle name column that may contain str OR list
            def name_matches(x, target):
                target_lower = target.lower()
                if isinstance(x, list):
                    return any(isinstance(n, str) and target_lower in n.lower() for n in x)
                return isinstance(x, str) and target_lower in x.lower()
    
            roads = edges[edges["name"].apply(lambda x: name_matches(x, street_name))]
    
            if not roads.empty:
                traces = gdf_to_traces(roads, part, color)
                centroid = roads.geometry.unary_union.centroid
                return traces, (centroid.y, centroid.x)

        except Exception as e:
            print(f"[street error] {override['query']}: {e}")

        # Fallback to pin
        pt = geocode_point(override["query"])
        if pt:
            traces = [go.Scattermapbox(
                lon=[pt[1]], lat=[pt[0]],
                mode="markers",
                marker=dict(size=16, color=color),
                name=part, hoverinfo="name",
            )]
            return traces, pt
        return [], None

    # ── Explicit BOUNDARY override ──
    elif override and override["type"] == "boundary":
        gdf = fetch_osm_polygon(override["query"])
        if gdf is not None and not gdf.empty:
            traces = gdf_to_traces(gdf, part, color)
            centroid = gdf.geometry.centroid.iloc[0]
            time.sleep(0.3)
            return traces, (centroid.y, centroid.x)
        # Boundary polygon not found — fall back to a pin
        pt = geocode_point(override["query"])
        if pt:
            traces = [go.Scattermapbox(
                lon=[pt[1]], lat=[pt[0]],
                mode="markers",
                marker=dict(size=16, color=color),
                name=part, hoverinfo="name",
            )]
            return traces, pt
        return [], None

    # ── No override: try OSM polygon first, then pin ──
    else:
        gdf = fetch_osm_polygon(part)
        if gdf is not None and not gdf.empty:
            traces = gdf_to_traces(gdf, part, color)
            centroid = gdf.geometry.centroid.iloc[0]
            time.sleep(0.3)
            return traces, (centroid.y, centroid.x)

        pt = geocode_point(f"{part}, {SEARCH_AREA}")
        if pt:
            traces = [go.Scattermapbox(
                lon=[pt[1]], lat=[pt[0]],
                mode="markers",
                marker=dict(size=16, color=color),
                name=part, hoverinfo="name",
            )]
            return traces, pt

        return [], None

# ─────────────────────────────────────────
# CACHE HELPERS
# ─────────────────────────────────────────
def _serialize(traces, centers):
    return {
        "centers": centers,
        "traces": [t.to_plotly_json() for t in traces],
    }

def _rebuild_from_cache(raw_location: str):
    cached = geo_cache[raw_location]
    centers = cached["centers"]
    traces = []
    for td in cached["traces"]:
        t = go.Scattermapbox(
            lon=td.get("lon", []),
            lat=td.get("lat", []),
            mode=td.get("mode", "markers"),
            name=td.get("name", ""),
            fill=td.get("fill", "none"),
            fillcolor=td.get("fillcolor", "rgba(0,0,0,0)"),
            line=td.get("line", {}),
            marker=td.get("marker", {}),
            hoverinfo=td.get("hoverinfo", "name"),
        )
        traces.append(t)
    return traces, _mean_center(centers)

def _mean_center(centers):
    if not centers:
        return (40.44, -79.99)  # default: Allegheny County
    lats = [c[0] for c in centers]
    lons = [c[1] for c in centers]
    return (sum(lats) / len(lats), sum(lons) / len(lons))

# ─────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────
df = pd.read_excel(EXCEL_FILE, sheet_name="FinalSheet")
df.columns = df.columns.str.strip()
df["Grant Amount"] = (
    df["Grant Amount"].replace(r'[\$,]', '', regex=True).astype(float)
)
df["Project Category 2"] = df["Project Category 2"].replace("N/A", pd.NA)
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
df["All Categories"] = df[["Project Category 1", "Project Category 2"]].apply(
    lambda x: [c for c in x if pd.notna(c)], axis=1
)

categories = sorted(set(c for sub in df["All Categories"] for c in sub))
years      = sorted(df["Year"].dropna().unique())
locations  = sorted(df["Location"].dropna().unique())

DETAIL_COLS = [
    c for c in ["Description", "Grant Description", "Notes", "Recipient", "Organization"]
    if c in df.columns
]

# ─────────────────────────────────────────
# DASH APP
# ─────────────────────────────────────────
app = Dash(__name__, suppress_callback_exceptions=True)
server = app.server

CARD_STYLE = {
    "background": "#ffffff",
    "borderRadius": "8px",
    "padding": "10px 14px",
    "marginBottom": "6px",
    "boxShadow": "0 1px 4px rgba(0,0,0,0.10)",
    "cursor": "pointer",
    "fontSize": "13px",
    "border": "1px solid #e4e4e4",
    "transition": "background 0.15s",
}

app.layout = html.Div([

    # ── Header ──
    html.Div([
        html.H1("Grant Allocation Map Explorer",
                style={"margin": 0, "fontFamily": "Georgia, serif",
                       "fontSize": "24px", "color": "#1a1a2e"}),
        html.P("Allegheny County  |  Clean Air Fund",
               style={"margin": "3px 0 0", "color": "#666", "fontSize": "13px"}),
    ], style={
        "padding": "16px 24px 12px",
        "borderBottom": "2px solid #1a1a2e",
        "backgroundColor": "#f7f7f2",
    }),

    html.Div([

        # ── LEFT PANEL: filters + project list ──
        html.Div([
            html.H3("Filters", style={
                "marginTop": 0, "fontSize": "13px",
                "textTransform": "uppercase", "letterSpacing": "1px", "color": "#555",
            }),

            html.Label("Category", style={"fontSize": "12px", "color": "#777"}),
            dcc.Dropdown(
                id="cat_filter",
                options=[{"label": c, "value": c} for c in categories],
                value=categories, multi=True,
                style={"marginBottom": "12px", "fontSize": "12px"},
            ),

            html.Label("Year", style={"fontSize": "12px", "color": "#777"}),
            dcc.Dropdown(
                id="year_filter",
                options=[{"label": str(int(y)), "value": y} for y in years],
                value=years, multi=True,
                style={"marginBottom": "12px", "fontSize": "12px"},
            ),

            html.Label("Location", style={"fontSize": "12px", "color": "#777"}),
            dcc.Dropdown(
                id="loc_filter",
                options=[{"label": l, "value": l} for l in locations],
                value=locations, multi=True,
                style={"marginBottom": "16px", "fontSize": "12px"},
            ),

            html.Hr(style={"borderColor": "#ddd", "margin": "0 0 12px"}),

            html.H3("Projects", style={
                "fontSize": "13px", "textTransform": "uppercase",
                "letterSpacing": "1px", "color": "#555", "margin": "0 0 10px",
            }),

            html.Div(id="project_list", style={
                "maxHeight": "calc(100vh - 420px)",
                "overflowY": "auto",
                "paddingRight": "4px",
            }),

        ], style={
            "width": "300px",
            "minWidth": "260px",
            "padding": "18px 16px",
            "backgroundColor": "#f7f7f2",
            "borderRight": "1px solid #ddd",
            "overflowY": "auto",
            "height": "calc(100vh - 72px)",
            "boxSizing": "border-box",
        }),

        # ── RIGHT PANEL: detail card + map ──
        html.Div([
            html.Div(id="project_detail", style={
                "padding": "14px 22px",
                "backgroundColor": "#ffffff",
                "borderBottom": "1px solid #e0e0e0",
                "maxHeight": "160px",
                "overflowY": "auto",
                "boxSizing": "border-box",
                "flexShrink": 0,
            }),

            dcc.Graph(
                id="map",
                style={"height": "calc(100vh - 232px)", "flex": 1},
                config={"scrollZoom": True},
            ),

        ], style={"flex": 1, "display": "flex", "flexDirection": "column"}),

    ], style={
        "display": "flex",
        "height": "calc(100vh - 72px)",
        "overflow": "hidden",
    }),

    dcc.Store(id="selected_idx", data=None),

], style={
    "fontFamily": "system-ui, -apple-system, sans-serif",
    "height": "100vh",
    "overflow": "hidden",
    "backgroundColor": "#f0ede8",
})

# ─────────────────────────────────────────
# CALLBACK: Project list
# ─────────────────────────────────────────
@app.callback(
    Output("project_list", "children"),
    Input("cat_filter", "value"),
    Input("year_filter", "value"),
    Input("loc_filter", "value"),
)
def update_list(cats, yrs, locs):
    no_match = [html.P("No projects match the current filters.",
                       style={"color": "#999", "fontSize": "13px"})]
    if not cats or not yrs or not locs:
        return no_match

    filtered = df[df["Year"].isin(yrs) & df["Location"].isin(locs)]
    filtered = filtered[
        filtered["All Categories"].apply(lambda x: any(c in cats for c in x))
    ]

    if filtered.empty:
        return no_match

    items = []
    for i, row in filtered.iterrows():
        cat_label = row["Project Category 1"]
        if pd.notna(row.get("Project Category 2", pd.NA)):
            cat_label += f", {row['Project Category 2']}"
        year_str = str(int(row["Year"])) if pd.notna(row["Year"]) else "?"

        items.append(html.Div([
            html.Div(row["Location"],
                     style={"fontWeight": "600", "color": "#1a1a2e",
                            "marginBottom": "3px", "lineHeight": "1.3"}),
            html.Div(
                f"${row['Grant Amount']:,.0f}  ·  {year_str}",
                style={"color": "#e63946", "fontWeight": "700", "fontSize": "12px"},
            ),
            html.Div(cat_label,
                     style={"color": "#777", "fontSize": "11px", "marginTop": "2px"}),
        ],
        id={"type": "proj_btn", "index": int(i)},
        n_clicks=0,
        style=CARD_STYLE,
        ))

    return items

# ─────────────────────────────────────────
# CALLBACK: Store selected project index
# Uses callback_context to detect exactly which button was clicked,
# rather than guessing from max(n_clicks) which is unreliable.
# ─────────────────────────────────────────
@app.callback(
    Output("selected_idx", "data"),
    Input({"type": "proj_btn", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def store_selected(clicks):
    if not callback_context.triggered:
        return None

    # prop_id looks like: '{"index":5,"type":"proj_btn"}.n_clicks'
    triggered_id = callback_context.triggered[0]["prop_id"]

    try:
        # Strip the '.n_clicks' suffix, then parse the JSON dict
        id_part = triggered_id.rsplit(".", 1)[0]
        parsed = json.loads(id_part)
        return parsed["index"]
    except Exception:
        return None

# ─────────────────────────────────────────
# CALLBACK: Update map + detail card
# ─────────────────────────────────────────
@app.callback(
    Output("map", "figure"),
    Output("project_detail", "children"),
    Input("selected_idx", "data"),
)
def update_map(idx):

    def empty_fig():
        fig = go.Figure(go.Scattermapbox())
        fig.update_layout(
            mapbox=dict(style="carto-positron",
                        center=dict(lat=40.44, lon=-79.99), zoom=10),
            margin=dict(r=0, t=0, l=0, b=0),
            showlegend=False,
            paper_bgcolor="#f0ede8",
        )
        return fig

    if idx is None:
        placeholder = html.P(
            "← Select a project from the list to view its location on the map.",
            style={"color": "#999", "margin": 0, "fontSize": "14px"},
        )
        return empty_fig(), placeholder

    row = df.iloc[int(idx)]
    location_raw = row["Location"]

    try:
        traces, (clat, clon) = resolve_location(location_raw)
    except Exception as err:
        print(f"[geo error] {location_raw}: {err}")
        traces, (clat, clon) = [], (40.44, -79.99)

    fig = go.Figure(data=traces or [go.Scattermapbox()])

    # Compute bounding box from all trace coordinates to fit all locations
    import math
    all_lats, all_lons = [], []
    for trace in (traces or []):
        for v in (trace.lat or []):
            if v is not None:
                all_lats.append(v)
        for v in (trace.lon or []):
            if v is not None:
                all_lons.append(v)

    # Override zoom for specific locations
    ZOOM_OVERRIDES = {
        "Allegheny County": (40.44, -79.99, 8.5),
        "Munhall Borough": (40.395, -79.895, 12),
        "Monongahela River Valley": (40.25, -79.95, 7.5),
        "Northgate School District": (40.50, -80.05688569633367, 13),
        "CCAC Allegheny Campus, CCAC North Campus, CCAC Boyce Campus, CCAC South Campus": (40.44, -79.99, 9.5),
    }

    if location_raw in ZOOM_OVERRIDES:
        clat, clon, zoom = ZOOM_OVERRIDES[location_raw]
    elif all_lats and all_lons:
        min_lat, max_lat = min(all_lats), max(all_lats)
        min_lon, max_lon = min(all_lons), max(all_lons)
        clat = (min_lat + max_lat) / 2
        clon = (min_lon + max_lon) / 2
        lat_span = max_lat - min_lat
        lon_span = max_lon - min_lon
        max_span = max(lat_span, lon_span)
        if max_span == 0:
            zoom = 15
        elif max_span < 0.005:
            zoom = 15
        elif max_span < 0.01:
            zoom = 15
        elif max_span < 0.05:
            zoom = 13
        elif max_span < 0.15:
            zoom = 11
        elif max_span < 0.4:
            zoom = 10
        elif max_span < 1.0:
            zoom = 9
        else:
            zoom = 8
    else:
        clat, clon = 40.44, -79.99
        zoom = 10

    fig.update_layout(
        mapbox=dict(
            style="carto-positron",
            center=dict(lat=clat, lon=clon),
            zoom=zoom,
        ),
        margin=dict(r=0, t=0, l=0, b=0),
        showlegend=len(traces) > 1 and location_raw != "Corrigan Dr. in South Park",
        paper_bgcolor="#f0ede8",
        legend=dict(
            bgcolor="rgba(255,255,255,0.88)",
            bordercolor="#ccc",
            borderwidth=1,
            font=dict(size=12),
            x=0.01, y=0.99,
        ),
    )

    # Detail card
    year_str = str(int(row["Year"])) if pd.notna(row["Year"]) else "N/A"
    date_str = row["Date"].strftime("%B %d, %Y") if pd.notna(row["Date"]) else year_str
    cat_parts = [str(row["Project Category 1"])]
    if pd.notna(row.get("Project Category 2", pd.NA)):
        cat_parts.append(str(row["Project Category 2"]))

    detail_children = [
        html.Div([
            html.Span(location_raw, style={
                "fontWeight": "700", "fontSize": "16px", "color": "#1a1a2e",
            }),
            html.Span(f"  ${row['Grant Amount']:,.0f}", style={
                "fontWeight": "700", "fontSize": "16px",
                "color": "#e63946", "marginLeft": "10px",
            }),
        ]),
        html.Div([
            html.Span("Date: ", style={"fontWeight": "700", "color": "#444"}),
            html.Span(date_str, style={"color": "#444"}),
        ], style={"fontSize": "12px", "marginTop": "5px"}),
        html.Div([
            html.Span(f"{'Categories' if len(cat_parts) > 1 else 'Category'}: ", style={"fontWeight": "700", "color": "#444"}),
            html.Span(', '.join(cat_parts), style={"color": "#444"}),
        ], style={"fontSize": "12px", "marginTop": "3px"}),
    ]

    for col in DETAIL_COLS:
        val = row.get(col, pd.NA)
        if pd.notna(val) and str(val).strip():
            detail_children.append(html.Div([
                html.Span(f"{col}: ", style={"fontWeight": "700", "color": "#444"}),
                html.Span(str(val), style={"color": "#444"}),
            ], style={"fontSize": "12px", "marginTop": "3px"}))

    # Project Description last, below Organization
    proj_desc = row.get("Project Description")
    if pd.notna(proj_desc) and str(proj_desc).strip():
        detail_children.append(html.Div([
            html.Span("Project Description: ", style={"fontWeight": "700", "color": "#444"}),
            html.Span(str(proj_desc), style={"color": "#444"}),
        ], style={"fontSize": "12px", "marginTop": "3px"}))

    return fig, html.Div([c for c in detail_children if c is not None])

# ─────────────────────────────────────────
# RUN
# ─────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, port=8050)

