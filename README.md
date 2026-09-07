# AI-Integrated 5D Project Control System
Automated Quantity Takeoff, Cost Estimation, Resource Scheduling and Cash Flow
Forecasting from 2D Construction Drawings

**M.E. Construction Engineering & Management — Semester 3 Project**
Thirumalai Engineering College (Affiliated to Anna University)
Student: S. Thameahwaran (Reg. No. 513225418013) | Guide & HoD: Prof. Dhevan

---

## Running locally on your MacBook (macOS, Intel or Apple Silicon)

### 1. Prerequisites
Check Python 3 is installed:
```bash
python3 --version
```
If not installed, get it from https://www.python.org/downloads/macos/ (Python 3.10+ recommended).

### 2. Set up the project
Unzip the project folder, then in Terminal:
```bash
cd path/to/app
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

### 3. Regenerate the demo dataset (already included, but you can rebuild it)
```bash
cd data
python3 generate_data.py
python3 make_sample_plan.py
cd ..
```

### 4. Run the app
```bash
python3 app.py
```
You should see:
```
Starting local server at http://127.0.0.1:5050
```
Open that link in Chrome/Safari. The dashboard loads instantly — no internet
connection is required except for the Google Fonts / Chart.js CDN calls used
purely for styling and charts (the app works fully offline if you pre-cache
those, or swap in local copies before a venue with no Wi-Fi).

### 5. Demo flow for the examiner
1. **Overview** — project profile and cumulative cost S-curve.
2. **AI Quantity Takeoff** — click "Use Sample Plan" then "Run AI Takeoff" to
   show live computer-vision room detection from the 2D drawing.
3. **BOQ & Cost** — full 40-item Bill of Quantities with category cost
   breakdown charts.
4. **Schedule & Resources** — Gantt chart + day-wise labour/material/machinery
   requirement table.
5. **Delay Risk (AI)** — change the risk sliders (e.g., increase monsoon
   exposure days) and click **Predict Delay Risk** to show the Random Forest
   model responding live.
6. **Cash Flow Forecast** — weekly/monthly S-curve and peak fund requirement.

---

## Optional: Deploying a public link (Render.com)

The app is designed to run **locally** for your viva — this section is only if you also want a
shareable public URL (e.g. to send your HOD without opening your laptop).

**Note:** GitHub Pages **cannot** run this app — it only serves static HTML/CSS/JS, and this is a
Python/Flask application that needs a real server to run OpenCV and the ML model. Use a Python-
capable host instead:

1. Push this `app/` folder to a GitHub repository (make sure `requirements.txt`, `Procfile`, and
   `app.py` are at the repo root, or point Render at this subfolder).
2. Go to [render.com](https://render.com) → New → Web Service → connect your GitHub repo.
3. Render auto-detects the `Procfile`. If asked manually:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `gunicorn app:app --bind 0.0.0.0:$PORT`
4. Deploy. Render assigns a public URL like `https://your-app.onrender.com`.

The code already reads the `PORT` environment variable and switches to production mode
automatically when deployed — no further changes needed. Free-tier Render services sleep after
inactivity and take ~30-60 seconds to wake on the first request; this is normal.

## Project structure
```
app/
├── app.py                  Flask server + API routes + OpenCV QTO logic
├── requirements.txt
├── templates/index.html    Dashboard markup
├── static/css/style.css    Design system (blueprint-navy theme)
├── static/js/app.js        Frontend logic, Chart.js rendering
├── assets/                 Sample floor-plan image
└── data/
    ├── generate_data.py    Generates BOQ, schedule, cash flow, ML training data
    ├── make_sample_plan.py Generates the demo 2D floor-plan image
    ├── boq.csv / boq.json
    ├── schedule.csv / schedule.json
    ├── daily_resources.csv
    ├── weekly_cashflow.csv / monthly_cashflow.csv
    ├── historical_projects.csv     (260 synthetic past projects)
    ├── delay_model.pkl             (trained Random Forest bundle)
    └── project_meta.json
```

## Notes on the data
All figures (BOQ rates, schedule durations, historical project records) are
**realistic synthetic data** modelled on TNPWD/CPWD-style schedules of rates
and standard construction productivity norms, since no real client project
data was available at the time of this Semester 3 submission. Section 3.6 of
the project report documents every assumption. Real project data collected
during the author's freelance QS practice can be substituted directly into
`data/boq.csv` and `data/historical_projects.csv` in Semester 4 without any
code changes, as the app reads these files at startup.
