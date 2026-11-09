# Coach Dashboard Feature - Documentation

## Overview
The Coach Dashboard enables coaches to monitor and analyze detailed training progress for all their assigned athletes. Coaches can track monthly statistics, view performance trends, and provide personalized feedback.

## Features

### 1. Coach Account System
- **Coach Signup**: Special endpoint `/api/auth/signup-coach` for coach registration
- **Role Management**: Coaches have `role='coach'` while trainees have `role='athlete'`
- **Multi-Sport Support**: Coaches can manage both Boxing and Table Tennis athletes

### 2. Coach Analytics Dashboard (`admin.html`)
Coaches can access a comprehensive dashboard displaying:

#### Summary Cards
- **Total Athletes**: Number of athletes coached
- **Sessions This Month**: Total training sessions by all athletes in past 30 days
- **Average Performance**: Combined performance metrics across all athletes
- **Most Active Athlete**: Athlete with most sessions

#### Athletes Grid
- Quick view cards for each coached athlete
- Displays: username, email, skill level, sports, join date
- Monthly session count
- One-click access to detailed reports

#### Top Performers
- Leaderboard of best-performing athletes this month
- Ranked by average performance score
- Sortable and dynamic

### 3. Detailed Athlete Reports
Clicking "View Detailed Report" on any athlete opens a modal with:

#### Athlete Profile
- Skill level, primary sport, all-time sessions, performance rating

#### Monthly Performance (Last 30 Days)
- Total sessions, completed sessions
- Average technique accuracy, reaction score, balance score
- Training hours this month
- Performance range (highest/lowest scores)

#### Recent Sessions Table
- Last 10 training sessions with details:
  - Date, sport type, session type
  - Duration, performance score, completion status

#### Coaching Feedback
- AI-generated insights based on performance metrics
- Recommendations for training improvements
- Performance trend analysis

### 4. Backend Analytics Endpoints

#### GET `/api/analytics/coach/summary`
Returns overall statistics for all coached athletes
```json
{
  "total_athletes": 5,
  "total_sessions_this_month": 23,
  "completed_sessions_this_month": 20,
  "avg_performance_across_athletes": 78.5,
  "most_active_athlete": {"username": "john", "sessions": 8},
  "top_performers": [
    {"username": "john", "avg_performance": 85.5},
    {"username": "maria", "avg_performance": 82.3}
  ]
}
```

#### GET `/api/analytics/coach/athletes`
Returns list of all athletes coached by current coach
```json
[
  {
    "id": 1,
    "username": "athlete1",
    "email": "athlete1@example.com",
    "skill_level": "intermediate",
    "sport_type": "boxing",
    "linked_sports": ["boxing", "table_tennis"],
    "created_at": "2025-01-15T10:30:00"
  }
]
```

#### GET `/api/analytics/coach/athlete/{athlete_id}/monthly-report`
Returns comprehensive monthly report for specific athlete
```json
{
  "athlete_id": 1,
  "athlete_username": "john",
  "skill_level": "advanced",
  "sport_type": "boxing",
  "linked_sports": ["boxing", "table_tennis"],
  "total_sessions": 45,
  "this_month_sessions": 8,
  "performance_rating": 85.5,
  "monthly_stats": {
    "total_sessions": 8,
    "completed_sessions": 8,
    "avg_performance_score": 82.3,
    "avg_technique_accuracy": 81.5,
    "avg_reaction_score": 80.2,
    "avg_balance_score": 79.8,
    "highest_performance": 95.0,
    "lowest_performance": 65.0,
    "total_training_hours": 5
  },
  "recent_sessions": [...]
}
```

## Database Schema

### Athlete Model Updates
New fields added:
- `role` (String): "athlete" or "coach"
- `coach_id` (Integer, FK): Self-referential foreign key to coach's athlete record

### Migration
Database automatically migrates on backend startup:
- Adds `role` and `coach_id` columns if they don't exist
- Existing athletes default to `role='athlete'`

## Usage Flow

### For Coaches

1. **Create Coach Account**
   - Navigate to signup page and register as coach
   - Or use `/api/auth/signup-coach` endpoint

2. **Access Dashboard**
   - Login to main dashboard
   - "Coach Analytics" link appears in navbar if user is coach
   - Click to open admin.html

3. **View Summary**
   - See overview cards with system-wide stats
   - Check top performers list

4. **Monitor Specific Athlete**
   - Find athlete in grid
   - Click "View Detailed Report"
   - Analyze monthly statistics
   - Review recent sessions
   - Read coaching feedback

### For Admins
Assign athletes to coaches by setting `coach_id` on athlete records (future feature)

## Frontend Components

### admin.html
- Responsive dashboard layout
- Summary cards with key metrics
- Athletes grid with quick stats
- Modal for detailed reports
- Top performers leaderboard

### admin.js
- Fetches data from analytics endpoints
- Handles authentication via JWT token
- Generates AI coaching feedback
- Formats dates and scores
- Responsive data display

## Authorization

All coach endpoints require:
1. Valid JWT token in Authorization header
2. User must have `role='coach'`
3. Accessing another athlete's report requires that athlete to be coached by the requesting coach

## Future Enhancements

1. **Coach-Athlete Assignment**: Admin interface to assign athletes to coaches
2. **Performance Charts**: Visual graphs of progress over time
3. **Custom Feedback**: Coaches add notes to athletes
4. **Export Reports**: Generate PDF/CSV reports for athletes
5. **Goal Setting**: Set and track training goals with athletes
6. **Notifications**: Alert coaches when athletes reach milestones

## Testing

Sample test data creation:
```python
# Create coach account
POST /api/auth/signup-coach
{
  "email": "coach1@example.com",
  "username": "coach1",
  "password": "secure123"
}

# Login as coach
POST /api/auth/login
username=coach1&password=secure123

# View coached athletes (using coach JWT token)
GET /api/analytics/coach/athletes
Headers: Authorization: Bearer {coach_token}

# Get athlete report
GET /api/analytics/coach/athlete/{athlete_id}/monthly-report
Headers: Authorization: Bearer {coach_token}
```

## File Modified/Created

Backend:
- `backend/app/models/athlete.py` - Added role and coach_id fields
- `backend/app/database.py` - Added migration for new columns
- `backend/app/routes/auth.py` - Added CoachCreate/CoachResponse models, signup-coach endpoint, added role field to AthleteResponse
- `backend/app/routes/analytics.py` - NEW file with all coach analytics endpoints
- `backend/main.py` - Added analytics router

Frontend:
- `frontend/pages/admin.html` - NEW coach dashboard UI
- `frontend/js/admin.js` - NEW coach dashboard JavaScript logic
- `frontend/pages/dashboard.html` - Added conditional admin link in navbar

## Security Considerations

- Authentication required for all endpoints
- Coach can only view athletes they coach
- Role-based access control enforced on endpoints
- Access JWTs expire after 15 minutes; refresh tokens rotate on renewal
- Passwords hashed with PBKDF2-SHA256

## Performance Notes

- Monthly calculations done on-demand (not pre-computed)
- Filters sessions from past 30 days server-side
- Pagination available for large datasets (future)
- Client-side display optimized with grid layouts
