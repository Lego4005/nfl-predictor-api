# NFL Schedule API Quick Reference

## Base Configuration

```javascript
// JavaScript/TypeScript
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://your-project-id.supabase.co'
const supabaseKey = 'your-anon-key'
const supabase = createClient(supabaseUrl, supabaseKey)
```

```python
# Python
from supabase import create_client, Client

url = "https://your-project-id.supabase.co"
key = "your-anon-key"
supabase = create_client(url, key)
```

## Common API Endpoints

### REST API (Direct HTTP)
```bash
# Base URL
https://your-project-id.supabase.co/rest/v1/nfl_games_2025

# Headers (required for all requests)
apikey: your-anon-key
Authorization: Bearer your-anon-key
Content-Type: application/json
```

## Frequently Used Queries

### 1. Get All Games for a Specific Week
```javascript
// JavaScript
const { data } = await supabase
  .from('nfl_games_2025')
  .select('*')
  .eq('week', 1)
  .order('game_datetime')
```

```bash
# REST API
curl "https://your-project-id.supabase.co/rest/v1/nfl_games_2025?week=eq.1&order=game_datetime" \
  -H "apikey: your-anon-key" \
  -H "Authorization: Bearer your-anon-key"
```

### 2. Get Games for a Specific Team
```javascript
// JavaScript
const { data } = await supabase
  .from('nfl_games_2025')
  .select('*')
  .or(`away_team.eq.DAL,home_team.eq.DAL`)
  .order('game_datetime')
```

```bash
# REST API
curl "https://your-project-id.supabase.co/rest/v1/nfl_games_2025?or=(away_team.eq.DAL,home_team.eq.DAL)&order=game_datetime" \
  -H "apikey: your-anon-key" \
  -H "Authorization: Bearer your-anon-key"
```

### 3. Get Today's Games
```javascript
// JavaScript
const today = new Date().toISOString().split('T')[0]
const { data } = await supabase
  .from('nfl_games_2025')
  .select('*')
  .eq('game_date', today)
  .order('game_time')
```

### 4. Get Primetime Games
```javascript
// JavaScript
const { data } = await supabase
  .from('nfl_games_2025')
  .select('*')
  .eq('is_primetime', true)
  .order('game_datetime')
```

```bash
# REST API
curl "https://your-project-id.supabase.co/rest/v1/nfl_games_2025?is_primetime=eq.true&order=game_datetime" \
  -H "apikey: your-anon-key" \
  -H "Authorization: Bearer your-anon-key"
```

### 5. Get Games by Network
```javascript
// JavaScript
const { data } = await supabase
  .from('nfl_games_2025')
  .select('*')
  .eq('network', 'NBC')
  .order('game_datetime')
```

### 6. Get International Games
```javascript
// JavaScript
const { data } = await supabase
  .from('nfl_games_2025')
  .select('*')
  .eq('is_international', true)
  .order('game_datetime')
```

### 7. Get Games in Date Range
```javascript
// JavaScript
const { data } = await supabase
  .from('nfl_games_2025')
  .select('*')
  .gte('game_date', '2025-09-01')
  .lte('game_date', '2025-09-30')
  .order('game_datetime')
```

### 8. Get Specific Game Details
```javascript
// JavaScript
const { data } = await supabase
  .from('nfl_games_2025')
  .select('*')
  .eq('game_id', '2025090401')
  .single()
```

## Advanced Queries

### 1. Get Team's Home Games Only
```javascript
const { data } = await supabase
  .from('nfl_games_2025')
  .select('*')
  .eq('home_team', 'DAL')
  .order('game_datetime')
```

### 2. Get Weekend Games (Saturday/Sunday)
```javascript
const { data } = await supabase
  .from('nfl_games_2025')
  .select('*')
  .in('day_of_week', ['Saturday', 'Sunday'])
  .order('game_datetime')
```

### 3. Get Games with Specific Columns Only
```javascript
const { data } = await supabase
  .from('nfl_games_2025')
  .select('game_id, away_team_name, home_team_name, game_datetime, network')
  .eq('week', 1)
  .order('game_datetime')
```

### 4. Count Games by Network
```javascript
const { data } = await supabase
  .from('nfl_games_2025')
  .select('network', { count: 'exact' })
```

### 5. Get Games in Specific Timezone
```javascript
const { data } = await supabase
  .from('nfl_games_2025')
  .select('*')
  .eq('timezone', 'PT')
  .order('game_datetime')
```

## Filtering Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `eq` | Equals | `week=eq.1` |
| `neq` | Not equals | `week=neq.1` |
| `gt` | Greater than | `week=gt.5` |
| `gte` | Greater than or equal | `week=gte.5` |
| `lt` | Less than | `week=lt.10` |
| `lte` | Less than or equal | `week=lte.10` |
| `like` | Pattern matching | `away_team_name=like.*Cowboys*` |
| `ilike` | Case insensitive like | `city=ilike.*angeles*` |
| `in` | In list | `network=in.(NBC,CBS,FOX)` |
| `is` | Is null/not null | `state=is.null` |

