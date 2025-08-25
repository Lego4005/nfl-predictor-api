from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from typing import Dict, Any, List, Optional, Tuple
import os, io, csv, http.client, json as pyjson, re
from fpdf import FPDF
from urllib.parse import urlencode
from datetime import datetime, timedelta, timezone

APP_VERSION = "RESILIENT-DIAG-2.3.1"

app = FastAPI(title="NFL Predictor API", version=APP_VERSION)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    s = NFL_2025_WEEK1_UTC + WEEK_LENGTH * (week - 1)
    return s, s + WEEK_LENGTH

# ---------- helpers ----------
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
    try: return sorted(items, key=lambda r: r.get(key, 0.0), reverse=True)[:n]
    except Exception: return items[:n]

def _json_get(host: str, path: str, https=True, timeout=12, headers: Optional[Dict[str,str]]=None):
    try:
        conn = http.client.HTTPSConnection(host, timeout=timeout) if https else http.client.HTTPConnection(host, timeout=timeout)
        conn.request("GET", path, headers=headers or {})
        resp = conn.getresponse()
        st = resp.status
        if st != 200:
            body = ""
            try: body = resp.read(200).decode("utf-8", "ignore")
            except Exception: pass
            return {"_raw": body}, f"http {st}", st
        return pyjson.loads(resp.read().decode("utf-8")), None, st
    except Exception as e:
        return None, f"{type(e).__name__}", None
    finally:
        try: conn.close()
        except Exception: pass

def parse_commence_utc(s: Optional[str]) -> Optional[datetime]:
    if not s: return None
    try: return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception: return None

def extract_number(text: Optional[str]) -> Optional[float]:
    if not isinstance(text, str): return None
    m = re.search(r"(-?\d+(\.\d+)?)", text)
    return safe_float(m.group(1)) if m else None

# ---------- prop label normalization ----------
def normalize_prop_label(key_or_text: str) -> Tuple[str, str]:
    s = (key_or_text or "").lower()
    if "player_pass_yds" in s or "passing yards" in s:      return ("Passing Yards", "yds")
    if "player_pass_tds" in s or "passing touchdowns" in s: return ("Passing TDs", "TDs")
    if "player_pass_att" in s or "pass attempts" in s:      return ("Passing Attempts", "att")
    if "player_rush_yds" in s or "rushing yards" in s:      return ("Rushing Yards", "yds")
    if "player_rush_att" in s or "rushing attempts" in s:   return ("Rushing Attempts", "att")
    if "player_rec_yds"  in s or "receiving yards" in s:    return ("Receiving Yards", "yds")
    if "player_receptions" in s or "receptions" in s:       return ("Receptions", "rec")
    return (key_or_text or "Prop", "")

