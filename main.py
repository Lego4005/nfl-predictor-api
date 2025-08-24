from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from typing import Dict, Any, List, Optional, Tuple
import os, io, csv, http.client, json as pyjson
from fpdf import FPDF

APP_VERSION = "LIVE-LINES-ODDSAPI-1.0.0"

app = FastAPI(title="NFL Predictor API", version=APP_VERSION)

# -------- CORS --------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------- ENV --------
ODDS_API_KEY = (os.getenv("ODDS_API_KEY") or "").strip()
ODDS_REGION  = (os.getenv("ODDS_REGION") or "us").strip()
ODDS_SPORT   = (os.getenv("ODDS_SPORT") or "americanfootball_nfl").strip()

# -------- Helpers --------
def safe_float(x, default=None):
    try: return float(x)
    except Exception: return default

def american_to_prob(odds: Optional[float]) -> Optional[float]:
    if odds is None: return None
    try:
        o = float(odds)
        if o > 0:  return 100.0 / (o + 100.0)
        if o < 0:  return (-o) / ((-o) + 100.0)
        return None
    except Exception:
        return None

def deflate_vig(pa: Optional[float], pb: Optional[float]) -> Tuple[Optional[float], Optional[float]]:
    if pa is None or pb is None: return (pa, pb)
    s = pa + pb
    if s <= 0: return (pa, pb)
    return (pa / s, pb / s)

def rank_top_n(items: List[Dict[str, Any]], key: str, n: int = 5) -> List[Dict[str, Any]]:
    try:
        return sorted(items, key=lambda r: r.get(key, 0.0), reverse=True)[:n]
    except Exception:
        return items[:n]

def _json_get(host: str, path: str, https=True, timeout=10) -> Optional[Any]:
    try:
        conn = http.client.HTTPSConnection(host, timeout=timeout) if https else http.client.HTTPConnection(host, timeout=timeout)
        conn.request("GET", path)
        resp = conn.getresponse()
        if resp.status != 200:
            return None
        return pyjson.loads(resp.read().decode("utf-8"))
    except Exception:
        return None
    finally:
        try: conn.close()
        except Exception: pass

# -------- Odds API fetch --------
def fetch_market_snap() -> Optional[List[Dict[str, Any]]]:
    if not ODDS_API_KEY:
        return None

    base = f"/v4/sports/{ODDS_SPORT}/odds"
    qs = f"regions={ODDS_REGION}&oddsFormat=american&apiKey={ODDS_API_KEY}"

    h2h = _json_get("api.the-odds-api.com", f"{base}?markets=h2h&{qs}")
    spd = _json_get("api.the-odds-api.com", f"{base}?markets=spreads&{qs}")
    tot = _json_get("api.the-odds-api.com", f"{base}?markets=totals&{qs}")

    if not isinstance(h2h, list) or len(h2h) == 0:
        return None

    def idx(rows):
        out = {}
        if not isinstance(rows, list): return out
        for g in rows:
            try:
                home = g.get("home_team")
                away = None
                bks = g.get("bookmakers") or []
                if bks and bks[0].get("markets"):
                    outs = bks[0]["markets"][0].get("outcomes") or []
                    names = [o.get("name") for o in outs if o.get("name")]
                    for nm in names:
                        if nm and nm != home:
                            away = nm; break
                out[(home or "", away or "")] = g
            except Exception:
                continue
        return out

    h2h_idx = idx(h2h)
    spd_idx = idx(spd or [])
    tot_idx = idx(tot or [])

    games = []
    for key, row in h2h_idx.items():
        try:
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
            # Spread
            srow = spd_idx.get(key)
            if srow:
                bks = srow.get("bookmakers") or []
                if bks and bks[0].get("markets"):
                    outs = bks[0]["markets"][0].get("outcomes") or []
                    for o in outs:
                        pt = safe_float(o.get("point")); nm = o.get("name")
                        if pt is not None and pt < 0:
                            entry["spread"] = pt; entry["spread_team"] = nm; break
            # Total
            trow = tot_idx.get(key)
            if trow:
                bks = trow.get("bookmakers") or []
                if bks and bks[0].get("markets"):
                    outs = bks[0]["markets"][0].get("outcomes") or []
                    for o in outs:
                        nm = (o.get("name") or "").lower()
                        if nm == "over":
                            entry["total"] = safe_float(o.get("point"))
                            entry["over_odds"] = safe_float(o.get("price"))
                        elif nm == "under":
                            if entry["total"] is None: entry["total"] = safe_float(o.get("point"))
                            entry["under_odds"] = safe_float(o.get("price"))
            games.append(entry)
        except Exception:
            continue
    return games if games else None

# -------- Mock fallback --------
def mock_games() -> List[Dict[str, Any]]:
    return [{
        "home_team":"BUF","away_team":"NYJ","h2h_home":-120,"h2h_away":110,
        "spread":-3.5,"spread_team":"BUF","total":45.5,"over_odds":-110,"under_odds":-110
    }]

