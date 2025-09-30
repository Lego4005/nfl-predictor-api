# Confidence Pool Hooks Documentation

Complete documentation for the Confidence Pool real-time React hooks implementation.

## Overview

The Confidence Pool hooks provide a comprehensive real-time betting and prediction tracking system with:
- **Expert bankroll tracking** with risk metrics
- **Live betting feed** with real-time updates
- **AI Council predictions** with weighted voting
- **Expert memories** (episodic memory system)
- **Prediction battles** (expert disagreements)
- **WebSocket integration** for live updates

---

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Hooks Reference](#hooks-reference)
4. [Types](#types)
5. [Examples](#examples)
6. [Real-time Features](#real-time-features)
7. [Testing](#testing)

---

## Installation

All hooks are exported from `/src/hooks/confidencePool.ts`:

```typescript
import {
  useExpertBankrolls,
  useLiveBettingFeed,
  useCouncilPredictions,
  useExpertMemories,
  usePredictionBattles,
  useConfidencePoolWebSocket
} from '@/hooks/confidencePool';
```

---

## Quick Start

### Basic Example

```typescript
import { useExpertBankrolls, useLiveBettingFeed } from '@/hooks/confidencePool';

function ConfidencePoolDashboard() {
  // Fetch expert bankrolls (auto-refreshes every 30s)
  const { data: bankrollsData, isLoading } = useExpertBankrolls();

  // Fetch live betting feed
  const { data: bettingData } = useLiveBettingFeed({
    status: 'pending',
    realtime: true // Enable real-time subscriptions
  });

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      <h1>Expert Bankrolls</h1>
      {bankrollsData?.bankrolls.map(bankroll => (
        <div key={bankroll.expert_id}>
          {bankroll.expert_emoji} {bankroll.expert_name}:
          ${bankroll.current_balance.toFixed(2)}
        </div>
      ))}

      <h1>Live Bets</h1>
      {bettingData?.bets.map(bet => (
        <div key={bet.bet_id}>
          {bet.expert_emoji} {bet.expert_name} bet ${bet.bet_amount} on {bet.prediction}
        </div>
      ))}
    </div>
  );
}
```

---

## Hooks Reference

### 1. useExpertBankrolls

Fetches and tracks expert virtual bankrolls with real-time Supabase subscriptions.

**Signature:**
```typescript
function useExpertBankrolls(
  options?: UseExpertBankrollsOptions
): UseQueryResult<BankrollsResponse>
```

**Options:**
```typescript
interface UseExpertBankrollsOptions {
  refetchInterval?: number;          // Default: 30000 (30s)
  enabled?: boolean;                 // Default: true
  sortBy?: 'balance' | 'roi' | 'risk' | 'change';
  filterByStatus?: ('safe' | 'warning' | 'danger' | 'eliminated')[];
}
```

**Response:**
```typescript
interface BankrollsResponse {
  bankrolls: ExpertBankroll[];
  summary: {
    total_eliminated: number;
    avg_balance: number;
    total_wagered: number;
    most_aggressive: string;
    safest: string;
  };
  timestamp: string;
}
```

**Example:**
```typescript
// Sort by ROI, only show safe/warning experts
const { data, isLoading, error } = useExpertBankrolls({
  sortBy: 'roi',
  filterByStatus: ['safe', 'warning'],
  refetchInterval: 15000 // Refresh every 15s
});

// Access data
if (data) {
  console.log('Top expert:', data.bankrolls[0].expert_name);
  console.log('Total eliminated:', data.summary.total_eliminated);
}
```

---

### 2. useLiveBettingFeed

Fetches live expert bets with real-time updates for new bets and settlements.

**Signature:**
```typescript
function useLiveBettingFeed(
  options?: UseLiveBettingFeedOptions
): UseQueryResult<BettingFeedResponse>
```

**Options:**
```typescript
interface UseLiveBettingFeedOptions {
  game_id?: string;                  // Filter by specific game
  expert_id?: string;                // Filter by specific expert
  status?: 'pending' | 'won' | 'lost' | 'push' | 'all';
  limit?: number;                    // Default: 50
  realtime?: boolean;                // Enable WebSocket subscriptions (default: true)
}
```

**Response:**
```typescript
interface BettingFeedResponse {
  bets: LiveBet[];
  summary: {
    total_at_risk: number;
    potential_payout: number;
    avg_confidence: number;
    total_bets: number;
    experts_active: number;
  };
  timestamp: string;
}
```

**Example:**
```typescript
// Get all pending bets for a specific game
const { data } = useLiveBettingFeed({
  game_id: '2025_05_KC_BUF',
  status: 'pending',
  realtime: true
});

// Listen for new bets via custom events
useEffect(() => {
  const handleBetPlaced = (e: CustomEvent) => {
    console.log('New bet placed:', e.detail);
  };

  window.addEventListener('bet-placed', handleBetPlaced);
  return () => window.removeEventListener('bet-placed', handleBetPlaced);
}, []);
```

---

### 3. useCouncilPredictions

Fetches AI Council predictions with weighted voting and consensus data.

**Signature:**
```typescript
function useCouncilPredictions(
  options?: UseCouncilPredictionsOptions
): UseQueryResult<CouncilPredictionsResponse>
```

**Options:**
```typescript
interface UseCouncilPredictionsOptions {
  week?: number;                     // NFL week number
  season?: number;                   // Default: 2025
  expert_id?: string;                // Filter by specific expert
  min_confidence?: number;           // Default: 0.5 (50%)
}
```

**Response:**
```typescript
interface CouncilPredictionsResponse {
  predictions: CouncilPrediction[];
  weekly_data: {
    week: number;
    season: number;
    council_members: Array<{
      expert_id: string;
      rank: number;
      selection_score: number;
      reason_selected: string;
    }>;
    total_predictions: number;
    consensus_quality: number;        // 0-1 score
  };
  timestamp: string;
}
```

**Example:**
```typescript
// Get week 5 predictions with high confidence
const { data } = useCouncilPredictions({
  week: 5,
  min_confidence: 0.75
});

// Display council members and their picks
data?.predictions.forEach(pred => {
  console.log(
    `${pred.expert_emoji} ${pred.expert_name} (${pred.council_position}) ` +
    `picks ${pred.prediction.team} with ${(pred.prediction.confidence * 100).toFixed(0)}% confidence`
  );
});
```

---

### 4. useExpertMemories

Fetches expert episodic memories for the Memory Lane feature.

**Signature:**
```typescript
function useExpertMemories(
  options?: UseExpertMemoriesOptions
): UseQueryResult<MemoriesResponse>
```

**Options:**
```typescript
interface UseExpertMemoriesOptions {
  expert_id?: string;
  limit?: number;                    // Default: 20
  offset?: number;                   // Default: 0
  filters?: {
    memory_type?: 'lesson_learned' | 'success_pattern' | 'failure_analysis' | 'insight';
    min_importance?: number;          // 0-1
    emotional_filter?: 'positive' | 'negative' | 'neutral' | 'all';
    time_range?: 'week' | 'month' | 'season' | 'all_time';
  };
}
```

**Response:**
```typescript
interface MemoriesResponse {
  memories: ExpertMemory[];
  total_count: number;
  pagination: {
    offset: number;
    limit: number;
    has_more: boolean;
  };
}
```

**Example:**
```typescript
// Get important lessons learned by The Gambler
const { data, fetchNextPage, hasNextPage } = useExpertMemories({
  expert_id: 'the-gambler',
  limit: 10,
  filters: {
    memory_type: 'lesson_learned',
    min_importance: 0.7,
    emotional_filter: 'negative'  // Painful lessons
  }
});

// Infinite scroll
const loadMore = () => {
  if (hasNextPage) fetchNextPage();
};
```

---

### 5. usePredictionBattles

Detects and tracks expert prediction battles (disagreements >3 points).

**Signature:**
```typescript
function usePredictionBattles(
  options?: UsePredictionBattlesOptions
): UseQueryResult<BattlesResponse>
```

**Options:**
```typescript
interface UsePredictionBattlesOptions {
  week?: number;
  min_difference?: number;           // Default: 3.0
  category?: 'spread' | 'total' | 'winner' | 'props';
  status?: 'pending' | 'settled';    // Default: 'pending'
}
```

**Response:**
```typescript
interface BattlesResponse {
  battles: PredictionBattle[];
  summary: {
    total_battles: number;
    avg_difference: number;
    most_contested_game: string;
  };
}
```

**Example:**
```typescript
// Find major spread disagreements
const { data } = usePredictionBattles({
  category: 'spread',
  min_difference: 5.0,
  status: 'pending'
});

// Display battles
data?.battles.forEach(battle => {
  console.log(
    `⚔️ ${battle.expert_a.expert_emoji} vs ${battle.expert_b.expert_emoji} ` +
    `on ${battle.game_details.away_team} @ ${battle.game_details.home_team}: ` +
    `${battle.difference.toFixed(1)} point difference`
  );
});
```

---

### 6. useConfidencePoolWebSocket

Enhanced WebSocket hook for real-time Confidence Pool events.

**Signature:**
```typescript
function useConfidencePoolWebSocket(
  options?: UseConfidencePoolWebSocketOptions
): WebSocketHookReturn
```

**Options:**
```typescript
interface UseConfidencePoolWebSocketOptions {
  url?: string;
  autoReconnect?: boolean;           // Default: true
  maxReconnectAttempts?: number;     // Default: 5
  reconnectInterval?: number;        // Default: 3000ms
  onBetPlaced?: (event: BetPlacedEvent) => void;
  onBetSettled?: (event: BetSettledEvent) => void;
  onExpertEliminated?: (event: ExpertEliminatedEvent) => void;
  onLineMovement?: (event: LineMovementEvent) => void;
  onBankrollUpdate?: (event: BankrollUpdateEvent) => void;
}
```

**Return:**
```typescript
interface WebSocketHookReturn {
  connectionState: {
    connected: boolean;
    reconnectAttempts: number;
    lastHeartbeat: string;
    latency: number;
  };
  lastEvent: WebSocketEvent | null;
  sendMessage: (message: any) => void;
  connect: () => void;
  disconnect: () => void;
  isConnected: boolean;
}
```

**Example:**
```typescript
const {
  connectionState,
  lastEvent,
  isConnected
} = useConfidencePoolWebSocket({
  onBetPlaced: (event) => {
    console.log('🎲 New bet:', event.bet.expert_name, event.bet.bet_amount);
    toast.success(`${event.bet.expert_emoji} ${event.bet.expert_name} just bet $${event.bet.bet_amount}!`);
  },
  onExpertEliminated: (event) => {
    console.log('💀 Expert eliminated:', event.expert_name);
    toast.error(`${event.expert_emoji} ${event.expert_name} has been eliminated!`);
  },
  onBankrollUpdate: (event) => {
    console.log('💰 Bankroll update:', event.expert_id, event.new_balance);
  }
});

return (
  <div>
    <div>Connection: {isConnected ? '🟢 Connected' : '🔴 Disconnected'}</div>
    <div>Latency: {connectionState.latency}ms</div>
    {lastEvent && (
      <div>Last event: {lastEvent.type}</div>
    )}
  </div>
);
```

---

## Real-time Features

### Supabase Real-time Subscriptions

All hooks automatically subscribe to relevant Supabase real-time events:

```typescript
// useExpertBankrolls - Auto subscribes to bankroll updates
const { data } = useExpertBankrolls(); // Updates in real-time

// useLiveBettingFeed - Auto subscribes to new bets and settlements
const { data } = useLiveBettingFeed({ realtime: true });

// useCouncilPredictions - Auto subscribes to prediction updates
const { data } = useCouncilPredictions();

// usePredictionBattles - Auto subscribes to prediction changes
const { data } = usePredictionBattles();
```

### WebSocket Events

The WebSocket hook emits custom events for toast notifications:

```typescript
useEffect(() => {
  // Listen for bet placed events
  const handleBetPlaced = (e: CustomEvent<BetPlacedEvent>) => {
    toast.success(`${e.detail.bet.expert_emoji} placed a bet!`);
  };

  // Listen for expert eliminations
  const handleElimination = (e: CustomEvent<ExpertEliminatedEvent>) => {
    toast.error(`${e.detail.expert_emoji} ${e.detail.expert_name} eliminated!`);
  };

  window.addEventListener('bet-placed', handleBetPlaced);
  window.addEventListener('expert-eliminated', handleElimination);

  return () => {
    window.removeEventListener('bet-placed', handleBetPlaced);
    window.removeEventListener('expert-eliminated', handleElimination);
  };
}, []);
```

---

## Testing

Comprehensive test suite available in `/tests/hooks/confidencePool.test.ts`.

Run tests:
```bash
npm run test:hooks
```

Example test:
```typescript
import { renderHook, waitFor } from '@testing-library/react';
import { useExpertBankrolls } from '@/hooks/confidencePool';

test('fetches expert bankrolls', async () => {
  const { result } = renderHook(() => useExpertBankrolls());

  await waitFor(() => {
    expect(result.current.isSuccess).toBe(true);
  });

  expect(result.current.data?.bankrolls).toBeInstanceOf(Array);
});
```

---

## Database Schema Reference

The hooks query these Supabase tables:

- `expert_virtual_bankrolls` - Expert bankroll data
- `expert_virtual_bets` - Live bets and history
- `expert_predictions_comprehensive` - Council predictions view
- `expert_episodic_memories` - Memory Lane data
- `expert_predictions` - Raw predictions for battles
- `games` - Game data

All tables support real-time subscriptions via Supabase Realtime.

---

## Performance Optimization

1. **Query Caching**: TanStack Query caches results with configurable `staleTime`
2. **Refetch Intervals**: Configurable auto-refresh intervals
3. **Real-time Updates**: Supabase subscriptions invalidate cache on changes
4. **Pagination**: Offset-based pagination for large datasets
5. **Selective Loading**: Filter and sort options to minimize data transfer

---

## Support

For issues or questions:
- API Documentation: `/docs/API_GATEWAY_ARCHITECTURE.md`
- Database Schema: `/docs/DATABASE_SCHEMA.md`
- Supabase Docs: https://supabase.com/docs

---

**Built with:**
- React 18
- TypeScript 5
- TanStack Query v5
- Supabase JS Client v2
- WebSocket API