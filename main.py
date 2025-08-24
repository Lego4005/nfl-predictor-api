from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import csv
import io
import datetime
import random
from fpdf import FPDF
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data generator
def get_mock_predictions(week: int):
    teams = ["BUF", "KC", "PHI", "DAL", "MIA", "CIN", "SF", "NYJ", "DET", "BAL"]
    players = ["Josh Allen", "Patrick Mahomes", "Jalen Hurts", "Lamar Jackson", "Tyreek Hill", "Christian McCaffrey"]
    props = ["Pass Yards", "Rush TDs", "Receiving Yards", "Completions", "Interceptions"]

    random.seed(week)

    return {
        "top5_su": [
            {"home": random.choice(teams), "away": random.choice(teams), "su_pick": random.choice(teams), "su_confidence": round(random.uniform(0.6, 0.9), 2)}
            for _ in range(5)
        ],
        "top5_ats": [
            {"ats_pick": random.choice(teams), "ats_confidence": round(random.uniform(0.6, 0.9), 2)}
            for _ in range(5)
        ],
        "top5_totals": [
            {"tot_pick": f"{random.choice(['Over', 'Under'])} {random.randint(39, 55)}", "tot_confidence": round(random.uniform(0.6, 0.9), 2)}
            for _ in range(5)
        ],
        "top5_props": [
            {"player": random.choice(players), "prop_type": random.choice(props), "prediction": random.randint(50, 300), "confidence": round(random.uniform(0.6, 0.9), 2)}
            for _ in range(5)
        ],
        "top5_fantasy": [
            {"player": random.choice(players), "position": random.choice(["QB", "RB", "WR", "TE"]), "salary": random.randint(5500, 9900), "value_score": round(random.uniform(2.5, 3.8), 2)}
            for _ in range(5)
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
    data = get_mock_predictions(week)

    if format == "json":
        return JSONResponse(content=data)

    elif format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)

        for section, entries in data.items():
            writer.writerow([section])
            writer.writerow(entries[0].keys())
            for entry in entries:
                writer.writerow(entry.values())
            writer.writerow([])  # blank line between sections

        response = io.BytesIO(output.getvalue().encode())
        return FileResponse(response, media_type='text/csv', filename=f"week{week}_predictions.csv")

    elif format == "pdf":
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"NFL Week {week} Predictions", ln=True, align="C")

        for section, entries in data.items():
            pdf.ln(10)
            pdf.set_font("Arial", "B", 12)
            pdf.cell(200, 10, section.replace("_", " ").title(), ln=True)
            pdf.set_font("Arial", size=10)
            for entry in entries:
                line = ", ".join([f"{k}: {v}" for k, v in entry.items()])
                pdf.multi_cell(0, 8, line)

        filename = f"week{week}_predictions.pdf"
        filepath = f"/tmp/{filename}"
        pdf.output(filepath)

        return FileResponse(filepath, media_type='application/pdf', filename=filename)

    else:
        raise HTTPException(status_code=400, detail="Invalid format. Use 'json', 'csv', or 'pdf'")