# ---------------- Odds API: games ----------------
def fetch_market_snap() -> Optional[List[Dict[str, Any]]]:
    if not ODDS_API_KEY: return None
    qs   = urlencode({"regions": ODDS_REGION or "us", "oddsFormat": "american", "apiKey": ODDS_API_KEY})
    base = f"/v4/sports/{ODDS_SPORT}/odds"
    h2h, _, _ = _json_get("api.the-odds-api.com", f"{base}?markets=h2h&{qs}")
    spd, _, _ = _json_get("api.the-odds-api.com", f"{base}?markets=spreads&{qs}")
    tot, _, _ = _json_get("api.the-odds-api.com", f"{base}?markets=totals&{qs}")
    if not isinstance(h2h, list) or not h2h: return None

    def index_by_teams(rows):
        out = {}
        if not isinstance(rows, list): return out
        for g in rows:
            try:
                home = g.get("home_team"); away = g.get("away_team")
                ct   = parse_commence_utc(g.get("commence_time"))
                if not home or not away:
                    bks = g.get("bookmakers") or []
                    if bks and bks[0].get("markets"):
                        outs = bks[0]["markets"][0].get("outcomes") or []
                        for o in outs:
                            nm = o.get("name")
                            if nm and nm != home: away = nm; break
                if not home or not away: continue
                out[(home, away)] = (g, ct)
            except Exception:
                continue
        return out

    h2h_idx = index_by_teams(h2h)
    spd_idx = {k: v[0] for k, v in index_by_teams(spd or []).items()}
    tot_idx = {k: v[0] for k, v in index_by_teams(tot or []).items()}

    games: List[Dict[str, Any]] = []
    for key, (row, ct) in h2h_idx.items():
        try:
            home, away = key
            entry = {
                "home_team": home, "away_team": away,
                "commence_time": ct.isoformat() if ct else None,
                "h2h_home": None, "h2h_away": None,
                "spread": None, "spread_team": None,
                "total": None, "over_odds": None, "under_odds": None
            }
            # moneylines
            for bm in (row.get("bookmakers") or []):
                for mk in (bm.get("markets") or []):
                    for o in (mk.get("outcomes") or []):
                        if o.get("name") == home: entry["h2h_home"] = safe_float(o.get("price"))
                        elif o.get("name") == away: entry["h2h_away"] = safe_float(o.get("price"))
                if entry["h2h_home"] is not None or entry["h2h_away"] is not None: break
            # spreads
            srow = spd_idx.get(key)
            if srow:
                done = False
                for bm in (srow.get("bookmakers") or []):
                    for mk in (bm.get("markets") or []):
                        for o in (mk.get("outcomes") or []):
                            pt = safe_float(o.get("point")); nm = o.get("name")
                            if pt is not None and pt < 0:
                                entry["spread"] = pt; entry["spread_team"] = nm
                                done = True; break
                        if done: break
                    if done: break
            # totals
            trow = tot_idx.get(key)
            if trow:
                best_line=None; op=None; up=None
                for bm in (trow.get("bookmakers") or []):
                    for mk in (bm.get("markets") or []):
                        outs = mk.get("outcomes") or []
                        over = next((o for o in outs if (o.get("name") or "").lower()=="over"), None)
                        under= next((o for o in outs if (o.get("name") or "").lower()=="under"), None)
                        over_pt = safe_float((over or {}).get("point"))
                        under_pt= safe_float((under or {}).get("point"))
                        line = over_pt if over_pt is not None else under_pt
                        if line is not None:
                            best_line = line
                            op = safe_float((over or {}).get("price"))
                            up = safe_float((under or {}).get("price"))
                            break
                    if best_line is not None: break
                if best_line is not None:
                    entry["total"]      = best_line
                    entry["over_odds"]  = op
                    entry["under_odds"] = up
            games.append(entry)
        except Exception:
            continue
    return games if games else None

# ---------- Odds API props (broadened regions) ----------
PROP_MARKETS = ",".join([
    "player_pass_yds","player_pass_tds","player_pass_att",
    "player_rush_yds","player_rush_att",
    "player_rec_yds","player_receptions",
])
def fetch_player_props_raw_oddsapi() -> Optional[List[Dict[str, Any]]]:
    if not ODDS_API_KEY: return None
    broader = f"{ODDS_REGION or 'us'},uk,eu,au"
    qs = urlencode({"regions": broader, "oddsFormat":"american", "apiKey": ODDS_API_KEY, "markets": PROP_MARKETS})
    data, _, _ = _json_get("api.the-odds-api.com", f"/v4/sports/{ODDS_SPORT}/odds?{qs}")
    return data if isinstance(data, list) else None

# ---------- SportsDataIO props (try query and header) ----------
def fetch_sportsdataio_rows(path: str) -> Tuple[int, int]:
    # returns counts for diagnostics only (keeps code smaller here)
    d1, _, s1 = _json_get("api.sportsdata.io", f"{path}?key={SPORTSDATAIO_KEY}")
    c1 = len(d1) if isinstance(d1, list) else 0
    d2, _, s2 = _json_get("api.sportsdata.io", path,
                          headers={"Ocp-Apim-Subscription-Key": SPORTSDATAIO_KEY} if SPORTSDATAIO_KEY else None)
    c2 = len(d2) if isinstance(d2, list) else 0
    return (c1 if c1 else 0), (c2 if c2 else 0)

