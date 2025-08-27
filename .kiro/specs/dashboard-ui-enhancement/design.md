# Design Document

## Overview

The NFL Predictor dashboard enhancement focuses on fixing frontend display issues and ensuring proper category-specific data rendering. The backend API already provides complete and accurate data for all prediction categories. The solution involves debugging the React application, ensuring proper build processes, and implementing robust tab switching with category-specific data display.

## Architecture

### Current State Analysis
- **Backend API**: ✅ Working perfectly - provides distinct data for all 5 categories
- **Data Structure**: ✅ Complete - includes SU, ATS, totals, props, and fantasy data
- **Frontend React**: ❌ Display issues - tabs not showing category-specific content
- **Build Process**: ❌ Potentially broken - React app may not be building/serving correctly

### Solution Architecture
```
Frontend Layer:
├── React TypeScript Application (src/NFLDashboard.tsx)
├── Tab Switching Logic (state-based rendering)
├── Category-Specific Components (ATS, Totals, Fantasy, Props)
└── Data Transformation Layer (API response handling)

Backend Integration:
├── API Service (existing - working correctly)
├── Data Fetching (existing - provides all categories)
└── Error Handling (existing - robust error management)
```

## Components and Interfaces

### Tab Management System
```typescript
interface TabState {
  activeTab: 'main' | 'ats' | 'totals' | 'props' | 'fantasy';
  data: WeeklyPredictionData;
  loading: boolean;
}

interface WeeklyPredictionData {
  best_picks: StraightUpPick[];      // 16 games
  ats_picks: ATSPick[];              // 16 games with spreads
  totals_picks: TotalsPick[];        // 16 games with O/U lines
  prop_bets: PropBet[];              // 10 ranked props
  fantasy_picks: FantasyPick[];      // 8 optimized players
}
```

### Category-Specific Data Models
```typescript
interface ATSPick {
  matchup: string;           // "NYJ @ BUF"
  ats_pick: string;         // "BUF -7.5"
  spread: number;           // -7.5
  ats_confidence: number;   // 0.65
}

interface TotalsPick {
  matchup: string;          // "NYJ @ BUF"
  tot_pick: string;         // "Over 47.5"
  total_line: number;       // 47.5
  tot_confidence: number;   // 0.665
}

interface FantasyPick {
  player: string;           // "Josh Allen"
  position: string;         // "QB"
  team: string;            // "BUF"
  salary: number;          // 8500
  projection: number;      // 24.8
  value: number;           // 2.92
  confidence: number;      // 0.78
}
```

### Visual Design System
```typescript
interface StyleSystem {
  colors: {
    favorites: '#dc2626';      // Red for negative spreads
    underdogs: '#22c55e';      // Green for positive spreads
    over: '#dc2626';           // Red for Over picks
    under: '#2563eb';          // Blue for Under picks
    highConfidence: '#22c55e'; // Green for >70%
    medConfidence: '#f59e0b';  // Yellow for 60-70%
    lowConfidence: '#6b7280';  // Gray for <60%
  };
  positions: {
    QB: { bg: '#dbeafe', color: '#1e40af' };
    RB: { bg: '#dcfce7', color: '#166534' };
    WR: { bg: '#fef3c7', color: '#92400e' };
    TE: { bg: '#f3f4f6', color: '#6b7280' };
  };
}
```

## Data Models

### API Response Structure (Confirmed Working)
```json
{
  "best_picks": [
    {
      "matchup": "NYJ @ BUF",
      "su_pick": "BUF",
      "su_confidence": 0.74
    }
  ],
  "ats_picks": [
    {
      "matchup": "NYJ @ BUF",
      "ats_pick": "BUF -7.5",
      "spread": -7.5,
      "ats_confidence": 0.65
    }
  ],
  "totals_picks": [
    {
      "matchup": "NYJ @ BUF",
      "tot_pick": "Over 47.5",
      "total_line": 47.5,
      "tot_confidence": 0.665
    }
  ],
  "fantasy_picks": [
    {
      "player": "Josh Allen",
      "position": "QB",
      "team": "BUF",
      "salary": 8500,
      "projection": 24.8,
      "value": 2.92,
      "confidence": 0.78
    }
  ]
}
```

### Frontend State Management
```typescript
const [tab, setTab] = useState<string>('main');
const [data, setData] = useState<any>(null);
const [loading, setLoading] = useState<boolean>(false);

// Tab switching logic
const renderTabContent = () => {
  switch(tab) {
    case 'ats':
      return <ATSTable data={data?.ats_picks || []} />;
    case 'totals':
      return <TotalsTable data={data?.totals_picks || []} />;
    case 'fantasy':
      return <FantasyTable data={data?.fantasy_picks || []} />;
    case 'props':
      return <PropsTable data={data?.prop_bets || []} />;
    default:
      return <StraightUpTable data={data?.best_picks || []} />;
  }
};
```

## Error Handling

### Build Process Debugging
1. **Dependency Check**: Verify all npm packages are installed correctly
2. **TypeScript Compilation**: Ensure no type errors preventing build
3. **Development Server**: Confirm Vite dev server starts without errors
4. **API Connection**: Validate frontend can connect to backend API

### Runtime Error Handling
```typescript
interface ErrorBoundaryState {
  hasError: boolean;
  errorMessage: string;
  retryable: boolean;
}

const handleTabSwitch = (newTab: string) => {
  try {
    setTab(newTab);
    // Ensure data exists for the selected tab
    if (!data || !data[`${newTab}_picks`]) {
      console.warn(`No data available for ${newTab} tab`);
    }
  } catch (error) {
    console.error('Tab switch error:', error);
    setNotifications(prev => [...prev, {
      type: 'error',
      message: 'Failed to switch tabs',
      retryable: true
    }]);
  }
};
```

## Testing Strategy

### Frontend Testing Approach
1. **Component Testing**: Verify each tab renders correct data
2. **Integration Testing**: Test API data flow to frontend components
3. **Visual Testing**: Confirm styling and formatting for each category
4. **Build Testing**: Ensure React app builds and serves correctly

### Test Scenarios
```typescript
describe('Dashboard Tab Switching', () => {
  test('ATS tab shows spread data', () => {
    // Verify ATS picks display with spreads and confidence
  });
  
  test('Totals tab shows O/U data', () => {
    // Verify totals picks display with lines and O/U indicators
  });
  
  test('Fantasy tab shows optimizer data', () => {
    // Verify fantasy picks display with salaries and projections
  });
});
```

### Manual Testing Checklist
- [ ] React app builds without errors (`npm run build`)
- [ ] Development server starts (`npm run dev`)
- [ ] All 5 tabs display distinct data
- [ ] ATS tab shows spreads and game lines
- [ ] Totals tab shows O/U lines and picks
- [ ] Fantasy tab shows salary and projection data
- [ ] Props tab shows ranked player props
- [ ] Visual styling matches design system
- [ ] Error handling works for API failures

## Implementation Priority

### Phase 1: Build Process Fix
1. Verify and fix npm dependencies
2. Resolve TypeScript compilation errors
3. Ensure Vite development server works
4. Test API connectivity

### Phase 2: Tab Content Enhancement
1. Verify tab switching logic works correctly
2. Enhance ATS display with proper spread formatting
3. Enhance Totals display with O/U indicators
4. Implement fantasy optimizer display
5. Add visual enhancements and styling

### Phase 3: User Experience Polish
1. Add loading states for tab switches
2. Implement error handling for missing data
3. Add responsive design improvements
4. Optimize performance for large datasets