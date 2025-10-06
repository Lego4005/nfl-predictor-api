// Vercel serverless function for expert data
export default function handler(req, res) {
  const experts = [
    { expert_id: '1', display_name: 'The Analyst', personality: 'conservative', avatar_emoji: '📊', accuracy_rate: 0.756, predictions_count: 42 },
    { expert_id: '2', display_name: 'The Gambler', personality: 'risk_taking', avatar_emoji: '🎲', accuracy_rate: 0.623, predictions_count: 38 },
    { expert_id: '3', display_name: 'The Rebel', personality: 'contrarian', avatar_emoji: '😈', accuracy_rate: 0.698, predictions_count: 45 },
    { expert_id: '4', display_name: 'The Hunter', personality: 'value_seeking', avatar_emoji: '🎯', accuracy_rate: 0.812, predictions_count: 40 },
    { expert_id: '5', display_name: 'The Rider', personality: 'momentum', avatar_emoji: '🏇', accuracy_rate: 0.734, predictions_count: 41 },
    { expert_id: '6', display_name: 'The Scholar', personality: 'fundamentalist', avatar_emoji: '📚', accuracy_rate: 0.789, predictions_count: 43 },
    { expert_id: '7', display_name: 'The Chaos', personality: 'randomness', avatar_emoji: '🌪️', accuracy_rate: 0.501, predictions_count: 39 },
    { expert_id: '8', display_name: 'The Intuition', personality: 'gut_feel', avatar_emoji: '🔮', accuracy_rate: 0.654, predictions_count: 44 },
    { expert_id: '9', display_name: 'The Quant', personality: 'statistics', avatar_emoji: '🤖', accuracy_rate: 0.823, predictions_count: 42 },
    { expert_id: '10', display_name: 'The Reversal', personality: 'mean_reversion', avatar_emoji: '↩️', accuracy_rate: 0.712, predictions_count: 40 },
    { expert_id: '11', display_name: 'The Fader', personality: 'anti_narrative', avatar_emoji: '🚫', accuracy_rate: 0.687, predictions_count: 41 },
    { expert_id: '12', display_name: 'The Sharp', personality: 'smart_money', avatar_emoji: '💎', accuracy_rate: 0.845, predictions_count: 38 },
    { expert_id: '13', display_name: 'The Underdog', personality: 'upset_seeker', avatar_emoji: '🐕', accuracy_rate: 0.598, predictions_count: 42 },
    { expert_id: '14', display_name: 'The Consensus', personality: 'crowd_following', avatar_emoji: '👥', accuracy_rate: 0.667, predictions_count: 44 },
    { expert_id: '15', display_name: 'The Exploiter', personality: 'inefficiency_hunting', avatar_emoji: '🔍', accuracy_rate: 0.778, predictions_count: 39 }
  ];

  res.status(200).json(experts);
}
