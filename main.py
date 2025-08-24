from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="NFL Predictor API - SMOKE", version="0.0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

@app.get("/")
def root():
    return {"ok": True, "app": "NFL Predictor API - SMOKE"}

@app.get("/ping")
def ping():
    return {"ok": True}

@app.get("/v1/health")
def health():
    return {"ok": True, "version": "0.0.1", "routes": ["/", "/ping", "/v1/health", "/v1/best-picks/2025/{week}", "/v1/lineup/2025/{week}"]}

@app.get("/v1/best-picks/2025/{week}")
def best_picks(week: int):
    return {
        "top5_su": [{"home":"BUF","away":"NYJ","su_pick":"BUF","su_confidence":0.78}],
        "top5_ats": [{"ats_pick":"DET -3.5","ats_confidence":0.70}],
        "top5_totals": [{"tot_pick":"Over 45.5","tot_confidence":0.66}],
        "top5_props": [{"player":"Josh Allen","prop_type":"Pass Yards","prediction":286,"confidence":0.72}],
        "top5_fantasy": [{"player":"Ja'Marr Chase","position":"WR","salary":8800,"value_score":3.45}]
    }

@app.get("/v1/lineup/2025/{week}")
def lineup(week: int):
    return {
        "week": week, "salary_cap": 50000, "total_salary": 49800, "projected_points": 162.4,
        "lineup": [{"position":"QB","player":"Jalen Hurts","team":"PHI","salary":7900,"proj_points":24.3}]
    }
