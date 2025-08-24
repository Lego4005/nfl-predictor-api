from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, Response
from typing import Dict, Any, List, Optional, Tuple
import os, io, csv, random, datetime, http.client, json as pyjson
from fpdf import FPDF

APP_VERSION = "LIVE-LINES-1.0.0"

app = FastAPI(title="NFL Predictor API", version=APP_VERSION)

# -------- CORS --------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict to your frontend domain later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------- ENV --------
ODDS_API_KEY = (os.getenv("ODDS_API_KEY") or "").strip()
ODDS_REGION  = (os.getenv("ODDS_REGION") or "us").strip()   # us | uk | eu | au

# -------- Helpers --------
def safe_float(x, default=None):
    try: return float(x)
    except: return default

def american_to_prob(odds: Optional[float]) -> Optional[float]:
    if odds is None: return None
    try: o = float(odds)
    except: return None
    if o > 0:  return 100.0 / (o + 100.0)
    if o < 0:  return (-o) / ((-o) + 100.0)
    return None

def deflate_vig(pa: Optional[float], pb: Optional[float]) -> Tuple[Optional[float], Optional[float]]:
    if pa is None or pb is None: return (pa, pb)
    s = pa + pb
    if s <= 0: return (pa, pb)
    return (pa / s, pb / s)

def rank_top_n(items: List[Dict[str, Any]], key: str, n: int = 5) -> List[Dict[str, Any]]:
    return sorted(items, key=lambda r: r.get(key, 0.0), reverse=True)[:n]

def _json_get(host: str, path: str, https=True, timeout=12) -> Optional[Any]:
    try:
        conn = http.client.HTTPSConnection(host, timeout=timeout) if https else http.client.HTTPConnection(host, timeout=timeout)
        conn.request("GET", path)
        resp = conn.getresponse()
        if resp.status != 200:
            return None
        data = pyjson.loads(resp.read().decode("utf-8"))
        return data
    except Exception:
        return None
    finally:
        try: conn.close()
        except Exception: pass

# -------- The Odds API fetch --------
def fetch_market_snap() -> Optional[List[Dict[str, Any]]]:
    """Fetch H2H, spreads, totals snapshots. Endpoint is event-based (no week filter)."""
    if not ODDS_API_KEY:
        return None

    # Build URLs cleanly (avoid InvalidURL)
    h2h_path = f"/v4/sports/americanfootball_nfl/odds?regions={ODDS_REGION}&markets=h2h&oddsFormat=american&apiKey={ODDS_API_KEY}"
    spd_path = f"/v4/sports/americanfootball_nfl/odds?regions={ODDS_REGION}&markets=spreads&oddsFormat=american&apiKey={ODDS_API_KEY}"
    tot_path = f"/v4/sports/americanfootball_nfl/odds?regions={ODDS_REGION}&markets=totals&oddsFormat=american&apiKey={ODDS_API_KEY}"

    h2h = _json_get("api.the-odds-api.com", h2h_path)
    spd = _json_get("api.the-odds-api.com", spd_path)
    tot = _json_get("api.the-odds-api.com", tot_path)
    if not h2h or not isinstance(h2h, list):
        return None

    def idx(rows):
        out = {}
        for g in rows:
            home = g.get("home_team")
            # Infer away from the first bookmaker market names
            away = None
            bks = g.get("bookmakers") or []
            if bks and bks[0].get("markets"):
                outs = bks[0]["markets"][0].get("outcomes") or []
                names = [o.get("name") for o in outs if o.get("name")]
                for nm in names:
                    if nm and nm != home:
                        away = nm; break
            out[(home or "", away or "")] = g
        return out

    h2h_idx = idx(h2h)
    spd_idx = idx(spd or [])
    tot_idx = idx(tot or [])

    games = []
    for key, row in h2h_idx.items():
        home, away = key
        entry = {"home_team": home, "away_team": away,
                 "h2h_home": None, "h2h_away": None,
                 "spread": None, "spread_team": None,
                 "total": None, "over_odds": None, "under_odds": None}
        # H2H
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
                    pt = safe_float(o.get("point")); nm = o.get("name")
                    if pt is not None and pt < 0:
                        fav, fav_line = nm, pt; break
                if fav_line is not None:
                    entry["spread"] = fav_line; entry["spread_team"] = fav
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

# -------- Fallback (mock) --------
TEAMS = ["BUF","KC","SF","DAL","MIA","PHI","CIN","DET","BAL","GB","SEA","LAR","JAX","NYJ","NYG","CLE","PIT","MIN","NO","HOU",
         "ATL","TEN","IND","LV","DEN","CHI","TB","WAS","CAR","ARI","NE","LAC"]

def mock_games() -> List[Dict[str, Any]]:
    random.seed(1337)
    pool = TEAMS[:]
    random.shuffle(pool)
    games = []
    for i in range(0, min(10, len(pool)-1), 2):
        home, away = pool[i], pool[i+1]
        # Fake lines
        line = random.choice([-6.5,-4.5,-3.5,-2.5,-1.5,-0.5])
        fav = home
        total = random.choice([41.5,43.5,45.5,47.5,49.5])
        games.append({
            "home_team": home, "away_team": away,
            "h2h_home": -120, "h2h_away": 110,
            "spread": line, "spread_team": fav,
            "total": total, "over_odds": -110, "under_odds": -110
        })
    return games

