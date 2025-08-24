from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, Response
from typing import Dict, Any, List, Optional, Tuple
import os, io, csv, random, datetime, http.client, json as pyjson
from fpdf import FPDF

app = FastAPI(title="NFL Predictor API", version="2.5.0")

# ---------- CORS ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to your Vercel domain later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- ENV ----------
ODDS_API_KEY        = os.getenv("ODDS_API_KEY", "").strip()
ODDS_REGION         = os.getenv("ODDS_REGION", "us")
SPORTSDATAIO_KEY    = os.getenv("SPORTSDATAIO_KEY", "").strip()
FANTASYDATA_API_KEY = os.getenv("FANTASYDATA_API_KEY", "").strip()
FANTASY_SEASON      = os.getenv("FANTASY_SEASON", "2025REG")  # e.g., 2025REG

# ---------- Helpers ----------
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

def _json_get(host: str, path: str, headers: Optional[Dict[str,str]]=None, https=True, timeout=12) -> Optional[Any]:
    try:
        conn = http.client.HTTPSConnection(host, timeout=timeout) if https else http.client.HTTPConnection(host, timeout=timeout)
        conn.request("GET", path, headers=headers or {})
        resp = conn.getresponse()
        if resp.status != 200: return None
        return pyjson.loads(resp.read().decode("utf-8"))
    except Exception:
        return None
    finally:
        try: conn.close()
        except Exception: pass

