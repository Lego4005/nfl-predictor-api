# 🏈 NFL 2025 Predictor API

A FastAPI-powered backend for delivering weekly NFL predictions against the spread, straight-up, totals, player props, and fantasy value picks — optimized for betting and DFS insights.

## 🔧 Features

- Predictive engine returns:
  - Top 5 Straight-Up winners
  - Top 5 Against the Spread (ATS) picks
  - Top 5 Over/Under Totals
  - Top 5 Prop Bets by player
  - Top 5 Fantasy Value picks (DFS)
- Download results in: JSON, CSV, PDF
- Built for the 2025 NFL season

## 🚀 Installation

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

## 📡 API Endpoints

### Get Predictions
`GET /v1/best-picks/2025/{week}`

### Download Predictions
`GET /v1/best-picks/2025/{week}/download?format=json|csv|pdf`

## 🛠 Deployment Options
- Render.com
- Railway.app
- Replit
