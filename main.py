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
        ],
        "top5_ats": [
            {"ats_pick": "DET", "ats_confidence": 0.81},
            {"ats_pick": "PHI", "ats_confidence": 0.75},
        ],
        "top5_totals": [
            {"tot_pick": "Over 45.5", "tot_confidence": 0.68},
            {"tot_pick": "Under 42", "tot_confidence": 0.66},
        ],
        "top5_props": [
            {"player": "Josh Allen", "prop_type": "Pass Yards", "prediction": 286, "confidence": 0.72},
            {"player": "Jalen Hurts", "prop_type": "Rush TDs", "prediction": 1, "confidence": 0.69},
        ],
        "top5_fantasy": [
            {"player": "Christian McCaffrey", "position": "RB", "salary": 9300, "value_score": 3.12},
            {"player": "Tyreek Hill", "position": "WR", "salary": 8900, "value_score": 2.94},
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
