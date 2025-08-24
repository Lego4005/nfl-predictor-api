from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, Response
from typing import Dict, Any, List, Optional, Tuple
import os, io, csv, random, datetime, http.client, json as pyjson
from fpdf import FPDF

app = FastAPI(title="NFL Predictor API", version="2.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- ENV ----
ODDS_API_KEY = os.getenv("ODDS_API_KEY", "").strip()
ODDS_REGION = os.getenv("ODDS_REGION", "us")  # us | uk | eu | au
PREDICTION_PROVIDER = os.getenv("PREDICTION_PROVIDER", "market").lower()  # market | ml

# ---- Helpers ----
def american_to_prob(odds: Optional[float]) -> Optional[float]:
    if odds is None: return None
    try:
        o = float(odds)
    except Exception:
        return None
    if o > 0:  return 100.0 / (o + 100.0)
    if o < 0:  return (-o) / ((-o) + 100.0)
    return None

def deflate_vig(pa: Optional[float], pb: Optional[float]) -> Tuple[Optional[float], Optional[float]]:
    if pa is None or pb is None: return (pa, pb)
    s = pa + pb
    if s <= 0: return (pa, pb)
    return (pa / s, pb / s)

def safe_float(x, default=None):
    try: return float(x)
    except Exception: return default

def rank_top_n(items: List[Dict[str, Any]], key: str, n: int = 5) -> List[Dict[str, Any]]:
    return sorted(items, key=lambda r: r.get(key, 0.0), reverse=True)[:n]

# ---- The Odds API ----
def _oddsapi_get(path: str, params: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    if not ODDS_API_KEY:
        return None
    q = "&".join(f"{k}={v}" for k,v in params.items())
    url = f"/v4{path}?apiKey={ODDS_API_KEY}&{q}"
    try:
        conn = http.client.HTTPSConnection("api.the-odds-api.com", timeout=12)
        conn.request("GET", url)
        resp = conn.getresponse()
        if resp.status != 200:
            return None
        data = pyjson.loads(resp.read().decode("utf-8"))
        return data if isinstance(data, list) else None
    except Exception:
        return None
    finally:
        try: conn.close()
        except Exception: pass

def fetch_market_snap() -> Optional[List[Dict[str, Any]]]:
    """Fetch latest H2H, spreads, totals (event-based; no week filter)."""
    h2h = _oddsapi_get("/sports/americanfootball_nfl/odds",
                       {"regions": ODDS_REGION, "markets": "h2h", "oddsFormat": "american"})
    spd = _oddsapi_get("/sports/americanfootball_nfl/odds",
                       {"regions": ODDS_REGION, "markets": "spreads", "oddsFormat": "american"})
    tot = _oddsapi_get("/sports/americanfootball_nfl/odds",
                       {"regions": ODDS_REGION, "markets": "totals", "oddsFormat": "american"})
    if not h2h: return None

    def idx(rows):
        out = {}
        for g in rows:
            home = g.get("home_team")
            # crude away inference from market outcomes
            away = None
            bks = g.get("bookmakers") or []
            if bks and bks[0].get("markets"):
                outs = bks[0]["markets"][0].get("outcomes") or []
                names = [o.get("name") for o in outs if o.get("name")]
                for nm in names:
                    if nm != home:
                        away = nm
                        break
            out[(home or "", away or "")] = g
        return out

    h2h_idx = idx(h2h)
    spd_idx = idx(spd or [])
    tot_idx = idx(tot or [])

    games = []
    for key, row in h2h_idx.items():
        home, away = key
        entry = {
            "home_team": home, "away_team": away,
            "h2h_home": None, "h2h_away": None,
            "spread": None, "spread_team": None,
            "total": None, "over_odds": None, "under_odds": None
        }
        # H2H odds
        bks = row.get("bookmakers") or []
        if bks and bks[0].get("markets"):
            outs = bks[0]["markets"][0].get("outcomes") or []
            for o in outs:
                if o.get("name") == home: entry["h2h_home"] = safe_float(o.get("price"))
                elif o.get("name") == away: entry["h2h_away"] = safe_float(o.get("price"))

        # Spreads
        srow = spd_idx.get(key)
        if srow:
            bks = srow.get("bookmakers") or []
            if bks and bks[0].get("markets"):
                outs = bks[0]["markets"][0].get("outcomes") or []
                fav, fav_line = None, None
                for o in outs:
                    pt = safe_float(o.get("point"))
                    nm = o.get("name")
                    if pt is not None and pt < 0:  # favorite is negative
                        fav, fav_line = nm, pt
                        break
                if fav_line is not None:
                    entry["spread"] = fav_line
                    entry["spread_team"] = fav

        # Totals
        trow = tot_idx.get(key)
        if trow:
            bks = trow.get("bookmakers") or []
            if bks and bks[0].get("markets"):
                outs = bks[0]["markets"][0].get("outcomes") or []
                for o in outs:
                    if o.get("name") == "Over":
                        entry["total"] = safe_float(o.get("point"))
                        entry["over_odds"] = safe_float(o.get("price"))
                    elif o.get("name") == "Under":
                        entry["total"] = safe_float(o.get("point")) if entry["total"] is None else entry["total"]
                        entry["under_odds"] = safe_float(o.get("price"))
        games.append(entry)
    return games

# ---- Fallback mock slate ----
TEAMS = ["BUF","KC","SF","DAL","MIA","PHI","CIN","DET","BAL","GB",
         "SEA","LAR","JAX","NYJ","NYG","CLE","PIT","MIN","NO","HOU",
         "ATL","TEN","IND","LV","DEN","CHI","TB","WAS","CAR","ARI","NE","LAC"]

def mock_games_for_week(week: int) -> List[Dict[str, Any]]:
    random.seed(1337 + week)
    pool = TEAMS[:]; random.shuffle(pool)
    games = []
    for i in range(0, min(10, len(pool)-1), 2):
        home, away = pool[i], pool[i+1]
        # fake moneylines
        home_ml = random.choice([-170,-150,-130,-110,110,130,150])
        away_ml = random.choice([-170,-150,-130,-110,110,130,150])
        # favorite by ML
        fav = home if home_ml < away_ml else away
        line = random.choice([-6.5,-4.5,-3.5,-2.5,-1.5,-0.5])
        if fav == away: line = -line
        total = random.choice([41.5,43.5,45.5,47.5,49.5])
        over_odds = random.choice([-115,-110,-105,100,105])
        under_odds = random.choice([-115,-110,-105,100,105])
        games.append({
            "home_team": home, "away_team": away,
            "h2h_home": home_ml if home_ml < 0 else None,
            "h2h_away": away_ml if away_ml < 0 else None,
            "spread": float(line), "spread_team": fav,
            "total": float(total),
            "over_odds": float(over_odds), "under_odds": float(under_odds)
        })
    return games

# ---- Build SU/ATS/Totals from games ----
def build_from_games(games: List[Dict[str, Any]]) -> Dict[str, Any]:
    su_rows, ats_rows, tot_rows = [], [], []
    for g in games:
        home, away = g["home_team"], g["away_team"]
        p_home = american_to_prob(g.get("h2h_home"))
        p_away = american_to_prob(g.get("h2h_away"))
        if p_home is None and p_away is not None: p_home = 1 - p_away
        if p_away is None and p_home is not None: p_away = 1 - p_home
        ph_fair, pa_fair = deflate_vig(p_home, p_away)
        if ph_fair is None or pa_fair is None: ph_fair, pa_fair = 0.5, 0.5

        # SU
        su_pick = home if ph_fair >= pa_fair else away
        su_rows.append({
            "home": home, "away": away,
            "su_pick": su_pick,
            "su_confidence": round(max(ph_fair, pa_fair), 4)
        })

        # ATS (provide both string and numeric spread)
        fav, spread = g.get("spread_team"), g.get("spread")
        if fav and spread is not None:
            fav_prob = ph_fair if fav == home else pa_fair
            sign_char = "-" if spread < 0 else "+"
            ats_rows.append({
                "ats_pick": f"{fav} {sign_char}{abs(spread)}",
                "spread": float(spread),
                "ats_confidence": round(max(0.50, min(0.75, 0.46 + 0.5 * abs(fav_prob - 0.5))), 4)
            })

        # Totals
        op = american_to_prob(g.get("over_odds"))
        up = american_to_prob(g.get("under_odds"))
        if op is not None and up is not None:
            of, uf = deflate_vig(op, up)
        else:
            of, uf = 0.5, 0.5
        if of >= uf:
            tot_rows.append({
                "tot_pick": f"Over {g.get('total')}",
                "tot_confidence": round(of, 4)
            })
        else:
            tot_rows.append({
                "tot_pick": f"Under {g.get('total')}",
                "tot_confidence": round(uf, 4)
            })

    return {
        "top5_su": rank_top_n(su_rows, "su_confidence", 5),
        "top5_ats": rank_top_n(ats_rows, "ats_confidence", 5),
        "top5_totals": rank_top_n(tot_rows, "tot_confidence", 5),
    }

def get_market_predictions() -> Dict[str, Any]:
    snap = fetch_market_snap()
    games = snap if snap else mock_games_for_week(1)  # fallback
    return build_from_games(games)

# ---- Props & Fantasy placeholders (we'll wire next) ----
def build_props_placeholder(week: int) -> List[Dict[str, Any]]:
    random.seed(2000 + week)
    players = ["Josh Allen","Jalen Hurts","Patrick Mahomes","Lamar Jackson",
               "Tyreek Hill","Ja'Marr Chase","Justin Jefferson","CMC"]
    types = ["Pass Yards","Rush Yards","Receiving Yards","Pass TDs","Receptions"]
    rows = []
    for _ in range(5):
        p, t = random.choice(players), random.choice(types)
        pred = (random.randint(240,330) if t=="Pass Yards" else
                random.randint(55,115) if t=="Rush Yards" else
                random.randint(65,130) if t=="Receiving Yards" else
                random.randint(1,3) if t=="Pass TDs" else
                random.randint(4,9))
        rows.append({"player": p, "prop_type": t, "prediction": pred, "confidence": round(random.uniform(0.55,0.8),2)})
    return rows

def build_fantasy_placeholder(week: int) -> List[Dict[str, Any]]:
    random.seed(3000 + week)
    players = ["Josh Allen","CMC","Tyreek Hill","CeeDee Lamb","Davante Adams","Bijan Robinson","Dalton Kincaid"]
    positions = ["QB","RB","WR","TE"]
    out = []
    for _ in range(5):
        p, pos = random.choice(players), random.choice(positions)
        sal = random.randint(5200, 9800)
        val = round(random.uniform(2.2, 3.6), 2)
        out.append({"player": p, "position": pos, "salary": sal, "value_score": val})
    return out

def get_best_picks_payload(week: int) -> Dict[str, Any]:
    core = get_market_predictions()  # SU/ATS/Totals
    return {
        **core,
        "top5_props": build_props_placeholder(week),
        "top5_fantasy": build_fantasy_placeholder(week)
    }

# ---- Classic DFS lineup (placeholder) ----
def get_mock_lineup(week: int) -> Dict:
    random.seed(4000 + week)
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
        ]
    }

