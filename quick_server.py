from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])

@app.get('/v1/best-picks/2025/{week}')
def get_picks(week: int):
    return {
        'season': 2025,
        'week': str(week),
        'last_updated_utc': '2025-08-26T12:00:00Z',
        'games': [
            {
                'game_id': f'2025-W{week:02d}-BUF-NYJ',
                'kickoff_utc': '2025-09-07T17:00:00Z',
                'home': {'team': 'Bills', 'abbr': 'BUF', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/BUF.png'},
                'away': {'team': 'Jets', 'abbr': 'NYJ', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/NYJ.png'},
                'su': {'pick': 'HOME', 'confidence': 0.74},
                'ats': {'spread_team': 'HOME', 'spread': 3.5, 'pick': 'HOME', 'confidence': 0.69},
                'totals': {'line': 45.5, 'pick': 'OVER', 'confidence': 0.62}
            },
            {
                'game_id': f'2025-W{week:02d}-KC-LAC',
                'kickoff_utc': '2025-09-07T20:00:00Z',
                'home': {'team': 'Chiefs', 'abbr': 'KC', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/KC.png'},
                'away': {'team': 'Chargers', 'abbr': 'LAC', 'logo': 'https://a.espncdn.com/i/teamlogos/nfl/500/LAC.png'},
                'su': {'pick': 'HOME', 'confidence': 0.68},
                'ats': {'spread_team': 'HOME', 'spread': 6.5, 'pick': 'AWAY', 'confidence': 0.65},
                'totals': {'line': 52.5, 'pick': 'UNDER', 'confidence': 0.58}
            }
        ],
        'props': [
            {
                'prop_id': f'2025-W{week:02d}-BUF-NYJ-allen-passyds',
                'game_id': f'2025-W{week:02d}-BUF-NYJ',
                'player': 'Josh Allen',
                'team': 'BUF',
                'position': 'QB',
                'market': 'Passing Yards',
                'book': 'DraftKings',
                'line': 285.5,
                'pick': 'OVER',
                'confidence': 0.67
            }
        ],
        'fantasy': {
            'salary_cap': 50000,
            'lineup': [
                {
                    'player': 'Josh Allen',
                    'team': 'BUF',
                    'position': 'QB',
                    'salary': 8200,
                    'projected_points': 22.4,
                    'value': 2.73,
                    'game_id': f'2025-W{week:02d}-BUF-NYJ'
                }
            ],
            'alternates': []
        },
        'exports': {
            'csv': {
                'su': 'Home,Away,Su Pick,Su Confidence,Game Id,Kickoff',
                'ats': 'Matchup,ATS Pick,Spread,ATS Confidence,Game Id,Kickoff',
                'totals': 'Matchup,Pick,Line,Confidence,Game Id,Kickoff',
                'props': 'Player,Market,Pick,Line,Confidence,Book,Game,Game Id,Kickoff',
                'fantasy': 'Player,Position,Team,Salary,Projected Points,Value,Game Id'
            },
            'pdf_spec': {
                'title': f'NFL 2025 Predictions — Week {week}',
                'sections': ['Straight-Up','ATS','Totals','Props','Fantasy'],
                'footer': 'API: http://localhost:8002 • Generated {local_time}'
            }
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host='127.0.0.1', port=9000)