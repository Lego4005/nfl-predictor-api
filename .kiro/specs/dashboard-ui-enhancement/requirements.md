# Requirements Document

## Introduction

The NFL Predictor dashboard currently has frontend display issues where users cannot properly view the distinct prediction categories (ATS, Totals, Props, Fantasy). While the backend API provides complete and accurate data for all categories, the frontend React application is not displaying this data correctly across different tabs. Users need a fully functional dashboard that shows category-specific data with proper formatting, game lines, and the fantasy optimizer.

## Requirements

### Requirement 1

**User Story:** As a sports bettor, I want to view Against the Spread (ATS) predictions with game lines, so that I can make informed betting decisions on point spreads.

#### Acceptance Criteria

1. WHEN I click the "ATS" tab THEN the system SHALL display 16 games with ATS picks
2. WHEN viewing ATS data THEN the system SHALL show the spread line for each game (e.g., -7.5, +3.0)
3. WHEN viewing ATS data THEN the system SHALL display the ATS pick (which team to bet)
4. WHEN viewing ATS data THEN the system SHALL show ATS confidence percentages
5. WHEN viewing ATS data THEN the system SHALL color-code spreads (red for favorites, green for underdogs)

### Requirement 2

**User Story:** As a sports bettor, I want to view Totals (Over/Under) predictions with game lines, so that I can make informed betting decisions on point totals.

#### Acceptance Criteria

1. WHEN I click the "Totals" tab THEN the system SHALL display 16 games with totals picks
2. WHEN viewing totals data THEN the system SHALL show the total line for each game (e.g., 47.5, 49.5)
3. WHEN viewing totals data THEN the system SHALL display Over/Under picks with visual indicators (🔥 for Over, ❄️ for Under)
4. WHEN viewing totals data THEN the system SHALL show totals confidence percentages
5. WHEN viewing totals data THEN the system SHALL color-code lines based on scoring expectations

### Requirement 3

**User Story:** As a fantasy football player, I want to view the fantasy optimizer with player rankings and salary information, so that I can build optimal DFS lineups.

#### Acceptance Criteria

1. WHEN I click the "Fantasy" tab THEN the system SHALL display 8 optimized fantasy players
2. WHEN viewing fantasy data THEN the system SHALL show player salary information (e.g., $8,500, $9,200)
3. WHEN viewing fantasy data THEN the system SHALL display projected points for each player
4. WHEN viewing fantasy data THEN the system SHALL show value multipliers (e.g., 2.92x, 2.40x)
5. WHEN viewing fantasy data THEN the system SHALL color-code positions (QB=blue, RB=green, WR=yellow, TE=gray)
6. WHEN viewing fantasy data THEN the system SHALL highlight top 3 picks with diamond icons (💎)

### Requirement 4

**User Story:** As a user, I want each tab to show distinct category-specific data, so that I can access different types of predictions without confusion.

#### Acceptance Criteria

1. WHEN I switch between tabs THEN the system SHALL display different data for each category
2. WHEN viewing the Straight-Up tab THEN the system SHALL show only win/loss predictions
3. WHEN viewing the ATS tab THEN the system SHALL show only spread-related data
4. WHEN viewing the Totals tab THEN the system SHALL show only over/under data
5. WHEN viewing the Props tab THEN the system SHALL show only player prop bets
6. WHEN viewing the Fantasy tab THEN the system SHALL show only DFS optimization data

### Requirement 5

**User Story:** As a user, I want the React application to build and run properly, so that I can access the dashboard through a modern web interface.

#### Acceptance Criteria

1. WHEN I run `npm install` THEN the system SHALL install all required dependencies without errors
2. WHEN I run `npm run dev` THEN the system SHALL start the development server successfully
3. WHEN I access the dashboard THEN the system SHALL load without JavaScript errors
4. WHEN the dashboard loads THEN the system SHALL fetch data from the backend API
5. WHEN data is loaded THEN the system SHALL display all tabs with proper functionality