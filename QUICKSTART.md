### Rate Limiting (optional)

The backend includes a rate-limiting middleware. You can tune it via environment variables:

```
RATE_LIMIT_REQUESTS=60
RATE_LIMIT_WINDOW_SECONDS=60
REDIS_URL=redis://localhost:6379/0   # optional: use Redis for distributed limits
```

If `REDIS_URL` is not set or Redis isn't available, an in-memory limiter is used (single-process only).

# 🚀 Quick Start Guide - PocketCoach AI

## Complete Setup & Running Instructions

---

## ✨ What You'll Get

After following this guide, you'll have:
- ✅ Backend API running on http://localhost:8080
- ✅ Frontend running on http://localhost:3000
- ✅ Database seeded with 15 sports skills
- ✅ Ready to create athlete accounts
- ✅ Live AI training sessions active

**Total setup time:** ~5 minutes

---

## 🎯 System Requirements

- **Python 3.8+** - Check: `python --version`
- **Modern browser** - Chrome, Firefox, or Edge (latest versions)
- **Webcam** - For pose detection
- **Internet connection** - For MediaPipe models (first load)
- **Ports available** - 8080 (backend) and 3000 (frontend)

---

## 🚀 Step-by-Step Setup

### Step 1: Activate Virtual Environment

**Windows (PowerShell):**
```powershell
cd C:\Users\[YourUsername]\OneDrive\Desktop\boxing
.\.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
cd C:\Users\[YourUsername]\OneDrive\Desktop\boxing
.venv\Scripts\activate.bat
```

**macOS/Linux:**
```bash
cd ~/Desktop/boxing
source .venv/bin/activate
```

### Step 2: Start Backend Server

In your terminal (with venv activated):
```bash
python backend\main.py
```

**Expected Output:**
```
INFO:     Application startup complete
✅ Database initialized successfully
🚀 PocketCoach AI backend is running on http://localhost:8080
```

**Keep this terminal open!** Backend is now running.

### Step 3: Start Frontend Server

**Open a NEW terminal** and run:

**Windows (PowerShell):**
```powershell
cd C:\Users\[YourUsername]\OneDrive\Desktop\boxing
.\.venv\Scripts\Activate.ps1
cd frontend
python -m http.server 3000
```

**macOS/Linux:**
```bash
cd ~/Desktop/boxing
source .venv/bin/activate
cd frontend
python -m http.server 3000
```

**Expected Output:**
```
Serving HTTP on 0.0.0.0 port 3000 (http://0.0.0.0:3000/)
```

**Keep this terminal open!** Frontend is now serving.

### Step 4: Seed the Skills Database

**Open a THIRD terminal** and run:

```bash
# cd to project root first
cd C:\Users\[YourUsername]\OneDrive\Desktop\boxing

# Activate venv
.\.venv\Scripts\Activate.ps1  # Windows PowerShell
# OR
source .venv/bin/activate    # macOS/Linux

# Seed the database
python -c "import requests; requests.post('http://localhost:8080/api/skills/seed')"
```

**Or use curl:**
```bash
curl -X POST http://localhost:8080/api/skills/seed
```

**Or visit in browser:**
- Go to: http://localhost:8080/docs
- Find `/api/skills/seed` endpoint
- Click "Try it out" → "Execute"

**Expected Response:**
```json
{
  "message": "Skills seeded successfully",
  "table_tennis_skills": 7,
  "boxing_skills": 8,
  "total_skills": 15
}
```

---

## ✅ Verify Everything is Working

### Check Backend Health
```bash
curl http://localhost:8080/health
```

Expected response:
```json
{"status":"healthy","service":"PocketCoach AI Backend","port":8080}
```

### Check Frontend
Open browser: http://localhost:3000

You should see the landing page with:
- PocketCoach AI title
- Sport selection cards (Table Tennis & Boxing)
- "Get Started" button

### Check API Documentation
Open browser: http://localhost:8080/docs

You should see the interactive API documentation with all endpoints listed.

---

## 🎮 Using PocketCoach AI

### 1. Create Your First Account