## Response Format

All API responses return data in this format:
```json
{
  "game_id": "2025090401",
  "season": 2025,
  "week": 1,
  "game_type": "REG",
  "game_date": "2025-09-04",
  "game_time": "20:20:00",
  "game_datetime": "2025-09-04T20:20:00",
  "day_of_week": "Thursday",
  "away_team": "DAL",
  "away_team_name": "Dallas Cowboys",
  "home_team": "PHI",
  "home_team_name": "Philadelphia Eagles",
  "network": "NBC",
  "stadium": "Lincoln Financial Field",
  "city": "Philadelphia",
  "state": "PA",
  "timezone": "ET",
  "is_primetime": true,
  "is_playoff": false,
  "is_international": false,
  "international_location": null,
  "kickoff_time_et": "20:20:00",
  "kickoff_time_local": "20:20:00",
  "created_at": "2025-09-17T04:00:00.000Z",
  "updated_at": "2025-09-17T04:00:00.000Z"
}
```

## Error Handling

```javascript
// JavaScript
try {
  const { data, error } = await supabase
    .from('nfl_games_2025')
    .select('*')
    .eq('week', 1)
  
  if (error) {
    console.error('Supabase error:', error.message)
    return
  }
  
  // Process data
  console.log('Games:', data)
} catch (err) {
  console.error('Network error:', err)
}
```

## Rate Limits

- **Free Tier**: 500 requests per hour
- **Pro Tier**: 10,000 requests per hour
- **Team/Enterprise**: Custom limits

## Team Abbreviations Reference

| Team | Code | Full Name |
|------|------|-----------|
| Arizona Cardinals | ARI | Arizona Cardinals |
| Atlanta Falcons | ATL | Atlanta Falcons |
| Baltimore Ravens | BAL | Baltimore Ravens |
| Buffalo Bills | BUF | Buffalo Bills |
| Carolina Panthers | CAR | Carolina Panthers |
| Chicago Bears | CHI | Chicago Bears |
| Cincinnati Bengals | CIN | Cincinnati Bengals |
| Cleveland Browns | CLE | Cleveland Browns |
| Dallas Cowboys | DAL | Dallas Cowboys |
| Denver Broncos | DEN | Denver Broncos |
| Detroit Lions | DET | Detroit Lions |
| Green Bay Packers | GB | Green Bay Packers |
| Houston Texans | HOU | Houston Texans |
| Indianapolis Colts | IND | Indianapolis Colts |
| Jacksonville Jaguars | JAX | Jacksonville Jaguars |
| Kansas City Chiefs | KC | Kansas City Chiefs |
| Las Vegas Raiders | LV | Las Vegas Raiders |
| Los Angeles Chargers | LAC | Los Angeles Chargers |
| Los Angeles Rams | LAR | Los Angeles Rams |
| Miami Dolphins | MIA | Miami Dolphins |
| Minnesota Vikings | MIN | Minnesota Vikings |
| New England Patriots | NE | New England Patriots |
| New Orleans Saints | NO | New Orleans Saints |
| New York Giants | NYG | New York Giants |
| New York Jets | NYJ | New York Jets |
| Philadelphia Eagles | PHI | Philadelphia Eagles |
| Pittsburgh Steelers | PIT | Pittsburgh Steelers |
| San Francisco 49ers | SF | San Francisco 49ers |
| Seattle Seahawks | SEA | Seattle Seahawks |
| Tampa Bay Buccaneers | TB | Tampa Bay Buccaneers |
| Tennessee Titans | TEN | Tennessee Titans |
| Washington Commanders | WSH | Washington Commanders |

## Quick Copy-Paste Examples

### Get This Week's Games (JavaScript)
```javascript
const thisWeek = 2; // Change to current week
const { data: games } = await supabase
  .from('nfl_games_2025')
  .select('away_team_name, home_team_name, game_datetime, network')
  .eq('week', thisWeek)
  .order('game_datetime');
```

### Get Team Schedule (JavaScript)
```javascript
const team = 'DAL'; // Change to desired team
const { data: schedule } = await supabase
  .from('nfl_games_2025')
  .select('*')
  .or(`away_team.eq.${team},home_team.eq.${team}`)
  .order('game_datetime');
```

### Get Today's Games (REST API)
```bash
TODAY=$(date +%Y-%m-%d)
curl "https://your-project-id.supabase.co/rest/v1/nfl_games_2025?game_date=eq.$TODAY&order=game_time" \
  -H "apikey: your-anon-key" \
  -H "Authorization: Bearer your-anon-key"
```

