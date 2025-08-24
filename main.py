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
            {"home": "LAR", "away": "ARI", "su_pick": "LAR", "su_confidence": 0.74},
            {"home": "DEN", "away": "LV", "su_pick": "DEN", "su_confidence": 0.71},
            {"home": "GB", "away": "CHI", "su_pick": "GB", "su_confidence": 0.69},
            {"home": "NYJ", "away": "NE", "su_pick": "NYJ", "su_confidence": 0.67},
            {"home": "DAL", "away": "HOU", "su_pick": "DAL", "su_confidence": 0.66},
        ],
        "top5_ats": [
            {"ats_pick": "CLE", "ats_confidence": 0.79},
            {"ats_pick": "PIT", "ats_confidence": 0.77},
            {"ats_pick": "MIN", "ats_confidence": 0.75},
            {"ats_pick": "BUF", "ats_confidence": 0.73},
            {"ats_pick": "BAL", "ats_confidence": 0.71},
        ],
        "top5_totals": [
            {"tot_pick": "Over 48.5", "tot_confidence": 0.72},
            {"tot_pick": "Under 41", "tot_confidence": 0.69},
            {"tot_pick": "Over 44", "tot_confidence": 0.68},
            {"tot_pick": "Under 39", "tot_confidence": 0.65},
            {"tot_pick": "Over 51", "tot_confidence": 0.64},
        ],
        "top5_props": [
            {"player": "Lamar Jackson", "prop_type": "Rush Yards", "prediction": 93, "confidence": 0.75},
            {"player": "Justin Fields", "prop_type": "Pass TDs", "prediction": 2, "confidence": 0.70},
            {"player": "Amon-Ra St. Brown", "prop_type": "Receiving Yards", "prediction": 112, "confidence": 0.69},
            {"player": "Tony Pollard", "prop_type": "Rush Yards", "prediction": 87, "confidence": 0.66},
            {"player": "Joe Burrow", "prop_type": "Pass Yards", "prediction": 310, "confidence": 0.65},
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
        "total_salary": 49900,
        "projected_points": 164.2,
        "lineup": [
            {"position": "QB", "player": "Lamar Jackson", "team": "BAL", "salary": 7800, "proj_points": 25.2},
            {"position": "RB", "player": "Bijan Robinson", "team": "ATL", "salary": 7800, "proj_points": 22.4},
            {"position": "RB", "player": "Travis Etienne", "team": "JAX", "salary": 6900, "proj_points": 19.1},
            {"position": "WR", "player": "Ja'Marr Chase", "team": "CIN", "salary": 8800, "proj_points": 27.0},
            {"position": "WR", "player": "Puka Nacua", "team": "LAR", "salary": 6700, "proj_points": 17.3},
            {"position": "WR", "player": "Zay Flowers", "team": "BAL", "salary": 5600, "proj_points": 15.0},
            {"position": "TE", "player": "Dalton Kincaid", "team": "BUF", "salary": 5200, "proj_points": 14.2},
            {"position": "FLEX", "player": "Tony Pollard", "team": "DAL", "salary": 6500, "proj_points": 17.0},
            {"position": "DST", "player": "Jets", "team": "NYJ", "salary": 4400, "proj_points": 9.0}
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
