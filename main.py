from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from typing import Dict, Any, List, Optional, Tuple
import os, io, csv, http.client, json as pyjson
from fpdf import FPDF
from urllib.parse import urlencode
from datetime import datetime, timedelta, timezone

APP_VERSION = "LIVE-LINES+PROPS-FALLBACK-1.4.0"

app = FastAPI(title="NFL Predictor API", version=APP_VERSION)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# ENV
ODDS_API_KEY     = (os.getenv("ODDS_API_KEY") or "").strip()
ODDS_REGION      = ((os.getenv("ODDS_REGION") or "us").strip().lower())
ODDS_SPORT       = ((os.getenv("ODDS_SPORT")  or "americanfootball_nfl").strip().lower())
SPORTSDATAIO_KEY = (os.getenv("SPORTSDATAIO_KEY") or "").strip()

# NFL 2025 calendar (UTC)
NFL_2025_WEEK1_UTC = datetime(2025, 9, 1, 0, 0, 0, tzinfo=timezone.utc)
WEEK_LENGTH = timedelta(days=7)

def week_window_utc(week: int) -> Tuple[datetime, datetime]:
    start = NFL_2025_WEEK1_UTC + WEEK_LENGTH * (week - 1)
    return start, start + WEEK_LENGTH

# ---------------- Helpers ----------------
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

def _json_get(host: str, path: str, https=True, timeout=10):
    """Return (data, err, status)."""
    try:
        conn = http.client.HTTPSConnection(host, timeout=timeout) if https else http.client.HTTPConnection(host, timeout=timeout)
        conn.request("GET", path)
        resp = conn.getresponse()
        status = resp.status
        if status != 200:
            return None, f"http {status}", status
        body = resp.read()
        data = pyjson.loads(body.decode("utf-8"))
        return data, None, status
    except Exception as e:
        return None, f"{type(e).__name__}", None
    finally:
        try: conn.close()
        except Exception: pass

def parse_commence_utc(s: Optional[str]) -> Optional[datetime]:
    if not s: return None
    try: return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception: return None

# ---------------- Odds API: games ----------------
def fetch_market_snap() -> Optional[List[Dict[str, Any]]]:
    if not ODDS_API_KEY: return None
    qs = urlencode({"regions": ODDS_REGION, "oddsFormat": "american", "apiKey": ODDS_API_KEY})
    base = f"/v4/sports/{ODDS_SPORT}/odds"
    h2h, _, _ = _json_get("api.the-odds-api.com", f"{base}?markets=h2h&{qs}")
    spd, _, _ = _json_get("api.the-odds-api.com", f"{base}?markets=spreads&{qs}")
    tot, _, _ = _json_get("api.the-odds-api.com", f"{base}?markets=totals&{qs}")
    if not isinstance(h2h, list) or not h2h: return None

    def idx(rows):
        out = {}
        if not isinstance(rows, list): return out
        for g in rows:
            try:
                home = g.get("home_team")
                ct = parse_commence_utc(g.get("commence_time"))
                away = None
                bks = g.get("bookmakers") or []
                if bks and bks[0].get("markets"):
                    outs = bks[0]["markets"][0].get("outcomes") or []
                    names = [o.get("name") for o in outs if o.get("name")]
                    for nm in names:
                        if nm and nm != home:
                            away = nm; break
                out[(home or "", away or "")] = (g, ct)
            except Exception:
                continue
        return out

    h2h_idx = idx(h2h)
    spd_idx = {k: v[0] for k, v in idx(spd or []).items()}
    tot_idx = {k: v[0] for k, v in idx(tot or []).items()}

    games = []
    for key, (row, ct) in h2h_idx.items():
        try:
            home, away = key
            entry = {"home_team": home, "away_team": away,
                     "commence_time": ct.isoformat() if ct else None,
                     "h2h_home": None, "h2h_away": None,
                     "spread": None, "spread_team": None,
                     "total": None, "over_odds": None, "under_odds": None}
            # moneyline
            bks = row.get("bookmakers") or []
            if bks and bks[0].get("markets"):
                outs = bks[0]["markets"][0].get("outcomes") or []
                for o in outs:
                    if o.get("name") == home: entry["h2h_home"] = safe_float(o.get("price"))
                    elif o.get("name") == away: entry["h2h_away"] = safe_float(o.get("price"))
            # spread
            srow = spd_idx.get(key)
            if srow:
                bks = srow.get("bookmakers") or []
                if bks and bks[0].get("markets"):
                    outs = bks[0]["markets"][0].get("outcomes") or []
                    for o in outs:
                        pt = safe_float(o.get("point")); nm = o.get("name")
                        if pt is not None and pt < 0:
                            entry["spread"] = pt; entry["spread_team"] = nm; break
            # totals
            trow = tot_idx.get(key)
            if trow:
                bks = trow.get("bookmakers") or []
                if bks and bks[0].get("markets"):
                    outs = bks[0]["markets"][0].get("outcomes") or []
                    over_pt = under_pt = None
                    for o in outs:
                        nm = (o.get("name") or "").lower()
                        if nm == "over":
                            over_pt = safe_float(o.get("point"))
                            entry["over_odds"] = safe_float(o.get("price"))
                        elif nm == "under":
                            under_pt = safe_float(o.get("point"))
                            entry["under_odds"] = safe_float(o.get("price"))
                    # prefer over line when both exist; they should match
                    entry["total"] = over_pt if over_pt is not None else under_pt
            games.append(entry)
        except Exception:
            continue
    return games if games else None