# -------- Build SU/ATS/Totals from games --------
def build_su_ats_totals(games: List[Dict[str, Any]]) -> Dict[str, Any]:
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

        # ATS
        fav, spread = g.get("spread_team"), g.get("spread")
        if fav and spread is not None:
            fav_prob = ph_fair if fav == home else pa_fair
            sign_char = "-" if spread < 0 else "+"
            ats_rows.append({
                "ats_pick": f"{fav} {sign_char}{abs(spread)}",
                "spread": float(spread),
                "ats_confidence": round(max(0.50, min(0.75, 0.46 + 0.5*abs(fav_prob-0.5))), 4)
            })

        # Totals
        op = american_to_prob(g.get("over_odds"))
        up = american_to_prob(g.get("under_odds"))
        if op is not None and up is not None: of, uf = deflate_vig(op, up)
        else: of, uf = 0.5, 0.5

        if of >= uf:
            tot_rows.append({"tot_pick": f"Over {g.get('total')}", "tot_confidence": round(of, 4)})
        else:
            tot_rows.append({"tot_pick": f"Under {g.get('total')}", "tot_confidence": round(uf, 4)})

    return {
        "top5_su": rank_top_n(su_rows, "su_confidence", 5),
        "top5_ats": rank_top_n(ats_rows, "ats_confidence", 5),
        "top5_totals": rank_top_n(tot_rows, "tot_confidence", 5),
        # Keep props/fantasy placeholder for UI stability
        "top5_props": [
            {"player":"Josh Allen","prop_type":"Pass Yards","prediction":286,"confidence":0.72},
            {"player":"Jalen Hurts","prop_type":"Rush TDs","prediction":1,"confidence":0.69},
            {"player":"Justin Jefferson","prop_type":"Receiving Yards","prediction":105,"confidence":0.67},
            {"player":"Bijan Robinson","prop_type":"Rush Yards","prediction":88,"confidence":0.66},
            {"player":"Patrick Mahomes","prop_type":"Pass TDs","prediction":3,"confidence":0.64},
        ],
        "top5_fantasy": [
            {"player":"Ja'Marr Chase","position":"WR","salary":8800,"value_score":3.45},
            {"player":"Bijan Robinson","position":"RB","salary":7800,"value_score":3.22},
            {"player":"Travis Etienne","position":"RB","salary":6900,"value_score":3.10},
            {"player":"Davante Adams","position":"WR","salary":8400,"value_score":2.98},
            {"player":"Dalton Kincaid","position":"TE","salary":5200,"value_score":2.86},
        ],
    }

def get_live_or_mock_payload() -> Dict[str, Any]:
    snap = fetch_market_snap()
    games = snap if snap else mock_games()
    return build_su_ats_totals(games)

# -------- Root & Health --------
@app.get("/")
def root():
    return {
        "name": "NFL Predictor API",
        "version": APP_VERSION,
        "routes": [
            "/", "/ping", "/v1/health",
            "/v1/best-picks/2025/{week}",
            "/v1/best-picks/2025/{week}/download?format=json|csv|pdf",
            "/v1/lineup/2025/{week}",
        ],
    }

@app.get("/ping")
def ping():
    return {"ok": True, "ts": datetime.datetime.utcnow().isoformat() + "Z"}

@app.get("/v1/health")
def health():
    # Try a shallow Odds API call to detect simple misconfigurations
    status = "skipped (no key)"
    sample = 0
    if ODDS_API_KEY:
        shallow_path = f"/v4/sports/americanfootball_nfl/odds?regions={ODDS_REGION}&markets=h2h&oddsFormat=american&apiKey={ODDS_API_KEY}"
        data = _json_get("api.the-odds-api.com", shallow_path)
        if isinstance(data, list):
            status = "200"
            sample = len(data[:1])
        else:
            status = "error or empty"

    return {
        "ok": True,
        "version": APP_VERSION,
        "odds_api_key_set": bool(ODDS_API_KEY),
        "odds_region": ODDS_REGION,
        "odds_shallow_status": status,
        "odds_sample_items": sample,
        "ts": datetime.datetime.utcnow().isoformat() + "Z",
    }

# -------- Core: live SU/ATS/Totals + placeholders --------
@app.get("/v1/best-picks/2025/{week}")
def best_picks(week: int):
    if week < 1 or week > 18:
        raise HTTPException(status_code=400, detail="Invalid week (1–18)")
    return get_live_or_mock_payload()

@app.get("/v1/best-picks/2025/{week}/download")
def download(week: int, format: str = Query("json", regex="^(json|csv|pdf)$")):
    if week < 1 or week > 18:
        raise HTTPException(status_code=400, detail="Invalid week (1–18)")
    data = get_live_or_mock_payload()

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

# -------- DFS lineup (placeholder) --------
@app.get("/v1/lineup/2025/{week}")
def lineup(week: int, site: str = Query("DK", regex="^(DK|FD)$")):
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
