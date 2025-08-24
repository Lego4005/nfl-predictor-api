from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, Response
from typing import Dict, Any, List, Optional, Tuple
import os, io, csv, random, datetime, sqlite3, http.client, json as pyjson
from fpdf import FPDF

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ODDS_API_KEY = os.getenv("ODDS_API_KEY", "").strip()
ODDS_REGION = os.getenv("ODDS_REGION", "us")
PREDICTION_PROVIDER = os.getenv("PREDICTION_PROVIDER", "market").lower()  # market | ml
DB_PATH = os.getenv("DB_PATH", "predictions.db")

# -----------------------------
# DB
# -----------------------------
def init_db():
    with sqlite3.connect(DB_PATH) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
              id INTEGER PRIMARY KEY,
              week INTEGER,
              payload TEXT,
              created_at TEXT
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS outcomes (
              id INTEGER PRIMARY KEY,
              week INTEGER,
              game_id TEXT,
              final_home_score INTEGER,
              final_away_score INTEGER,
              spread_line REAL,
              total_line REAL,
              recorded_at TEXT
            )
        """)

def save_predictions(week: int, payload: Dict[str, Any]):
    with sqlite3.connect(DB_PATH) as con:
        con.execute(
            "INSERT INTO predictions (week, payload, created_at) VALUES (?,?,?)",
            (week, pyjson.dumps(payload), datetime.datetime.utcnow().isoformat()+"Z")
        )

# -----------------------------
# Odds helpers
# -----------------------------
def american_to_prob(odds: Optional[float]) -> Optional[float]:
    if odds is None:
        return None
    try:
        o = float(odds)
    except Exception:
        return None
    if o > 0:
        return 100.0 / (o + 100.0)
    if o < 0:
        return (-o) / ((-o) + 100.0)
    return None

def deflate_vig(p_a: Optional[float], p_b: Optional[float]) -> Tuple[Optional[float], Optional[float]]:
    if p_a is None or p_b is None:
        return (p_a, p_b)
    s = p_a + p_b
    if s <= 0:
        return (p_a, p_b)
    return (p_a / s, p_b / s)

def rank_top_n(items: List[Dict[str, Any]], key: str, n: int = 5) -> List[Dict[str, Any]]:
    return sorted(items, key=lambda r: r.get(key, 0.0), reverse=True)[:n]

def safe_float(x, default=None):
    try:
        return float(x)
    except Exception:
        return default

# -----------------------------
# External odds (The Odds API)
# -----------------------------
def _oddsapi_get(path: str, params: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    if not ODDS_API_KEY:
        return None
    query = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"/v4{path}?apiKey={ODDS_API_KEY}&{query}"
    try:
        conn = http.client.HTTPSConnection("api.the-odds-api.com", timeout=10)
        conn.request("GET", url)
        resp = conn.getresponse()
        if resp.status != 200:
            return None
        body = resp.read()
        data = pyjson.loads(body.decode("utf-8"))
        return data if isinstance(data, list) else None
    except Exception:
        return None
    finally:
        try:
            conn.close()
        except Exception:
            pass

def fetch_week_odds_from_api(week: int) -> Optional[List[Dict[str, Any]]]:
    # Demo: pull latest markets; no calendar mapping to "week" here.
    h2h = _oddsapi_get("/sports/americanfootball_nfl/odds",
                       {"regions": ODDS_REGION, "markets": "h2h", "oddsFormat": "american"})
    spd = _oddsapi_get("/sports/americanfootball_nfl/odds",
                       {"regions": ODDS_REGION, "markets": "spreads", "oddsFormat": "american"})
    tot = _oddsapi_get("/sports/americanfootball_nfl/odds",
                       {"regions": ODDS_REGION, "markets": "totals", "oddsFormat": "american"})
    if not h2h:
        return None

    def idx(rows):
        out = {}
        for g in rows:
            home = g.get("home_team")
            away = None
            bks = g.get("bookmakers") or []
            if bks and bks[0].get("markets"):
                outcomes = bks[0]["markets"][0].get("outcomes") or []
                names = [o.get("name") for o in outcomes]
                for nm in names:
                    if nm and nm != home:
                        away = nm
                        break
            out[(home or "", away or "")] = g
        return out

    h2h_idx = idx(h2h)
    spd_idx = idx(spd or [])
    tot_idx = idx(tot or [])

    results = []
    for key, row in h2h_idx.items():
        home, away = key
        entry = {
            "home_team": home, "away_team": away,
            "h2h_home": None, "h2h_away": None,
            "spread": None, "spread_team": None,
            "total": None, "over_odds": None, "under_odds": None
        }
        # H2H
        bks = row.get("bookmakers") or []
        if bks and bks[0].get("markets"):
            outcomes = bks[0]["markets"][0].get("outcomes") or []
            for o in outcomes:
                if o.get("name") == home:
                    entry["h2h_home"] = safe_float(o.get("price"))
                elif o.get("name") == away:
                    entry["h2h_away"] = safe_float(o.get("price"))
        # Spreads
        srow = spd_idx.get(key)
        if srow:
            bks = srow.get("bookmakers") or []
            if bks and bks[0].get("markets"):
                outcomes = bks[0]["markets"][0].get("outcomes") or []
                fav = None
                fav_line = None
                for o in outcomes:
                    pt = safe_float(o.get("point"))
                    nm = o.get("name")
                    if pt is not None and pt < 0:
                        fav = nm
                        fav_line = pt
                        break
                if fav_line is not None:
                    entry["spread"] = fav_line
                    entry["spread_team"] = fav
        # Totals
        trow = tot_idx.get(key)
        if trow:
            bks = trow.get("bookmakers") or []
            if bks and bks[0].get("markets"):
                outcomes = bks[0]["markets"][0].get("outcomes") or []
                for o in outcomes:
                    if o.get("name") == "Over":
                        entry["total"] = safe_float(o.get("point"))
                        entry["over_odds"] = safe_float(o.get("price"))
                    elif o.get("name") == "Under":
                        entry["total"] = safe_float(o.get("point")) if entry["total"] is None else entry["total"]
                        entry["under_odds"] = safe_float(o.get("price"))
        results.append(entry)
    return results

# -----------------------------
# Mock games (fallback)
# -----------------------------
TEAMS = ["BUF","KC","PHI","DAL","MIA","CIN","SF","NYJ","DET","BAL","SEA","GB","MIN","LAR","PIT","JAX"]

def mock_games_for_week(week: int) -> List[Dict[str, Any]]:
    random.seed(1337 + week)
    pool = TEAMS[:]
    random.shuffle(pool)
    games = []
    for i in range(0, min(10, len(pool)-1), 2):
        home, away = pool[i], pool[i+1]
        home_ml = random.choice([-170, -150, -130, -110, 110, 130, 150])
        away_ml = random.choice([-170, -150, -130, -110, 110, 130, 150])
        if home_ml == away_ml:
            away_ml = 100 if away_ml != 100 else -105
        spread_fav = home if home_ml < away_ml else away
        spread_val = random.choice([-6.5,-4.5,-3.5,-2.5,-1.5,-0.5])
        if spread_fav == away:
            spread_val = -spread_val
        total = random.choice([41.5, 43.5, 45.5, 47.5, 49.5])
        over_odds = random.choice([-115, -110, -105, 100, 105])
        under_odds = random.choice([-115, -110, -105, 100, 105])
        games.append({
            "home_team": home, "away_team": away,
            "h2h_home": home_ml if home_ml < 0 else None,
            "h2h_away": away_ml if away_ml < 0 else None,
            "spread": float(spread_val),
            "spread_team": spread_fav,
            "total": float(total),
            "over_odds": float(over_odds),
            "under_odds": float(under_odds)
        })
    return games

# -----------------------------
# Build predictions from games
# -----------------------------
def build_from_games(games: List[Dict[str, Any]]) -> Dict[str, Any]:
    su_rows, ats_rows, tot_rows = [], [], []
    for g in games:
        home, away = g["home_team"], g["away_team"]
        p_home = american_to_prob(g.get("h2h_home"))
        p_away = american_to_prob(g.get("h2h_away"))
        if p_home is None and p_away is not None:
            p_home = 1 - p_away
        if p_away is None and p_home is not None:
            p_away = 1 - p_home
        p_home_fair, p_away_fair = deflate_vig(p_home, p_away)
        if p_home_fair is None or p_away_fair is None:
            p_home_fair, p_away_fair = 0.5, 0.5

        su_pick = home if p_home_fair >= p_away_fair else away
        su_conf = round(max(p_home_fair, p_away_fair), 4)
        su_rows.append({"home": home, "away": away, "su_pick": su_pick, "su_confidence": su_conf})

        fav = g.get("spread_team")
        spread = g.get("spread")
        if fav and spread is not None:
            fav_prob = p_home_fair if fav == home else p_away_fair
            ats_rows.append({
                "matchup": f"{away} @ {home}",
                "ats_pick": f"{fav} {spread}",
                "ats_confidence": round(max(0.50, min(0.70, 0.45 + 0.5*abs(fav_prob-0.5))), 4)
            })

        over_p = american_to_prob(g.get("over_odds"))
        under_p = american_to_prob(g.get("under_odds"))
        if over_p is not None and under_p is not None:
            over_fair, under_fair = deflate_vig(over_p, under_p)
        else:
            over_fair, under_fair = 0.5, 0.5

        if over_fair >= under_fair:
            tot_rows.append({
                "matchup": f"{away} @ {home}",
                "tot_pick": f"Over {g.get('total')}",
                "tot_confidence": round(over_fair, 4)
            })
        else:
            tot_rows.append({
                "matchup": f"{away} @ {home}",
                "tot_pick": f"Under {g.get('total')}",
                "tot_confidence": round(under_fair, 4)
            })

    return {
        "top5_su": rank_top_n(su_rows, "su_confidence", 5),
        "top5_ats": rank_top_n(ats_rows, "ats_confidence", 5),
        "top5_totals": rank_top_n(tot_rows, "tot_confidence", 5),
        "top5_props": [{"player": "TBD", "prop_type": "TBD", "prediction": 0, "confidence": 0.0} for _ in range(5)],
        "top5_fantasy": [{"player": "TBD", "position": "TBD", "salary": 0, "value_score": 0.0} for _ in range(5)]
    }

def get_market_predictions(week: int) -> Dict[str, Any]:
    api_games = fetch_week_odds_from_api(week)
    games = api_games if api_games else mock_games_for_week(week)
    return build_from_games(games)

def get_ml_predictions(week: int) -> Dict[str, Any]:
    # Stub for future ML models
    random.seed(999 + week)
    return {
        "top5_su": [{"home": "TBD", "away": "TBD", "su_pick": "TBD", "su_confidence": 0.55} for _ in range(5)],
        "top5_ats": [{"matchup": "TBD @ TBD", "ats_pick": "TBD -2.5", "ats_confidence": 0.55} for _ in range(5)],
        "top5_totals": [{"matchup": "TBD @ TBD", "tot_pick": "Over 45.5", "tot_confidence": 0.55} for _ in range(5)],
        "top5_props": [{"player": "TBD", "prop_type": "TBD", "prediction": 0, "confidence": 0.5} for _ in range(5)],
        "top5_fantasy": [{"player": "TBD", "position": "TBD", "salary": 0, "value_score": 0.0} for _ in range(5)]
    }

def get_predictions_for_week(week: int) -> Dict[str, Any]:
    if PREDICTION_PROVIDER == "ml":
        return get_ml_predictions(week)
    return get_market_predictions(week)

# -----------------------------
# Routes
# -----------------------------
@app.on_event("startup")
def on_start():
    init_db()

@app.get("/v1/health")
def health():
    return {"ok": True, "provider": PREDICTION_PROVIDER, "ts": datetime.datetime.utcnow().isoformat() + "Z"}

@app.get("/v1/debug")
def debug():
    return {
        "odds_api_key_set": bool(ODDS_API_KEY),
        "provider": PREDICTION_PROVIDER,
        "db_path": DB_PATH
    }

@app.get("/v1/best-picks/2025/{week}")
def best_picks(week: int):
    if week < 1 or week > 18:
        raise HTTPException(status_code=400, detail="Invalid week (1–18)")
    data = get_predictions_for_week(week)
    save_predictions(week, data)
    return data

@app.get("/v1/best-picks/2025/{week}/download")
def download_predictions(week: int, format: str = Query("json", regex="^(json|csv|pdf)$")):
    if week < 1 or week > 18:
        raise HTTPException(status_code=400, detail="Invalid week (1–18)")
    data = get_predictions_for_week(week)

    if format == "json":
        return JSONResponse(content=data)

    if format == "csv":
        # Build CSV in-memory then return as bytes with proper headers
        output = io.StringIO()
        writer = csv.writer(output)
        for section, entries in data.items():
            writer.writerow([section])
            if entries and isinstance(entries, list) and len(entries) > 0:
                writer.writerow(entries[0].keys())
                for row in entries:
                    writer.writerow(row.values())
            writer.writerow([])
        csv_str = output.getvalue()
        output.close()
        return Response(
            content=csv_str,
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="nfl_week{week}_predictions.csv"'}
        )

    if format == "pdf":
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=14)
        pdf.cell(200, 10, txt=f"NFL Week {week} Predictions", ln=True, align="C")
        for section, entries in data.items():
            pdf.ln(8)
            pdf.set_font("Arial", "B", 12)
            pdf.cell(200, 10, txt=section.replace("_", " ").title(), ln=True)
            pdf.set_font("Arial", size=10)
            if entries and isinstance(entries, list):
                for row in entries:
                    line = ", ".join(f"{k}: {v}" for k, v in row.items())
                    pdf.multi_cell(0, 7, line)
        filename = f"/tmp/nfl_week{week}_predictions.pdf"
        pdf.output(filename)
        return FileResponse(filename, media_type="application/pdf", filename=os.path.basename(filename))

    raise HTTPException(status_code=400, detail="Invalid format")