1. Go to http://localhost:3000
2. Click "Get Started" or "Login" → "Sign Up"
3. Fill in the form:
   ```
   Email: test@example.com
   Username: testathlete
   Password: Test@123
   Sport: Box Boxing (or Table Tennis)
   Skill Level: Beginner
   Dominant Hand: Right
   Height: 180 (optional)
   Weight: 75 (optional)
   ```
4. Click "Create Account"
5. Login with your credentials

### 2. View Dashboard

After login, you'll see:
- Welcome message
- Performance overview
- Training statistics
- Available skills for your sport
- Recent sessions

### 3. Start Your First Training Session

1. Click "Start New Training Session"
2. Select:
   - **Session Type:** Drill Practice (best for beginners)
   - **Skill:** Jab (for boxing) or Forehand Drive (for table tennis)
3. Click "Start Training Session"
4. Review the technique tips on the right

### 4. Enable Camera & Train

1. Click "Start Camera"
2. Allow browser to access your camera
3. Position yourself so your full body is visible
4. Perform the movement (Jab, punch, forehand drive, etc.)
5. Watch the real-time feedback on the right

**What you'll see:**
- ✅ Green feedback = Good technique
- ⚠️ Yellow feedback = Needs improvement
- ❌ Red feedback = Incorrect form
- Live performance score (0-100)
- Technique, reaction, and balance scores

### 5. End Session

1. Click "End Session"
2. Review your session summary
3. See your performance scores
4. Option to start new session or return to dashboard

### 6. Check Progress

1. Go to Dashboard
2. Check statistics:
   - Total sessions completed
   - Total training minutes
   - Average performance score
   - Recent session history

---

## 🧪 Test the System

### Integration Test Page

Want to test pose detection? Go to:
```
http://localhost:3000/integration-test.html
```

Here you can:
- ✅ Test camera and pose detection
- ✅ View live joint angles
- ✅ Monitor FPS (frames per second)
- ✅ See landmark confidence
- ✅ Test different sports and skills
- ✅ Verify all systems working

---

## 🎯 Sports & Skills Available

### Table Tennis 🏓
- Forehand Drive
- Backhand Drive
- Topspin
- Backspin
- Serve Technique
- Side Shuffle Footwork
- Smash

### Boxing 🥊
- Jab
- Cross
- Hook
- Uppercut
- Guard Position
- Slip & Roll
- Pivot Footwork
- Combination Drills

---

## 🛠️ Using Startup Scripts (Alternative)

Instead of manual terminal commands, you can use the startup scripts:

### Windows

**Start Backend:**
- Double-click: `start-backend.bat`
- A terminal will open and show when ready

**Start Frontend:**
- Double-click: `start-frontend.bat`
- Another terminal will open

### Linux/Mac

**Make scripts executable (first time only):**
```bash
chmod +x start-backend.sh start-frontend.sh
```

**Start Backend:**
```bash
./start-backend.sh
```

**Start Frontend (in new terminal):**
```bash
./start-frontend.sh
```

---

## 🔧 Troubleshooting

### Problem: Backend won't start - "Module not found"
**Solution:**
```bash
# Ensure venv is activated
.\.venv\Scripts\Activate.ps1  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Problem: Backend is already running
**Solution:**
- Check if port 8080 is in use
- Kill existing process or use different port
- Edit `backend/main.py` line: `uvicorn.run(...port=8080)`

### Problem: Frontend won't connect to backend
**Solution:**
- Verify backend is running: http://localhost:8080/health
- Check browser console for errors (F12)
- Ensure API_URL in JS files is correct
- Check CORS settings in backend

### Problem: Camera not working
**Solution:**
- Grant browser camera permissions
- Use HTTPS or localhost (security requirement)
- Try a different browser
- Check if another app is using camera
- Ensure good lighting

### Problem: Can't create account
**Solution:**
- Check internet connection
- Verify backend is running
- Check browser console for errors
- Ensure email is valid format
- Try different username

### Problem: Pose detection not working
**Solution:**
- Check internet (MediaPipe loads from CDN)
- Ensure full body is visible in frame
- Try good lighting conditions
- Clear browser cache (Ctrl+Shift+Delete)
- Try pose test page: http://localhost:3000/integration-test.html

---

## 📊 API Testing

### Using Swagger UI (Recommended)
1. Go to: http://localhost:8080/docs
2. Try any endpoint interactively
3. See request/response formats

### Using Curl

**Create account:**
```bash
curl -X POST http://localhost:8080/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@test.com",
    "username": "test",
    "password": "test123",
    "sport_type": "boxing"
  }'
