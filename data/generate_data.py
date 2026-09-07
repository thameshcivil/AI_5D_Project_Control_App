"""
Synthetic-but-realistic data generator for the AI-Integrated 5D Project Control System.
Project: G+2 Residential Apartment Building, "Thameahwaran Residency"
Location: Tamil Nadu (rates approximate TNPWD SOR 2025-26 style, INR)

Run: python3 generate_data.py
Outputs (in this folder):
  boq.csv, boq.json
  schedule.csv, schedule.json
  daily_resources.csv
  weekly_cashflow.csv, monthly_cashflow.csv
  historical_projects.csv   (for delay-risk ML model)
  delay_model.pkl, delay_model_meta.json
  project_meta.json
"""
import json
import random
import numpy as np
import pandas as pd
from datetime import date, timedelta

random.seed(42)
np.random.seed(42)

# ----------------------------------------------------------------------
# 1. PROJECT META
# ----------------------------------------------------------------------
project_meta = {
    "project_name": "Thameahwaran Residency",
    "project_type": "G+2 Residential Apartment Building (RCC Framed Structure)",
    "plot_size_sqm": 216.0,
    "plot_dims": "12.0 m x 18.0 m",
    "builtup_area_per_floor_sqm": 180.0,
    "num_floors": 3,
    "total_builtup_area_sqm": 540.0,
    "num_units": 6,
    "location": "Chennai, Tamil Nadu",
    "start_date": "2026-01-05",
    "estimated_duration_days": 210,
    "structure_type": "RCC Framed Structure with brick masonry infill",
    "foundation_type": "Isolated RCC footing",
}
with open("project_meta.json", "w") as f:
    json.dump(project_meta, f, indent=2)