def fetch_sportsdataio_props(season: str, week: int) -> List[Dict[str, Any]]:
    # try query first
    rows, _, _ = _json_get("api.sportsdata.io", f"/v3/nfl/odds/json/PlayerPropsByWeek/{season}/{week}?key={SPORTSDATAIO_KEY}")
    if not isinstance(rows, list) or not rows:
        # then header or second route
        rows, _, _ = _json_get("api.sportsdata.io", f"/v3/nfl/odds/json/PlayerPropsByWeek/{season}/{week}",
                               headers={"Ocp-Apim-Subscription-Key": SPORTSDATAIO_KEY} if SPORTSDATAIO_KEY else None)
    if not isinstance(rows, list) or not rows:
        rows, _, _ = _json_get("api.sportsdata.io", f"/v3/nfl/odds/json/PlayerGamePropsByWeek/{season}/{week}?key={SPORTSDATAIO_KEY}")
    if not isinstance(rows, list) or not rows:
        rows, _, _ = _json_get("api.sportsdata.io", f"/v3/nfl/odds/json/PlayerGamePropsByWeek/{season}/{week}",
                               headers={"Ocp-Apim-Subscription-Key": SPORTSDATAIO_KEY} if SPORTSDATAIO_KEY else None)
    if not isinstance(rows, list): rows = []

    picks: List[Dict[str, Any]] = []
    for p in rows:
        try:
            player = p.get("Name") or p.get("PlayerName") or "Unknown"
            raw_market = p.get("BetName") or p.get("BetType") or p.get("StatType") or p.get("PlayerPropType") or "Prop"
            label, units = normalize_prop_label(str(raw_market))
            line = (
                safe_float(p.get("Value")) or safe_float(p.get("Line")) or
                safe_float(p.get("Points")) or safe_float(p.get("BetValue")) or
                safe_float(p.get("PlayerPropStat")) or safe_float(p.get("PlayerPropLine")) or
                safe_float(p.get("PropValue")) or
                extract_number(p.get("Description")) or extract_number(p.get("BetDescription"))
            )
            if line is None: continue
            op = american_to_prob(safe_float(p.get("OverPayout")))
            up = american_to_prob(safe_float(p.get("UnderPayout")))
            if op is not None and up is not None:
                of, uf = deflate_vig(op, up)
                conf = max(of or 0.5, uf or 0.5)
                side = "Over" if (of or 0.5) >= (uf or 0.5) else "Under"
            else:
                conf = 0.625
                side = "Over"
            team = p.get("Team") or p.get("HomeTeam")
            opp  = p.get("Opponent") or p.get("AwayTeam")
            picks.append({
                "player": player, "prop_type": label, "units": units,
                "line": float(line), "pick": side, "confidence": round(conf, 3),
                "bookmaker": "SportsDataIO",
                "team": team, "opponent": opp
            })
        except Exception:
            continue
    return picks