```

**Login:**
```bash
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test&password=test123"
```

**Get user info (with token):**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  http://localhost:8080/api/auth/me
```

---

## 🎓 Learning Paths

### For Beginners
1. Create account (Table Tennis or Boxing)
2. Choose "Beginner" skill level
3. Start with basic skills (Forehand Drive / Jab)
4. Practice 3-5 times
5. Check progress on dashboard

### For Intermediate Athletes
1. Choose "Intermediate" skills
2. Practice complex movements
3. Focus on technique accuracy
4. Monitor performance trends

### For Advanced Athletes
1. Use "Advanced" skills
2. Try combination drills
3. Compete with yourself
4. Aim for 95+ performance scores

---

## 📱 Supported Platforms

- ✅ Windows 10/11 (Python 3.8+)
- ✅ macOS 10.14+ (Python 3.8+)
- ✅ Linux (Ubuntu 18.04+, Python 3.8+)
- ✅ Browsers: Chrome, Firefox, Edge, Safari

---

## 🔐 Security Notes

- **JWT access token:** 15-minute expiration; refresh tokens rotate on renewal
- **Password:** Hashed with bcrypt
- **Database:** SQLite (no external dependencies)
- **CORS:** Public access for development
- **In Production:** Change SECRET_KEY and configure CORS

**How to set `SECRET_KEY`**

Create a `.env` file in the project root or set environment variables in your deployment environment. Example `.env` contents:

```
SECRET_KEY=your-very-long-random-secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
DATABASE_URL=sqlite:///./pocketcoach.db
```

On Windows PowerShell you can set it for the current session before starting the backend:

```powershell
$env:SECRET_KEY = 'your-very-long-random-secret'
python backend\main.py
```

---

## 📚 Next Steps

1. ✅ **Understand the system:** Review all features
2. ✅ **Create test accounts:** Try different sports
3. ✅ **Train with different skills:** Practice each movement
4. ✅ **Check statistics:** Monitor your progress
5. ✅ **Review code:** Learn how it works
6. ✅ **Customize:** Modify skills and feedback

---

## 🆘 Getting Help

1. **Check API Docs:** http://localhost:8080/docs
2. **View Logs:** Check terminal output
3. **Test Integration:** http://localhost:3000/integration-test.html
4. **Browse Console:** Press F12 in browser
5. **Read README:** Full documentation in README.md

---

## 🎉 You're All Set!

Your PocketCoach AI system is ready!

**Start training and improve your technique with AI-powered feedback!**

```
Frontend:  http://localhost:3000
Backend:   http://localhost:8080
API Docs:  http://localhost:8080/docs
Test Page: http://localhost:3000/integration-test.html
```

Happy training! 🏋️🎯

---

**Need more help? Check PROJECT_COMPLETION_SUMMARY.md for detailed information.**

## URLs Summary

| Service | URL |
|---------|-----|
| **Backend API** | http://localhost:8080 |
| **API Docs** | http://localhost:8080/docs |
| **Frontend Home** | http://localhost:3000 |
| **Login Page** | http://localhost:3000/pages/login.html |
| **Dashboard** | http://localhost:3000/pages/dashboard.html |
| **Training Session** | http://localhost:3000/pages/session.html |
| **Profile** | http://localhost:3000/pages/profile.html |
| **Integration Test** | http://localhost:3000/integration-test.html |

---

## Default Test Account
You can create your own account or use these test credentials after creating them:

```
Username: testathlete
Password: password123
Sport: Boxing or Table Tennis
```

---

## Tips for Best Experience

1. **Good Lighting:** Ensure your training area is well-lit
2. **Camera Position:** Full body should be visible in frame
3. **Clear Space:** Have enough room to move freely
4. **Stable Connection:** Keep backend running during sessions
5. **Browser Choice:** Chrome or Edge recommended for best MediaPipe performance

---

## Next Steps

1. ✅ Start both backend and frontend
2. ✅ Seed the skills database
3. ✅ Create an account
4. ✅ Run integration test
5. ✅ Start your first training session!

Happy training! 🥊🏓
