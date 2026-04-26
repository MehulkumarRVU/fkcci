# Admin Link - Complete Test Guide

## Changes Made

✅ **Updated auth.js** - Now has coach signup support with account type selector  
✅ **Updated login.html** - Added account type selector (Athlete/Coach)  
✅ **Updated dashboard.html, profile.html, session.html, session-live.html** - Admin link detection now with logging  
✅ **Fixed ForeignKey import** in athlete.py  

## How to Test Admin Link NOW

### Method 1: Create New Coach Account (Recommended)

1. **Go to:** http://localhost:3000/pages/login.html

2. **Click "Sign up" link**

3. **Select Account Type:**
   - Choose `🏋️ Coach` from the dropdown (NOT Athlete)
   - Notice the sport/skill fields DISAPPEAR

4. **Fill in Coach Registration:**
   ```
   Email: mycoach@example.com
   Username: mycoach
   Password: CoachPass123
   ```

5. **Click "Create Account"**

6. **Auto-redirects to login**
   - Login with: `mycoach` / `CoachPass123`

7. **You'll see navbar with "Coach Analytics" link!**

### Method 2: Use Existing Test Coach

Already created coaches:
- **Username:** `testcoach`
- **Password:** `secret123`

### Method 3: Using API (For Testing)

```bash
curl -X POST http://localhost:8080/api/auth/signup-coach \
  -H "Content-Type: application/json" \
  -d '{
    "email": "quickcoach@example.com",
    "username": "quickcoach",
    "password": "test123"
  }'
```

Then login with `quickcoach` / `test123`

## Where the Admin Link Appears

After login as coach, you'll see it in the navbar:

```
Dashboard | Start Session | **Coach Analytics** | Profile | Logout
                                 ↑
                          Click this as coach
```

It appears on all pages:
- ✓ Dashboard
- ✓ Profile  
- ✓ Session Setup
- ✓ Live Session

## What "Coach Analytics" Does

Clicking on "Coach Analytics" takes you to admin.html which shows:

1. **Summary Cards** - Total athletes, sessions, performance, top performer
2. **Athletes Grid** - List of coaching athletes
3. **Top Performers** - Ranked athletes by performance
4. **Detailed Reports** - Click any athlete for:
   - Monthly performance metrics
   - Recent sessions with scores
   - AI coaching recommendations

## Debugging if You Don't See It

### Check 1: Are you logged in as a coach?

Open browser console (F12) and paste:
```javascript
JSON.parse(localStorage.getItem('athlete')).role
```

Expected output: `"coach"`

### Check 2: Check all athlete data

```javascript
JSON.parse(localStorage.getItem('athlete'))
```

Should show:
```json
{
  "id": 12,
  "username": "testcoach",
  "role": "coach",
  ...
}
```

### Check 3: Check if element exists and is being shown

```javascript
// See all console messages about admin link
const adminLink = document.getElementById('adminLink');
console.log('Admin link found:', !!adminLink);
console.log('Display:', adminLink?.style.display);
```

### Check 4: Manually toggle visibility

Try this in console to manually show it:
```javascript
document.getElementById('adminLink').style.display = 'block';
```

If this works, the element exists and CSS is fine - the script just needs to run.

## Test Checklist

- [ ] Account type selector appears on signup form
- [ ] When "Coach" selected, sport fields disappear  
- [ ] Can create coach account successfully
- [ ] Login redirects to dashboard
- [ ] "Coach Analytics" link visible in navbar
- [ ] Can click "Coach Analytics" link
- [ ] admin.html page loads with coaches dashboard
- [ ] Can see summary cards with athlete data
- [ ] Can view detailed athlete reports

## Common Issues Fixed

| Issue | Status | Fix |
|-------|--------|-----|
| ForeignKey import missing | ✅ FIXED | Added to athlete.py imports |
| Role not being set | ✅ VERIFIED | Confirmed in backend test |
| Admin link broken | ✅ IMPROVED | Updated with better detection |
| No coach signup UI | ✅ ADDED | Account type selector on signup |
| Script timing issue | ✅ FIXED | Using DOMContentLoaded event |

## Questions?

What happens when you:
1. Go to sign up
2. Select "Coach" account type
3. Create coach account
4. Login
5. Check navbar

Let me know what you see!
