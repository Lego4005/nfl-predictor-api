# NFL User Picks Feature

## Overview

The User Picks feature allows users to select winners for NFL games and assign confidence levels (1-10) to each pick. This feature includes form validation, database storage, and a comprehensive UI for managing picks.

## Components

### 1. UserPicks.jsx
Main React component with:
- **Game Selection**: Click to select winner for each game
- **Confidence Slider**: 1-10 scale for each pick
- **Form Validation**: Ensures unique confidence levels and valid ranges
- **Tabs Interface**: Switch between making picks and viewing current picks
- **Real-time Statistics**: Shows total picks and average confidence
- **Loading States**: Smooth loading and submission feedback

### 2. UserPicksContainer.jsx
Wrapper component that:
- Fetches game data from the API
- Manages server connectivity status
- Handles data refresh functionality
- Provides error handling and fallback data

### 3. userPicksService.js
Service layer for API communication:
- Submit picks to database
- Retrieve user picks
- Delete individual picks
- Get picks statistics
- Client-side validation

### 4. Backend API (working_server.py)
SQLite-based API with endpoints:
- `POST /api/user-picks/submit` - Submit picks
- `GET /api/user-picks` - Get all user picks
- `DELETE /api/user-picks/{pick_id}` - Delete a pick
- `GET /api/user-picks/stats` - Get statistics

## Features

### ✅ Core Functionality
- Select winner for each game
- Set confidence level (1-10 scale)
- Submit picks to database
- View current picks
- Real-time validation

### ✅ Form Validation
- Confidence levels must be unique across all picks
- Confidence must be between 1-10
- Winner selection required
- Clear error messages

### ✅ User Experience
- Responsive design for mobile/desktop
- Animated transitions and feedback
- Loading states during submission
- Server connectivity indicators
- Confidence level descriptions

### ✅ Data Persistence
- SQLite database storage
- Automatic database initialization
- Support for multiple users
- Pick history and statistics

## Usage

### Starting the Application

1. **Start the backend server:**
   ```bash
   python working_server.py
   ```
   Server runs on `http://127.0.0.1:8084`

2. **Start the React frontend:**
   ```bash
   npm run dev
   ```
   Frontend runs on `http://localhost:5173`

3. **Navigate to picks:**
   Click the "My Picks" button in the top-right corner

### Making Picks

1. **Select Winners**: Click on team cards to select winners
2. **Set Confidence**: Use the slider to set confidence (1-10)
3. **Submit**: Click "Submit Picks" when ready
4. **View Results**: Switch to "My Picks" tab to see submitted picks

### Validation Rules

- Each game must have a unique confidence level
- Confidence must be between 1 and 10
- All picks must have both winner and confidence selected
- Cannot submit empty picks

## API Endpoints

### Submit Picks
```
POST /api/user-picks/submit
Content-Type: application/json

{
  "picks": [
    {
      "gameId": "game_123",
      "winner": "KC",
      "confidence": 10,
      "timestamp": "2024-01-01T00:00:00Z"
    }
  ],
  "userId": "user_123"
}
```

### Get User Picks
```
GET /api/user-picks?user_id=user_123

Response:
{
  "success": true,
  "picks": [...],
  "total": 5
}
```

### Get Statistics
```
GET /api/user-picks/stats?user_id=user_123

Response:
{
  "success": true,
  "stats": {
    "total_picks": 10,
    "average_confidence": 6.5,
    "confidence_distribution": {
      "10": 2,
      "8": 3,
      "6": 5
    }
  }
}
```

## Testing

### Automated Testing
```bash
# Test the API endpoints
python scripts/test_user_picks.py
```

### Manual Testing
1. Start both backend and frontend
2. Navigate to "My Picks" tab
3. Select winners and set confidence levels
4. Submit picks and verify they appear in "My Picks"
5. Test validation by trying duplicate confidence levels

## File Structure

```
src/
├── components/
│   ├── UserPicks.jsx              # Main picks component
│   ├── UserPicksContainer.jsx     # Data management wrapper
│   └── ui/                        # Reusable UI components
├── services/
│   └── userPicksService.js        # API service layer
├── data/
│   └── nflTeams.js               # Team data and logos
└── index.css                     # Includes slider styling

scripts/
└── test_user_picks.py            # API testing script

docs/
└── USER_PICKS_FEATURE.md         # This documentation
```

## Database Schema

```sql
CREATE TABLE user_picks (
    id TEXT PRIMARY KEY,
    user_id TEXT DEFAULT 'default_user',
    game_id TEXT NOT NULL,
    winner TEXT NOT NULL,
    confidence INTEGER NOT NULL,
    timestamp TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, game_id)
);
```

## Configuration

### Environment Variables
- Default user ID: `default_user` (for single-user setup)
- Database file: `user_picks.db` (created automatically)
- API base URL: `http://127.0.0.1:8084/api`

### Customization
- Confidence range: Modify `min="1" max="10"` in UserPicks.jsx
- Validation rules: Update `validatePicks()` in userPicksService.js
- Styling: Customize CSS classes in index.css

## Troubleshooting

### Common Issues

1. **Server not responding**
   - Check if `python working_server.py` is running
   - Verify port 8084 is available
   - Check console for error messages

2. **Database errors**
   - Database is created automatically on first run
   - Check file permissions in project directory
   - Delete `user_picks.db` to reset database

3. **Frontend not loading picks**
   - Check browser console for network errors
   - Verify API endpoints are responding
   - Check CORS configuration in backend

4. **Validation errors**
   - Ensure each game has unique confidence level
   - Check that confidence is between 1-10
   - Verify all required fields are filled

### Debug Mode
Enable detailed logging by checking browser console and server logs for detailed error information.

## Future Enhancements

- **Multi-user authentication**
- **Pick history and performance tracking**
- **Social features (leaderboards, sharing)**
- **Advanced analytics and insights**
- **Push notifications for game updates**
- **Integration with real-time scores**

## Support

For issues or questions about the User Picks feature:
1. Check this documentation
2. Run the test script to verify API functionality
3. Check browser console and server logs for errors
4. Review the validation rules and requirements