# ----------------------------------------------------------------------
# 2. BILL OF QUANTITIES (BOQ) - realistic TNPWD-style SOR items
# ----------------------------------------------------------------------
boq_items = [
    # (Sl, Item description, Unit, Quantity, Rate_INR)
    ("1", "Site clearance and layout marking", "sqm", 216.0, 18.0),
    ("2", "Earthwork excavation for foundation in ordinary soil, up to 1.5m depth", "cum", 168.0, 210.0),
    ("3", "PCC (1:4:8) bed for footings, 100mm thick", "cum", 21.6, 4650.0),
    ("4", "RCC M25 for isolated footings incl. formwork & reinforcement", "cum", 38.4, 8250.0),
    ("5", "RCC M25 for column footings pedestal", "cum", 9.6, 8450.0),
    ("6", "Backfilling with excavated earth, consolidated in layers", "cum", 96.0, 145.0),
    ("7", "RCC M25 for columns (G+2), incl. formwork & reinforcement", "cum", 64.8, 9200.0),
    ("8", "RCC M25 for plinth beam", "cum", 14.2, 8900.0),
    ("9", "Brick masonry in CM 1:6 for plinth wall, 230mm thick", "cum", 22.5, 5450.0),
    ("10", "Damp proof course (DPC) 40mm thick, CC 1:2:4 with waterproofing compound", "sqm", 62.0, 320.0),
    ("11", "RCC M25 for beams (all floors), incl. formwork & reinforcement", "cum", 58.6, 9350.0),
    ("12", "RCC M25 for slabs (all floors), 125mm thick, incl. formwork & reinforcement", "cum", 91.1, 9050.0),
    ("13", "RCC M25 for staircase waist slab and steps", "cum", 12.4, 9550.0),
    ("14", "Brick masonry in CM 1:6 for superstructure walls, 230mm thick (all floors)", "cum", 187.5, 5600.0),
    ("15", "Brick masonry in CM 1:6 for partition walls, 115mm thick", "cum", 42.0, 5850.0),
    ("16", "Internal cement plastering, 12mm thick, CM 1:6", "sqm", 1450.0, 175.0),
    ("17", "External cement plastering (sponge finish), 20mm thick, CM 1:4", "sqm", 620.0, 235.0),
    ("18", "Ceiling plastering, 10mm thick, CM 1:4", "sqm", 540.0, 190.0),
    ("19", "Vitrified tile flooring (600x600mm), incl. bedding", "sqm", 486.0, 950.0),
    ("20", "Anti-skid ceramic tile flooring for toilets/balcony", "sqm", 54.0, 720.0),
    ("21", "Granite flooring for staircase and lobby", "sqm", 68.0, 1450.0),
    ("22", "Flush doors with frame (single leaf, 900mm)", "nos", 18.0, 8200.0),
    ("23", "Main door - teak wood frame with panel shutter", "nos", 6.0, 22500.0),
    ("24", "UPVC windows with glass shutters (1200x1200mm)", "nos", 24.0, 9800.0),
    ("25", "Ventilators with glass louvers (600x450mm)", "nos", 12.0, 3200.0),
    ("26", "Internal wall painting - acrylic emulsion, two coats", "sqm", 1450.0, 95.0),
    ("27", "External wall painting - exterior emulsion, two coats with primer", "sqm", 620.0, 135.0),
    ("28", "Enamel painting for doors/windows/grills", "sqm", 210.0, 110.0),
    ("29", "Internal electrical wiring, wiring points (light/fan/plug)", "point", 168.0, 950.0),
    ("30", "Electrical distribution board, MCB, main switch installation", "unit", 6.0, 6500.0),
    ("31", "Concealed plumbing - water supply lines (CPVC)", "point", 42.0, 1650.0),
    ("32", "Sanitary fittings - WC, wash basin, CP fittings (per toilet set)", "set", 6.0, 18500.0),
    ("33", "Drainage and sewer lines, incl. PVC pipes and fittings", "rm", 96.0, 620.0),
    ("34", "Overhead water tank (RCC, 5000L capacity) incl. plumbing", "nos", 1.0, 45000.0),
    ("35", "Terrace waterproofing (brick bat coba + APP membrane)", "sqm", 180.0, 385.0),
    ("36", "MS railing for staircase and balconies", "rm", 58.0, 1850.0),
    ("37", "Compound wall (brick masonry with plaster & paint), 1.8m height", "rm", 60.0, 2450.0),
    ("38", "Gate - MS fabricated with painting", "nos", 1.0, 28000.0),
    ("39", "Site development - paving, minor landscaping", "sqm", 60.0, 620.0),
    ("40", "Miscellaneous works & contingency provision (2.5%)", "LS", 1.0, 0.0),  # computed below
]

boq = pd.DataFrame(boq_items, columns=["sl_no", "description", "unit", "quantity", "rate_inr"])
boq["amount_inr"] = (boq["quantity"] * boq["rate_inr"]).round(2)

subtotal = boq.loc[boq["sl_no"] != "40", "amount_inr"].sum()
contingency = round(subtotal * 0.025, 2)
boq.loc[boq["sl_no"] == "40", "amount_inr"] = contingency
boq.loc[boq["sl_no"] == "40", "rate_inr"] = contingency

# Category tagging for cost-distribution charts
category_map = {
    "1": "Preliminary", "2": "Earthwork", "3": "Substructure", "4": "Substructure",
    "5": "Substructure", "6": "Earthwork", "7": "Superstructure (RCC)", "8": "Superstructure (RCC)",
    "9": "Masonry", "10": "Substructure", "11": "Superstructure (RCC)", "12": "Superstructure (RCC)",
    "13": "Superstructure (RCC)", "14": "Masonry", "15": "Masonry", "16": "Finishing",
    "17": "Finishing", "18": "Finishing", "19": "Finishing", "20": "Finishing", "21": "Finishing",
    "22": "Doors & Windows", "23": "Doors & Windows", "24": "Doors & Windows", "25": "Doors & Windows",
    "26": "Painting", "27": "Painting", "28": "Painting", "29": "Electrical", "30": "Electrical",
    "31": "Plumbing", "32": "Plumbing", "33": "Plumbing", "34": "Plumbing",
    "35": "Waterproofing", "36": "Miscellaneous", "37": "Miscellaneous", "38": "Miscellaneous",
    "39": "Miscellaneous", "40": "Contingency",
}
boq["category"] = boq["sl_no"].map(category_map)

