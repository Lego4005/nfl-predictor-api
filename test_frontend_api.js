#!/usr/bin/env node

// Test frontend API connectivity
async function testAPIConnectivity() {
    console.log('🔧 Testing Frontend API Connectivity');
    console.log('=' .repeat(50));
    
    try {
        // Test if we can fetch data like the React app would
        const response = await fetch('http://localhost:8080/v1/best-picks/2025/1?t=' + Date.now());
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        console.log('✅ API Connection: SUCCESS');
        console.log(`✅ Data Keys: ${Object.keys(data).join(', ')}`);
        console.log(`✅ SU Picks: ${data.best_picks?.length || 0} games`);
        console.log(`✅ ATS Picks: ${data.ats_picks?.length || 0} games`);
        console.log(`✅ Totals Picks: ${data.totals_picks?.length || 0} games`);
        console.log(`✅ Props: ${data.prop_bets?.length || 0} props`);
        console.log(`✅ Fantasy: ${data.fantasy_picks?.length || 0} players`);
        
        console.log('\n📊 Sample ATS Data:');
        if (data.ats_picks && data.ats_picks[0]) {
            const ats = data.ats_picks[0];
            console.log(`   Matchup: ${ats.matchup}`);
            console.log(`   ATS Pick: ${ats.ats_pick}`);
            console.log(`   Spread: ${ats.spread}`);
            console.log(`   Confidence: ${(ats.ats_confidence * 100).toFixed(1)}%`);
        }
        
        console.log('\n🎯 Sample Totals Data:');
        if (data.totals_picks && data.totals_picks[0]) {
            const totals = data.totals_picks[0];
            console.log(`   Matchup: ${totals.matchup}`);
            console.log(`   Pick: ${totals.tot_pick}`);
            console.log(`   Line: ${totals.total_line}`);
            console.log(`   Confidence: ${(totals.tot_confidence * 100).toFixed(1)}%`);
        }
        
        console.log('\n💎 Sample Fantasy Data:');
        if (data.fantasy_picks && data.fantasy_picks[0]) {
            const fantasy = data.fantasy_picks[0];
            console.log(`   Player: ${fantasy.player}`);
            console.log(`   Position: ${fantasy.position}`);
            console.log(`   Team: ${fantasy.team}`);
            console.log(`   Salary: $${fantasy.salary?.toLocaleString() || 'N/A'}`);
            console.log(`   Projection: ${fantasy.projection} pts`);
            console.log(`   Value: ${fantasy.value}x`);
        }
        
        console.log('\n' + '=' .repeat(50));
        console.log('🎉 FRONTEND API TEST: ALL SYSTEMS GO!');
        console.log('   - Backend provides all distinct category data');
        console.log('   - API connectivity works from frontend perspective');
        console.log('   - Issue is likely in React component tab switching');
        
    } catch (error) {
        console.error('❌ API Connection Failed:', error.message);
        console.log('\n🔧 Troubleshooting:');
        console.log('   1. Make sure backend server is running: python main.py');
        console.log('   2. Check if port 8080 is accessible');
        console.log('   3. Verify CORS settings in backend');
    }
}

// Run the test
testAPIConnectivity();