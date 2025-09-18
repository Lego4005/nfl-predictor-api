# Supabase NFL Schedule Setup Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Supabase Account Setup](#supabase-account-setup)
3. [Project Creation](#project-creation)
4. [Database Setup](#database-setup)
5. [Table Creation](#table-creation)
6. [Data Import](#data-import)
7. [API Configuration](#api-configuration)
8. [Security Setup](#security-setup)
9. [Testing the Setup](#testing-the-setup)
10. [Client Integration Examples](#client-integration-examples)
11. [Troubleshooting](#troubleshooting)

## Prerequisites

Before starting, ensure you have:
- A web browser
- Basic understanding of SQL
- The NFL schedule files generated earlier:
  - `nfl_schedule_schema.sql`
  - `nfl_schedule_data.sql`
  - `nfl_schedule_2025.json`

## Supabase Account Setup

### Step 1: Create a Supabase Account
1. Go to [https://supabase.com](https://supabase.com)
2. Click "Start your project" or "Sign Up"
3. Choose your preferred sign-up method:
   - GitHub (recommended for developers)
   - Google
   - Email/Password
4. Complete the registration process
5. Verify your email if required

### Step 2: Choose Your Plan
- **Free Tier**: Perfect for development and small projects
  - 2 projects
  - 500MB database space
  - 50MB file storage
  - 2GB bandwidth
- **Pro Tier**: For production applications ($25/month)
- **Team/Enterprise**: For larger organizations

## Project Creation

### Step 1: Create a New Project
1. From your Supabase dashboard, click "New Project"
2. Fill in the project details:
   - **Name**: `nfl-schedule-2025` (or your preferred name)
   - **Database Password**: Create a strong password (save this!)
   - **Region**: Choose the region closest to your users
   - **Pricing Plan**: Select your preferred plan
3. Click "Create new project"
4. Wait for the project to be provisioned (usually 1-2 minutes)

### Step 2: Access Your Project
1. Once created, you'll be redirected to your project dashboard
2. Note your project URL (format: `https://[project-id].supabase.co`)
3. Save your project reference ID for later use

## Database Setup

### Step 1: Access the SQL Editor
1. In your Supabase project dashboard, navigate to "SQL Editor" in the left sidebar
2. You'll see the SQL query interface

### Step 2: Create the NFL Games Table
1. In the SQL Editor, paste the contents of `nfl_schedule_schema.sql`:

```sql
CREATE TABLE nfl_games_2025 (
  game_id varchar(20) PRIMARY KEY,
  season integer,
  week integer,
  game_type varchar(10),
  game_date date,
  game_time time,
  game_datetime timestamp,
  day_of_week varchar(10),
  away_team varchar(3),
  away_team_name varchar(50),
  home_team varchar(3),
  home_team_name varchar(50),
  network varchar(20),
  stadium varchar(100),
  city varchar(50),
  state varchar(2),
  timezone varchar(3),
  is_primetime boolean,
  is_playoff boolean,
  is_international boolean,
  international_location varchar(50),
  kickoff_time_et time,
  kickoff_time_local time,
  created_at timestamp DEFAULT now(),
  updated_at timestamp DEFAULT now()
);

CREATE INDEX idx_season_week ON nfl_games_2025 (season, week);
CREATE INDEX idx_game_date ON nfl_games_2025 (game_date);
CREATE INDEX idx_teams ON nfl_games_2025 (away_team, home_team);
CREATE INDEX idx_network ON nfl_games_2025 (network);
```

2. Click "Run" to execute the SQL
3. You should see a success message

## Table Creation

### Step 1: Verify Table Creation
1. Navigate to "Table Editor" in the left sidebar
2. You should see the `nfl_games_2025` table listed
3. Click on the table to view its structure
4. Verify all columns are present and correctly typed

### Step 2: Configure Row Level Security (RLS)
1. In the Table Editor, click on your `nfl_games_2025` table
2. Click the "Settings" tab
3. Enable "Row Level Security" if you want to control access
4. For public read access, create a policy:

```sql
-- Allow public read access to NFL games
CREATE POLICY "Public read access" ON nfl_games_2025
FOR SELECT USING (true);
```

## Data Import

### Method 1: SQL Insert Statements
1. Return to the SQL Editor
2. Paste the contents of `nfl_schedule_data.sql`
3. Click "Run" to insert the data
4. Verify the data was inserted by running:

```sql
SELECT COUNT(*) FROM nfl_games_2025;
```

### Method 2: CSV Import (Alternative)
1. Convert the JSON data to CSV format if needed
2. In Table Editor, click on `nfl_games_2025`
3. Click "Insert" → "Import data from CSV"
4. Upload your CSV file
5. Map the columns correctly
6. Click "Import"

### Method 3: JSON Import via API (Advanced)
Use the Supabase JavaScript client to import from the JSON file:

```javascript
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'YOUR_SUPABASE_URL'
const supabaseKey = 'YOUR_SUPABASE_ANON_KEY'
const supabase = createClient(supabaseUrl, supabaseKey)

// Import games from JSON
const { data, error } = await supabase
  .from('nfl_games_2025')
  .insert(gamesArray)
```

## API Configuration

### Step 1: Get Your API Keys
1. Navigate to "Settings" → "API" in your project
2. Copy the following values:
   - **Project URL**: `https://[project-id].supabase.co`
   - **Anon/Public Key**: For client-side access
   - **Service Role Key**: For server-side access (keep secret!)

### Step 2: Configure API Access
1. In "Settings" → "API", review the auto-generated API documentation
2. Your NFL games table will be automatically available at:
   - `GET /rest/v1/nfl_games_2025` - Get all games
   - `GET /rest/v1/nfl_games_2025?week=eq.1` - Get Week 1 games
   - `GET /rest/v1/nfl_games_2025?away_team=eq.DAL` - Get Dallas Cowboys away games

## Security Setup

### Step 1: Configure Authentication (Optional)
If you want to restrict access:
1. Navigate to "Authentication" in the sidebar
2. Configure your preferred authentication providers
3. Set up user roles and permissions

### Step 2: Set Up Row Level Security Policies
For public read-only access:

```sql
-- Enable RLS
ALTER TABLE nfl_games_2025 ENABLE ROW LEVEL SECURITY;

-- Allow public read access
CREATE POLICY "Public read access" ON nfl_games_2025
FOR SELECT USING (true);

-- Restrict write access to authenticated users only
CREATE POLICY "Authenticated write access" ON nfl_games_2025
FOR ALL USING (auth.role() = 'authenticated');
```

### Step 3: Configure CORS (if needed)
1. Go to "Settings" → "API"
2. Configure CORS settings for your domain
3. Add your website domains to the allowed origins

## Testing the Setup

### Step 1: Test via Supabase Dashboard
1. Go to "Table Editor"
2. Click on `nfl_games_2025`
3. Verify you can see all the imported data
4. Try filtering by week: `week = 1`
5. Try sorting by game_date

### Step 2: Test via API
Use curl to test your API:

```bash
# Get all games
curl "https://[your-project-id].supabase.co/rest/v1/nfl_games_2025" \
  -H "apikey: [your-anon-key]" \
  -H "Authorization: Bearer [your-anon-key]"

# Get Week 1 games
curl "https://[your-project-id].supabase.co/rest/v1/nfl_games_2025?week=eq.1" \
  -H "apikey: [your-anon-key]" \
  -H "Authorization: Bearer [your-anon-key]"

# Get games by team
curl "https://[your-project-id].supabase.co/rest/v1/nfl_games_2025?away_team=eq.DAL" \
  -H "apikey: [your-anon-key]" \
  -H "Authorization: Bearer [your-anon-key]"
```

### Step 3: Test Common Queries
Try these SQL queries in the SQL Editor:

```sql
-- Get all Week 1 games
SELECT * FROM nfl_games_2025 WHERE week = 1 ORDER BY game_datetime;

-- Get all primetime games
SELECT * FROM nfl_games_2025 WHERE is_primetime = true ORDER BY game_datetime;

-- Get games by network
SELECT * FROM nfl_games_2025 WHERE network = 'NBC' ORDER BY game_datetime;

-- Get international games
SELECT * FROM nfl_games_2025 WHERE is_international = true;

-- Get games for a specific team
SELECT * FROM nfl_games_2025 
WHERE away_team = 'DAL' OR home_team = 'DAL' 
ORDER BY game_datetime;
```

## Client Integration Examples

### JavaScript/TypeScript (Web)
```javascript
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://your-project-id.supabase.co'
const supabaseKey = 'your-anon-key'
const supabase = createClient(supabaseUrl, supabaseKey)

// Get all games for Week 1
async function getWeek1Games() {
  const { data, error } = await supabase
    .from('nfl_games_2025')
    .select('*')
    .eq('week', 1)
    .order('game_datetime')
  
  if (error) console.error('Error:', error)
  return data
}

// Get games for a specific team
async function getTeamGames(teamCode) {
  const { data, error } = await supabase
    .from('nfl_games_2025')
    .select('*')
    .or(`away_team.eq.${teamCode},home_team.eq.${teamCode}`)
    .order('game_datetime')
  
  if (error) console.error('Error:', error)
  return data
}

// Get today's games
async function getTodaysGames() {
  const today = new Date().toISOString().split('T')[0]
  const { data, error } = await supabase
    .from('nfl_games_2025')
    .select('*')
    .eq('game_date', today)
    .order('game_time')
  
  if (error) console.error('Error:', error)
  return data
}
```

### Python
```python
import os
from supabase import create_client, Client

url: str = "https://your-project-id.supabase.co"
key: str = "your-anon-key"
supabase: Client = create_client(url, key)

# Get all games for Week 1
def get_week1_games():
    response = supabase.table('nfl_games_2025').select("*").eq('week', 1).order('game_datetime').execute()
    return response.data

# Get games for a specific team
def get_team_games(team_code):
    response = supabase.table('nfl_games_2025').select("*").or_(f"away_team.eq.{team_code},home_team.eq.{team_code}").order('game_datetime').execute()
    return response.data

# Get primetime games
def get_primetime_games():
    response = supabase.table('nfl_games_2025').select("*").eq('is_primetime', True).order('game_datetime').execute()
    return response.data
```

### React Component Example
```jsx
import React, { useState, useEffect } from 'react';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient('your-url', 'your-key');

function NFLSchedule() {
  const [games, setGames] = useState([]);
  const [selectedWeek, setSelectedWeek] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchGames();
  }, [selectedWeek]);

  async function fetchGames() {
    setLoading(true);
    const { data, error } = await supabase
      .from('nfl_games_2025')
      .select('*')
      .eq('week', selectedWeek)
      .order('game_datetime');
    
    if (error) {
      console.error('Error fetching games:', error);
    } else {
      setGames(data);
    }
    setLoading(false);
  }

  return (
    <div>
      <h1>NFL Schedule 2025</h1>
      <select 
        value={selectedWeek} 
        onChange={(e) => setSelectedWeek(e.target.value)}
      >
        {[...Array(18)].map((_, i) => (
          <option key={i + 1} value={i + 1}>Week {i + 1}</option>
        ))}
      </select>
      
      {loading ? (
        <p>Loading...</p>
      ) : (
        <div>
          {games.map(game => (
            <div key={game.game_id} className="game-card">
              <h3>{game.away_team_name} @ {game.home_team_name}</h3>
              <p>Date: {game.game_date}</p>
              <p>Time: {game.kickoff_time_et} ET</p>
              <p>Network: {game.network}</p>
              <p>Stadium: {game.stadium}, {game.city}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default NFLSchedule;
```

## Troubleshooting

### Common Issues and Solutions

#### 1. "relation does not exist" Error
- **Cause**: Table wasn't created properly
- **Solution**: Re-run the table creation SQL in the SQL Editor

#### 2. "permission denied" Error
- **Cause**: Row Level Security is enabled but no policies exist
- **Solution**: Create appropriate RLS policies or disable RLS for testing

#### 3. API Returns Empty Results
- **Cause**: Incorrect API key or URL
- **Solution**: Verify your project URL and API keys in Settings → API

#### 4. CORS Errors in Browser
- **Cause**: Domain not whitelisted
- **Solution**: Add your domain to CORS settings in Settings → API

#### 5. Data Import Fails
- **Cause**: Data type mismatches or constraint violations
- **Solution**: Check the error message and verify data formats

### Performance Optimization

#### 1. Add Additional Indexes
```sql
-- Index for date range queries
CREATE INDEX idx_game_date_range ON nfl_games_2025 (game_date, game_time);

-- Index for team schedule queries
CREATE INDEX idx_team_schedule ON nfl_games_2025 (away_team, home_team, game_date);

-- Index for network programming
CREATE INDEX idx_network_schedule ON nfl_games_2025 (network, game_date, game_time);
```

#### 2. Use Specific Selects
Instead of `SELECT *`, specify only needed columns:
```sql
SELECT game_id, away_team_name, home_team_name, game_datetime, network 
FROM nfl_games_2025 
WHERE week = 1;
```

#### 3. Implement Caching
For frequently accessed data, implement client-side caching or use Supabase's built-in caching features.

### Backup and Maintenance

#### 1. Regular Backups
- Supabase automatically backs up your database
- For additional security, export your data regularly:
```sql
-- Export all data
SELECT * FROM nfl_games_2025;
```

#### 2. Monitor Usage
- Check your project's usage in the Supabase dashboard
- Monitor API calls and database size
- Upgrade your plan if needed

#### 3. Update Data
To add new games or update existing ones:
```sql
-- Add a new game
INSERT INTO nfl_games_2025 (game_id, season, week, ...) VALUES (...);

-- Update game information
UPDATE nfl_games_2025 
SET kickoff_time_et = '20:30:00' 
WHERE game_id = '2025090401';
```

## Next Steps

1. **Expand the Schema**: Add tables for teams, players, statistics
2. **Real-time Updates**: Implement real-time score updates
3. **Advanced Queries**: Create views for complex analytics
4. **Mobile App**: Build a mobile app using the API
5. **Webhooks**: Set up webhooks for real-time notifications

## Support Resources

- [Supabase Documentation](https://supabase.com/docs)
- [Supabase Discord Community](https://discord.supabase.com/)
- [Supabase GitHub](https://github.com/supabase/supabase)
- [API Reference](https://supabase.com/docs/reference/javascript/introduction)

This setup provides a robust foundation for any NFL schedule application with real-time capabilities, secure access, and scalable architecture.