total_project_cost = boq["amount_inr"].sum()
boq.to_csv("boq.csv", index=False)
boq.to_json("boq.json", orient="records", indent=2)

# ----------------------------------------------------------------------
# 3. CONSTRUCTION SCHEDULE (activity-level, sequenced) + day-wise resources
# ----------------------------------------------------------------------
# Productivity norms (CPWD-style output per gang per day) -> duration per activity
activities = [
    # name, category, quantity, unit, output_per_day, mason, helper, barbender, carpenter, machinery, start_offset_days
    ("Site clearance & layout", "Preliminary", 216, "sqm", 120, 0, 4, 0, 0, "Total Station", 0),
    ("Excavation for foundation", "Earthwork", 168, "cum", 14, 0, 10, 0, 0, "JCB Excavator", 2),
    ("PCC bed for footings", "Substructure", 21.6, "cum", 6, 2, 6, 0, 0, "Concrete Mixer", 14),
    ("Footing reinforcement & shuttering", "Substructure", 38.4, "cum", 5.0, 3, 5, 5, 4, "Bar Bending Machine", 18),
    ("Footing concreting", "Substructure", 38.4, "cum", 8, 2, 8, 0, 0, "Concrete Mixer, Vibrator", 26),
    ("Column footing pedestal", "Substructure", 9.6, "cum", 3, 2, 4, 2, 2, "Concrete Mixer", 30),
    ("Backfilling & consolidation", "Earthwork", 96, "cum", 16, 0, 8, 0, 0, "Plate Compactor", 33),
    ("Plinth beam reinforcement & shuttering", "Superstructure (RCC)", 14.2, "cum", 3.0, 2, 4, 3, 3, "Bar Bending Machine", 39),
    ("Plinth beam concreting", "Superstructure (RCC)", 14.2, "cum", 6, 2, 6, 0, 0, "Concrete Mixer, Vibrator", 44),
    ("Plinth masonry", "Masonry", 22.5, "cum", 3.2, 4, 6, 0, 0, "-", 47),
    ("DPC laying", "Substructure", 62, "sqm", 25, 2, 3, 0, 0, "-", 55),
    ("Ground floor columns", "Superstructure (RCC)", 21.6, "cum", 3.6, 3, 5, 4, 4, "Bar Bending Machine", 57),
    ("Ground floor beams & slab shuttering", "Superstructure (RCC)", 30.3, "cum", 3.0, 3, 6, 4, 5, "Tower Hoist", 63),
    ("Ground floor beam & slab concreting", "Superstructure (RCC)", 30.3, "cum", 7.5, 3, 10, 0, 0, "Concrete Mixer, Vibrator, Hoist", 73),
    ("Ground floor masonry", "Masonry", 76.5, "cum", 4.3, 5, 7, 0, 0, "-", 77),
    ("First floor columns", "Superstructure (RCC)", 21.6, "cum", 3.6, 3, 5, 4, 4, "Bar Bending Machine", 80),
    ("First floor beams & slab shuttering", "Superstructure (RCC)", 30.3, "cum", 3.0, 3, 6, 4, 5, "Tower Hoist", 86),
    ("First floor beam & slab concreting", "Superstructure (RCC)", 30.3, "cum", 7.5, 3, 10, 0, 0, "Concrete Mixer, Vibrator, Hoist", 96),
    ("First floor masonry", "Masonry", 76.5, "cum", 4.3, 5, 7, 0, 0, "-", 100),
    ("Second floor columns", "Superstructure (RCC)", 21.6, "cum", 3.6, 3, 5, 4, 4, "Bar Bending Machine", 103),
    ("Second floor beams & slab shuttering", "Superstructure (RCC)", 30.5, "cum", 3.0, 3, 6, 4, 5, "Tower Hoist", 109),
    ("Second floor beam & slab concreting", "Superstructure (RCC)", 30.5, "cum", 7.5, 3, 10, 0, 0, "Concrete Mixer, Vibrator, Hoist", 119),
    ("Second floor masonry incl. partitions", "Masonry", 76.5, "cum", 4.3, 5, 7, 0, 0, "-", 123),
    ("Staircase construction", "Superstructure (RCC)", 12.4, "cum", 1.6, 2, 4, 2, 2, "-", 100),
    ("Internal plastering", "Finishing", 1450, "sqm", 48, 8, 8, 0, 0, "-", 141),
    ("External plastering", "Finishing", 620, "sqm", 35, 5, 6, 0, 0, "Scaffolding", 141),
    ("Ceiling plastering", "Finishing", 540, "sqm", 32, 5, 5, 0, 0, "-", 145),
    ("Terrace waterproofing", "Waterproofing", 180, "sqm", 22, 3, 4, 0, 0, "-", 141),
    ("Flooring - vitrified/ceramic/granite", "Finishing", 608, "sqm", 30, 6, 6, 0, 0, "-", 161),
    ("Doors & windows fixing", "Doors & Windows", 60, "nos", 5, 3, 3, 0, 3, "-", 155),
    ("Electrical first fix (conduiting)", "Electrical", 168, "point", 10, 0, 0, 0, 0, "-", 100),
    ("Plumbing first fix", "Plumbing", 42, "point", 5, 0, 0, 0, 0, "-", 100),
    ("Internal painting", "Painting", 1450, "sqm", 42, 6, 5, 0, 0, "-", 176),
    ("External painting", "Painting", 620, "sqm", 32, 5, 5, 0, 0, "Scaffolding", 176),
    ("Electrical second fix & fittings", "Electrical", 168, "point", 14, 0, 0, 0, 0, "-", 176),
    ("Plumbing second fix & sanitary fittings", "Plumbing", 48, "point", 6, 0, 0, 0, 0, "-", 176),
    ("Overhead tank construction", "Plumbing", 1, "nos", 0.1, 2, 3, 2, 1, "-", 141),
    ("MS railing installation", "Miscellaneous", 58, "rm", 8, 2, 2, 0, 0, "Welding Machine", 176),
    ("Compound wall & gate", "Miscellaneous", 60, "rm", 6, 3, 4, 0, 0, "-", 141),
    ("Site development & handover cleaning", "Miscellaneous", 60, "sqm", 20, 0, 5, 0, 0, "-", 195),
]

