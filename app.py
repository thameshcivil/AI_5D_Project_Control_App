"""
AI-Integrated 5D Project Control System
Automated Quantity Takeoff, Cost Estimation, Resource Scheduling and Cash Flow
Forecasting from 2D Construction Drawings

M.E. Construction Engineering & Management - Semester 3 Project
Author: S. Thameahwaran (Reg. No. 513225418013)
Guide: Prof. Dhevan, HoD
Thirumalai Engineering College (Affiliated to Anna University)

Run locally:
    cd app
    pip3 install -r requirements.txt
    python3 app.py
Then open http://127.0.0.1:5050 in your browser.
"""
import os
import io
import json
import pickle
import base64

import numpy as np
import pandas as pd
import cv2
from flask import Flask, jsonify, request, render_template, send_from_directory

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

app = Flask(__name__)

# ------------------------------------------------------------------
# Load all pre-generated data once at startup
# ------------------------------------------------------------------
def _read_csv(name):
    return pd.read_csv(os.path.join(DATA_DIR, name))

boq_df = _read_csv("boq.csv")
schedule_df = _read_csv("schedule.csv")
daily_resources_df = _read_csv("daily_resources.csv")
weekly_cf_df = _read_csv("weekly_cashflow.csv")
monthly_cf_df = _read_csv("monthly_cashflow.csv")
daily_cf_df = _read_csv("daily_cashflow.csv")
historical_df = _read_csv("historical_projects.csv")

with open(os.path.join(DATA_DIR, "project_meta.json")) as f:
    project_meta = json.load(f)

with open(os.path.join(DATA_DIR, "delay_model_meta.json")) as f:
    delay_model_meta = json.load(f)

with open(os.path.join(DATA_DIR, "delay_model.pkl"), "rb") as f:
    _model_bundle = pickle.load(f)
    clf_model = _model_bundle["classifier"]
    reg_model = _model_bundle["regressor"]
    label_encoder = _model_bundle["label_encoder"]
    feature_cols = _model_bundle["features"]

RATE_PER_SQM_CONST = {  # used to translate detected area -> quick BOQ estimate in QTO demo
    "brickwork_cum_per_sqm_wall": 0.23,  # 230mm thick wall -> cum per sqm of wall face
}


# ------------------------------------------------------------------
# Page routes
# ------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html", meta=project_meta)


@app.route("/assets/<path:filename>")
def assets(filename):
    return send_from_directory(ASSETS_DIR, filename)


# ------------------------------------------------------------------
# API: project overview
# ------------------------------------------------------------------
@app.route("/api/overview")
def api_overview():
    total_cost = float(boq_df["amount_inr"].sum())
    return jsonify({
        "meta": project_meta,
        "total_project_cost": round(total_cost, 0),
        "boq_item_count": int(len(boq_df)),
        "schedule_activity_count": int(len(schedule_df)),
        "cost_per_sqm": round(total_cost / project_meta["total_builtup_area_sqm"], 0),
        "delay_model_accuracy": delay_model_meta["classifier_accuracy"],
        "delay_model_auc": delay_model_meta["classifier_auc"],
    })


# ------------------------------------------------------------------
# API: BOQ
# ------------------------------------------------------------------
@app.route("/api/boq")
def api_boq():
    cat_summary = boq_df.groupby("category")["amount_inr"].sum().sort_values(ascending=False)
    return jsonify({
        "items": boq_df.to_dict(orient="records"),
        "total_cost": round(float(boq_df["amount_inr"].sum()), 0),
        "category_summary": [{"category": k, "amount": round(float(v), 0)} for k, v in cat_summary.items()],
    })


# ------------------------------------------------------------------
# API: Schedule / Gantt + day-wise resources
# ------------------------------------------------------------------
@app.route("/api/schedule")
def api_schedule():
    return jsonify({"activities": schedule_df.to_dict(orient="records")})


@app.route("/api/resources/daily")
def api_daily_resources():
    limit = request.args.get("limit", type=int)
    df = daily_resources_df.copy()
    if limit:
        df = df.head(limit)
    return jsonify({"rows": df.to_dict(orient="records")})


@app.route("/api/resources/summary")
def api_resource_summary():
    peak_mason = int(daily_resources_df["mason"].max())
    peak_helper = int(daily_resources_df["helper"].max())
    peak_date_mason = daily_resources_df.loc[daily_resources_df["mason"].idxmax(), "date"]
    total_cement = round(float(daily_resources_df["cement_bags"].sum()), 0)
    total_steel = round(float(daily_resources_df["steel_kg"].sum()), 0)
    total_bricks = round(float(daily_resources_df["bricks_nos"].sum()), 0)
    return jsonify({
        "peak_mason": peak_mason, "peak_helper": peak_helper, "peak_date_mason": peak_date_mason,
        "total_cement_bags": total_cement, "total_steel_kg": total_steel, "total_bricks": total_bricks,
    })


# ------------------------------------------------------------------
# API: Cash flow
# ------------------------------------------------------------------
@app.route("/api/cashflow/weekly")
def api_cashflow_weekly():
    return jsonify({"rows": weekly_cf_df.to_dict(orient="records")})


@app.route("/api/cashflow/monthly")
def api_cashflow_monthly():
    return jsonify({"rows": monthly_cf_df.to_dict(orient="records")})


# ------------------------------------------------------------------
# API: Delay Risk Prediction (Random Forest)
# ------------------------------------------------------------------
@app.route("/api/delay/meta")
def api_delay_meta():
    return jsonify(delay_model_meta)


