# GASP Clean Air Fund — Grant Allocation Dashboard

This project was developed for the **Group Against Smog and Pollution (GASP)**, a prominent Pittsburgh-based non-profit organization founded in 1969, dedicated to fighting for clean air in Southwestern Pennsylvania.

The dashboard provides an interactive map and data visualizations exploring GASP's Clean Air Fund grant allocations across Allegheny County from 2015 to 2024.

---

## Live Map
The interactive grant allocation map is live and accessible here:
**https://gasp-clean-air-map.onrender.com**

Note: The map is hosted on Render's free tier. If the app has been inactive, it may take up to 30 seconds to load on the first visit.

---

## File Descriptions

| File | Description |
|---|---|
| `map.py` | Main interactive map application built with Dash and Plotly. Displays grant locations on a map with filters by category, year, and location. |
| `charts.ipynb` | Jupyter notebook containing all data visualizations and charts analyzing grant spending trends, categories, and organizations. |
| `charts.html` | Exported HTML version of the charts for easy viewing without running code. |
| `FinalSheet.xlsx` | The cleaned grant allocation dataset covering 2015–2024, including grant amounts, locations, organizations, categories, and project descriptions. |
| `geo_cache.json` | Cached geographic boundary data from OpenStreetMap, used to speed up map loading. |
| `requirements.txt` | Python dependencies required to run the map application. |
| `Procfile` | Configuration file for Render deployment. |
| `GASP Clean Air Fund Wireframe.pdf` | Original project wireframe and design reference. |

---

## Running the Map

The map is deployed and accessible at:
**https://gasp-clean-air-map.onrender.com**

To run locally, ensure Python 3.8+ is installed, then:

Step 1 — Install dependencies:
```bash
pip install -r requirements.txt
```

Step 2 — Run the app:
```bash
python map.py
```

Step 3 — Open in your browser and navigate to the local address shown in the terminal output.

---

## Data

The dataset (`FinalSheet.xlsx`) contains 69 grant allocations from 2015 to 2024, totaling **$17,389,785** in Clean Air Fund grants across Allegheny County. Each record includes:
- Grant amount and date
- Project category
- Recipient organization
- Location
- Project description

---

## Team

This project was developed by students at the University of Pittsburgh:

- Abby Gopal
- Neha Kotha
- Hannah Kwee
- Lasya Nedunuri

---

Built with Python, Dash, Plotly, and OpenStreetMap.