sched_rows = []
start_date = date(2026, 1, 5)

def add_working_days(d, n_days):
    """Add n working days skipping Sundays."""
    days_added = 0
    cur = d
    while days_added < n_days:
        cur = cur + timedelta(days=1)
        if cur.weekday() != 6:  # skip Sunday
            days_added += 1
    return cur

act_id = 1
for (name, cat, qty, unit, out_per_day, mason, helper, barbender, carpenter, machinery, offset) in activities:
    duration = max(1, int(np.ceil(qty / out_per_day)))
    s = add_working_days(start_date, offset) if offset > 0 else start_date
    e = add_working_days(s, duration - 1) if duration > 1 else s
    sched_rows.append({
        "activity_id": f"A{act_id:02d}",
        "activity": name,
        "category": cat,
        "quantity": qty,
        "unit": unit,
        "duration_days": duration,
        "start_date": s.isoformat(),
        "end_date": e.isoformat(),
        "mason": mason,
        "helper": helper,
        "barbender": barbender,
        "carpenter": carpenter,
        "machinery": machinery,
    })
    act_id += 1

schedule = pd.DataFrame(sched_rows)
schedule.to_csv("schedule.csv", index=False)
schedule.to_json("schedule.json", orient="records", indent=2)

project_end_date = pd.to_datetime(schedule["end_date"]).max()
actual_duration = (project_end_date - pd.Timestamp(start_date)).days
project_meta["actual_planned_end_date"] = project_end_date.date().isoformat()
project_meta["actual_planned_duration_days"] = int(actual_duration)
with open("project_meta.json", "w") as f:
    json.dump(project_meta, f, indent=2)

