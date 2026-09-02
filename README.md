# 🎯 PocketCoach AI

**AI-Powered Real-Time Sports Technique Coach**

PocketCoach AI is an intelligent training system that uses device cameras and AI pose detection to provide real-time feedback for **Table Tennis 🏓**, **Boxing 🥊**, and a growing set of indoor sports. Perfect for beginners, intermediate, and advanced athletes looking to improve their technique, reaction time, and overall performance.

Phase 1 UI now includes indoor sports integration with enhanced dashboard, session setup, profile management, and live training flow.

---

## 🌟 Features

### 🎥 Real-Time AI Analysis
- Live pose detection using MediaPipe
- Instant technique feedback
- Joint angle calculations
- Movement tracking and scoring

### 📊 Performance Tracking
- Technique Accuracy Score (0-100)
- Reaction Speed Analysis
- Balance & Stability Metrics
- Overall Performance Rating

### � Supported Sports & Drills
PocketCoach AI supports a broad set of indoor sports and training categories. Detailed skill drills are currently seeded for Table Tennis, Boxing, and Badminton, while additional supported sports are available with baseline technique drills.

#### Sports with detailed drills
- **Table Tennis 🏓**
  - Forehand Drive
  - Backhand Drive
  - Topspin
  - Backspin
  - Serve Technique
  - Side Shuffle Footwork
  - Smash
- **Boxing 🥊**
  - Jab
  - Cross
  - Hook
  - Uppercut
  - Guard Position
  - Slip & Roll
  - Pivot Footwork
- **Badminton 🏸**
  - Serve Technique
  - Clear
  - Smash
  - Drop Shot
  - Net Play
  - Split Step Footwork

#### Additional supported sports
- Tennis 🎾
- Pickleball 🥎
- Squash 🏓
- Kickboxing 🥊
- Muay Thai 🦵
- Karate 🥋
- Taekwondo 🥋
- Judo 🥋
- Brazilian Jiu-Jitsu 🥋
- Wrestling 🤼
- Fencing 🤺
- Basketball 🏀
- Volleyball 🏐
- Handball 🤾
- Indoor Archery 🏹
- AI Gym Coach 🏋️
- Stretching 🤸
- Mobility Training 🦴
- Rehabilitation 🩺
- Home Workouts 🏠
- Calisthenics 💪

> For each additional supported sport, PocketCoach seeds a baseline drill named **Basic &lt;sport&gt; Technique** to provide a starting point for technique analysis and future drill expansion.

---

## 🏗️ Architecture

### Docker & Cloud Readiness
- Added `backend/Dockerfile` for containerized FastAPI deployment.
- Added `docker-compose.yml` with `backend`, `postgres`, `redis`, and `nginx` services.
- Added `.dockerignore` to reduce build context size.
- Added `nginx.conf` for reverse proxying frontend requests to the backend.

### Running with Docker
1. Copy `.env.example` to `.env` and set `SECRET_KEY`.
2. Start services:
   ```bash
   docker compose up --build
   ```
3. Backend API is available at `http://localhost:8080`.
4. Nginx reverse proxy is available at `http://localhost`.

### Environment variables
- `DATABASE_URL` can point to PostgreSQL using `postgresql+psycopg2://user:password@host:port/dbname`
- `REDIS_URL` enables Redis-backed rate limiting
- `CORS_ALLOWED_ORIGINS` controls allowed origins for the API

---

## 🏗️ Architecture

### Backend (FastAPI + Python)
- **Port:** 8080
- **Framework:** FastAPI
- **Database:** SQLite with SQLAlchemy ORM
- **Authentication:** JWT tokens (7-day expiry)
- **AI Analysis:** MediaPipe pose detection integration

### Frontend (HTML5/CSS3/JavaScript)
- **Port:** 3000 (recommended)
- **Technology:** Vanilla JavaScript, no frameworks
- **UI Components:** Responsive design with CSS Grid
- **Real-time Processing:** MediaPipe Pose in browser

---

## 📁 Project Structure