def build_top_props_for_week(week: int) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    diag: Dict[str, Any] = {}
    picks: List[Dict[str, Any]] = []

    raw = fetch_player_props_raw_oddsapi()
    diag["oddsapi_props_present"] = bool(raw) and isinstance(raw, list)
    if raw:
        start, end = week_window_utc(week)
        for ev in raw:
            ct = parse_commence_utc(ev.get("commence_time"))
            if ct and not (start <= ct < end): continue
            matchup = f"{ev.get('away_team')} @ {ev.get('home_team')}" if ev.get("away_team") and ev.get("home_team") else None
            for bm in (ev.get("bookmakers") or []):
                for mk in (bm.get("markets") or []):
                    outs = mk.get("outcomes") or []
                    over = next((o for o in outs if (o.get("name") or "").lower()=="over"), None)
                    under= next((o for o in outs if (o.get("name") or "").lower()=="under"), None)
                    line = safe_float((over or under or {}).get("point"))
                    if line is None: continue
                    op = american_to_prob(safe_float((over or {}).get("price")))
                    up = american_to_prob(safe_float((under or {}).get("price")))
                    of, uf = deflate_vig(op or 0.5, up or 0.5)
                    side   = "Over" if (of or 0.5) >= (uf or 0.5) else "Under"
                    conf   = max(of or 0.5, uf or 0.5)
                    raw_key = mk.get("key") or mk.get("market") or "Prop"
                    label, units = normalize_prop_label(str(raw_key))
                    player = mk.get("player") or mk.get("player_name") or "Unknown"
                    picks.append({
                        "player": str(player), "prop_type": label, "units": units,
                        "line": float(line), "pick": side, "confidence": round(conf, 3),
                        "bookmaker": bm.get("title") or bm.get("key") or "OddsAPI",
                        "matchup": matchup
                    })

    if not picks:
        sdio = fetch_sportsdataio_props("2025REG", week)
        picks = sdio

    # dedupe keep highest confidence
    best: Dict[Tuple[str,str], Dict[str,Any]] = {}
    for p in picks:
        k = (p["player"], p["prop_type"])
        if k not in best or p["confidence"] > best[k]["confidence"]:
            best[k] = p
    top = list(best.values())
    top.sort(key=lambda x: x["confidence"], reverse=True)
    diag["final_count"] = len(top)
    return top[:5], diag

# ---------- fallback game ----------
def mock_games() -> List[Dict[str, Any]]:
    ct = datetime(2025,9,5,0,21,0, tzinfo=timezone.utc).isoformat()
    return [{
        "home_team":"BUF","away_team":"NYJ","commence_time": ct,
        "h2h_home":-120,"h2h_away":110,
        "spread":-3.5,"spread_team":"BUF","total":45.5,"over_odds":-110,"under_odds":-110
    }]

