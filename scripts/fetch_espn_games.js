import fetch from 'node-fetch';
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.VITE_SUPABASE_URL || 'https://vaypgzvivahnfegnlinn.supabase.co';
const supabaseKey = process.env.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZheXBnenZpdmFobmZlZ25saW5uIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc4NzEzMjIsImV4cCI6MjA3MzQ0NzMyMn0.RISVGvci0v8GD1DtmnOD9lgJSYyfErDg1c__24K82ws';

const supabase = createClient(supabaseUrl, supabaseKey);

async function fetchAndStoreGames() {
  try {
    console.log('Fetching games from ESPN API...');
    const response = await fetch('https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard');
    const data = await response.json();

    if (!data.events || data.events.length === 0) {
      console.log('No games found in ESPN API');
      return;
    }

    console.log(`Found ${data.events.length} games from ESPN`);

    const games = data.events.map(event => {
      const competition = event.competitions[0];
      const homeTeam = competition.competitors.find(c => c.homeAway === 'home');
      const awayTeam = competition.competitors.find(c => c.homeAway === 'away');

      const statusType = competition.status?.type?.name;
      let status = 'scheduled';
      if (statusType === 'STATUS_IN_PROGRESS') status = 'live';
      else if (statusType === 'STATUS_FINAL') status = 'final';

      return {
        espn_game_id: event.id,
        home_team: homeTeam.team.abbreviation,
        away_team: awayTeam.team.abbreviation,
        home_score: parseInt(homeTeam.score) || 0,
        away_score: parseInt(awayTeam.score) || 0,
        game_time: event.date,
        week: data.week?.number || event.week?.number || 2,
        season: 2025,
        venue: competition.venue?.fullName || null,
        status: status,
        status_detail: competition.status?.type?.shortDetail || '',
        is_live: status === 'live',
        current_period: competition.status?.period || null,
        quarter: competition.status?.period || null,
        time_remaining: competition.status?.displayClock || null,
      };
    });

    // Upsert games to Supabase
    for (const game of games) {
      const { data: existing } = await supabase
        .from('games')
        .select('id')
        .eq('espn_game_id', game.espn_game_id)
        .single();

      if (existing) {
        // Update existing game
        const { error } = await supabase
          .from('games')
          .update(game)
          .eq('espn_game_id', game.espn_game_id);

        if (error) {
          console.error(`Error updating game ${game.home_team} vs ${game.away_team}:`, error);
        } else {
          console.log(`Updated: ${game.away_team} @ ${game.home_team} - ${game.status}`);
        }
      } else {
        // Insert new game
        const { error } = await supabase
          .from('games')
          .insert(game);

        if (error) {
          console.error(`Error inserting game ${game.home_team} vs ${game.away_team}:`, error);
        } else {
          console.log(`Inserted: ${game.away_team} @ ${game.home_team} - ${game.status}`);
        }
      }
    }

    console.log('✅ ESPN data sync complete!');

  } catch (error) {
    console.error('Error fetching ESPN data:', error);
  }
}

fetchAndStoreGames();