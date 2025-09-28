// NFL Model Projections Application
const appData = {
  "header": {
    "title": "NFL Model Projections",
    "week": "Week 4",
    "year": "2025"
  },
  "columns": [
    {
      "title": "Thursday, Sep 25",
      "subtitle": "",
      "evCount": 0,
      "games": [
        {
          "id": "sea-ari",
          "time": "06:19 PM",
          "status": "final",
          "away": {"code": "SEA", "record": "2-1", "logo": "🦅", "score": 23},
          "home": {"code": "ARI", "record": "2-1", "logo": "🔴", "score": 20},
          "lines": {
            "close": {"awaySpread": -1.5, "awayPrice": -108, "homeSpread": 1.5, "homePrice": -108},
            "model": {"awaySpread": -1.5, "awayProb": 54.5, "homeSpread": 1.5, "homeProb": 45.5}
          }
        }
      ]
    },
    {
      "title": "Sunday, Sep 28",
      "subtitle": "early",
      "evCount": 1,
      "games": [
        {
          "id": "min-pit",
          "time": "09:30 AM",
          "away": {"code": "MIN", "record": "2-1", "logo": "⚡"},
          "home": {"code": "PIT", "record": "2-1", "logo": "⚫"},
          "lines": {
            "open": {"awaySpread": -2.5, "awayPrice": -115, "homeSpread": 2.5, "homePrice": -105},
            "current": {"awaySpread": -2.5, "awayPrice": -115, "homeSpread": 2.5, "homePrice": -105},
            "model": {"awaySpread": -2.5, "awayProb": 54.5, "homeSpread": 2.5, "homeProb": 45.5}
          }
        },
        {
          "id": "no-buf",
          "time": "01:00 PM",
          "away": {"code": "NO", "record": "0-3", "logo": "⚜️"},
          "home": {"code": "BUF", "record": "3-0", "logo": "🦬"},
          "lines": {
            "open": {"awaySpread": 16.5, "awayPrice": -110, "homeSpread": -16.5, "homePrice": -110},
            "current": {"awaySpread": 14.5, "awayPrice": -112, "homeSpread": -14.5, "homePrice": -108},
            "model": {"awaySpread": 14.5, "awayProb": 15.5, "homeSpread": -14.5, "homeProb": 84.5}
          }
        },
        {
          "id": "cle-det",
          "time": "01:00 PM",
          "away": {"code": "CLE", "record": "1-2", "logo": "🟤"},
          "home": {"code": "DET", "record": "2-1", "logo": "🦁"},
          "lines": {
            "open": {"awaySpread": 8.5, "awayPrice": -110, "homeSpread": -8.5, "homePrice": 100},
            "current": {"awaySpread": 10.0, "awayPrice": -110, "homeSpread": -10.0, "homePrice": -110},
            "model": {"awaySpread": 11.0, "awayProb": 15.0, "homeSpread": -11.0, "homeProb": 85.0}
          }
        },
        {
          "id": "ten-hou",
          "time": "01:00 PM",
          "away": {"code": "TEN", "record": "0-3", "logo": "🔥"},
          "home": {"code": "HOU", "record": "0-3", "logo": "🐂"},
          "lines": {
            "open": {"awaySpread": 7.0, "awayPrice": -108, "homeSpread": -7.0, "homePrice": -115},
            "current": {"awaySpread": 7.0, "awayPrice": -105, "homeSpread": -7.0, "homePrice": -115},
            "model": {"awaySpread": 7.0, "awayProb": 24.1, "homeSpread": -7.0, "homeProb": 75.9}
          }
        },
        {
          "id": "car-ne",
          "time": "01:00 PM",
          "away": {"code": "CAR", "record": "1-2", "logo": "🐾"},
          "home": {"code": "NE", "record": "1-2", "logo": "🏈"},
          "lines": {
            "open": {"awaySpread": 5.5, "awayPrice": -110, "homeSpread": -5.5, "homePrice": -110},
            "current": {"awaySpread": 5.5, "awayPrice": -110, "homeSpread": -5.5, "homePrice": -110},
            "model": {"awaySpread": 5.0, "awayProb": 36.4, "homeSpread": -5.0, "homeProb": 63.6}
          }
        },
        {
          "id": "lac-nyg",
          "time": "01:00 PM",
          "away": {"code": "LAC", "record": "3-0", "logo": "⚡"},
          "home": {"code": "NYG", "record": "0-3", "logo": "🔵"},
          "lines": {
            "open": {"awaySpread": -6.0, "awayPrice": -110, "homeSpread": 6.0, "homePrice": -110},
            "current": {"awaySpread": -6.5, "awayPrice": -108, "homeSpread": 6.5, "homePrice": -108},
            "model": {"awaySpread": -6.5, "awayProb": 74.5, "homeSpread": 6.5, "homeProb": 25.5}
          }
        }
      ]
    },
    {
      "title": "Sunday, Sep 28",
      "subtitle": "late",
      "evCount": 1,
      "games": [
        {
          "id": "ind-lar",
          "time": "04:05 PM",
          "away": {"code": "IND", "record": "3-0", "logo": "🐎"},
          "home": {"code": "LAR", "record": "2-1", "logo": "🐏"},
          "lines": {
            "open": {"awaySpread": 3.5, "awayPrice": -110, "homeSpread": -3.5, "homePrice": -110},
            "current": {"awaySpread": 3.5, "awayPrice": -113, "homeSpread": -3.5, "homePrice": -107},
            "model": {"awaySpread": 3.5, "awayProb": 35.5, "homeSpread": -3.5, "homeProb": 64.5}
          }
        },
        {
          "id": "jax-sf",
          "time": "04:05 PM",
          "away": {"code": "JAX", "record": "2-1", "logo": "🐆"},
          "home": {"code": "SF", "record": "3-0", "logo": "⛰️"},
          "lines": {
            "open": {"awaySpread": 3.0, "awayPrice": -102, "homeSpread": -3.0, "homePrice": -118},
            "current": {"awaySpread": 3.5, "awayPrice": -117, "homeSpread": -3.5, "homePrice": -103},
            "model": {"awaySpread": 3.5, "awayProb": 35.5, "homeSpread": -3.5, "homeProb": 64.5}
          }
        },
        {
          "id": "bal-kc",
          "time": "04:25 PM",
          "away": {"code": "BAL", "record": "1-2", "logo": "🐦‍⬛"},
          "home": {"code": "KC", "record": "1-2", "logo": "🔴"},
          "lines": {
            "open": {"awaySpread": -2.5, "awayPrice": -110, "homeSpread": 2.5, "homePrice": -110},
            "current": {"awaySpread": -2.5, "awayPrice": -118, "homeSpread": 2.5, "homePrice": -104},
            "model": {"awaySpread": -2.5, "awayProb": 64.5, "homeSpread": 2.5, "homeProb": 35.5}
          }
        },
        {
          "id": "chi-oak",
          "time": "04:25 PM",
          "away": {"code": "CHI", "record": "1-2", "logo": "🐻"},
          "home": {"code": "OAK", "record": "1-2", "logo": "⚫"},
          "lines": {
            "open": {"awaySpread": -1.5, "awayPrice": 100, "homeSpread": 1.5, "homePrice": -120},
            "current": {"awaySpread": 1.5, "awayPrice": -110, "homeSpread": -1.5, "homePrice": -110},
            "model": {"awaySpread": 0.5, "awayProb": 46.9, "homeSpread": -0.5, "homeProb": 53.1}
          }
        },
        {
          "id": "gb-dal",
          "time": "08:20 PM",
          "away": {"code": "GB", "record": "2-1", "logo": "🧀"},
          "home": {"code": "DAL", "record": "1-2", "logo": "⭐"},
          "lines": {
            "open": {"awaySpread": -7.0, "awayPrice": -105, "homeSpread": 7.0, "homePrice": -115},
            "current": {"awaySpread": -7.0, "awayPrice": -110, "homeSpread": 7.0, "homePrice": -110},
            "model": {"awaySpread": -4.5, "awayProb": 62.0, "homeSpread": 4.5, "homeProb": 38.0}
          }
        }
      ]
    },
    {
      "title": "Monday, Sep 29",
      "subtitle": "",
      "evCount": 0,
      "games": [
        {
          "id": "nyj-mia",
          "time": "07:15 PM",
          "away": {"code": "NYJ", "record": "0-3", "logo": "✈️"},
          "home": {"code": "MIA", "record": "0-3", "logo": "🐬"},
          "lines": {
            "open": {"awaySpread": 2.5, "awayPrice": -102, "homeSpread": -2.5, "homePrice": -118},
            "current": {"awaySpread": 2.5, "awayPrice": -102, "homeSpread": -2.5, "homePrice": -120},
            "model": {"awaySpread": 2.5, "awayProb": 35.5, "homeSpread": -2.5, "homeProb": 64.5}
          }
        },
        {
          "id": "cin-den",
          "time": "08:15 PM",
          "away": {"code": "CIN", "record": "2-1", "logo": "🐅"},
          "home": {"code": "DEN", "record": "1-2", "logo": "🐴"},
          "lines": {
            "open": {"awaySpread": 7.0, "awayPrice": -108, "homeSpread": -7.0, "homePrice": -112},
            "current": {"awaySpread": 7.5, "awayPrice": -110, "homeSpread": -7.5, "homePrice": -110},
            "model": {"awaySpread": 7.5, "awayProb": 25.5, "homeSpread": -7.5, "homeProb": 74.5}
          }
        }
      ]
    }
  ]
};

