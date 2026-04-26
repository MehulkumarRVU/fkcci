# 👨‍💻 Developer Guide - PocketCoach AI

Quick reference for developers working with PocketCoach AI.

---

## 📁 File Organization

### Backend Routes
```
backend/app/routes/
├── auth.py          - /api/auth/login, /api/auth/signup, /api/auth/me
├── sessions.py      - /api/sessions/* endpoints for session management
├── skills.py        - /api/skills/* endpoints for skill library
└── analysis.py      - /api/analysis/* endpoints for AI feedback
```

### Frontend Pages
```
frontend/pages/
├── login.html       - Authentication (login/signup form)
├── dashboard.html   - Main dashboard with stats and recent sessions
├── session.html     - Live training session with camera and feedback
└── profile.html     - User profile and settings management
```

### Frontend Scripts
```
frontend/js/
├── app.js           - Global helpers and main logic (83 lines)
├── auth.js          - Login/signup handling (~120 lines)
├── session.js       - Live session management (325+ lines)
├── pose-detection.js - MediaPipe integration (320+ lines)
├── sports-analyzer.js - Client analysis engine (300+ lines)
└── profile.js       - Profile updates (200+ lines)
```

---

## 🔌 API Endpoints Cheat Sheet

### Authentication
```
POST   /api/auth/signup          - Create account
POST   /api/auth/login           - Login (returns JWT token)
GET    /api/auth/me              - Get current user (requires token)
POST   /api/auth/refresh         - Refresh token (requires token)
```

### Sessions
```
POST   /api/sessions/             - Create new session
GET    /api/sessions/             - List user sessions
GET    /api/sessions/{id}         - Get session details
PUT    /api/sessions/{id}         - Update session with scores
DELETE /api/sessions/{id}         - Delete session
GET    /api/sessions/stats/summary - Get user statistics
```

### Skills
```
GET    /api/skills/               - List skills (filter by sport_type, difficulty_level)
GET    /api/skills/{id}           - Get skill details
POST   /api/skills/               - Create new skill
POST   /api/skills/seed           - Initialize database with 15 skills
```

### Analysis
```
POST   /api/analysis/analyze           - Analyze session data
POST   /api/analysis/realtime-feedback - Get instant feedback on pose
```

---

## 🔑 Key Constants & Variables

### Sports Types
```javascript
"table_tennis"  - Table Tennis
"boxing"        - Boxing
```

### Skill Levels
```javascript
"beginner"      - Beginner level
"intermediate"  - Intermediate level
"advanced"      - Advanced level
```

### Session Types
```javascript
"drill"                - Focused practice
"shadow"               - Solo shadow boxing/practice
"sparring"             - Partner practice
"match_simulation"     - Competitive practice
```

### Score Thresholds
```javascript
90+  - Excellent (GREEN)
75+  - Good (BLUE)
60+  - Average (YELLOW)
<60  - Poor (RED)
```

---

## 🔐 Authentication Flow

### Login Process
```
1. User enters username/password
2. POST to /api/auth/login
3. Backend verifies password (bcrypt)
4. Returns JWT token
5. Client stores token in localStorage
6. All future requests include: Authorization: Bearer {token}
```

