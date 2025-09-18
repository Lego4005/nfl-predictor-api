import axios from 'axios';
import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

const supabaseUrl = process.env.VITE_SUPABASE_URL;
const supabaseAnonKey = process.env.VITE_SUPABASE_ANON_KEY;
const ESPN_BASE_URL = process.env.VITE_ESPN_API_BASE || 'https://site.api.espn.com/apis/site/v2/sports/football/nfl';

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing Supabase environment variables');
}

const supabase = createClient(supabaseUrl, supabaseAnonKey);

async function syncGames() {
  console.log('🏈 Starting ESPN to Supabase sync...\n');

  try {
    // 1. Fetch from ESPN
    console.log('📡 Fetching from ESPN API...');
    const response = await axios.get(`${ESPN_BASE_URL}/scoreboard`);
    const events = response.data.events || [];
    console.log(`✅ Found ${events.length} games from ESPN\n`);

    // 2. Process and sync each game
    let synced = 0;
    const errors = [];

    for (const event of events) {
      try {
        const competition = event.competitions[0];
        const homeTeam = competition.competitors.find(c => c.homeAway === 'home');
        const awayTeam = competition.competitors.find(c => c.homeAway === 'away');

        const gameData = {
          espn_game_id: event.id,
          home_team: homeTeam.team.abbreviation,
          away_team: awayTeam.team.abbreviation,
          home_score: parseInt(homeTeam.score) || 0,
          away_score: parseInt(awayTeam.score) || 0,
          game_time: new Date(event.date).toISOString(),
          week: event.week?.number || null,
          season: event.season?.year || new Date().getFullYear(),
          season_type: event.season?.type?.name || 'regular',
          status: mapESPNStatus(event.status.type.name),
          quarter: competition.status?.period || null,
          time_remaining: competition.status?.displayClock || null,
          venue: competition.venue?.fullName || null,
          venue_city: competition.venue?.address?.city || null,
          venue_state: competition.venue?.address?.state || null,
        };

        // Upsert to Supabase
        const { error } = await supabase
          .from('games')
          .upsert(gameData, {
            onConflict: 'espn_game_id'
          });

        if (error) {
          errors.push({ gameId: event.id, error: error.message });
          console.log(`❌ Failed to sync ${awayTeam.team.abbreviation} @ ${homeTeam.team.abbreviation}: ${error.message}`);
        } else {
          synced++;
          console.log(`✅ Synced: ${awayTeam.team.abbreviation} @ ${homeTeam.team.abbreviation}`);
        }

      } catch (gameError) {
        errors.push({ gameId: event.id, error: gameError.message });
      }
    }

    // 3. Summary
    console.log('\n📊 Sync Summary:');
    console.log(`   Total games: ${events.length}`);
    console.log(`   Successfully synced: ${synced}`);
    console.log(`   Errors: ${errors.length}\n`);

    // 4. Check what's in the database
    console.log('🔍 Checking database...');
    const { data: dbGames, error: dbError } = await supabase
      .from('games')
      .select('*')
      .order('game_time', { ascending: true })
      .limit(10);

    if (dbError) {
      console.log('❌ Error reading from database:', dbError.message);
    } else {
      console.log(`✅ Database now has ${dbGames?.length || 0} games\n`);

      if (dbGames && dbGames.length > 0) {
        console.log('📅 Upcoming games:');
        dbGames.forEach(game => {
          const gameTime = new Date(game.game_time);
          console.log(`   ${game.away_team} @ ${game.home_team} - ${gameTime.toLocaleDateString()} ${gameTime.toLocaleTimeString()}`);
        });
      }
    }

  } catch (error) {
    console.error('❌ Sync failed:', error.message);
  }
}

function mapESPNStatus(espnStatus) {
  const statusMap = {
    'STATUS_SCHEDULED': 'scheduled',
    'STATUS_IN_PROGRESS': 'live',
    'STATUS_FINAL': 'final',
    'STATUS_POSTPONED': 'postponed',
    'STATUS_CANCELED': 'canceled',
    'STATUS_HALFTIME': 'live',
    'STATUS_END_PERIOD': 'live'
  };
  return statusMap[espnStatus] || 'scheduled';
}

// Run the sync
syncGames();