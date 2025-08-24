from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, Response
from typing import Dict, Any, List, Optional, Tuple
import os, io, csv, random, datetime, sqlite3, http.client, json as pyjson
from fpdf import FPDF

app = FastAPI(title="NFL Predictor API", version="1.2.0")

# -----------------------------
# CORS
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict to your frontend later if you like
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Env & Globals
# -----------------------------
ODDS_API_KEY = os.getenv("ODDS_API_KEY", "").strip()
ODDS_REGION = os.getenv("ODDS_REGION", "us")
PREDICTION_PROVIDER = os.getenv("PREDICTION_PROVIDER", "market").lower()  # market | ml
DB_PATH = os.getenv("DB_PATH", "predictions.db")

# FantasyData (optional for DFS projections)
FANTASYDATA_API_KEY = os.getenv("FANTASYDATA_API_KEY", "").strip()  # header: Ocp-Apim-Subscription-Key

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
# THE ODDS API helpers
# -----------------------------
def _oddsapi_get(path: str, params: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    if not ODDS_API_KEY:
        return None
    query = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"/v4{path}?apiKey={ODDS_API_KEY}&{query}"
    try:
        conn = http.client.HTTPSConnection("api.the-odds-api.com", timeout=12)
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

def fetch_week_odds_from_api() -> Optional[List[Dict[str, Any]]]:
    # Not week-specific (API is event-based), but good enough to reflect current market
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
# Player Props (The Odds API)
# -----------------------------
PROP_MARKETS = ",".join([
    "player_pass_yds",
    "player_pass_tds",
    "player_rush_yds",
    "player_rec_yds",
    "player_receptions",
])

def fetch_player_props_from_oddsapi() -> Optional[List[Dict[str, Any]]]:
    if not ODDS_API_KEY:
        return None
    rows = _oddsapi_get("/sports/americanfootball_nfl/odds",
                        {"regions": ODDS_REGION, "markets": PROP_MARKETS, "oddsFormat": "american"})
    return rows

def build_prop_picks_from_oddsapi() -> List[Dict[str, Any]]:
    """
    For each player market, choose the side (Over/Under) with higher fair probability
    based on the best bookmaker listed. Rank by confidence and return top 5.
    """
    data = fetch_player_props_from_oddsapi()
    if not data:
        return []

    picks = []
    for event in data:
        for bm in (event.get("bookmakers") or []):
            for mkt in (bm.get("markets") or []):
                market_key = mkt.get("key")  # e.g., player_pass_yds
                outcomes = mkt.get("outcomes") or []
                # Normalize: find Over/Under with point & price
                over = next((o for o in outcomes if (o.get("name") or "").lower() == "over"), None)
                under = next((o for o in outcomes if (o.get("name") or "").lower() == "under"), None)
                player_name = mkt.get("player") or mkt.get("player_name") or None  # some feeds include this
                line = None
                over_prob = under_prob = None

                if over:
                    line = safe_float(over.get("point"), line)
                    over_prob = american_to_prob(safe_float(over.get("price")))
                if under:
                    line = safe_float(under.get("point"), line)
                    under_prob = american_to_prob(safe_float(under.get("price")))

                if over_prob is None and under_prob is None:
                    continue

                o_fair, u_fair = deflate_vig(over_prob or 0.5, under_prob or 0.5)
                if o_fair is None or u_fair is None:
                    continue

                side = "Over" if o_fair >= u_fair else "Under"
                conf = max(o_fair, u_fair)
                picks.append({
                    "player": player_name or "TBD",
                    "prop_type": market_key or "prop",
                    "line": line,
                    "pick": side,
                    "confidence": round(conf, 3),
                    "bookmaker": bm.get("title") or "N/A",
                })

    # Deduplicate by (player, prop_type) keeping the highest confidence
    dedup = {}
    for p in picks:
        key = (p["player"], p["prop_type"])
        if key not in dedup or p["confidence"] > dedup[key]["confidence"]:
            dedup[key] = p

    top = list(dedup.values())
    top.sort(key=lambda x: x["confidence"], reverse=True)
    return top[:5]

# -----------------------------
# Fantasy/DFS (FantasyData)
# -----------------------------
def fetch_fantasy_from_fantasydata(week: int) -> Optional[List[Dict[str, Any]]]:
    """
    Uses FantasyData projections: top players by projected fantasy points.
    API doc (example): /projections/json/PlayerGameProjectionStatsByWeek/{season}/{week}
    Header: Ocp-Apim-Subscription-Key: <key>
    """
    if not FANTASYDATA_API_KEY:
        return None

    # Season format e.g., 2025REG / 2025PRE depending on timing; we default to REG here.
    season = "2025REG"
    path = f"/v3/nfl/projections/json/PlayerGameProjectionStatsByWeek/{season}/{week}"
    try:
        conn = http.client.HTTPSConnection("api.fantasydata.net", timeout=12)
        conn.request("GET", path, headers={"Ocp-Apim-Subscription-Key": FANTASYDATA_API_KEY})
        resp = conn.getresponse()
        if resp.status != 200:
            return None
        body = resp.read()
        arr = pyjson.loads(body.decode("utf-8"))
        if not isinstance(arr, list):
            return None
        # Map minimal fields
        rows = []
        for r in arr:
            rows.append({
                "player": r.get("Name") or r.get("ShortName") or "TBD",
                "position": r.get("Position") or "",
                "team": r.get("Team") or "",
                "proj_points": safe_float(r.get("FantasyPointsDraftKings"), safe_float(r.get("FantasyPoints"), 0.0)),
                "salary": safe_float(r.get("DraftKingsSalary"), 0.0),
            })
        return rows
    except Exception:
        return None
    finally:
        try:
            conn.close()
        except Exception:
            pass

def build_fantasy_picks(week: int) -> List[Dict[str, Any]]:
    data = fetch_fantasy_from_fantasydata(week)
    if not data:
        # placeholder if no key or API failed
        random.seed(1000 + week)
        players = [
            ("Josh Allen","QB"), ("Christian McCaffrey","RB"), ("Tyreek Hill","WR"),
            ("CeeDee Lamb","WR"), ("Travis Kelce","TE"), ("Lamar Jackson","QB"),
            ("Ja'Marr Chase","WR"), ("Amon-Ra St. Brown","WR"), ("Bijan Robinson","RB"),
            ("Garrett Wilson","WR")
        ]
        rows = []
        for i in range(5):
            name, pos = random.choice(players)
            salary = random.randint(4500, 9500)
            proj = round(random.uniform(12, 28), 2)
            value = round(proj / max(salary,1) * 1000.0, 3)  # pts per $1k
            rows.append({
                "player": name, "position": pos, "salary": salary,
                "proj_points": proj, "value_score": value
            })
        return rows

    # Rank by value if salary present, else by projected points
    for r in data:
        pts = r.get("proj_points") or 0.0
        sal = r.get("salary") or 0.0
        r["value_score"] = round((pts / sal) * 1000.0, 3) if sal > 0 else round(pts, 3)

    data.sort(key=lambda x: (x.get("value_score") or 0.0), reverse=True)
    top = []
    for r in data[:25]:  # sample more, then pick diverse positions
        top.append({
            "player": r.get("player","TBD"),
            "position": r.get("position",""),
            "salary": r.get("salary", 0.0),
            "proj_points": r.get("proj_points", 0.0),
            "value_score": r.get("value_score", 0.0)
        })
        if len(top) >= 5:
            break
    return top

# -----------------------------
# Mock games (fallback for SU/ATS/Totals)
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
# Build SU/ATS/Totals from games
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
    }

