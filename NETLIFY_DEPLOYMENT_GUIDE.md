# Frontend Netlify Deployment Guide

## Problem
Frontend on Netlify showing "Failed to fetch" when trying to login.

## Root Cause
1. ❌ Jinja2 templates in `/templates` can't run on static Netlify
2. ❌ No proper static HTML frontend
3. ❌ No API client with correct BASE_URL
4. ❌ API_BASE_URL pointing to localhost instead of Render backend

## Solution

### Step 1: Static Frontend Files Created

The following files are now available in `/static/`:

#### Core API Client: `/static/js/api.js`
- ✅ Sets `API_BASE = "https://cgs-attendance-system.onrender.com"`
- ✅ Implements `login(username, password, role)`
- ✅ Handles retry logic for network failures
- ✅ Returns proper JSON responses
- ✅ Includes admin and employee endpoints

#### Auth Helper: `/static/js/auth.js`
- ✅ `isLoggedIn()` - Check if user authenticated
- ✅ `getCurrentUser()` - Get stored user data
- ✅ `requireAuth()` - Redirect to login if not authenticated
- ✅ `requireAdmin()` - Redirect to login if not admin
- ✅ `showError()` / `showSuccess()` - Display messages

#### Static Pages:

**1. `/static/login.html`**
- ✅ Pure HTML (no Jinja2)
- ✅ Employee and Admin login forms
- ✅ Uses `/js/api.js` for login API call
- ✅ Handles form submission with fetch()
- ✅ Stores user data in localStorage
- ✅ Redirects to dashboard on success

**2. `/static/dashboard.html`**
- ✅ Employee dashboard
- ✅ Shows user info from localStorage
- ✅ Test API buttons for debugging
- ✅ Protected by requireAuth()

**3. `/static/admin.html`**
- ✅ Admin dashboard
- ✅ Shows admin controls
- ✅ View employees, attendance, settings
- ✅ Protected by requireAdmin()

---

## Deployment Steps

### Step 1: Copy Static Files to Netlify

The following files need to be deployed to Netlify:

```
/static/
├── login.html
├── dashboard.html
├── admin.html
├── styles.css (already exists)
├── script.js (existing)
├── js/
│   ├── api.js (NEW)
│   ├── auth.js (NEW)
│   └── bootstrap.bundle.min.js (existing)
└── css/
    ├── all.min.css (existing)
    └── bootstrap.min.css (existing)
```

### Step 2: Update Netlify Site Build Configuration

