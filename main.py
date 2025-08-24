from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, Response
from typing import Dict, Any, Optional
import os, io, csv, random, datetime, http.client, json as pyjson
from fpdf import FPDF

app = FastAPI(title="NFL Predictor API", version="1.1.0")

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # you can restrict to your Vercel domain later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- ENV -----------------
ODDS_API_KEY         = os.getenv("ODDS_API_KEY", "").strip()
ODDS_REGION          = os.getenv("ODDS_REGION", "us")
SPORTSDATAIO_KEY     = os.getenv("SPORTSDATAIO_KEY", "").strip()
FANTASYDATA_API_KEY  = os.getenv("FANTASYDATA_API_KEY", "").strip()
FANTASY_SEASON       = os.getenv("FANTASY_SEASON", "2025REG")  # season code, NOT a secret key

# ---------------- Mock Data (current baseline) ----------------
def get_mock_predictions(week: int) -> Dict[str, Any]:
    random.seed(1000 + week)
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
        ],
    }

def get_mock_lineup(week: int) -> Dict[str, Any]:
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
            {"position": "DST", "player": "Dallas Cowboys", "team": "DAL", "salary": 4100, "proj_points": 9.0},
        ],
    }

# ---------------- Health & Debug ----------------
@app.get("/v1/health")
def health():
    """Simple health/flags endpoint."""
    return {
        "ok": True,
        "odds_api_key_set": bool(ODDS_API_KEY),
        "sportsdataio_key_set": bool(SPORTSDATAIO_KEY := os.getenv("SPORTSDATAIO_KEY", "").strip()),
        "fantasydata_key_set": bool(FANTASYDATA_API_KEY),
        "fantasy_season": FANTASY_SEASON,
        "ts": datetime.datetime.utcnow().isoformat() + "Z",
    }

@app.get("/v1/debug/providers")
def debug_providers(week: int = 1):
    """
    Attempts shallow calls to providers and returns status/sample.
    No secrets are returned; we only show counts/status.
    """
    results: Dict[str, Any] = {"env": {
        "odds_api_key_set": bool(ODDS_API_KEY),
        "sportsdataio_key_set": bool(SPORTSDATAIO_KEY),
        "fantasydata_key_set": bool(FANTASYDATA_API_KEY),
        "fantasy_season": FANTASY_SEASON,
    }}

    # SportsDataIO props (if key set)
    try:
        if SPORTSDATAIO_KEY:
            conn = http.client.HTTPSConnection("api.sportsdata.io", timeout=8)
            path = f"/v3/nfl/props/json/PlayerGamePropsByWeek/{FANTASY_SEASON}/{week}"
            conn.request("GET", path, headers={"Ocp-Apim-Subscription-Key": SPORTSDATAIO_KEY})
            resp = conn.getresponse()
            body = resp.read()
            status = resp.status
            sample = []
            if status == 200:
                data = pyjson.loads(body.decode("utf-8"))
                if isinstance(data, list):
                    sample = data[:2]
            results["sportsdataio"] = {"status": status, "path": path, "sample_count": len(sample), "sample": sample}
            conn.close()
        else:
            results["sportsdataio"] = {"status": "skipped (no key)"}
    except Exception as e:
        results["sportsdataio"] = {"status": f"error: {type(e).__name__}"}

    # FantasyData projections (if key set)
    try:
        if FANTASYDATA_API_KEY:
            conn = http.client.HTTPSConnection("api.fantasydata.net", timeout=8)
            path = f"/v3/nfl/projections/json/PlayerGameProjectionStatsByWeek/{FANTASY_SEASON}/{week}"
            conn.request("GET", path, headers={"Ocp-Apim-Subscription-Key": FANTASYDATA_API_KEY})
            resp = conn.getresponse()
            body = resp.read()
            status = resp.status
            sample = []
            if status == 200:
                data = pyjson.loads(body.decode("utf-8"))
                if isinstance(data, list):
                    sample = data[:2]
            results["fantasydata"] = {"status": status, "path": path, "sample_count": len(sample), "sample": sample}
            conn.close()
        else:
            results["fantasydata"] = {"status": "skipped (no key)"}
    except Exception as e:
        results["fantasydata"] = {"status": f"error: {type(e).__name__}"}

    # Odds API shallow H2H (if key set)
    try:
        if ODDS_API_KEY:
            conn = http.client.HTTPSConnection("api.the-odds-api.com", timeout=8)
            path = f"/v4/sports/americanfootball_nfl/odds?regions=us&markets=h2h&apiKey={ODDS_API_KEY}"
            conn.request("GET", path)
            resp = conn.getresponse()
            body = resp.read()
            status = resp.status
            sample = []
            if status == 200:
                data = pyjson.loads(body.decode("utf-8"))
                if isinstance(data, list):
                    sample = data[:1]
            results["oddsapi"] = {"status": status, "path": path, "sample_count": len(sample)}
            conn.close()
        else:
            results["oddsapi"] = {"status": "skipped (no key)"}
    except Exception as e:
        results["oddsapi"] = {"status": f"error: {type(e).__name__}"}

    return results

# ---------------- Core Routes ----------------
@app.get("/v1/best-picks/2025/{week}")
def best_picks(week: int):
    if week < 1 or week > 18:
        raise HTTPException(status_code=400, detail="Invalid week (1–18)")
    return get_mock_predictions(week)

@app.get("/v1/best-picks/2025/{week}/download")
def download(week: int, format: str = Query("json", regex="^(json|csv|pdf)$")):
    if week < 1 or week > 18:
        raise HTTPException(status_code=400, detail="Invalid week (1–18)")
    data = get_mock_predictions(week)

    if format == "json":
        # Use Response to avoid any serialization edge cases
        import json as _json
        return Response(content=_json.dumps(data), media_type="application/json")

    if format == "csv":
        s = io.StringIO()
        w = csv.writer(s)
        for section, rows in data.items():
            w.writerow([section])
            if rows and isinstance(rows, list):
                w.writerow(rows[0].keys())
                for r in rows:
                    w.writerow(r.values())
            w.writerow([])
        return Response(
            content=s.getvalue(),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename=nfl_week{week}_predictions.csv"},
        )

    if format == "pdf":
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"NFL 2025 - Week {week} Predictions", ln=True, align="C")
        for section, rows in data.items():
            pdf.ln(10)
            pdf.set_font("Arial", style="B", size=12)
            pdf.cell(200, 10, txt=section.upper(), ln=True)
            pdf.set_font("Arial", size=10)
            if rows and isinstance(rows, list):
                for row in rows:
                    line = ", ".join([f"{k}: {v}" for k, v in row.items()])
                    pdf.multi_cell(0, 8, txt=line)
        filename = f"/tmp/nfl_week{week}_predictions.pdf"
        pdf.output(filename)
        return FileResponse(filename, media_type="application/pdf", filename=filename)

    raise HTTPException(status_code=400, detail="Invalid format")

@app.get("/v1/lineup/2025/{week}")
def lineup(week: int, site: str = Query("DK", regex="^(DK|FD)$")):
    return get_mock_lineup(week)
