from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import Dict, List
import csv
import io
import random

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TEAMS = [
    "BUF","KC","SF","DAL","MIA","PHI","CIN","DET","BAL","GB",
    "SEA","LAR","JAX","NYJ","NYG","CLE","PIT","MIN","NO","HOU",
    "ATL","TEN","IND","LV","DEN","CHI","TB","WAS","CAR","ARI","NE","LAC"
]

def _ats_pick_with_spread(team: str) -> Dict:
    """Create one ATS record with spread and confidence.
       Half the time it selects a favorite (-spread), half an underdog (+spread)."""
    base_pts = random.choice([0.5, 1.5, 2.5, 3.5, 4.5, 6.5, 7.5])
    sign = random.choice([-1, 1])  # -1 favorite, +1 underdog
    spread_val = round(sign * base_pts, 1)
    # Format ats_pick like "DET -3.5" or "NYG +2.5"
    sign_char = "-" if spread_val < 0 else "+"
    ats_pick_str = f"{team} {sign_char}{abs(spread_val)}"
    conf = round(random.uniform(0.65, 0.85), 2)
    return {"ats_pick": ats_pick_str, "spread": spread_val, "ats_confidence": conf}

def get_mock_predictions(week: int) -> Dict:
    random.seed(10_000 + week)

    # SU
    top5_su = []
    for _ in range(5):
        home, away = random.sample(TEAMS, 2)
        winner = random.choice([home, away])
        top5_su.append({
            "home": home,
            "away": away,
            "su_pick": winner,
            "su_confidence": round(random.uniform(0.62, 0.86), 2)
        })

    # ATS (now includes spreads)
    top5_ats = []
    seen = set()
    for _ in range(5):
        t = random.choice(TEAMS)
        # avoid trivial duplicates
        tries = 0
        while t in seen and tries < 10:
            t = random.choice(TEAMS); tries += 1
        seen.add(t)
        top5_ats.append(_ats_pick_with_spread(t))

    # Totals
    top5_totals = []
    for _ in range(5):
        side = random.choice(["Over", "Under"])
        tot = random.choice([39.5, 41.0, 41.5, 43.5, 45.5, 47.5, 49.5, 51.0])
        top5_totals.append({
            "tot_pick": f"{side} {tot}",
            "tot_confidence": round(random.uniform(0.58, 0.8), 2)
        })

    # Props (placeholder, readable)
    players = [
        "Josh Allen","Jalen Hurts","Patrick Mahomes","Lamar Jackson",
        "Tyreek Hill","Ja'Marr Chase","Justin Jefferson","Christian McCaffrey"
    ]
    prop_types = ["Pass Yards","Rush Yards","Receiving Yards","Pass TDs","Receptions"]
    top5_props = []
    for _ in range(5):
        p = random.choice(players)
        pt = random.choice(prop_types)
        if pt == "Pass Yards":
            pred = random.randint(240, 330)
        elif pt == "Rush Yards":
            pred = random.randint(55, 115)
        elif pt == "Receiving Yards":
            pred = random.randint(65, 130)
        elif pt == "Pass TDs":
            pred = random.randint(1, 3)
        else:  # Receptions
            pred = random.randint(4, 9)
        top5_props.append({
            "player": p,
            "prop_type": pt,
            "prediction": pred,
            "confidence": round(random.uniform(0.55, 0.8), 2)
        })

    # Fantasy value (placeholder)
    positions = ["QB","RB","WR","TE"]
    top5_fantasy = []
    for _ in range(5):
        p = random.choice(players)
        pos = random.choice(positions)
        salary = random.randint(5000, 9500)
        value = round(random.uniform(2.2, 3.6), 2)
        top5_fantasy.append({
            "player": p,
            "position": pos,
            "salary": salary,
            "value_score": value
        })

    return {
        "top5_su": top5_su,
        "top5_ats": top5_ats,        # <-- includes "spread" and "ats_pick" string with line
        "top5_totals": top5_totals,
        "top5_props": top5_props,
        "top5_fantasy": top5_fantasy
    }

def get_mock_lineup(week: int) -> Dict:
    random.seed(20_000 + week)
    return {
        "week": week,
        "salary_cap": 50000,
        "total_salary": 49800,
        "projected_points": 162.4,
        "lineup": [
            {"position": "QB", "player": "Jalen Hurts", "team": "PHI", "salary": 7900, "proj_points": 24.3},
            {"position": "RB", "player": "Christian McCaffrey", "team": "SF", "salary": 9300, "proj_points": 26.1},
            {"position": "RB", "player": "Rachaad White", "team": "TB", "salary": 6200, "proj_points": 18.2},
            {"position": "WR", "player": "Tyreek Hill", "team": "MIA", "salary": 8900, "proj_points": 25.4},
            {"position": "WR", "player": "Chris Olave", "team": "NO", "salary": 6600, "proj_points": 17.2},
            {"position": "WR", "player": "Zay Flowers", "team": "BAL", "salary": 5600, "proj_points": 14.5},
            {"position": "TE", "player": "Sam LaPorta", "team": "DET", "salary": 4800, "proj_points": 13.0},
            {"position": "FLEX", "player": "Nico Collins", "team": "HOU", "salary": 5000, "proj_points": 14.7},
            {"position": "DST", "player": "Dallas Cowboys", "team": "DAL", "salary": 4100, "proj_points": 9.0}
        ]
    }

@app.get("/v1/best-picks/2025/{week}")
def get_predictions(week: int):
    if week < 1 or week > 18:
        raise HTTPException(status_code=400, detail="Invalid week")
    return get_mock_predictions(week)

@app.get("/v1/best-picks/2025/{week}/download")
def download_predictions(week: int, format: str):
    if week < 1 or week > 18:
        raise HTTPException(status_code=400, detail="Invalid week")
    picks = get_mock_predictions(week)

    if format == "json":
        return picks

    elif format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        for category, items in picks.items():
            writer.writerow([category])
            if items:
                writer.writerow(items[0].keys())
                for row in items:
                    writer.writerow(row.values())
            writer.writerow([])
        output.seek(0)
        return FileResponse(io.BytesIO(output.getvalue().encode()),
                            media_type='text/csv',
                            filename=f"week_{week}_predictions.csv")

    elif format == "pdf":
        from fpdf import FPDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"NFL 2025 - Week {week} Predictions", ln=True, align='C')
        for category, items in picks.items():
            pdf.ln(10)
            pdf.set_font("Arial", style='B', size=12)
            pdf.cell(200, 10, txt=category.upper(), ln=True)
            pdf.set_font("Arial", size=10)
            for item in items:
                line = ", ".join([f"{k}: {v}" for k, v in item.items()])
                pdf.multi_cell(0, 8, txt=line)
        filename = f"week_{week}_predictions.pdf"
        pdf.output(filename)
        return FileResponse(filename, media_type='application/pdf')

    else:
        raise HTTPException(status_code=400, detail="Invalid format")

@app.get("/v1/lineup/2025/{week}")
def get_dfs_lineup(week: int):
    if week < 1 or week > 18:
        raise HTTPException(status_code=400, detail="Invalid week")
    return get_mock_lineup(week)
