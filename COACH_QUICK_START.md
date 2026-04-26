# Coach Dashboard - Quick Start Guide

## How to Test the Coach Dashboard

### Step 1: Create a Coach Account

#### Option A: Via Frontend
1. Navigate to login page
2. Fill signup form with coach credentials:
   - Email: `coach@example.com`
   - Username: `coachuser`
   - Password: `secret123`
3. Select sport (doesn't matter for coach)
4. Click "Sign Up"

#### Option B: Via API
```bash
curl -X POST http://localhost:8080/api/auth/signup-coach \
  -H "Content-Type: application/json" \
  -d '{
    "email": "coach@example.com",
    "username": "coachuser",
    "password": "secret123"
  }'
```

### Step 2: Create an Athlete Account (to Manage)

1. Logout from coach account
2. Create a new athlete account:
   - Username: `athlete1`
   - Sport: `boxing`
   - Other details as desired
3. This athlete will appear in coach's dashboard once the coach-athlete relationship is set

**Note**: Currently, athletes are auto-assigned. In production, an admin system will allow coaches to explicitly assign athletes.

### Step 3: Access Coach Dashboard

1. **Login as Coach**
   - Username: `coachuser`
   - Password: `secret123`

2. **View Dashboard**
   - After login, you're on athlete dashboard
   - Look for "Coach Analytics" link in navbar (only visible for coaches)
   - Click to access coach dashboard

3. **Explore Features**
   - **Summary Cards**: Total athletes, sessions, performance, most active
   - **Athletes Grid**: List of athletes with summary stats
   - **Top Performers**: Ranked list of best athletes
   - **Detailed Reports**: Click "View Detailed Report" on any athlete

### Step 4: Generate Test Data

To see meaningful data in the coach dashboard:

1. **Create Multiple Athletes**
   - Create 2-3 more athlete accounts
   - Have them do different sports

2. **Run Training Sessions**
   - Login as each athlete
   - Start training sessions
   - Complete them with various performance scores

3. **View Coach Analytics**
   - Login as coach
   - Dashboard will populate with all data
   - Monthly stats will show aggregated performance

### Endpoint Testing

#### Get Coach Summary
```bash
curl -X GET http://localhost:8080/api/analytics/coach/summary \
  -H "Authorization: Bearer {COACH_TOKEN}"
```

#### Get Coached Athletes
```bash
curl -X GET http://localhost:8080/api/analytics/coach/athletes \
  -H "Authorization: Bearer {COACH_TOKEN}"
```

#### Get Athlete Monthly Report
```bash
curl -X GET http://localhost:8080/api/analytics/coach/athlete/1/monthly-report \
  -H "Authorization: Bearer {COACH_TOKEN}"
```

## URL Paths

- **Coach Dashboard**: `http://localhost:3000/pages/admin.html`
- **Main Dashboard**: `http://localhost:3000/pages/dashboard.html`
- **Login**: `http://localhost:3000/pages/login.html`

## What You'll See

### Summary Section
```
Total Athletes: 3
Sessions This Month: 15
Avg Performance: 78.5%
Most Active: john (8 sessions)
```

### Athletes Grid
Each athlete card shows:
- Username
- Email
- Skill Level
- Primary Sport
- Sports They Practice
- Join Date
- "View Detailed Report" button

### Detailed Report Modal
When clicked, shows:
- Athlete profile info
- This month's performance metrics
- Recent 10 training sessions with scores
- AI coaching feedback and recommendations

## Features Demonstrated

✅ Coach account creation  
✅ Role-based access control  
✅ Multi-sport athlete support  
✅ Monthly performance aggregation  
✅ Per-athlete detailed analytics  
✅ Session history tracking  
✅ AI coaching feedback  
✅ Responsive dashboard  
✅ Modal-based detailed views  
✅ Real-time data from backend  

## Troubleshooting

### "Coach Analytics" link doesn't appear?
- Make sure you're logged in as a coach (role='coach')
- Check browser console for any errors
- Verify token is valid in localStorage

### No athletes showing?
- Athletes must be created to appear
- Check if coach_id relationship is set correctly
- Current system auto-assigns; future version will have explicit assignment

### Statistics show 0?
- Athletes need to complete training sessions
- Month tracking is based on session start_time
- Allow 30 days for monthly calculations

### API errors?
- Verify backend is running on port 8080
- Check Authorization header has valid JWT token
- Ensure user role is 'coach'

## Next Steps

1. **Extend Coach Features**
   - Add athlete assignment interface
   - Create export/PDF reports
   - Add performance charts

2. **Athlete Features**
   - View coach-assigned feedback
   - Track progress vs coach goals

3. **Admin Panel**
   - Manage coach-athlete relationships
   - View all users and roles