# -----------------------------
# Market vs ML switch
# -----------------------------
def get_market_predictions() -> Dict[str, Any]:
    api_games = fetch_week_odds_from_api()
    games = api_games if api_games else mock_games_for_week(1)  # not truly week-bound
    return build_from_games(games)

def get_ml_predictions() -> Dict[str, Any]:
    random.seed(999)
    return {
        "top5_su": [{"home": "TBD", "away": "TBD", "su_pick": "TBD", "su_confidence": 0.55} for _ in range(5)],
        "top5_ats": [{"matchup": "TBD @ TBD", "ats_pick": "TBD -2.5", "ats_confidence": 0.55} for _ in range(5)],
        "top5_totals": [{"matchup": "TBD @ TBD", "tot_pick": "Over 45.5", "tot_confidence": 0.55} for _ in range(5)],
    }

def get_predictions_core() -> Dict[str, Any]:
    if PREDICTION_PROVIDER == "ml":
        return get_ml_predictions()
    return get_market_predictions()

# -----------------------------
# Routes
# -----------------------------
@app.on_event("startup")
def on_start():
    init_db()

@app.get("/")
def root():
    return {
        "name": "NFL Predictor API",
        "status": "ok",
        "docs": "/docs",
        "examples": {
            "health": "/v1/health",
            "week_1_predictions": "/v1/best-picks/2025/1",
            "download_csv": "/v1/best-picks/2025/1/download?format=csv"
        }
    }

@app.get("/v1/health")
def health():
    return {
        "ok": True,
        "provider": PREDICTION_PROVIDER,
        "odds_api_key_set": bool(ODDS_API_KEY),
        "fantasydata_key_set": bool(FANTASYDATA_API_KEY),
        "ts": datetime.datetime.utcnow().isoformat()+"Z"
    }

@app.get("/v1/debug")
def debug():
    return {
        "provider": PREDICTION_PROVIDER,
        "db_path": DB_PATH,
        "odds_api_key_set": bool(ODDS_API_KEY),
        "fantasydata_key_set": bool(FANTASYDATA_API_KEY),
    }

@app.get("/v1/best-picks/2025/{week}")
def best_picks(week: int):
    if week < 1 or week > 18:
        raise HTTPException(status_code=400, detail="Invalid week (1–18)")

    core = get_predictions_core()
    # Props
    prop_picks = build_prop_picks_from_oddsapi() if ODDS_API_KEY else []
    if not prop_picks:
        # graceful placeholders if no key or API returns nothing
        random.seed(week + 2025)
        sample_players = ["Josh Allen", "Patrick Mahomes", "Tyreek Hill", "Jalen Hurts", "Christian McCaffrey",
                          "Justin Jefferson", "Lamar Jackson", "Amon-Ra St. Brown", "Ja'Marr Chase", "Joe Burrow"]
        sample_types = ["player_pass_yds", "player_rush_yds", "player_rec_yds", "player_pass_tds", "player_receptions"]
        prop_picks = [{
            "player": random.choice(sample_players),
            "prop_type": random.choice(sample_types),
            "line": random.randint(40, 300),
            "pick": random.choice(["Over", "Under"]),
            "confidence": round(random.uniform(0.52, 0.7), 3),
            "bookmaker": "N/A",
        } for _ in range(5)]

    # Fantasy
    fantasy = build_fantasy_picks(week)

    payload = {
        **core,
        "top5_props": prop_picks[:5],
        "top5_fantasy": fantasy[:5]
    }
    save_predictions(week, payload)
    return payload

@app.get("/v1/best-picks/2025/{week}/download")
def download_predictions(week: int, format: str = Query("json", regex="^(json|csv|pdf)$")):
    if week < 1 or week > 18:
        raise HTTPException(status_code=400, detail="Invalid week (1–18)")
    data = best_picks(week)

    if format == "json":
        return JSONResponse(content=data)

    if format == "csv":
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