# ---- Routes ----
@app.get("/v1/health")
def health():
    return {"ok": True, "provider": PREDICTION_PROVIDER, "odds_api_key_set": bool(ODDS_API_KEY),
            "ts": datetime.datetime.utcnow().isoformat()+"Z"}

@app.get("/v1/best-picks/2025/{week}")
def best_picks(week: int):
    if week < 1 or week > 18:
        raise HTTPException(status_code=400, detail="Invalid week (1–18)")
    return get_best_picks_payload(week)

@app.get("/v1/best-picks/2025/{week}/download")
def download(week: int, format: str = Query("json", regex="^(json|csv|pdf)$")):
    if week < 1 or week > 18:
        raise HTTPException(status_code=400, detail="Invalid week (1–18)")
    data = get_best_picks_payload(week)

    if format == "json":
        return JSONResponse(content=data)

    if format == "csv":
        s = io.StringIO(); w = csv.writer(s)
        for section, rows in data.items():
            w.writerow([section])
            if rows and isinstance(rows, list):
                w.writerow(rows[0].keys())
                for r in rows: w.writerow(r.values())
            w.writerow([])
        return Response(content=s.getvalue(),
                        media_type="text/csv; charset=utf-8",
                        headers={"Content-Disposition": f'attachment; filename="nfl_week{week}_predictions.csv"'})

    if format == "pdf":
        pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial", size=14)
        pdf.cell(200, 10, txt=f"NFL Week {week} Predictions", ln=True, align="C")
        for section, rows in data.items():
            pdf.ln(8); pdf.set_font("Arial","B",12)
            pdf.cell(200, 10, txt=section.replace("_"," ").title(), ln=True)
            pdf.set_font("Arial", size=10)
            if rows and isinstance(rows, list):
                for r in rows:
                    line = ", ".join(f"{k}: {v}" for k,v in r.items())
                    pdf.multi_cell(0, 7, line)
        fp = f"/tmp/nfl_week{week}_predictions.pdf"; pdf.output(fp)
        return FileResponse(fp, media_type="application/pdf", filename=os.path.basename(fp))

    raise HTTPException(status_code=400, detail="Invalid format")

@app.get("/v1/lineup/2025/{week}")
def get_dfs_lineup(week: int):
    if week < 1 or week > 18:
        raise HTTPException(status_code=400, detail="Invalid week (1–18)")
    return get_mock_lineup(week)