### Protected Routes
Token required for:
- GET /api/auth/me
- POST /api/sessions/*
- GET /api/sessions/*
- DELETE /api/sessions/*
- PUT /api/sessions/*
- POST /api/analysis/*

---

## 📊 Database Models

### Athletes
```python
id, email, username, hashed_password, sport_type, skill_level,
dominant_hand, height, weight, training_frequency_per_week,
membership_tier, total_sessions, performance_rating, is_active,
created_at, updated_at
```

### Sessions
```python
id, athlete_id, sport_type, session_type, start_time, end_time,
duration_minutes, is_completed, performance_score, technique_accuracy,
reaction_score, balance_score, session_data, created_at
```

### Skills
```python
id, name, sport_type, description, technique_tips, common_mistakes,
safety_warning, difficulty_level, primary_focus, is_active,
created_at, updated_at
```

---

## 🧪 Common Development Tasks

### Adding a New Skill
```python
# In skills.py - POST /api/skills/
curl -X POST http://localhost:8080/api/skills/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Backhand Loop",
    "sport_type": "table_tennis",
    "description": "Offensive backhand stroke",
    "difficulty_level": "advanced",
    "primary_focus": "power"
  }'
```

### Modifying Pose Analysis
Edit: `backend/app/utils/sports_pose_analyzer.py`
- `analyze_table_tennis()` - Table Tennis analysis logic
- `analyze_boxing()` - Boxing analysis logic
- Adjust angles, thresholds, feedback messages

### Adding Feedback Message
In `sports_pose_analyzer.py`:
```python
feedback.append("✅ Good form!")  # Success
feedback.append("⚠️ Adjust position")  # Warning
feedback.append("❌ Incorrect angle")  # Error
```

### Changing Analysis Threshold
```python
# Example: Change elbow angle requirement
if 130 <= arm_angle <= 170:  # Current threshold
    feedback.append("✅ Good arm extension.")
else:
    feedback.append("❌ Elbow not properly extended.")
```

---

## 🔄 Data Flow

### Training Session Flow
```
1. User clicks "Start Session"
2. Frontend POST /api/sessions/ → Creates session
3. User clicks "Start Camera"
4. MediaPipe detects pose in real-time
5. Every 30 frames: POST /api/analysis/realtime-feedback
6. Backend analyzes landmarks → Returns score + feedback
7. Frontend displays score + feedback live
8. User clicks "End Session"
9. Frontend PUT /api/sessions/{id} with final scores
10. Backend updates athlete stats
11. Frontend displays session summary
```

---

## 🎨 Frontend Architecture

### State Management (localStorage)
```javascript
localStorage.getItem('token')          // JWT token
localStorage.getItem('athlete')        // Current athlete data
localStorage.getItem('currentSession') // Active session (optional)
```

### Class-Based Organization
```javascript
// PoseDetector class - Handles MediaPipe
- initialize()
- startCamera()
- stopCamera()
- detectFrame()
- onResults()
- drawLandmarks()

// SportsAnalyzer class - Client-side analysis
- analyzeLocally()
- calculateAngle()
- addFeedback()
- getAverageScore()
- formatFeedback()
```

---

## 🐛 Common Issues & Solutions

### Issue: CORS Error
**Solution:** Backend has CORS enabled for all origins in development
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue: Token Expired
**Solution:** Call `/api/auth/refresh` with current token
```bash
curl -H "Authorization: Bearer {token}" \
  http://localhost:8080/api/auth/refresh
```

### Issue: Pose Detection Slow
**Solution:** Check FPS counter in integration test page
- FPS < 20: Reduce video resolution or increase detection interval
- FPS > 30: Good performance

### Issue: Wrong Scores
**Solution:** Check calculation in `sports_pose_analyzer.py`
- Review joint angles
- Check threshold values
- Analyze feedback logic

---

## 📝 Code Style Guide

### Python (Backend)
- Use type hints: `def func(param: str) -> int:`
- Follow PEP 8 conventions
- Add docstrings to functions
- Use descriptive variable names

### JavaScript (Frontend)
- Use camelCase for variables: `const myVariable = value;`
- Use const/let (no var)
- Add comments for complex logic
- Use arrow functions: `() => {}`

### HTML/CSS
- Use semantic HTML5 elements
- Follow BEM naming for classes: `.block__element--modifier`
- Use CSS variables for colors
- Mobile-first responsive design

---

## 🚀 Deployment Checklist

Before deploying to production:

- [ ] Change SECRET_KEY in `backend/app/routes/auth.py`
- [ ] Set DEBUG=False in FastAPI
- [ ] Configure CORS for specific domains only
- [ ] Use environment variables for configuration
- [ ] Switch from SQLite to PostgreSQL
- [ ] Enable HTTPS/SSL
- [ ] Set up proper logging
- [ ] Configure database backups
- [ ] Set up monitoring and alerts
- [ ] Create admin user account
- [ ] Test with production data
- [ ] Document secrets and credentials

---

## 📚 Dependencies Reference

### Backend
```python
fastapi>=0.115.0           # Web framework
sqlalchemy>=2.0.36         # ORM
pydantic>=2.10.5           # Data validation
mediapipe>=0.10.20         # Pose detection
opencv-python>=4.10.0      # Computer vision
python-jose>=3.3.0         # JWT tokens
passlib>=1.7.4             # Password hashing
```

### Frontend
```
@mediapipe/pose            # CDN-based pose detection
CSS3 (Grid, Flexbox)       # Layout
HTML5                      # Markup
Vanilla JavaScript         # No framework needed
```

---

## 🧪 Testing

### Test Backend Endpoint
```bash
# Create account
curl -X POST http://localhost:8080/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","username":"test","password":"test123","sport_type":"boxing"}'

# Get all skills
curl http://localhost:8080/api/skills/

# Get API docs
open http://localhost:8080/docs
```

### Test Frontend
- Open browser DevTools (F12)
- Check Console tab for errors
- Check Network tab for API calls
- Use Integration Test page: http://localhost:3000/integration-test.html

---

## 🎓 Learning Resources

### Understanding the Code
1. Start with `main.py` - See app initialization
2. Review `routes/auth.py` - Understand authentication
3. Study `models/` - Database structure
4. Examine `utils/sports_pose_analyzer.py` - Core analysis logic
5. Read `frontend/js/session.js` - Live session flow

### External Resources
- FastAPI Docs: https://fastapi.tiangolo.com/
- MediaPipe Pose: https://mediapipe.dev/
- SQLAlchemy ORM: https://www.sqlalchemy.org/
- Pydantic: https://docs.pydantic.dev/

---

## 🤝 Contributing

### Code Review Checklist
- [ ] Code follows style guide
- [ ] No hardcoded values
- [ ] Error handling implemented
- [ ] Comments for complex logic
- [ ] Tested on multiple browsers (frontend)
- [ ] Verified with API docs (backend)
- [ ] No console errors or warnings

---

## 📞 Support

For technical issues:
1. Check Django logs in terminal
2. Review browser console (F12)
3. Check API docs at /docs
4. Verify database is initialized
5. Restart both servers

---

**Happy coding! 🚀**