# ---------------- Odds API: props (primary) ----------------
PROP_MARKETS = ",".join([
    "player_pass_yds",
    "player_pass_tds",
    "player_pass_att",      # attempts (if available)
    "player_rush_yds",
    "player_rush_att",      # attempts (if available)
    "player_rec_yds",
    "player_receptions",
])

def fetch_player_props_raw() -> Optional[List[Dict[str, Any]]]:
    if not ODDS_API_KEY: return None
    qs = urlencode({"regions": ODDS_REGION, "oddsFormat":"american", "apiKey": ODDS_API_KEY, "markets": PROP_MARKETS})
    base = f"/v4/sports/{ODDS_SPORT}/odds"
    data, _, _ = _json_get("api.the-odds-api.com", f"{base}?{qs}")
    return data if isinstance(data, list) else None

# ---------------- SportsDataIO: props (fallback) ----------------
def fetch_sportsdataio_props(season: str, week: int) -> List[Dict[str, Any]]:
    key = SPORTSDATAIO_KEY
    if not key: return []
    path = f"/v3/nfl/odds/json/PlayerPropsByWeek/{season}/{week}?key={key}"
    data, err, st = _json_get("api.sportsdata.io", path)
    if not isinstance(data, list): return []
    picks: List[Dict[str, Any]] = []
    for p in data:
        try:
            player = p.get("Name") or p.get("PlayerName") or "Unknown"
            market = p.get("BetName") or "Prop"
            line = safe_float(p.get("Value"))
            over_price = safe_float(p.get("OverPayout"))
            under_price= safe_float(p.get("UnderPayout"))
            op = american_to_prob(over_price)
            up = american_to_prob(under_price)
            of, uf = deflate_vig(op or 0.5, up or 0.5)
            conf = max(of or 0.5, uf or 0.5)
            side = "Over" if (of or 0.5) >= (uf or 0.5) else "Under"
            picks.append({
                "player": player,
                "prop_type": market,
                "line": line,
                "pick": side,
                "confidence": round(conf, 3),
                "bookmaker": "SportsDataIO",
            })
        except Exception:
            continue
    return picks

def build_top_props_for_week(week: int) -> List[Dict[str, Any]]:
    picks: List[Dict[str, Any]] = []
    raw = fetch_player_props_raw()
    if raw:
        start_utc, end_utc = week_window_utc(week)
        for ev in raw:
            ct = parse_commence_utc(ev.get("commence_time"))
            if ct and not (start_utc <= ct < end_utc):
                continue
            for bm in (ev.get("bookmakers") or []):
                for m in (bm.get("markets") or []):
                    outs = m.get("outcomes") or []
                    over = next((o for o in outs if (o.get("name") or "").lower()=="over"), None)
                    under= next((o for o in outs if (o.get("name") or "").lower()=="under"), None)
                    line = safe_float((over or under or {}).get("point"))
                    if line is None: 
                        continue
                    op = american_to_prob(safe_float((over or {}).get("price")))
                    up = american_to_prob(safe_float((under or {}).get("price")))
                    of, uf = deflate_vig(op or 0.5, up or 0.5)
                    conf = max(of or 0.5, uf or 0.5)
                    side = "Over" if (of or 0.5) >= (uf or 0.5) else "Under"
                    player = m.get("player") or m.get("player_name") or "Unknown"
                    prop_key = m.get("key") or m.get("market") or "prop"
                    picks.append({
                        "player": str(player),
                        "prop_type": prop_key,
                        "line": line,
                        "pick": side,
                        "confidence": round(conf, 3),
                        "bookmaker": bm.get("title") or bm.get("key") or "OddsAPI",
                    })
                if picks: break
    # Fallback if empty
    if not picks:
        season = "2025REG"
        picks = fetch_sportsdataio_props(season, week)

    # Deduplicate (player, prop_type), keep highest confidence; then top 5
    best: Dict[Tuple[str,str], Dict[str,Any]] = {}
    for p in picks:
        k = (p["player"], p["prop_type"])
        if k not in best or p["confidence"] > best[k]["confidence"]:
            best[k] = p
    top = list(best.values())
    top.sort(key=lambda x: x["confidence"], reverse=True)
    return top[:5]

# ---------------- Fallback game ----------------
def mock_games() -> List[Dict[str, Any]]:
    ct = datetime(2025,9,5,0,21,0, tzinfo=timezone.utc).isoformat()
    return [{
        "home_team":"BUF","away_team":"NYJ","commence_time": ct,
        "h2h_home":-120,"h2h_away":110,
        "spread":-3.5,"spread_team":"BUF","total":45.5,"over_odds":-110,"under_odds":-110
    }]