# ---------- The Odds API (live SU/ATS/Totals) ----------
def _oddsapi_get(path: str, params: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    if not ODDS_API_KEY: return None
    q = "&".join(f"{k}={v}" for k,v in params.items())
    return _json_get("api.the-odds-api.com", f"/v4{path}?apiKey={ODDS_API_KEY}&{q}")

def fetch_market_snap() -> Optional[List[Dict[str, Any]]]:
    h2h = _oddsapi_get("/sports/americanfootball_nfl/odds", {"regions": ODDS_REGION, "markets": "h2h", "oddsFormat": "american"})
    spd = _oddsapi_get("/sports/americanfootball_nfl/odds", {"regions": ODDS_REGION, "markets": "spreads", "oddsFormat": "american"})
    tot = _oddsapi_get("/sports/americanfootball_nfl/odds", {"regions": ODDS_REGION, "markets": "totals", "oddsFormat": "american"})
    if not h2h: return None

    def idx(rows):
        out = {}
        for g in rows:
            home = g.get("home_team")
            away = None
            bks = g.get("bookmakers") or []
            if bks and bks[0].get("markets"):
                outs = bks[0]["markets"][0].get("outcomes") or []
                names = [o.get("name") for o in outs if o.get("name")]
                for nm in names:
                    if nm != home:
                        away = nm; break
            out[(home or "", away or "")] = g
        return out

    h2h_idx = idx(h2h); spd_idx = idx(spd or []); tot_idx = idx(tot or [])
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

TEAMS = ["BUF","KC","SF","DAL","MIA","PHI","CIN","DET","BAL","GB","SEA","LAR","JAX","NYJ","NYG","CLE","PIT","MIN","NO","HOU",
         "ATL","TEN","IND","LV","DEN","CHI","TB","WAS","CAR","ARI","NE","LAC"]

def mock_games_for_week(week: int) -> List[Dict[str, Any]]:
    random.seed(1337 + week)
    pool = TEAMS[:]; random.shuffle(pool)
    games = []
    for i in range(0, min(10, len(pool)-1), 2):
        home, away = pool[i], pool[i+1]
        home_ml = random.choice([-170,-150,-130,-110,110,130,150])
        away_ml = random.choice([-170,-150,-130,-110,110,130,150])
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

        su_rows.append({
            "home": home, "away": away,
            "su_pick": home if ph_fair >= pa_fair else away,
            "su_confidence": round(max(ph_fair, pa_fair), 4)
        })

        fav, spread = g.get("spread_team"), g.get("spread")
        if fav and spread is not None:
            fav_prob = ph_fair if fav == home else pa_fair
            sign_char = "-" if spread < 0 else "+"
            ats_rows.append({
                "ats_pick": f"{fav} {sign_char}{abs(spread)}",
                "spread": float(spread),
                "ats_confidence": round(max(0.50, min(0.75, 0.46 + 0.5*abs(fav_prob-0.5))), 4)
            })

        op = american_to_prob(g.get("over_odds"))
        up = american_to_prob(g.get("under_odds"))
        if op is not None and up is not None:
            of, uf = deflate_vig(op, up)
        else:
            of, uf = 0.5, 0.5

        if of >= uf:
            tot_rows.append({"tot_pick": f"Over {g.get('total')}",  "tot_confidence": round(of, 4)})
        else:
            tot_rows.append({"tot_pick": f"Under {g.get('total')}", "tot_confidence": round(uf, 4)})

    return {
        "top5_su": rank_top_n(su_rows, "su_confidence", 5),
        "top5_ats": rank_top_n(ats_rows, "ats_confidence", 5),
        "top5_totals": rank_top_n(tot_rows, "tot_confidence", 5),
    }

def get_market_predictions() -> Dict[str, Any]:
    snap = fetch_market_snap()
    games = snap if snap else mock_games_for_week(1)
    return build_su_ats_totals(games)

# ---------- SportsDataIO props (only) ----------
def fetch_sportsdataio_props(week: int) -> List[Dict[str, Any]]:
    if not SPORTSDATAIO_KEY: return []
    path = f"/v3/nfl/props/json/PlayerGamePropsByWeek/{FANTASY_SEASON}/{week}"
    data = _json_get("api.sportsdata.io", path, headers={"Ocp-Apim-Subscription-Key": SPORTSDATAIO_KEY})
    if not data: return []
    picks = []
    for r in data:
        player = r.get("Name")
        market = r.get("PropType") or r.get("StatType") or "prop"
        line = safe_float(r.get("Value"))
        if not player or line is None: continue
        picks.append({
            "player": player,
            "prop_type": market,
            "line": line,
            "pick": "Over",          # SDIO payouts sometimes available; conservative default here
            "confidence": 0.55,
            "bookmaker": "SportsDataIO"
        })
    return rank_top_n(picks, "confidence", 5)

# ---------- FantasyData (value picks) ----------
def fetch_fantasydata_week(week: int) -> Optional[List[Dict[str, Any]]]:
    if not FANTASYDATA_API_KEY: return None
    path = f"/v3/nfl/projections/json/PlayerGameProjectionStatsByWeek/{FANTASY_SEASON}/{week}"
    return _json_get("api.fantasydata.net", path, headers={"Ocp-Apim-Subscription-Key": FANTASYDATA_API_KEY})

def build_fantasy_week(week: int) -> List[Dict[str, Any]]:
    arr = fetch_fantasydata_week(week)
    if not arr:
        # Placeholder value list
        random.seed(3000 + week)
        players = ["Josh Allen","CMC","Tyreek Hill","CeeDee Lamb","Davante Adams","Bijan Robinson","Dalton Kincaid"]
        positions = ["QB","RB","WR","TE"]
        out = []
        for _ in range(5):
            p, pos = random.choice(players), random.choice(positions)
            sal = random.randint(5200, 9800)
            val = round(random.uniform(2.2, 3.6), 2)
            out.append({"player": p, "position": pos, "salary": sal, "proj_points": round(val*sal/1000.0,2), "value_score": val})
        return out

    rows = []
    for r in arr:
        name = r.get("Name") or r.get("ShortName") or "TBD"
        pos  = r.get("Position") or ""
        team = r.get("Team") or ""
        pts  = safe_float(r.get("FantasyPointsDraftKings"), safe_float(r.get("FantasyPoints"), 0.0))
        sal  = safe_float(r.get("DraftKingsSalary"), 0.0)
        value= round((pts / sal) * 1000.0, 3) if sal and sal > 0 else round(pts, 3)
        rows.append({"player": name, "position": pos, "team": team, "salary": sal or 0.0,
                     "proj_points": round(pts or 0.0, 2), "value_score": value})
    rows.sort(key=lambda x: (x.get("value_score") or 0.0), reverse=True)
    return rows[:5]

# ---------- Compose payload ----------
def get_best_picks_payload(week: int) -> Dict[str, Any]:
    core = get_market_predictions()
    # Props via SportsDataIO only (with fallback)
    props = fetch_sportsdataio_props(week)
    if not props:
        random.seed(2000 + week)
        players = ["Josh Allen","Jalen Hurts","Patrick Mahomes","Lamar Jackson","Tyreek Hill","Ja'Marr Chase"]
        types = ["Pass Yards","Rush Yards","Receiving Yards","Pass TDs","Receptions"]
        props = [{"player": random.choice(players), "prop_type": random.choice(types),
                  "line": random.randint(55, 310), "pick": "Over", "confidence": 0.55, "bookmaker": "N/A"}
                 for _ in range(5)]
    fantasy = build_fantasy_week(week)
    return {**core, "top5_props": props[:5], "top5_fantasy": fantasy}

# ---------- DFS lineup (placeholder) ----------
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

# ---------- Routes ----------
@app.get("/v1/health")
def health():
    return {
        "ok": True,
        "odds_api_key_set": bool(ODDS_API_KEY),
        "sportsdataio_key_set": bool(SPORTSDATAIO_KEY),
        "fantasydata_key_set": bool(FANTASYDATA_API_KEY),
        "ts": datetime.datetime.utcnow().isoformat()+"Z"
    }

@app.get("/v1/best-picks/2025/{week}")
def best_picks(week: int):
    if week < 1 or week > 18: raise HTTPException(status_code=400, detail="Invalid week (1–18)")
    return get_best_picks_payload(week)

@app.get("/v1/best-picks/2025/{week}/download")
def download(week: int, format: str = Query("json", regex="^(json|csv|pdf)$")):
    if week < 1 or week > 18: raise HTTPException(status_code=400, detail="Invalid week (1–18)")
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
                        headers={"Content-Disposition": f'attachment; filename=\"nfl_week{week}_predictions.csv\""})
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
def get_dfs_lineup(week: int, site: str = Query("DK", regex="^(DK|FD)$")):
    # Placeholder lineup; optimizer/salaries can be re-enabled later
    return get_mock_lineup(week)
