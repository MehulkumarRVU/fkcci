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
PocketCoach AI currently exposes exactly nine active training categories. Historical records from retired categories remain readable, but retired categories cannot be selected for new accounts, sessions, skills, or analysis requests.

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

#### Additional active categories
- **Gym 🏋️**
- Stretching 🤸
- Mobility Training 🦴
- Rehabilitation 🩺
- Home Workouts 🏠
- Calisthenics 💪

## Adaptive Training and ParaSports Support

Adaptive Training is an optional mode inside the existing nine categories; it
does not add a tenth category. Athletes can save a non-medical profile with a
preferred standing, seated, or wheelchair-based setup, camera orientation,
equipment notes, accessibility preferences, and an approved movement reference.
Profiles can be edited or removed through the authenticated adaptive profile
API.

The current implemented foundation provides:

- Exercise-specific required-landmark gating for seated and standing
  upper-body movements.
- Configurable references and angle-based personalized scoring for adaptive
  reach, punch, and racket-arm exercises.
- Front/side camera guidance, explicit insufficient-evidence and ambiguous
  observation statuses, and session persistence of adaptive setup metadata.
- Keyboard-label-compatible setup controls and text status guidance in the
  training workflow.

Adaptive catalog routes:

- `GET /api/adaptive/catalog?category=table_tennis`
- `GET`, `PUT`, and `DELETE /api/adaptive/profile`
- `GET /api/adaptive/capabilities`

Signup and profile integration:

- Signup offers Standard Training or Adaptive Training and stores only the
  selected setup/preferences; no diagnosis or disability disclosure is
  required.
- Profile settings can be enabled, disabled without deleting them, cancelled,
  reloaded after login, or explicitly removed.
- If a later profile save fails, the account remains usable and standard
  training is unaffected; the profile page reports that the save can be
  retried.

Verification:

```powershell
& 'C:\Users\isha1\AppData\Local\Programs\Python\Python312\python.exe' -m pytest backend/tests
& 'C:\Users\isha1\AppData\Local\Programs\Python\Python312\python.exe' -m compileall -q backend
& 'C:\Users\isha1\AppData\Local\Programs\Python\Python312\python.exe' -m pip check
```

Frontend JavaScript syntax was verified with Node.js 26.13.0:

```powershell
Get-ChildItem frontend -Recurse -Filter *.js |
  ForEach-Object { & 'C:\Program Files\nodejs\node.exe' --check $_.FullName }
```

The repository has no `package.json` or configured frontend build/lint runner,
so no npm build or lint command is available. Browser smoke testing covered
signup category selection, adaptive signup preferences, authenticated profile
persistence, and adaptive session exercise/camera guidance. A full WCAG audit
was not performed. The premium responsive layout was checked in a browser at
320, 375, 390, 430, 768, 820, 1024, 1280, 1440, and 1920 CSS-pixel widths;
the tested pages had no horizontal overflow. Physical iPhone, iPad, Android
phone, and Android tablet validation was not performed because no reachable
physical device was available.

This foundation is implemented and covered by automated tests, but it is not
clinical validation and does not infer a disability, diagnosis, impairment, or
Paralympic eligibility. Para Table Tennis and Para-Badminton stroke/contact
recognition, wheelchair-specific movement validation, expert agreement,
validated athlete baselines, and depth-dependent analysis remain planned until
consented athlete/coach data and suitable camera validation are available.
Rehabilitation restrictions and targets should be supplied or approved by a
qualified healthcare professional where clinically necessary. The system does
not diagnose, prescribe treatment, assess injury severity, or determine return
to sport.

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
4. Nginx serves the frontend and reverse-proxies `/api` at `http://localhost`.

### Environment variables
- `DATABASE_URL` can point to PostgreSQL using `postgresql+psycopg2://user:password@host:port/dbname`
- `REDIS_URL` enables Redis-backed rate limiting
- `CORS_ALLOWED_ORIGINS` controls allowed origins for the API
- `ENV=production` requires an explicit 32-character `SECRET_KEY` and explicit
  non-wildcard CORS origins.
- `FRONTEND_BASE_URL` must be the public HTTPS frontend URL for password-reset
  links.

The frontend uses the local API on ports 3000/5500 during development and
automatically uses same-origin `/api` requests behind nginx. Set
`window.POCKETCOACH_API_URL` before the frontend scripts load only when the API
is hosted at a separate public origin.

### Controlled deployment requirements

- Serve camera pages from HTTPS (or localhost during development); browsers
  block camera access from insecure origins.
- Use a managed PostgreSQL and Redis service in production rather than the
  development SQLite/default container credentials.
- Replace all example credentials in `.env`, restrict `CORS_ALLOWED_ORIGINS`
  to the real frontend origin, and terminate TLS at the reverse proxy.
- Run database initialization/migrations before accepting traffic. The
  application initializes compatibility columns at startup, while the SQL
  migration files remain the source of truth for existing deployments.
- The repository does not include a production CI/CD deployment or a physical
  device test harness. Android Chrome, iPhone/iPad Safari, and camera behavior
  on real hardware remain manual release-gate checks.

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
