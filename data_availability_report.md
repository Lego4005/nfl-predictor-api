# Sports Data API Test Results
Generated: 2025-09-29T20:41:38.445287

## 🔑 API Authentication Status

### SportsData.io
- **Status**: ✅ Authenticated
- **API Key**: Present

### The Odds API
- **Status**: ✅ Authenticated
- **API Key**: Present
- **Requests Remaining**: 492

---

## 📊 Data Availability by Category

### Summary
- ✅ **Fully Available**: 15 predictions
- ⚠️ **Partially Available**: 28 predictions
- ❌ **Not Available**: 0 predictions

---

### Outcome

| Status | Prediction | Data Sources | Notes |
|--------|-----------|--------------|-------|
| ✅ | Game Winner | SportsData.io (scores)<br>The Odds API (moneyline) | Historical data available for training |
| ✅ | Point Spread | The Odds API | Live odds available |
| ✅ | Total Points (Over/Under) | SportsData.io (scores)<br>The Odds API (totals) | Historical + live odds |
| ✅ | Victory Margin | SportsData.io (scores)<br>The Odds API (moneyline) | Historical data available for training |
| ✅ | Moneyline | The Odds API | Live odds available |

### Quarter

| Status | Prediction | Data Sources | Notes |
|--------|-----------|--------------|-------|
| ⚠️ | Q1 Winner | SportsData.io (scores - need quarter breakdown) | Need to verify quarter-by-quarter data availability |
| ⚠️ | Q1 Total Points | SportsData.io (scores - need quarter breakdown) | Need to verify quarter-by-quarter data availability |
| ⚠️ | Q2 Winner | SportsData.io (scores - need quarter breakdown) | Need to verify quarter-by-quarter data availability |
| ⚠️ | Q2 Total Points | SportsData.io (scores - need quarter breakdown) | Need to verify quarter-by-quarter data availability |
| ⚠️ | First Half Winner | SportsData.io (scores - need quarter breakdown) | Need to verify quarter-by-quarter data availability |
| ⚠️ | First Half Total | SportsData.io (scores - need quarter breakdown) | Need to verify quarter-by-quarter data availability |
| ⚠️ | Q3 Winner | SportsData.io (scores - need quarter breakdown) | Need to verify quarter-by-quarter data availability |
| ⚠️ | Q4 Winner | SportsData.io (scores - need quarter breakdown) | Need to verify quarter-by-quarter data availability |

### Team Performance

| Status | Prediction | Data Sources | Notes |
|--------|-----------|--------------|-------|
| ✅ | Team Touchdowns | SportsData.io (team stats) | Season and game-level stats available |
| ✅ | Team Field Goals | SportsData.io (team stats) | Season and game-level stats available |
| ✅ | Team Turnovers | SportsData.io (team stats) | Season and game-level stats available |
| ✅ | Team Penalties | SportsData.io (team stats) | Season and game-level stats available |
| ✅ | Team Rushing Yards | SportsData.io (team stats) | Season and game-level stats available |
| ✅ | Team Passing Yards | SportsData.io (team stats) | Season and game-level stats available |
| ✅ | Team Total Yards | SportsData.io (team stats) | Season and game-level stats available |
| ✅ | Team First Downs | SportsData.io (team stats) | Season and game-level stats available |
| ✅ | Team 3rd Down % | SportsData.io (team stats) | Season and game-level stats available |
| ✅ | Time of Possession | SportsData.io (team stats) | Season and game-level stats available |

### Player Props

| Status | Prediction | Data Sources | Notes |
|--------|-----------|--------------|-------|
| ⚠️ | QB Passing Yards | SportsData.io (historical) | Historical available, live props limited |
| ⚠️ | QB Passing TDs | SportsData.io (historical) | Historical available, live props limited |
| ⚠️ | QB Interceptions | SportsData.io (historical) | Historical available, live props limited |
| ⚠️ | RB Rushing Yards | SportsData.io (historical) | Historical available, live props limited |
| ⚠️ | RB Rushing TDs | SportsData.io (historical) | Historical available, live props limited |
| ⚠️ | WR Receiving Yards | SportsData.io (historical) | Historical available, live props limited |
| ⚠️ | WR Receptions | SportsData.io (historical) | Historical available, live props limited |
| ⚠️ | WR Receiving TDs | SportsData.io (historical) | Historical available, live props limited |
| ⚠️ | TE Receiving Yards | SportsData.io (historical) | Historical available, live props limited |
| ⚠️ | Kicker Field Goals Made | SportsData.io (historical) | Historical available, live props limited |
| ⚠️ | Defensive Sacks | SportsData.io (historical) | Historical available, live props limited |
| ⚠️ | Defensive Interceptions | SportsData.io (historical) | Historical available, live props limited |

### Special

| Status | Prediction | Data Sources | Notes |
|--------|-----------|--------------|-------|
| ⚠️ | First Score Type | SportsData.io (play-by-play may be needed) | Requires detailed play-by-play data - needs verification |
| ⚠️ | Longest Touchdown | SportsData.io (play-by-play may be needed) | Requires detailed play-by-play data - needs verification |
| ⚠️ | Safety Scored | SportsData.io (play-by-play may be needed) | Requires detailed play-by-play data - needs verification |
| ⚠️ | Game Goes to Overtime | SportsData.io (play-by-play may be needed) | Requires detailed play-by-play data - needs verification |
| ⚠️ | Successful 2-Point Conversion | SportsData.io (play-by-play may be needed) | Requires detailed play-by-play data - needs verification |
| ⚠️ | Punt Return TD | SportsData.io (play-by-play may be needed) | Requires detailed play-by-play data - needs verification |
| ⚠️ | Kick Return TD | SportsData.io (play-by-play may be needed) | Requires detailed play-by-play data - needs verification |
| ⚠️ | Defensive TD | SportsData.io (play-by-play may be needed) | Requires detailed play-by-play data - needs verification |

---

## ⚠️ Data Gaps & Missing Sources

No critical data gaps identified! ✅

---

## 💡 Recommendations

### Medium Priority
- **28 predictions** have partial data
- Verify data quality and completeness
- May need play-by-play or additional endpoints

### What's Working Well
- **15 predictions** are fully supported
- Focus initial development on these predictions
- Build baseline models with available data

---

## 📡 Available Endpoints

### SportsData.io
- Scores (Game results)
- Team Stats (Season)
- Team Stats (Game)
- Player Stats (Season)
- Player Stats (Game)
- Injuries
- Schedules
- Box Scores
- Play-by-Play
- Projected Stats
- Depth Charts
- Stadium Details
- Team Trends

### The Odds API
- h2h (Moneyline/Head-to-Head)
- spreads (Point Spreads)
- totals (Over/Under)
- h2h_lay (Lay Odds)
- outrights (Futures)
