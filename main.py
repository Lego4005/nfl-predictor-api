from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
import io, csv
from fpdf import FPDF

APP_VERSION = "SAFE-MODE-NO-TYPES-1.0.0"

app = FastAPI(title="NFL Predictor API (Safe Mode)", version=APP_VERSION)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------- Mock data generators (stable shapes for your UI) -------------
def mock_su(week):
    return [
        {"home": "BUF", "away": "NYJ", "matchup": "NYJ @ BUF", "su_pick": "BUF", "su_confidence": 0.534},
        {"home": "PHI", "away": "DAL", "matchup": "DAL @ PHI", "su_pick": "PHI", "su_confidence": 0.522},
        {"home": "WAS", "away": "NYG", "matchup": "NYG @ WAS", "su_pick": "WAS", "su_confidence": 0.516},
        {"home": "NO",  "away": "ARI", "matchup": "ARI @ NO",  "su_pick": "ARI", "su_confidence": 0.508},
        {"home": "CLE", "away": "CIN", "matchup": "CIN @ CLE", "su_pick": "CIN", "su_confidence": 0.506},
    ]

def mock_ats(week):
    return [
        {"matchup": "NYJ @ BUF", "ats_pick": "BUF -3.5", "spread": -3.5, "ats_confidence": 0.500},
        {"matchup": "DAL @ PHI", "ats_pick": "PHI -3.0", "spread": -3.0, "ats_confidence": 0.505},
        {"matchup": "NYG @ WAS", "ats_pick": "WAS -2.5", "spread": -2.5, "ats_confidence": 0.507},
        {"matchup": "ARI @ NO",  "ats_pick": "ARI +1.5", "spread":  1.5, "ats_confidence": 0.508},
        {"matchup": "CIN @ CLE", "ats_pick": "CIN -2.0", "spread": -2.0, "ats_confidence": 0.509},
    ]

def mock_totals(week):
    return [
        {"matchup": "NYJ @ BUF", "tot_pick": "Over 45.5", "total_line": 45.5, "tot_confidence": 0.500},
        {"matchup": "DAL @ PHI", "tot_pick": "Over 46.5", "total_line": 46.5, "tot_confidence": 0.511},
        {"matchup": "KC @ LAC",  "tot_pick": "Under 45.5", "total_line": 45.5, "tot_confidence": 0.511},
        {"matchup": "CAR @ JAX", "tot_pick": "Under 46.5", "total_line": 46.5, "tot_confidence": 0.511},
        {"matchup": "NYG @ WAS", "tot_pick": "Under 45.5", "total_line": 45.5, "tot_confidence": 0.511},
    ]

def mock_props(week):
    # Exact structure your UI expects (with numeric line + units + book + game)
    return [
        {"player": "Josh Allen",   "prop_type": "Passing Yards",   "units": "yds", "line": 285.5, "pick": "Over",  "confidence": 0.631, "bookmaker": "SportsDataIO", "team": "BUF", "opponent": "BAL"},
        {"player": "Jalen Hurts",  "prop_type": "Rushing Yards",   "units": "yds", "line":  46.5, "pick": "Over",  "confidence": 0.620, "bookmaker": "SportsDataIO", "team": "PHI", "opponent": "DAL"},
        {"player": "Puka Nacua",   "prop_type": "Receptions",      "units": "rec", "line":   6.5, "pick": "Under", "confidence": 0.615, "bookmaker": "SportsDataIO", "team": "LAR", "opponent": "HOU"},
        {"player": "Malik Nabers", "prop_type": "Receiving Yards", "units": "yds", "line":  69.5, "pick": "Under", "confidence": 0.612, "bookmaker": "SportsDataIO", "team": "NYG", "opponent": "WAS"},
        {"player": "Mike Evans",   "prop_type": "Fantasy Points",  "units": "pts", "line":  13.5, "pick": "Under", "confidence": 0.605, "bookmaker": "SportsDataIO", "team": "TB",  "opponent": "ATL"},
    ]

def mock_fantasy():
    return [
        {"player":"Ja'Marr Chase","position":"WR","salary":8800,"value_score":3.45},
        {"player":"Bijan Robinson","position":"RB","salary":7800,"value_score":3.22},
        {"player":"Travis Etienne","position":"RB","salary":6900,"value_score":3.10},
        {"player":"Davante Adams","position":"WR","salary":8400,"value_score":2.98},
        {"player":"Dalton Kincaid","position":"TE","salary":5200,"value_score":2.86},
    ]

def payload_for_week(week):
    return {
        "top5_su": mock_su(week),
        "top5_ats": mock_ats(week),
        "top5_totals": mock_totals(week),
        "top5_props": mock_props(week),
        "top5_fantasy": mock_fantasy(),
    }

# ----------------------- Routes -----------------------
@app.get("/")
def root():
    return {"ok": True, "version": APP_VERSION}

@app.get("/v1/health")
def health():
    return {"ok": True, "version": APP_VERSION, "status": "safe-mode", "hint": "mock data served to keep UI up"}

@app.get("/v1/debug/info")
def debug_info(week: int = 1):
    data = payload_for_week(week)
    return {
        "version": APP_VERSION,
        "counts": {
            "su": len(data["top5_su"]),
            "ats": len(data["top5_ats"]),
            "totals": len(data["top5_totals"]),
            "props": len(data["top5_props"]),
            "fantasy": len(data["top5_fantasy"]),
        }
    }

@app.get("/v1/best-picks/2025/{week}")
def best_picks(week: int):
    if week < 1 or week > 18:
        raise HTTPException(status_code=400, detail="Invalid week")
    return payload_for_week(week)

@app.get("/v1/best-picks/2025/{week}/download")
def download(week: int, format: str = Query("json", regex="^(json|csv|pdf)$")):
    if week < 1 or week > 18:
        raise HTTPException(status_code=400, detail="Invalid week")
    data = payload_for_week(week)

    if format == "json":
        import json as _json
        return Response(content=_json.dumps(data), media_type="application/json")

    if format == "csv":
        s = io.StringIO()
        w = csv.writer(s)
        for section, rows in data.items():
            if not isinstance(rows, list) or not rows:
                continue
            w.writerow([section])
            w.writerow(list(rows[0].keys()))
            for r in rows:
                w.writerow(list(r.values()))
            w.writerow([])
        return Response(
            content=s.getvalue(),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename=nfl_week{week}_predictions.csv"}
        )

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"NFL Week {week} Predictions", ln=True, align="C")
    for section, rows in data.items():
        if not isinstance(rows, list) or not rows:
            continue
        pdf.ln(8)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(200, 10, txt=section.upper(), ln=True)
        pdf.set_font("Arial", size=10)
        for r in rows:
            line = ", ".join([f"{k}: {v}" for k, v in r.items()])
            pdf.multi_cell(0, 8, line)
    filename = f"/tmp/nfl_week{week}.pdf"
    pdf.output(filename)
    return FileResponse(filename, media_type="application/pdf", filename=f"nfl_week{week}.pdf")
