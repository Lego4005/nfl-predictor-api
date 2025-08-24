from fastapi import FastAPI, HTTPException, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, Response
from typing import Dict, Any, List, Optional, Tuple
import os, io, csv, random, datetime, json as pyjson, sqlite3, joblib
from fpdf import FPDF

APP_VERSION = "ML-bridge-1.0.0"

# ---------- ENV / Paths ----------
DB_PATH = os.getenv("DB_PATH", "predictions.db")
MODEL_DIR = os.getenv("MODEL_DIR", "models")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")  # set this to protect /v1/admin/outcomes

# provider toggle for /v1/ml/predict endpoint (if you want to strictly require models)
PREDICTION_PROVIDER = os.getenv("PREDICTION_PROVIDER", "market").lower()  # "ml" | "market"

os.makedirs(MODEL_DIR, exist_ok=True)

app = FastAPI(title="NFL Predictor API", version=APP_VERSION)

# ---------- CORS ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- DB ----------
def init_db():
    with sqlite3.connect(DB_PATH) as con:
        con.execute("""
        CREATE TABLE IF NOT EXISTS games_labels (
          id INTEGER PRIMARY KEY,
          season TEXT,
          week INTEGER,
          home TEXT,
          away TEXT,
          home_score INTEGER,
          away_score INTEGER,
          spread_close REAL,
          total_close REAL,
          su_result INTEGER,  -- 1 if home won else 0
          ats_home_cover INTEGER, -- 1 if (home_score - away_score + spread_close) > 0 else 0
          over_hit INTEGER     -- 1 if (home_score + away_score) > total_close else 0
        )
        """)
        con.execute("CREATE INDEX IF NOT EXISTS idx_labels_season_week ON games_labels(season, week)")
init_db()

# ---------- Mock picks (unchanged shape so your UI stays happy) ----------
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
            {"ats_pick": "DET -3.5", "ats_confidence": 0.81},
            {"ats_pick": "PHI +2.5", "ats_confidence": 0.75},
            {"ats_pick": "ATL -1.5", "ats_confidence": 0.72},
            {"ats_pick": "JAX -2.5", "ats_confidence": 0.70},
            {"ats_pick": "NYG +3.5", "ats_confidence": 0.69},
        ],
        "top5_totals": [
            {"tot_pick": "Over 45.5", "tot_confidence": 0.68},
            {"tot_pick": "Under 42.0", "tot_confidence": 0.66},
            {"tot_pick": "Over 47.0", "tot_confidence": 0.65},
            {"tot_pick": "Under 38.5", "tot_confidence": 0.64},
            {"tot_pick": "Over 50.0", "tot_confidence": 0.63},
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

# ---------- Utility: load models if present ----------
def load_model(path: str):
    full = os.path.join(MODEL_DIR, path)
    return joblib.load(full) if os.path.exists(full) else None

SU_MODEL = load_model("su_model.pkl")
ATS_MODEL = load_model("ats_model.pkl")
TOT_MODEL = load_model("tot_model.pkl")

# ---------- Health / Debug ----------
@app.get("/v1/health")
def health():
    return {
        "ok": True,
        "version": APP_VERSION,
        "db_path": DB_PATH,
        "models": {
            "su": bool(SU_MODEL),
            "ats": bool(ATS_MODEL),
            "totals": bool(TOT_MODEL),
        },
        "ts": datetime.datetime.utcnow().isoformat() + "Z",
    }

@app.get("/v1/debug/providers")
def debug_providers():
    return {"note": "Providers shelved for now; focusing on ML + labels."}

# ---------- Core: UI-compatible endpoints ----------
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
        import json as _json
        return Response(content=_json.dumps(data), media_type="application/json")

    if format == "csv":
        s = io.StringIO(); w = csv.writer(s)
        for section, rows in data.items():
            w.writerow([section])
            if rows and isinstance(rows, list):
                w.writerow(rows[0].keys())
                for r in rows: w.writerow(r.values())
            w.writerow([])
        return Response(
            content=s.getvalue(),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename=nfl_week{week}_predictions.csv"},
        )

    if format == "pdf":
        pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"NFL 2025 - Week {week} Predictions", ln=True, align="C")
        for section, rows in data.items():
            pdf.ln(10); pdf.set_font("Arial", style="B", size=12)
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

