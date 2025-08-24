from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import random

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_mock_predictions(week: int):
    random.seed(week)

    teams = ["BUF", "NYJ", "KC", "CIN", "PHI", "SF", "DAL", "MIA", "DET", "BAL", "LAR", "SEA", "GB", "MIN", "NE", "TEN"]
    players = ["Josh Allen", "Patrick Mahomes", "Jalen Hurts", "Lamar Jackson", "Justin Jefferson", "Christian McCaffrey", "Tyreek Hill", "Joe Burrow", "Dak Prescott", "Aaron Rodgers"]
    positions = ["QB", "RB", "WR", "TE"]

    def random_team_pair():
        home = random.choice(teams)
        away = random.choice([t for t in teams if t != home])
        return home, away

    top5_su = []
    top5_ats = []
    top5_totals = []
    top5_props = []
    top5_fantasy = []

    for _ in range(5):
        home, away = random_team_pair()
        su_pick = random.choice([home, away])
        top5_su.append({
            "home": home,
            "away": away,
            "su_pick": su_pick,
            "su_confidence": round(random.uniform(0.65, 0.9), 2)
        })

        top5_ats.append({
            "ats_pick": random.choice(teams),
            "ats_confidence": round(random.uniform(0.65, 0.9), 2)
        })

        total_val = random.choice(["Over", "Under"]) + f" {random.randint(38, 55)}"
        top5_totals.append({
            "tot_pick": total_val,
            "tot_confidence": round(random.uniform(0.6, 0.85), 2)
        })

        player = random.choice(players)
        prop_type = random.choice(["Pass Yards", "Rush Yards", "Receiving TDs", "Rush TDs"])
        prediction = random.randint(50, 350)
        top5_props.append({
            "player": player,
            "prop_type": prop_type,
            "prediction": prediction,
            "confidence": round(random.uniform(0.6, 0.85), 2)
        })

        top5_fantasy.append({
            "player": player,
            "position": random.choice(positions),
            "salary": random.randint(6000, 10000),
            "value_score": round(random.uniform(2.5, 4.0), 2)
        })

    return {
        "top5_su": top5_su,
        "top5_ats": top5_ats,
        "top5_totals": top5_totals,
        "top5_props": top5_props,
        "top5_fantasy": top5_fantasy
    }

@app.get("/v1/best-picks/2025/{week}")
def best_picks(week: int):
    return get_mock_predictions(week)