```
pocket-coach/
├── backend/
│   ├── main.py                    # FastAPI application entry point
│   ├── requirements.txt           # Python dependencies
│   ├── pocketcoach.db            # SQLite database (auto-generated)
│   └── app/
│       ├── database.py           # Database configuration
│       ├── models/
│       │   ├── athlete.py        # Athlete model
│       │   ├── session.py        # Training session model
│       │   └── skill.py          # Skill library model
│       ├── routes/
│       │   ├── auth.py           # Authentication endpoints
│       │   ├── sessions.py       # Session management
│       │   ├── skills.py         # Skill library endpoints
│       │   └── analysis.py       # AI analysis endpoints
│       └── utils/
│           └── sports_pose_analyzer.py  # Pose analysis logic
│
└── frontend/
    ├── index.html                # Landing page
    ├── integration-test.html     # Pose detection test page
    ├── css/
    │   └── styles.css            # Global styles
    ├── js/
    │   ├── app.js                # Main application logic
    │   ├── auth.js               # Authentication handling
    │   ├── session.js            # Live session management
    │   ├── pose-detection.js     # MediaPipe pose detection
    │   ├── sports-analyzer.js    # Client-side analysis
    │   └── profile.js            # Profile management
    └── pages/
        ├── login.html            # Login/Signup page
        ├── dashboard.html        # Athlete dashboard
        ├── session.html          # Live training session
        └── profile.html          # Profile management
```

---

## 🚀 Getting Started

### Prerequisites

## Development

- Backend: see `backend/`
- Frontend: see `frontend/`

Local dev (recommended):

1. Copy `.env.example` to `.env` and set `SECRET_KEY` to a secure random value.

2. Create and activate a virtualenv, then install deps:

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\Activate.ps1 on Windows
pip install -r backend/requirements.txt
pip install -r backend/dev-requirements.txt
```

3. Run the backend and tests (helper script starts server, waits for /health, runs pytest):

```bash
# Linux/macOS
bash backend/scripts/start_server_for_tests.sh &
python -m pytest -q

# Windows (PowerShell helper)
powershell -ExecutionPolicy Bypass -File backend/scripts/run_tests_with_server.ps1
```
- Python 3.8 or higher
- Modern web browser (Chrome, Firefox, Edge)
- Webcam access
- Internet connection (for MediaPipe CDN)

### Installation

#### 1. Clone or Download the Project
```bash
cd boxing
```

#### 2. Setup Backend

**Install Python dependencies:**
```bash
cd backend
pip install -r requirements.txt
```

**Run the backend server:**
```bash
python main.py
```

The backend will start on `http://localhost:8080`

**Seed the skills database (first time only):**
```bash
curl -X POST http://localhost:8080/api/skills/seed
```

Or visit: `http://localhost:8080/docs` and use the interactive API docs to call `/api/skills/seed`

#### 3. Setup Frontend

**Using Python's built-in HTTP server:**
```bash
cd frontend
python -m http.server 3000
```

**Or using Node.js http-server:**
```bash
npm install -g http-server
cd frontend
http-server -p 3000
```

**Or using VS Code Live Server:**
- Install the "Live Server" extension
- Right-click `index.html` and select "Open with Live Server"

The frontend will be available at `http://localhost:3000`

---

## 📖 Usage Guide

### 1. Create an Account
- Navigate to `http://localhost:3000`
- Click "Get Started" or "Login"
- Fill in the signup form:
  - Email and username
  - Password (minimum 6 characters)
  - Select your sport (Table Tennis or Boxing)
  - Choose your skill level
  - Add optional physical stats

### 2. Access Dashboard
- View your performance overview
- Check session statistics
- Browse available skills for your sport

### 3. Start Training Session
- Click "Start New Training Session"
- Select session type:
  - **Drill Practice:** Focused skill training
  - **Shadow Training:** Solo practice
  - **Sparring:** Partner practice
  - **Match Simulation:** Competitive practice
- Choose a skill to practice
- Click "Start Training Session"

### 4. Live Training
- Click "Start Camera" to enable webcam
- Position yourself so your full body is visible
- Perform the selected skill
- Watch real-time feedback on the right panel
- Monitor your live performance scores
- View technique tips and common mistakes

### 5. End Session
- Click "End Session" when done
- Review your session summary
- Check overall performance scores
- View detailed metrics

