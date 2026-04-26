# Admin Link Not Showing - Debugging Guide

## Step 1: Verify You're Logged In As A Coach

### Option A: Create and Login as a New Coach
```
URL: http://localhost:3000/pages/login.html

On the login page:
- Click "Sign up" link
- Enter coach credentials:
  - Email: mycoach@example.com
  - Username: mycoach  
  - Password: pass123
- Select any sport (Boxing or Table Tennis)
- Click "Sign Up"
- Login with mycoach / pass123
```

### Option B: Use Test Coach Account
We already created a coach account. Try logging in with:
- **Username:** `testcoach`
- **Password:** `secret123`

## Step 2: Check Browser Console (F12)

1. **Open DevTools:** Press `F12` or right-click → "Inspect"
2. **Go to Console tab**
3. **Paste this command:**
```javascript
JSON.parse(localStorage.getItem('athlete')).role
```

### Expected Output:
- ✅ If you see `"coach"` → Admin link SHOULD appear
- ❌ If you see `"athlete"` → You're not logged in as a coach
- ❌ If you get an error → You're not logged in

## Step 3: Check localStorage Data

In the Console, paste:
```javascript
JSON.parse(localStorage.getItem('athlete'))
```

This will show all the athlete data. Look for:
```json
{
  "role": "coach",
  "username": "mycoach",
  ...
}
```

## Step 4: Navigate to Dashboard

1. Go to: http://localhost:3000/pages/dashboard.html
2. Look at the **navbar** (top of page)
3. You should see between "Start Session" and "Profile":

```
Dashboard | Start Session | Coach Analytics | Profile | Logout
                                ↑
                          Should appear for coaches
```

## Step 5: If "Coach Analytics" STILL Doesn't Show

Try these troubleshooting steps:

### A. Hard Refresh the Page
- Press `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)
- This clears browser cache

### B. Clear localStorage and Re-login
In Console, paste:
```javascript
localStorage.clear()
```
Then refresh and login again.

### C. Check the HTML
Right-click on the navbar → "Inspect Element" and look for:
```html
<li id="adminLink" style="display: none;">
  <a href="admin.html">Coach Analytics</a>
</li>
```

If you see `style="display: none;"` but it's NOT showing, the JavaScript isn't running.

### D. Check for JavaScript Errors
In Console, look for any **RED** error messages. 

If you see errors, provide them and I'll fix them immediately.

## Step 6: Verify Each Page

The admin link should appear on:
- ✓ Dashboard: http://localhost:3000/pages/dashboard.html
- ✓ Profile: http://localhost:3000/pages/profile.html
- ✓ Session Setup: http://localhost:3000/pages/session.html
- ✓ Live Session: http://localhost:3000/pages/session-live.html

## Quick Test Command

Copy and paste this entire block into the browser console:

```javascript
console.log('=== ADMIN LINK DEBUG ===');

// Check if logged in
const athlete = JSON.parse(localStorage.getItem('athlete') || 'null');
if (!athlete) {
    console.error('❌ NOT LOGGED IN');
} else {
    console.log('✅ Logged in as:', athlete.username);
    console.log('Role:', athlete.role);
    console.log('Is coach?', athlete.role === 'coach');
}

// Check if element exists
const adminLink = document.getElementById('adminLink');
if (adminLink) {
    console.log('✅ Admin link element found');
    console.log('Display style:', adminLink.style.display);
    console.log('Should show element...');
    adminLink.style.display = 'block';
    console.log('✅ Manually set display to block');
} else {
    console.error('❌ Admin link element NOT found on page');
}
```

## Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| "athlete is not defined" error | Not logged in | Login first |
| Role is "athlete" | Logged in as athlete, not coach | Login as coach |
| Element not found | Wrong page | Go to dashboard.html |
| Manually set to block works, but disappears on refresh | Script timing issue | Refresh page |

## If All Else Fails

1. Try a different browser or private/incognito mode
2. Check that backend is running: http://localhost:8080/docs
3. Ensure frontend is running: http://localhost:3000
4. Delete your browser's site data for localhost:3000 and re-login

## Questions?

What do you see when you:
1. Login as coach
2. Go to dashboard
3. Check console with: `JSON.parse(localStorage.getItem('athlete')).role`
