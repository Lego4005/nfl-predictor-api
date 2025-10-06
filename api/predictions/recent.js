// Vercel serverless function for recent predictions
export default function handler(req, res) {
  // Mock recent predictions data
  const mockPredictions = [
    {
      game_id: "KC_BUF_2025_W1",
      date: "2025-01-15T20:20:00Z",
      home_team: "KC",
      away_team: "BUF",
      consensus_winner: "KC",
      consensus_confidence: 0.72,
      status: "upcoming",
      expert_predictions: [
        { expert_name: "The Analyst", avatar_emoji: "📊", prediction: { winner: "KC", confidence: 0.75 }},
        { expert_name: "The Gambler", avatar_emoji: "🎲", prediction: { winner: "BUF", confidence: 0.68 }},
        { expert_name: "The Rebel", avatar_emoji: "😈", prediction: { winner: "BUF", confidence: 0.71 }},
        { expert_name: "The Hunter", avatar_emoji: "🎯", prediction: { winner: "KC", confidence: 0.82 }},
        { expert_name: "The Rider", avatar_emoji: "🏇", prediction: { winner: "KC", confidence: 0.73 }},
        { expert_name: "The Scholar", avatar_emoji: "📚", prediction: { winner: "KC", confidence: 0.79 }},
        { expert_name: "The Chaos", avatar_emoji: "🌪️", prediction: { winner: "BUF", confidence: 0.51 }},
        { expert_name: "The Intuition", avatar_emoji: "🔮", prediction: { winner: "KC", confidence: 0.65 }},
        { expert_name: "The Quant", avatar_emoji: "🤖", prediction: { winner: "KC", confidence: 0.83 }},
        { expert_name: "The Reversal", avatar_emoji: "↩️", prediction: { winner: "BUF", confidence: 0.71 }},
        { expert_name: "The Fader", avatar_emoji: "🚫", prediction: { winner: "BUF", confidence: 0.69 }},
        { expert_name: "The Sharp", avatar_emoji: "💎", prediction: { winner: "KC", confidence: 0.85 }},
        { expert_name: "The Underdog", avatar_emoji: "🐕", prediction: { winner: "BUF", confidence: 0.60 }},
        { expert_name: "The Consensus", avatar_emoji: "👥", prediction: { winner: "KC", confidence: 0.67 }},
        { expert_name: "The Exploiter", avatar_emoji: "🔍", prediction: { winner: "KC", confidence: 0.78 }}
      ]
    }
  ];

  res.status(200).json(mockPredictions);
}