**File**: `netlify.toml` (create if doesn't exist)

```toml
[build]
  # Static site - no build command needed
  publish = "static"

[[redirects]]
  from = "/"
  to = "/login.html"
  status = 200

[[redirects]]
  from = "/dashboard"
  to = "/dashboard.html"
  status = 200

[[redirects]]
  from = "/admin"
  to = "/admin.html"
  status = 200

# Redirect all unknown routes to login
[[redirects]]
  from = "/*"
  to = "/login.html"
  status = 200

[headers]
  [[headers.values]]
    key = "Cache-Control"
    value = "no-cache, no-store, must-revalidate"
  [[headers.values]]
    key = "X-Content-Type-Options"
    value = "nosniff"
```

### Step 3: Deploy to Netlify

**Option A: Using Netlify CLI**

```bash
# Install Netlify CLI if not installed
npm install -g netlify-cli

# Navigate to project directory
cd d:\Users\Pradeep\Downloads\cggs\CGS

# Deploy
netlify deploy --prod --dir=static
```

**Option B: Git Deployment**

```bash
cd d:\Users\Pradeep\Downloads\cggs\CGS

# Commit changes
git add static/
git add netlify.toml
git commit -m "Add: Static HTML frontend for Netlify deployment"

# Push to GitHub
git push origin main

# Netlify will auto-deploy from your connected GitHub repo
```

**Option C: Drag & Drop**

1. Go to https://app.netlify.com
2. Drag and drop the `/static` folder
3. Netlify will automatically deploy

---

## Testing the Deployment

### Test 1: Access Frontend

```bash
# Open in browser
https://cgs-attendance.netlify.app

# Expected: Login page appears
# Check browser console for "[API]" logs
```

### Test 2: Login with Test Credentials

```
Username: pradeep
Password: [your password]
Role: employee

OR

Username: admin
Password: [admin password]
Role: admin
```

### Test 3: Check Network Requests

1. Open DevTools (F12)
2. Go to Network tab
3. Click Login
4. Should see:
   - POST request to `https://cgs-attendance-system.onrender.com/login`
   - Status: 200 (if credentials correct)
   - Response: JSON with success=true

### Test 4: Browser Console Logs

Open browser console (F12 → Console) and look for:

```
✅ Good signs:
[API] Initializing API client with base URL: https://cgs-attendance-system.onrender.com
[API] POST https://cgs-attendance-system.onrender.com/login
[API] Response status: 200
[API] Login successful

❌ Bad signs:
Failed to fetch
cors error
Cannot reach backend
```

---

## Troubleshooting

### Issue: "Failed to fetch" on Login

**Check**:
1. ✅ Backend is running: `curl https://cgs-attendance-system.onrender.com/dashboard`
2. ✅ API_BASE is correct in `/static/js/api.js`
3. ✅ CORS headers enabled in Flask backend
4. ✅ Check browser Network tab for actual error

**Fix**:
```javascript
// In /static/js/api.js, verify:
const API_BASE = "https://cgs-attendance-system.onrender.com"; // ✅ CORRECT

// NOT:
const API_BASE = "http://localhost:5000"; // ❌ WRONG
const API_BASE = "http://127.0.0.1:5000"; // ❌ WRONG
```

### Issue: "Backend unreachable"

**Check**:
1. Backend Render URL: `https://cgs-attendance-system.onrender.com`
2. Can you access from browser? Test: `https://cgs-attendance-system.onrender.com/dashboard`

**Fix**: If backend URL is wrong, update in:
1. `/static/js/api.js` - Line 2: `const API_BASE = "..."`
2. Redeploy to Netlify

### Issue: "Unauthorized (401)" after Login

**Check**:
1. Credentials are correct
2. Database exists at `/attendance_system.db`
3. User exists in database

**Fix**:
```bash
# Check database
sqlite3 attendance_system.db "SELECT * FROM users LIMIT 5;"
```

### Issue: localStorage not persisting

**Check**:
1. Browser allows localStorage (not in private/incognito)
2. Netlify domain is allowed

**Fix**:
```javascript
// Verify in browser console:
localStorage.setItem("test", "value");
console.log(localStorage.getItem("test")); // Should print "value"
```

---

## File Structure After Deployment

```
Netlify Site (cgs-attendance.netlify.app)
├── login.html (entry point)
├── dashboard.html (employee page)
├── admin.html (admin page)
├── styles.css
├── script.js
├── js/
│   ├── api.js (API CLIENT)
│   ├── auth.js (AUTH HELPER)
│   └── bootstrap.bundle.min.js
└── css/
    ├── all.min.css
    └── bootstrap.min.css

Backend (cgs-attendance-system.onrender.com)
├── /login (POST) - returns JSON
├── /dashboard (GET) - returns JSON
├── /api/admin/* (all admin routes)
└── /api/employee/* (all employee routes)
```

---

## API Endpoint Mapping

### Frontend → Backend

```
Frontend Request          Backend Route         Response Format
================================================================================================

POST /login              → POST /login           {"success": true, "data": {...}}
GET  /dashboard          → GET /dashboard        {"success": true, "data": {...}}

GET  /api/admin/*        → GET /api/admin/*      {"success": true, "data": [...]}
POST /api/admin/*        → POST /api/admin/*     {"success": true, "message": "..."}
PUT  /api/admin/*        → PUT /api/admin/*      {"success": true, "message": "..."}
DELETE /api/admin/*      → DELETE /api/admin/*   {"success": true, "message": "..."}

GET  /api/employee/*     → GET /api/employee/*   {"success": true, "data": [...]}
POST /api/employee/*     → POST /api/employee/*  {"success": true, "message": "..."}
```

---

## CORS Configuration

**Backend** (`app.py` already configured):
```python
@app.after_request
def after_request(response):
    origin = request.headers.get('Origin')
    allowed_origins = [
        'https://cgs-attendance.netlify.app',  # ✅ Netlify
        'http://localhost:*'                    # ✅ Local dev
    ]
    if origin in allowed_origins or 'netlify.app' in origin:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
```

**Frontend** (`/static/js/api.js`):
```javascript
fetch(url, {
  method,
  credentials: "include",  // ✅ Include cookies
  headers: {
    "Content-Type": "application/json"
  }
})
```

---

## Security Notes

✅ **What's Secure**:
- Session cookies are HttpOnly (can't be accessed by JavaScript)
- Passwords hashed with werkzeug
- CSRF protection can be enabled

⚠️ **For Production**:
1. Enable `SESSION_COOKIE_SECURE = True` (requires HTTPS)
2. Change `SECRET_KEY` from "demo-secret-key-railway"
3. Enable CSRF protection: `WTF_CSRF_ENABLED = True`
4. Add rate limiting to login endpoint

---

## Deployment Checklist

- [ ] `/static/js/api.js` created with correct API_BASE
- [ ] `/static/js/auth.js` created
- [ ] `/static/login.html` created
- [ ] `/static/dashboard.html` created
- [ ] `/static/admin.html` created
- [ ] Backend URL verified: `https://cgs-attendance-system.onrender.com`
- [ ] CORS headers verified in Flask app.py
- [ ] Static files deployed to Netlify
- [ ] `/netlify.toml` created
- [ ] Test login: username/password correct
- [ ] Browser console shows "[API]" logs
- [ ] Network tab shows successful API calls
- [ ] Session persists after page reload
- [ ] Logout clears localStorage
- [ ] requireAuth() redirects unauthenticated users to login
- [ ] Admin pages require admin role

---

## Rollback Plan

If something breaks:

```bash
# Revert changes
git revert HEAD

# Or manually fix api.js
# Edit /static/js/api.js and verify:
# - Line 2: const API_BASE = "https://cgs-attendance-system.onrender.com"
# - No localhost URLs

# Redeploy
netlify deploy --prod --dir=static
```

---

## Next Steps

1. ✅ Deploy static files to Netlify
2. ✅ Test login flow end-to-end
3. ✅ Update remaining API endpoints
4. ✅ Deploy full employee/admin interfaces
5. ✅ Monitor Render backend logs

---

**Questions?** Check `/static/js/api.js` comments or run tests in browser console.