// Utility Functions
function formatSpread(spread) {
  if (spread === 0) return "PK";
  return spread > 0 ? `+${spread}` : `${spread}`;
}

function formatPrice(price) {
  if (price === 100) return "+100";
  return price > 0 ? `+${price}` : `${price}`;
}

function formatPercentage(prob) {
  const percentage = prob * 100;
  if (percentage >= 50) {
    return `-${(percentage - 50).toFixed(1)}%`;
  } else {
    return `+${(50 - percentage).toFixed(1)}%`;
  }
}

// Create number cell for different line types
function createNumCell(spread, price, isModel = false, isPercentage = false) {
  const spreadText = formatSpread(spread);
  let priceText;
  
  if (isModel && isPercentage) {
    priceText = formatPercentage(price);
  } else {
    priceText = formatPrice(price);
  }
  
  const priceClass = isModel && isPercentage ? 
    (price > 0.5 ? 'negative' : 'positive') : '';
  
  return `
    <div class="num-cell">
      <div class="num-line">${spreadText}</div>
      <div class="num-price ${priceClass}">${priceText}</div>
    </div>
  `;
}

// Create game card for regular games
function createGameCard(game) {
  const isFinal = game.status === 'final';
  const cardClass = isFinal ? 'game-card final-game' : 'game-card';
  
  let headers, awayNumbers, homeNumbers;
  
  if (isFinal) {
    // Final game - show Score, Close, Model
    headers = `
      <div class="game-headers">
        <span></span>
        <span>Score</span>
        <span>Close</span>
        <span>Model</span>
      </div>
    `;
    
    awayNumbers = `
      <div class="team-score">${game.away.score}</div>
      ${createNumCell(game.lines.close.awaySpread, game.lines.close.awayPrice)}
      ${createNumCell(game.lines.model.awaySpread, game.lines.model.awayProb, true, true)}
    `;
    
    homeNumbers = `
      <div class="team-score">${game.home.score}</div>
      ${createNumCell(game.lines.close.homeSpread, game.lines.close.homePrice)}
      ${createNumCell(game.lines.model.homeSpread, game.lines.model.homeProb, true, true)}
    `;
  } else {
    // Live game - show Open, Current, Model
    headers = `
      <div class="game-headers">
        <span></span>
        <span>Open</span>
        <span>Current</span>
        <span>Model</span>
      </div>
    `;
    
    awayNumbers = `
      ${createNumCell(game.lines.open.awaySpread, game.lines.open.awayPrice)}
      ${createNumCell(game.lines.current.awaySpread, game.lines.current.awayPrice)}
      ${createNumCell(game.lines.model.awaySpread, game.lines.model.awayProb, true, true)}
    `;
    
    homeNumbers = `
      ${createNumCell(game.lines.open.homeSpread, game.lines.open.homePrice)}
      ${createNumCell(game.lines.current.homeSpread, game.lines.current.homePrice)}
      ${createNumCell(game.lines.model.homeSpread, game.lines.model.homeProb, true, true)}
    `;
  }
  
  return `
    <div class="${cardClass}" data-game-id="${game.id}" onclick="handleGameClick('${game.id}')">
      <div class="game-time">${game.time}</div>
      ${headers}
      
      <!-- Away Team Row -->
      <div class="team-row">
        <div class="team-info">
          <div class="team-logo">${game.away.logo}</div>
          <div class="team-details">
            <span class="team-code">${game.away.code}</span>
            <span class="team-record">${game.away.record}</span>
          </div>
        </div>
        ${awayNumbers}
      </div>
      
      <!-- Home Team Row -->
      <div class="team-row">
        <div class="team-info">
          <div class="team-logo">${game.home.logo}</div>
          <div class="team-details">
            <span class="team-code">${game.home.code}</span>
            <span class="team-record">${game.home.record}</span>
          </div>
        </div>
        ${homeNumbers}
      </div>
    </div>
  `;
}