@app.route("/api/delay/predict", methods=["POST"])
def api_delay_predict():
    payload = request.get_json(force=True)
    try:
        risk_enc = label_encoder.transform([payload.get("material_delay_risk", "Medium")])[0]
    except Exception:
        risk_enc = 1

    row = {
        "planned_duration_days": float(payload.get("planned_duration_days", 245)),
        "num_floors": float(payload.get("num_floors", 3)),
        "monsoon_exposure_days": float(payload.get("monsoon_exposure_days", 20)),
        "labour_availability_pct": float(payload.get("labour_availability_pct", 80)),
        "material_delay_risk_enc": float(risk_enc),
        "contractor_experience_years": float(payload.get("contractor_experience_years", 8)),
        "site_accessibility_score": float(payload.get("site_accessibility_score", 7)),
        "design_change_frequency": float(payload.get("design_change_frequency", 2)),
        "funding_regularity_score": float(payload.get("funding_regularity_score", 7)),
        "permit_delay_days": float(payload.get("permit_delay_days", 10)),
    }
    X = pd.DataFrame([row])[feature_cols]
    proba = float(clf_model.predict_proba(X)[0][1])
    expected_delay_days = float(reg_model.predict(X)[0])
    importances = dict(zip(feature_cols, clf_model.feature_importances_.round(4)))
    top_factors = sorted(importances.items(), key=lambda kv: kv[1], reverse=True)[:5]

    risk_band = "Low" if proba < 0.35 else ("Medium" if proba < 0.65 else "High")

    return jsonify({
        "delay_probability_pct": round(proba * 100, 1),
        "risk_band": risk_band,
        "expected_delay_days": round(expected_delay_days, 1),
        "top_factors": [{"factor": k, "importance": v} for k, v in top_factors],
        "input_used": row,
    })


# ------------------------------------------------------------------
# API: AI Quantity Takeoff from an uploaded 2D drawing (OpenCV)
# ------------------------------------------------------------------
def _detect_rooms(gray, min_area_px=3000):
    """Rule-based CV pipeline: binarize -> find contours -> approximate
    polygons -> keep near-rectangular closed regions as candidate rooms."""
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, th = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    # thicken lines so wall gaps (doors) get bridged for contour closure
    kernel = np.ones((7, 7), np.uint8)
    closed = cv2.morphologyEx(th, cv2.MORPH_CLOSE, kernel, iterations=2)

    contours, hierarchy = cv2.findContours(closed, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    rooms = []
    if hierarchy is None:
        return rooms
    hierarchy = hierarchy[0]
    for i, cnt in enumerate(contours):
        area = cv2.contourArea(cnt)
        if area < min_area_px:
            continue
        # only inner contours (holes) represent enclosed rooms, not the outer wall silhouette
        if hierarchy[i][3] == -1:
            continue
        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
        x, y, w, h = cv2.boundingRect(cnt)
        rooms.append({
            "area_px": float(area),
            "bbox": [int(x), int(y), int(w), int(h)],
            "vertices": len(approx),
            "perimeter_px": float(peri),
        })
    return rooms


@app.route("/api/qto/analyze", methods=["POST"])
def api_qto_analyze():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400
    file = request.files["image"]
    px_per_m = float(request.form.get("px_per_m", 60))
    wall_height_m = float(request.form.get("wall_height_m", 3.0))

    file_bytes = np.frombuffer(file.read(), np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    if img is None:
        return jsonify({"error": "Could not decode image"}), 400
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    rooms = _detect_rooms(gray)
    scale_sqm_per_px2 = 1.0 / (px_per_m ** 2)

    results = []
    total_area_sqm = 0.0
    total_perimeter_m = 0.0
    for idx, r in enumerate(rooms, start=1):
        area_sqm = round(r["area_px"] * scale_sqm_per_px2, 2)
        perimeter_m = round(r["perimeter_px"] / px_per_m, 2)
        total_area_sqm += area_sqm
        total_perimeter_m += perimeter_m
        results.append({
            "room_id": f"R{idx}",
            "area_sqm": area_sqm,
            "perimeter_m": perimeter_m,
            "bbox_px": r["bbox"],
        })

    # Derived quick quantities for cross-check against manual QS take-off
    wall_length_m = round(total_perimeter_m / 2, 2)  # shared-wall approx correction
    brick_wall_volume_cum = round(wall_length_m * wall_height_m * 0.23, 2)
    plaster_area_sqm = round(total_area_sqm * 2.6, 2)  # rough internal wall+ceiling plaster proxy
    flooring_area_sqm = round(total_area_sqm, 2)

    return jsonify({
        "rooms_detected": len(results),
        "rooms": results,
        "total_carpet_area_sqm": round(total_area_sqm, 2),
        "estimated_wall_length_m": wall_length_m,
        "estimated_brickwork_volume_cum": brick_wall_volume_cum,
        "estimated_plaster_area_sqm": plaster_area_sqm,
        "estimated_flooring_area_sqm": flooring_area_sqm,
        "calibration_px_per_m": px_per_m,
    })


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5050))
    is_local = os.environ.get("PORT") is None  # no PORT var set -> assume local dev machine

    print("=" * 70)
    print(" AI-Integrated 5D Project Control System")
    if is_local:
        print(f" Starting local server at http://127.0.0.1:{port}")
    else:
        print(f" Starting server on 0.0.0.0:{port} (cloud deployment)")
    print("=" * 70)

    app.run(host="0.0.0.0", port=port, debug=is_local)