# ----------------------------------------------------------------------
# 4. DAY-WISE LABOUR / MATERIAL / MACHINERY REQUIREMENT
# ----------------------------------------------------------------------
# Material consumption norms per unit of activity quantity (approx, realistic)
material_norms = {
    "Superstructure (RCC)": {"cement_bags_per_cum": 6.5, "steel_kg_per_cum": 110, "sand_cum_per_cum": 0.45, "aggregate_cum_per_cum": 0.9},
    "Substructure": {"cement_bags_per_cum": 6.0, "steel_kg_per_cum": 95, "sand_cum_per_cum": 0.45, "aggregate_cum_per_cum": 0.9},
    "Masonry": {"cement_bags_per_cum": 1.8, "sand_cum_per_cum": 0.3, "bricks_per_cum": 500},
    "Finishing": {"cement_bags_per_sqm": 0.25, "sand_cum_per_sqm": 0.012},
    "Painting": {"paint_litre_per_sqm": 0.13},
    "Electrical": {}, "Plumbing": {}, "Waterproofing": {"cement_bags_per_sqm": 0.4},
    "Doors & Windows": {}, "Miscellaneous": {}, "Preliminary": {}, "Earthwork": {},
}

daily_rows = []
for _, row in schedule.iterrows():
    s = pd.to_datetime(row["start_date"])
    e = pd.to_datetime(row["end_date"])
    days = pd.bdate_range(s, e, freq="D")  # includes all days; we already skip Sundays in schedule
    days = [d for d in pd.date_range(s, e) if d.weekday() != 6]
    n = max(1, len(days))
    qty_per_day = row["quantity"] / n
    norms = material_norms.get(row["category"], {})
    for d in days:
        cement = qty_per_day * norms.get("cement_bags_per_cum", norms.get("cement_bags_per_sqm", 0))
        steel = qty_per_day * norms.get("steel_kg_per_cum", 0)
        sand = qty_per_day * norms.get("sand_cum_per_cum", norms.get("sand_cum_per_sqm", 0))
        aggregate = qty_per_day * norms.get("aggregate_cum_per_cum", 0)
        bricks = qty_per_day * norms.get("bricks_per_cum", 0)
        paint = qty_per_day * norms.get("paint_litre_per_sqm", 0)
        daily_rows.append({
            "date": d.date().isoformat(),
            "activity_id": row["activity_id"],
            "activity": row["activity"],
            "mason": row["mason"],
            "helper": row["helper"],
            "barbender": row["barbender"],
            "carpenter": row["carpenter"],
            "machinery": row["machinery"],
            "cement_bags": round(cement, 1),
            "steel_kg": round(steel, 1),
            "sand_cum": round(sand, 2),
            "aggregate_cum": round(aggregate, 2),
            "bricks_nos": round(bricks, 0),
            "paint_litre": round(paint, 2),
        })

daily_resources = pd.DataFrame(daily_rows)
# aggregate multiple activities that might land on same date (rare, sequential schedule) 
daily_agg = daily_resources.groupby("date").agg({
    "mason": "sum", "helper": "sum", "barbender": "sum", "carpenter": "sum",
    "cement_bags": "sum", "steel_kg": "sum", "sand_cum": "sum",
    "aggregate_cum": "sum", "bricks_nos": "sum", "paint_litre": "sum",
}).reset_index()
daily_resources.to_csv("daily_resources_detail.csv", index=False)
daily_agg.to_csv("daily_resources.csv", index=False)

# ----------------------------------------------------------------------
# 5. CASH FLOW (weekly & monthly) - material / labour / machinery / total
# ----------------------------------------------------------------------
# Approximate rate assumptions for cost-back-calculation (INR)
rates = {"mason_day": 950, "helper_day": 650, "barbender_day": 900, "carpenter_day": 900,
         "cement_bag": 420, "steel_kg": 68, "sand_cum": 1850, "aggregate_cum": 1650,
         "brick_nos": 8.5, "paint_litre": 260, "machinery_day": 3500}

