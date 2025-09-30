/**
 * Confidence Pool Hooks - Barrel Export
 * Central export point for all Confidence Pool related hooks
 */

// Expert Bankroll Hooks
export {
  useExpertBankrolls,
  useExpertBankrollHistory,
  useExpertRiskMetrics
} from './useExpertBankrolls';

// Live Betting Feed Hooks
export {
  useLiveBettingFeed,
  useExpertBetHistory
} from './useLiveBettingFeed';

// Council Predictions Hooks
export {
  useCouncilPredictions,
  useGameConsensus,
  useTopCouncilMembers
} from './useCouncilPredictions';

// Expert Memories Hooks
export {
  useExpertMemories,
  useExpertMemory,
  useExpertMemoryStats,
  useTopMemories
} from './useExpertMemories';

// Prediction Battles Hooks
export {
  usePredictionBattles,
  useHeadToHeadRecord
} from './usePredictionBattles';

// WebSocket Hook
export {
  useConfidencePoolWebSocket
} from './useConfidencePoolWebSocket';

// Re-export types
export type {
  ExpertBankroll,
  BankrollsResponse,
  LiveBet,
  BettingFeedResponse,
  CouncilPrediction,
  CouncilPredictionsResponse,
  ExpertMemory,
  MemoriesResponse,
  PredictionBattle,
  BattlesResponse,
  WebSocketEvent,
  BetPlacedEvent,
  BetSettledEvent,
  ExpertEliminatedEvent,
  LineMovementEvent,
  BankrollUpdateEvent
} from '../types/confidencePool';