// Handle game card clicks
function handleGameClick(gameId) {
  console.log('Game clicked:', gameId);
  showGameDetail(gameId);
}

// Handle navigation clicks
function handleNavClick(direction) {
  console.log('Navigation clicked:', direction);
  if (direction === 'prev') {
    alert('Previous Week: Week 3, 2025\n\nThis would load the previous week\'s games.');
  } else {
    alert('Next Week: Week 5, 2025\n\nThis would load the next week\'s games.');
  }
}

// Render games for each column
function renderColumn(columnIndex) {
  const column = appData.columns[columnIndex];
  const containerIds = ['thursday-games', 'sunday-early-games', 'sunday-late-games', 'monday-games'];
  const container = document.getElementById(containerIds[columnIndex]);
  
  if (!container) {
    console.warn('Container not found:', containerIds[columnIndex]);
    return;
  }
  
  const gamesHtml = column.games.map(game => createGameCard(game)).join('');
  container.innerHTML = gamesHtml;
  console.log('Rendered column', columnIndex, 'with', column.games.length, 'games');
}

// Game detail display
function showGameDetail(gameId) {
  console.log('Showing game detail for:', gameId);
  
  // Find game across all columns
  let selectedGame = null;
  let columnTitle = '';
  
  for (const column of appData.columns) {
    const game = column.games.find(g => g.id === gameId);
    if (game) {
      selectedGame = game;
      columnTitle = column.title + (column.subtitle ? ` ${column.subtitle}` : '');
      break;
    }
  }
  
  if (!selectedGame) {
    console.error('Game not found:', gameId);
    return;
  }
  
  const awayTeam = `${selectedGame.away.code} (${selectedGame.away.record})`;
  const homeTeam = `${selectedGame.home.code} (${selectedGame.home.record})`;
  
  let details = `GAME ANALYSIS\n\n${awayTeam} @ ${homeTeam}\n${columnTitle} - ${selectedGame.time}\n\n`;
  
  if (selectedGame.status === 'final') {
    details += `FINAL SCORE:\n`;
    details += `${selectedGame.away.code}: ${selectedGame.away.score}\n`;
    details += `${selectedGame.home.code}: ${selectedGame.home.score}\n\n`;
    details += `CLOSING LINES:\n`;
    details += `${selectedGame.away.code}: ${formatSpread(selectedGame.lines.close.awaySpread)} (${formatPrice(selectedGame.lines.close.awayPrice)})\n`;
    details += `${selectedGame.home.code}: ${formatSpread(selectedGame.lines.close.homeSpread)} (${formatPrice(selectedGame.lines.close.homePrice)})\n\n`;
    details += `MODEL PROJECTION:\n`;
    details += `${selectedGame.away.code}: ${(selectedGame.lines.model.awayProb * 100).toFixed(1)}% win probability\n`;
    details += `${selectedGame.home.code}: ${(selectedGame.lines.model.homeProb * 100).toFixed(1)}% win probability`;
  } else {
    details += `CURRENT LINES:\n`;
    details += `${selectedGame.away.code}: ${formatSpread(selectedGame.lines.current.awaySpread)} (${formatPrice(selectedGame.lines.current.awayPrice)})\n`;
    details += `${selectedGame.home.code}: ${formatSpread(selectedGame.lines.current.homeSpread)} (${formatPrice(selectedGame.lines.current.homePrice)})\n\n`;
    details += `OPENING LINES:\n`;
    details += `${selectedGame.away.code}: ${formatSpread(selectedGame.lines.open.awaySpread)} (${formatPrice(selectedGame.lines.open.awayPrice)})\n`;
    details += `${selectedGame.home.code}: ${formatSpread(selectedGame.lines.open.homeSpread)} (${formatPrice(selectedGame.lines.open.homePrice)})\n\n`;
    details += `MODEL PROJECTION:\n`;
    details += `${selectedGame.away.code}: ${(selectedGame.lines.model.awayProb * 100).toFixed(1)}% win probability\n`;
    details += `${selectedGame.home.code}: ${(selectedGame.lines.model.homeProb * 100).toFixed(1)}% win probability`;
  }
  
  alert(details);
}

// Initialize application
function init() {
  console.log('Initializing NFL Model Projections...');
  
  // Render all columns
  for (let i = 0; i < 4; i++) {
    renderColumn(i);
  }
  
  // Add navigation button handlers
  const navButtons = document.querySelectorAll('.nav-btn');
  if (navButtons.length >= 2) {
    navButtons[0].onclick = () => handleNavClick('prev');
    navButtons[1].onclick = () => handleNavClick('next');
    console.log('Navigation buttons configured');
  } else {
    console.warn('Navigation buttons not found');
  }
  
  console.log('NFL Model Projections initialized successfully');
}

// Start when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}