daily_resources["date"] = pd.to_datetime(daily_resources["date"])
df = daily_resources.copy()
df["labour_cost"] = (df["mason"] * rates["mason_day"] + df["helper"] * rates["helper_day"] +
                      df["barbender"] * rates["barbender_day"] + df["carpenter"] * rates["carpenter_day"])
df["material_cost"] = (df["cement_bags"] * rates["cement_bag"] + df["steel_kg"] * rates["steel_kg"] +
                        df["sand_cum"] * rates["sand_cum"] + df["aggregate_cum"] * rates["aggregate_cum"] +
                        df["bricks_nos"] * rates["brick_nos"] + df["paint_litre"] * rates["paint_litre"])
df["machinery_cost"] = np.where(df["machinery"] != "-", rates["machinery_day"], 0)
df["total_cost"] = df["labour_cost"] + df["material_cost"] + df["machinery_cost"]

# Scale so total equals BOQ total project cost (distributes overheads/finishing trades proportionally)
scale_factor = total_project_cost / df["total_cost"].sum()
for c in ["labour_cost", "material_cost", "machinery_cost", "total_cost"]:
    df[c] = (df[c] * scale_factor).round(0)

df["week"] = df["date"].dt.isocalendar().week
df["year"] = df["date"].dt.isocalendar().year
df["month"] = df["date"].dt.to_period("M").astype(str)
df["week_label"] = df["date"].dt.to_period("W-SAT").astype(str)

weekly = df.groupby("week_label").agg(
    week_start=("date", "min"), week_end=("date", "max"),
    material_cost=("material_cost", "sum"), labour_cost=("labour_cost", "sum"),
    machinery_cost=("machinery_cost", "sum"), total_cost=("total_cost", "sum"),
).reset_index()
weekly["cumulative_cost"] = weekly["total_cost"].cumsum()
weekly["cumulative_pct"] = (weekly["cumulative_cost"] / total_project_cost * 100).round(1)
weekly.to_csv("weekly_cashflow.csv", index=False)

monthly = df.groupby("month").agg(
    material_cost=("material_cost", "sum"), labour_cost=("labour_cost", "sum"),
    machinery_cost=("machinery_cost", "sum"), total_cost=("total_cost", "sum"),
).reset_index()
monthly["cumulative_cost"] = monthly["total_cost"].cumsum()
monthly["cumulative_pct"] = (monthly["cumulative_cost"] / total_project_cost * 100).round(1)
monthly.to_csv("monthly_cashflow.csv", index=False)

daily_cost_cols = df[["date", "labour_cost", "material_cost", "machinery_cost", "total_cost"]]
daily_cost_cols.to_csv("daily_cashflow.csv", index=False)

# ----------------------------------------------------------------------
# 6. HISTORICAL PROJECT DATASET for delay-risk ML model (synthetic, realistic)
# ----------------------------------------------------------------------
n_hist = 260
rows = []
for i in range(n_hist):
    planned_duration = np.random.randint(90, 400)
    monsoon_exposure_days = np.random.randint(0, 60)
    labour_availability_pct = np.clip(np.random.normal(82, 12), 40, 100)
    material_delay_risk = np.random.choice(["Low", "Medium", "High"], p=[0.5, 0.35, 0.15])
    contractor_experience_years = np.random.randint(1, 25)
    site_accessibility_score = np.random.randint(1, 10)  # 10 = excellent access
    design_change_frequency = np.random.poisson(2)
    num_floors_h = np.random.randint(1, 6)
    funding_regularity_score = np.random.randint(1, 10)  # 10 = fully regular payments
    permit_delay_days = np.random.randint(0, 45)

    mat_risk_num = {"Low": 0, "Medium": 1, "High": 2}[material_delay_risk]

    # underlying "true" delay generation logic (for realistic correlation)
    delay_score = (
        0.35 * (monsoon_exposure_days / 60) +
        0.30 * (1 - labour_availability_pct / 100) +
        0.30 * (mat_risk_num / 2) +
        0.15 * (design_change_frequency / 6) +
        0.20 * (1 - site_accessibility_score / 10) +
        0.15 * (permit_delay_days / 45) +
        0.15 * (1 - funding_regularity_score / 10) -
        0.10 * (contractor_experience_years / 25) +
        np.random.normal(0, 0.12)
    )
    delay_occurred = 1 if delay_score > 0.45 else 0
    delay_days = 0
    if delay_occurred:
        delay_days = int(np.clip(delay_score * planned_duration * np.random.uniform(0.15, 0.35), 3, 180))

    rows.append({
        "project_id": f"P{i+1:03d}",
        "planned_duration_days": planned_duration,
        "num_floors": num_floors_h,
        "monsoon_exposure_days": monsoon_exposure_days,
        "labour_availability_pct": round(labour_availability_pct, 1),
        "material_delay_risk": material_delay_risk,
        "contractor_experience_years": contractor_experience_years,
        "site_accessibility_score": site_accessibility_score,
        "design_change_frequency": design_change_frequency,
        "funding_regularity_score": funding_regularity_score,
        "permit_delay_days": permit_delay_days,
        "delay_occurred": delay_occurred,
        "delay_days": delay_days,
    })