# ---------- Admin: Outcomes ingestion (creates labels) ----------
@app.post("/v1/admin/outcomes")
def post_outcomes(
    payload: Dict[str, Any],
    x_admin_token: Optional[str] = Header(None)
):
    if ADMIN_TOKEN and x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

    season = str(payload.get("season") or "2025REG")
    week = int(payload.get("week") or 1)
    games = payload.get("games") or []

    if not games:
        raise HTTPException(400, "No games provided")

    with sqlite3.connect(DB_PATH) as con:
        for g in games:
            home = g["home"]; away = g["away"]
            hs = int(g["home_score"]); as_ = int(g["away_score"])
            spread = float(g["spread_close"])  # negative means home favored
            total = float(g["total_close"])
            su = 1 if hs > as_ else 0
            ats_home_cover = 1 if (hs - as_ + spread) > 0 else 0
            over_hit = 1 if (hs + as_) > total else 0
            con.execute("""
              INSERT INTO games_labels (season, week, home, away, home_score, away_score,
                                        spread_close, total_close, su_result, ats_home_cover, over_hit)
              VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, (season, week, home, away, hs, as_, spread, total, su, ats_home_cover, over_hit))
    return {"ok": True, "inserted": len(games)}

# ---------- ML Predict endpoint ----------
@app.post("/v1/ml/predict")
def ml_predict(payload: Dict[str, Any]):
    """
    Request body:
    {
      "games": [
        {"home":"BUF","away":"NYJ","spread_close":-3.5,"total_close":45.5}
      ]
    }
    Returns SU/ATS/Totals picks per game using trained models if available.
    """
    games = payload.get("games") or []
    if not games:
        raise HTTPException(400, "No games provided")

    # Load models fresh in case you retrained
    su_model = load_model("su_model.pkl")
    ats_model = load_model("ats_model.pkl")
    tot_model = load_model("tot_model.pkl")

    results = []
    for g in games:
        home = g["home"]; away = g["away"]
        spread = float(g["spread_close"])
        total = float(g["total_close"])

        # Features (minimal): SU & ATS → spread; Totals → total line
        # SU prob (home wins)
        if su_model:
            su_prob_home = float(su_model.predict_proba([[spread]])[0][1])
        else:
            # simple heuristic: more negative spread → higher home prob
            su_prob_home = 1 / (1 + pow(10, spread/10))

        su_pick = home if su_prob_home >= 0.5 else away
        su_conf = max(su_prob_home, 1 - su_prob_home)

        # ATS: prob home covers
        if ats_model:
            ats_prob_home_cover = float(ats_model.predict_proba([[spread]])[0][1])
        else:
            ats_prob_home_cover = 1 / (1 + pow(10, spread/8))
        ats_pick = f"{home} {abs(spread):.1f}" if spread < 0 else f"{away} {abs(spread):.1f}"
        ats_conf = max(ats_prob_home_cover, 1 - ats_prob_home_cover)

        # Totals: prob over
        if tot_model:
            over_prob = float(tot_model.predict_proba([[total]])[0][1])
        else:
            # crude: middling total → ~0.5, higher totals → nudge over
            over_prob = max(0.35, min(0.65, (total - 40) / 20 * 0.15 + 0.5))
        tot_pick = f"{'Over' if over_prob >= 0.5 else 'Under'} {total:.1f}"
        tot_conf = max(over_prob, 1 - over_prob)

        results.append({
            "home": home, "away": away,
            "su_pick": su_pick, "su_confidence": round(su_conf, 4),
            "ats_pick": ats_pick, "ats_confidence": round(ats_conf, 4),
            "tot_pick": tot_pick, "tot_confidence": round(tot_conf, 4),
        })

    return {"provider": "ml" if su_model and ats_model and tot_model else "heuristic",
            "games": results}