### 6. Track Progress
- Visit Dashboard to see:
  - Total sessions completed
  - Training minutes logged
  - Average performance scores
  - Recent session history

---

## 🗄️ Database Schema

### Athletes Table
- User authentication and profile
- Sport type and skill level
- Physical stats (height, weight)
- Performance rating
- Membership tier

### Sessions Table
- Training session records
- Performance scores
- Duration and timing
- Technique metrics
- Session data (JSON)

### Skills Table
- Sport-specific skills
- Technique tips
- Common mistakes
- Safety warnings
- Difficulty levels

---

## 🔐 API Endpoints

### Authentication
- `POST /api/auth/signup` - Create new athlete account
- `POST /api/auth/login` - Login and get JWT token
- `GET /api/auth/me` - Get current athlete info
- `POST /api/auth/refresh` - Refresh JWT token

### Sessions
- `POST /api/sessions/` - Create new session
- `GET /api/sessions/` - Get athlete's sessions
- `GET /api/sessions/{id}` - Get specific session
- `PUT /api/sessions/{id}` - Update session
- `DELETE /api/sessions/{id}` - Delete session
- `GET /api/sessions/stats/summary` - Get statistics

### Skills
- `GET /api/skills/` - Get all skills (filtered by sport)
- `GET /api/skills/{id}` - Get specific skill
- `POST /api/skills/` - Create new skill (admin)
- `POST /api/skills/seed` - Initialize skill library

### Analysis
- `POST /api/analysis/analyze` - Analyze full session data
- `POST /api/analysis/realtime-feedback` - Get instant feedback

---

## 🧪 Testing

### Integration Test Page
Navigate to `http://localhost:3000/integration-test.html`

**Features:**
- Test camera and pose detection
- View landmark detection in real-time
- Monitor FPS and confidence scores
- Test local analysis algorithms
- Verify backend API connectivity
- View joint angles live
- Test different sports and skills

---

## 🎨 Customization

### Adding New Skills
Use the FastAPI docs at `http://localhost:8080/docs`:
1. Navigate to `/api/skills/` POST endpoint
2. Provide skill details:
   - name
   - sport_type
   - description
   - technique_tips
   - common_mistakes
   - difficulty_level

### Modifying Analysis Logic
Edit `backend/app/utils/sports_pose_analyzer.py`:
- Adjust angle thresholds
- Add new joint checks
- Customize feedback messages
- Implement sport-specific rules

---

## 🐛 Troubleshooting

### Backend won't start
- Check Python version: `python --version`
- Ensure all dependencies installed: `pip install -r requirements.txt`
- Check if port 8080 is available

### Camera not working
- Grant camera permissions in browser
- Check if other apps are using camera
- Try a different browser
- Ensure HTTPS or localhost (required for camera access)

### Frontend can't connect to backend
- Verify backend is running on port 8080
- Check browser console for CORS errors
- Ensure API_URL is correct in JS files

### Pose detection not working
- Check internet connection (MediaPipe loads from CDN)
- Ensure good lighting conditions
- Position full body in camera frame
- Try clearing browser cache

---

## 🔮 Future Enhancements

### High Priority
- [ ] Video recording and playback
- [ ] Slow-motion replay
- [ ] Ball tracking (Table Tennis)
- [ ] Punch speed estimation (Boxing)
- [ ] ML-based technique scoring
- [ ] Session replay system
- [ ] Advanced analytics dashboard

### Additional Features
- [ ] Multi-athlete comparison
- [ ] Coach mode with remote viewing
- [ ] Training programs and plans
- [ ] Social features and leaderboards
- [ ] Mobile app versions
- [ ] Virtual sparring partner
- [ ] AR overlay improvements

---

## 📄 License

This project is provided as-is for educational and training purposes.

---

## 👥 Support

For issues, questions, or contributions:
- Check the integration test page first
- Review API documentation at `/docs`
- Ensure all dependencies are installed
- Verify camera permissions

---

## 🎯 Project Identity

**PocketCoach AI**
*Empowering athletes with intelligent, real-time technique coaching*

Focused on **Table Tennis** and **Boxing** performance optimization using cutting-edge AI technology.

---

**Built with ❤️ for athletes who want to train smarter, not just harder.**