# ---------- build sections ----------
def build_su_ats_totals(games: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not games: games = mock_games()  # resilience
    su_rows, ats_rows, tot_rows = [], [], []
    seen = set()
    for g in games:
        home, away = g.get("home_team"), g.get("away_team")
        key = (home or "", away or "")
        if key in seen: continue
        seen.add(key)
        matchup = f"{away} @ {home}"
        # SU
        p_home = american_to_prob(g.get("h2h_home"))
        p_away = american_to_prob(g.get("h2h_away"))
        if p_home is None and p_away is not None: p_home = 1 - p_away
        if p_away is None and p_home is not None: p_away = 1 - p_home
        ph_fair, pa_fair = deflate_vig(p_home, p_away)
        if ph_fair is None or pa_fair is None: ph_fair, pa_fair = 0.5, 0.5
        su_rows.append({"home": home,"away": away,"matchup": matchup,
                        "su_pick": home if ph_fair >= pa_fair else away,
                        "su_confidence": round(max(ph_fair, pa_fair), 4)})
        # ATS
        fav, spread = g.get("spread_team"), g.get("spread")
        if fav is not None and spread is not None:
            fav_prob = ph_fair if fav == home else pa_fair
            sign_char = "-" if spread < 0 else "+"
            ats_rows.append({"matchup": matchup,"ats_pick": f"{fav} {sign_char}{abs(spread)}",
                             "spread": float(spread),
                             "ats_confidence": round(max(0.50, min(0.75, 0.46 + 0.5*abs((fav_prob or 0.5) - 0.5))), 4)})
        # Totals
        total_line = g.get("total"); op = american_to_prob(g.get("over_odds")); up = american_to_prob(g.get("under_odds"))
        if total_line is not None:
            if op is not None and up is not None:
                of, uf = deflate_vig(op, up); pick_over = (of or 0.5) >= (uf or 0.5); conf = max(of or 0.5, uf or 0.5)
            else:
                pick_over = True; conf = 0.55
            tot_rows.append({"matchup": matchup,"tot_pick": f"{'Over' if pick_over else 'Under'} {float(total_line)}",
                             "total_line": float(total_line),"tot_confidence": round(conf, 4)})

    return {"top5_su": rank_top_n(su_rows, "su_confidence", 5),
            "top5_ats": rank_top_n(ats_rows, "ats_confidence", 5),
            "top5_totals": rank_top_n(tot_rows, "tot_confidence", 5)}

# ---------- core ----------
def get_live_payload_for_week(week: int) -> Dict[str, Any]:
    snap = fetch_market_snap() or []
    start, end = week_window_utc(week)
    filtered: List[Dict[str, Any]] = []
    for g in snap:
        ct = parse_commence_utc(g.get("commence_time"))
        if ct is None or (start <= ct < end): filtered.append(g)
    core  = build_su_ats_totals(filtered if filtered else snap)
    props, _ = build_top_props_for_week(week)
    return {**core, "top5_props": props,
            "top5_fantasy": [
                {"player":"Ja'Marr Chase","position":"WR","salary":8800,"value_score":3.45},
                {"player":"Bijan Robinson","position":"RB","salary":7800,"value_score":3.22},
                {"player":"Travis Etienne","position":"RB","salary":6900,"value_score":3.10},
                {"player":"Davante Adams","position":"WR","salary":8400,"value_score":2.98},
                {"player":"Dalton Kincaid","position":"TE","salary":5200,"value_score":2.86},
            ]}

# ---------- debug & routes ----------
@app.get("/")
def root(): return {"ok": True, "version": APP_VERSION}

@app.get("/v1/health")
def health():
    qs = urlencode({"regions": ODDS_REGION or "us", "markets":"h2h", "oddsFormat":"american", "apiKey": ODDS_API_KEY})
    data, err, st = _json_get("api.the-odds-api.com", f"/v4/sports/{ODDS_SPORT}/odds?{qs}")
    sample = len(data[:1]) if isinstance(data, list) else 0
    return {"ok": True, "version": APP_VERSION,
            "odds_api_key_set": bool(ODDS_API_KEY),
            "status": st, "err": err, "sample_items": sample}

@app.get("/v1/debug/providers")
def debug_providers(week: int = Query(1, ge=1, le=18)):
    broader = f"{ODDS_REGION or 'us'},uk,eu,au"
    odds_qs = urlencode({"regions": broader, "oddsFormat":"american","apiKey": ODDS_API_KEY, "markets": PROP_MARKETS})
    odds_data, odds_err, odds_st = _json_get("api.the-odds-api.com", f"/v4/sports/{ODDS_SPORT}/odds?{odds_qs}")
    odds_count = len(odds_data) if isinstance(odds_data, list) else 0

    diag = {}
    for route in [
        f"/v3/nfl/odds/json/PlayerPropsByWeek/2025REG/{week}",
        f"/v3/nfl/odds/json/PlayerGamePropsByWeek/2025REG/{week}",
    ]:
        qd, qe, qs_ = _json_get("api.sportsdata.io", f"{route}?key={SPORTSDATAIO_KEY}")
        hd, he, hs_ = _json_get("api.sportsdata.io", route,
                                headers={"Ocp-Apim-Subscription-Key": SPORTSDATAIO_KEY} if SPORTSDATAIO_KEY else None)
        diag[route] = {
            "query":  {"status": qs_, "err": qe, "count": (len(qd) if isinstance(qd, list) else 0), "sample": (qd[:1] if isinstance(qd, list) else qd)},
            "header": {"status": hs_, "err": he, "count": (len(hd) if isinstance(hd, list) else 0), "sample": (hd[:1] if isinstance(hd, list) else hd)},
        }

    return {"week": week, "oddsapi": {"status": odds_st, "err": odds_err, "count": odds_count},
            "sportsdataio": diag}

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
