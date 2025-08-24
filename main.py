from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import Dict
import json
import csv
import io
import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_mock_predictions(week: int):
    return {
        "top5_su": [
            {"home": "BUF", "away": "NYJ", "su_pick": "BUF", "su_confidence": 0.78},
            {"home": "KC", "away": "CIN", "su_pick": "KC", "su_confidence": 0.72},
            {"home": "SF", "away": "SEA", "su_pick": "SF", "su_confidence": 0.70},
            {"home": "DAL", "away": "PHI", "su_pick": "DAL", "su_confidence": 0.68},
            {"home": "MIA", "away": "NE", "su_pick": "MIA", "su_confidence": 0.65},
        ],
        "top5_ats": [
            {"ats_pick": "DET", "ats_confidence": 0.81},
            {"ats_pick": "PHI", "ats_confidence": 0.75},
            {"ats_pick": "ATL", "ats_confidence": 0.72},
            {"ats_pick": "JAX", "ats_confidence": 0.70},
            {"ats_pick": "NYG", "ats_confidence": 0.69},
        ],
        "top5_totals": [
            {"tot_pick": "Over 45.5", "tot_confidence": 0.68},
            {"tot_pick": "Under 42", "tot_confidence": 0.66},
            {"tot_pick": "Over 47", "tot_confidence": 0.65},
            {"tot_pick": "Under 38.5", "tot_confidence": 0.64},
            {"tot_pick": "Over 50", "tot_confidence": 0.63},
        ],
        "top5_props": [
            {"player": "Josh Allen", "prop_type": "Pass Yards", "prediction": 286, "confidence": 0.72},
            {"player": "Jalen Hurts", "prop_type": "Rush TDs", "prediction": 1, "confidence": 0.69},
            {"player": "Justin Jefferson", "prop_type": "Receiving Yards", "prediction": 105, "confidence": 0.67},
            {"player": "Bijan Robinson", "prop_type": "Rush Yards", "prediction": 88, "confidence": 0.66},
            {"player": "Patrick Mahomes", "prop_type": "Pass TDs", "prediction": 3, "confidence": 0.64},
        ],
        "top5_fantasy": [
            {"player": "Ja'Marr Chase", "position": "WR", "salary": 8800, "value_score": 3.45},
            {"player": "Bijan Robinson", "position": "RB", "salary": 7800, "value_score": 3.22},
            {"player": "Travis Etienne", "position": "RB", "salary": 6900, "value_score": 3.10},
            {"player": "Davante Adams", "position": "WR", "salary": 8400, "value_score": 2.98},
            {"player": "Dalton Kincaid", "position": "TE", "salary": 5200, "value_score": 2.86},
        ]
    }

def get_mock_lineup(week: int):
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
            writer.writerow(items[0].keys())
            for row in items:
                writer.writerow(row.values())
            writer.writerow([])
        output.seek(0)
        return FileResponse(io.BytesIO(output.getvalue().encode()), media_type='text/csv', filename=f"week_{week}_predictions.csv")

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