# ---------------- Build SU / ATS / Totals ----------------
def build_su_ats_totals(games: List[Dict[str, Any]]) -> Dict[str, Any]:
    su_rows, ats_rows, tot_rows = [], [], []
    seen = set()
    for g in games:
        home, away = g.get("home_team"), g.get("away_team")
        key = (home or "", away or "")
        if key in seen: continue
        seen.add(key)

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

        total_line = g.get("total")
        op = american_to_prob(g.get("over_odds"))
        up = american_to_prob(g.get("under_odds"))
        if total_line is not None and (op is not None and up is not None):
            of, uf = deflate_vig(op, up)
            if (of or 0.5) >= (uf or 0.5):
                tot_rows.append({"tot_pick": f"Over {total_line}", "total_line": float(total_line), "tot_confidence": round(of or 0.5, 4)})
            else:
                tot_rows.append({"tot_pick": f"Under {total_line}", "total_line": float(total_line), "tot_confidence": round(uf or 0.5, 4)})

    return {
        "top5_su": rank_top_n(su_rows, "su_confidence", 5),
        "top5_ats": rank_top_n(ats_rows, "ats_confidence", 5),
        "top5_totals": rank_top_n(tot_rows, "tot_confidence", 5),
    }

def get_live_payload_for_week(week: int) -> Dict[str, Any]:
    snap = fetch_market_snap()
    games = snap if snap else mock_games()
    start_utc, end_utc = week_window_utc(week)
    filtered = []
    for g in games:
        ct = parse_commence_utc(g.get("commence_time")) if isinstance(g.get("commence_time"), str) else parse_commence_utc(g.get("commence_time"))
        if ct is None or (start_utc <= ct < end_utc): filtered.append(g)
    if not filtered: filtered = games

    core = build_su_ats_totals(filtered)
    props = build_top_props_for_week(week)  # Odds API → SDIO fallback
    return {**core, "top5_props": props,
            "top5_fantasy": [
                {"player":"Ja'Marr Chase","position":"WR","salary":8800,"value_score":3.45},
                {"player":"Bijan Robinson","position":"RB","salary":7800,"value_score":3.22},
                {"player":"Travis Etienne","position":"RB","salary":6900,"value_score":3.10},
                {"player":"Davante Adams","position":"WR","salary":8400,"value_score":2.98},
                {"player":"Dalton Kincaid","position":"TE","salary":5200,"value_score":2.86},
            ]}

# ---------------- Routes ----------------
@app.get("/")
def root(): return {"ok": True, "version": APP_VERSION}

@app.get("/v1/health")
def health():
    qs = urlencode({"regions": ODDS_REGION, "markets":"h2h", "oddsFormat":"american", "apiKey": ODDS_API_KEY})
    base = f"/v4/sports/{ODDS_SPORT}/odds"
    data, err, st = _json_get("api.the-odds-api.com", f"{base}?{qs}")
    sample = len(data[:1]) if isinstance(data, list) else 0
    status = str(st) if st else (err or "no key" if not ODDS_API_KEY else "error")
    return {"ok": True, "version": APP_VERSION,
            "odds_api_key_set": bool(ODDS_API_KEY),
            "odds_region": ODDS_REGION, "odds_sport": ODDS_SPORT,
            "odds_shallow_status": status, "odds_sample_items": sample}

@app.get("/v1/debug/snap")
def debug_snap():
    qs = urlencode({"regions": ODDS_REGION, "oddsFormat":"american", "apiKey": ODDS_API_KEY})
    base = f"/v4/sports/{ODDS_SPORT}/odds"
    h2h, err1, st1 = _json_get("api.the-odds-api.com", f"{base}?markets=h2h&{qs}")
    spd, err2, st2 = _json_get("api.the-odds-api.com", f"{base}?markets=spreads&{qs}")
    tot, err3, st3 = _json_get("api.the-odds-api.com", f"{base}?markets=totals&{qs}")
    return {"sport": ODDS_SPORT, "region": ODDS_REGION,
            "h2h": {"status": st1, "error": err1, "count": (len(h2h) if isinstance(h2h, list) else 0)},
            "spreads": {"status": st2, "error": err2, "count": (len(spd) if isinstance(spd, list) else 0)},
            "totals": {"status": st3, "error": err3, "count": (len(tot) if isinstance(tot, list) else 0)}}

@app.get("/v1/best-picks/2025/{week}")
def best_picks(week: int):
    if week < 1 or week > 18: raise HTTPException(400, "Invalid week")
    return get_live_payload_for_week(week)

@app.get("/v1/best-picks/2025/{week}/download")
def download(week: int, format: str = Query("json", regex="^(json|csv|pdf)$")):
    if week < 1 or week > 18: raise HTTPException(400, "Invalid week")
    data = get_live_payload_for_week(week)
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
        return Response(content=s.getvalue(), media_type="text/csv; charset=utf-8",
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