historical = pd.DataFrame(rows)
historical.to_csv("historical_projects.csv", index=False)

# ----------------------------------------------------------------------
# 7. TRAIN DELAY-RISK ML MODEL (RandomForest classifier + regressor)
# ----------------------------------------------------------------------
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score, mean_absolute_error
from sklearn.preprocessing import LabelEncoder
import pickle

le = LabelEncoder()
historical["material_delay_risk_enc"] = le.fit_transform(historical["material_delay_risk"])

feature_cols = ["planned_duration_days", "num_floors", "monsoon_exposure_days",
                "labour_availability_pct", "material_delay_risk_enc", "contractor_experience_years",
                "site_accessibility_score", "design_change_frequency", "funding_regularity_score",
                "permit_delay_days"]

X = historical[feature_cols]
y_clf = historical["delay_occurred"]
y_reg = historical["delay_days"]

X_train, X_test, yc_train, yc_test, yr_train, yr_test = train_test_split(
    X, y_clf, y_reg, test_size=0.2, random_state=42, stratify=y_clf)

clf = RandomForestClassifier(n_estimators=200, max_depth=6, random_state=42)
clf.fit(X_train, yc_train)
clf_pred = clf.predict(X_test)
clf_proba = clf.predict_proba(X_test)[:, 1]
acc = accuracy_score(yc_test, clf_pred)
auc = roc_auc_score(yc_test, clf_proba)

reg = RandomForestRegressor(n_estimators=200, max_depth=6, random_state=42)
reg.fit(X_train, yr_train)
reg_pred = reg.predict(X_test)
mae = mean_absolute_error(yr_test, reg_pred)

feat_importance = dict(zip(feature_cols, clf.feature_importances_.round(4)))

with open("delay_model.pkl", "wb") as f:
    pickle.dump({"classifier": clf, "regressor": reg, "label_encoder": le, "features": feature_cols}, f)

model_meta = {
    "classifier_accuracy": round(acc, 4),
    "classifier_auc": round(auc, 4),
    "regressor_mae_days": round(mae, 2),
    "feature_importance": feat_importance,
    "train_size": len(X_train),
    "test_size": len(X_test),
    "algorithm": "Random Forest (200 trees, max_depth=6)",
}
with open("delay_model_meta.json", "w") as f:
    json.dump(model_meta, f, indent=2)

print("=== DATA GENERATION COMPLETE ===")
print(f"Total Project Cost (BOQ): Rs. {total_project_cost:,.0f}")
print(f"Planned Duration: {actual_duration} days ({actual_duration/30:.1f} months)")
print(f"BOQ items: {len(boq)} | Schedule activities: {len(schedule)} | Daily resource rows: {len(daily_resources)}")
print(f"Weekly cashflow rows: {len(weekly)} | Monthly cashflow rows: {len(monthly)}")
print(f"Historical projects for ML: {len(historical)}")
print(f"Delay model -> Accuracy: {acc:.3f}, AUC: {auc:.3f}, MAE(days): {mae:.2f}")
