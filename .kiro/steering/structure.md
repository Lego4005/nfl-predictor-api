# Project Structure

## Root Level
- `package.json` - Frontend dependencies and npm scripts
- `vite.config.js` - Vite build configuration
- `index.html` - Main HTML entry point
- `main.py` - FastAPI backend server
- `requirements.txt` - Python dependencies
- `README.md` - Deployment and setup instructions

## Frontend Structure (`src/`)
```
src/
├── main.jsx          # React app entry point
├── App.jsx           # Root component wrapper
├── NFLDashboard.jsx  # Main dashboard component
└── pages/
    └── Dashboard.jsx # Alternative dashboard (unused)
```

## Component Architecture
- **Single Page Application**: All functionality in NFLDashboard.jsx
- **Tabbed Interface**: main | props | fantasy | lineup tabs
- **Reusable Components**: Card, Section, Table components defined inline
- **State Management**: Local component state with hooks

## API Integration
- **Base URL**: Configurable via VITE_API_BASE environment variable
- **Endpoints**: `/v1/best-picks/2025/{week}` for data, `/v1/best-picks/2025/{week}/download` for exports
- **Cache Busting**: Timestamp query parameter for fresh data
- **Error Handling**: Loading states and error messages

## Data Flow
1. User selects week → API call triggered
2. Data fetched and stored in component state
3. Tabbed interface renders different data sections
4. Download buttons trigger direct API calls

## Styling Approach
- **No CSS Framework**: Pure inline styles throughout
- **Design System**: Consistent spacing, colors, and typography
- **Responsive**: Flexbox layouts with mobile considerations
- **Theme**: Clean, minimal design with card-based layout