# -------- Build SU/ATS/Totals --------
def build_su_ats_totals(games: List[Dict[str, Any]]) -> Dict[str, Any]:
    su_rows, ats_rows, tot_rows = [], [], []
    for g in games:
        home, away = g.get("home_team"), g.get("away_team")
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
                "ats_confidence": round(max(0.50, min(0.75, 0.46 + 0.5*abs((fav_prob or 0.5) - 0.5))), 4)
            })

        op = american_to_prob(g.get("over_odds"))
        up = american_to_prob(g.get("under_odds"))
        if op is not None and up is not None:
            of, uf = deflate_vig(op, up)
        else:
            of, uf = 0.5, 0.5

        if (of or 0.5) >= (uf or 0.5):
            tot_rows.append({"tot_pick": f"Over {g.get('total')}", "tot_confidence": round(of or 0.5, 4)})
        else:
            tot_rows.append({"tot_pick": f"Under {g.get('total')}", "tot_confidence": round(uf or 0.5, 4)})

    props = [{"player":"Josh Allen","prop_type":"Pass Yards","prediction":286,"confidence":0.72}]
    fantasy = [{"player":"Ja'Marr Chase","position":"WR","salary":8800,"value_score":3.45}]

    return {
        "top5_su": rank_top_n(su_rows, "su_confidence", 5),
        "top5_ats": rank_top_n(ats_rows, "ats_confidence", 5),
        "top5_totals": rank_top_n(tot_rows, "tot_confidence", 5),
        "top5_props": props,
        "top5_fantasy": fantasy,
    }

def get_live_or_mock_payload() -> Dict[str, Any]:
    snap = fetch_market_snap()
    games = snap if snap else mock_games()
    return build_su_ats_totals(games)

# -------- Routes --------
@app.get("/")
def root(): return {"ok": True, "version": APP_VERSION}

@app.get("/v1/health")
def health():
    status, sample = "no key", 0
    if ODDS_API_KEY:
        base = f"/v4/sports/{ODDS_SPORT}/odds"
        qs   = f"regions={ODDS_REGION}&markets=h2h&oddsFormat=american&apiKey={ODDS_API_KEY}"
        data = _json_get("api.the-odds-api.com", f"{base}?{qs}")
        if isinstance(data, list):
            status, sample = "200", len(data[:1])
        else:
            status = "error or empty"
    return {"ok": True, "version": APP_VERSION,
            "odds_api_key_set": bool(ODDS_API_KEY),
            "odds_region": ODDS_REGION,
            "odds_sport": ODDS_SPORT,
            "odds_shallow_status": status,
            "odds_sample_items": sample}

@app.get("/v1/debug/snap")
def debug_snap():
    if not ODDS_API_KEY:
        return {"ok": False, "reason": "No ODDS_API_KEY set"}
    base = f"/v4/sports/{ODDS_SPORT}/odds"
    qs   = f"regions={ODDS_REGION}&oddsFormat=american&apiKey={ODDS_API_KEY}"
    h2h = _json_get("api.the-odds-api.com", f"{base}?markets=h2h&{qs}")
    spd = _json_get("api.the-odds-api.com", f"{base}?markets=spreads&{qs}")
    tot = _json_get("api.the-odds-api.com", f"{base}?markets=totals&{qs}")
    def count_first(lst):
        return {"count": (len(lst) if isinstance(lst, list) else 0),
                "sample": (lst[:1] if isinstance(lst, list) and lst else [])}
    return {"sport": ODDS_SPORT, "region": ODDS_REGION,
            "h2h": count_first(h2h), "spreads": count_first(spd), "totals": count_first(tot)}

@app.get("/v1/best-picks/2025/{week}")
def best_picks(week: int):
    if week < 1 or week > 18: raise HTTPException(400, "Invalid week")
    return get_live_or_mock_payload()

@app.get("/v1/best-picks/2025/{week}/download")
def download(week: int, format: str = Query("json", regex="^(json|csv|pdf)$")):
    if week < 1 or week > 18: raise HTTPException(400, "Invalid week")
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
        return Response(content=s.getvalue(),
                        media_type="text/csv; charset=utf-8",
                        headers={"Content-Disposition": f"attachment; filename=nfl_week{week}_predictions.csv"})
    if format == "pdf":
        pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"NFL Week {week} Predictions", ln=True, align="C")
        for section, rows in data.items():
            pdf.ln(8); pdf.set_font("Arial","B",12); pdf.cell(200, 10, txt=section.upper(), ln=True)
            pdf.set_font("Arial", size=10)
            if rows and isinstance(rows, list):
                for row in rows:
                    line = ", ".join([f"{k}: {v}" for k,v in row.items()])
                    pdf.multi_cell(0, 8, line)
        fp = f"/tmp/nfl_week{week}.pdf"; pdf.output(fp)
        return FileResponse(fp, media_type="application/pdf", filename=os.path.basename(fp))
    raise HTTPException(400, "Invalid format")

@app.get("/v1/lineup/2025/{week}")
def lineup(week: int, site: str = Query("DK", regex="^(DK|FD)$")):
    return {"week": week, "salary_cap": 50000, "total_salary": 49800, "projected_points": 162.4,
            "lineup": [{"position":"QB","player":"Jalen Hurts","team":"PHI","salary":7900,"proj_points":24.3}]}
