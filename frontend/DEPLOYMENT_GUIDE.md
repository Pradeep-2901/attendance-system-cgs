# CGS Attendance System - Frontend Deployment Guide

## Overview

This is a static HTML/JavaScript frontend for the CGS Attendance Management System. It communicates with the Flask backend via REST API calls and is designed to be deployed on Netlify.

**Backend (Render):** https://cgs-attendance-backend.onrender.com  
**Frontend (Netlify):** https://cgs-attendance.netlify.app

---

## Prerequisites

- Netlify account (free: https://netlify.com)
- GitHub account (optional, for easier deployment)
- Backend running on Render or any HTTP server

---

## Deployment Options

### Option 1: Deploy via Netlify CLI (Recommended)

```bash
# 1. Install Netlify CLI
npm install -g netlify-cli

# 2. Navigate to frontend directory
cd frontend

# 3. Deploy
netlify deploy --prod --dir=.
```

### Option 2: Deploy via GitHub (Continuous Deployment)

```bash
# 1. Initialize Git repo (if not already)
git init

# 2. Add all files
git add .

# 3. Commit
git commit -m "Initial frontend deployment"

# 4. Create new repository on GitHub
# 5. Push to GitHub
git push -u origin main

# 6. In Netlify:
#    - Click "New site from Git"
#    - Connect GitHub account
#    - Select this repository
#    - Set Build settings:
#      Build command: (leave empty)
#      Publish directory: frontend
```

### Option 3: Drag & Drop

1. Go to https://app.netlify.com
2. Drag & drop the `frontend` folder
3. Done!

---

## Configuration

### Update API Base URL

Edit `js/api.js` and update the API_BASE:

```javascript
const API_BASE = window.location.hostname.includes("netlify.app")
    ? "https://your-render-backend.onrender.com"  // Your actual Render URL
    : "http://localhost:5000";
```

### Environment Variables (Optional)

In Netlify Dashboard:
1. Go to Site settings → Build & Deploy → Environment
2. Add variables if needed (e.g., for analytics, etc.)

---

## Verification Checklist

After deployment:

- [ ] Navigate to frontend URL
- [ ] Login with test credentials (pradeep/pradeep123)
- [ ] Check if dashboard loads
- [ ] Verify check-in/check-out works
- [ ] Test admin login (francis/francis123)
- [ ] Verify admin dashboard loads

---

## Backend Configuration (Render)

Ensure backend has CORS enabled in app.py:

```python
from flask_cors import CORS
CORS(app)  # ✅ Already configured

@app.after_request
def after_request(response):
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Allow-Origin'] = origin
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-CSRFToken, X-Requested-With'
    return response
```

---

## Testing

### Local Testing

```bash
# 1. Ensure backend is running
python app.py  # runs on http://localhost:5000

# 2. Serve frontend locally
python -m http.server 8000  # runs on http://localhost:8000

# 3. Visit http://localhost:8000
```

### Test Credentials

**Employee:**
- Username: `pradeep`
- Password: `pradeep123`

**Admin:**
- Username: `francis`
- Password: `francis123`

---

## Troubleshooting

### Login fails with "Invalid credentials"

- Verify backend is running
- Check API_BASE URL in js/api.js
- Ensure credentials exist in database
- Check browser console for CORS errors

### "Cannot GET /dashboard.html"

- Clear browser cache
- Check if netlify.toml is in root of `frontend` folder
- Netlify should redirect all routes to index.html (handled by netlify.toml)

### Photos not uploading

- Check camera permissions in browser
- Verify backend photo upload folder exists
- Check UPLOAD_FOLDER in Flask app.py

### Location not working

- Ensure browser has permission to access geolocation
- Check if site is served over HTTPS (required for geolocation)

---

## File Structure

```
frontend/
├── index.html              # Login page
├── dashboard.html          # Employee dashboard
├── admin.html             # Admin dashboard
├── attendance.html        # Attendance view (create if needed)
├── requests.html          # Leave/requests view (create if needed)
├── js/
│   ├── api.js            # API client (central)
│   ├── auth.js           # Authentication logic
│   ├── common.js         # Utility functions
│   ├── dashboard.js      # Employee dashboard logic
│   └── admin.js          # Admin dashboard logic
├── css/
│   └── (custom styles if needed)
├── netlify.toml          # Netlify configuration
└── README.md             # This file
```

---

## Key Features Implemented

✅ Login/Logout  
✅ Session management (localStorage + cookies)  
✅ Employee dashboard with attendance status  
✅ Check-in/Check-out with geolocation and photo capture  
✅ Admin dashboard with employee management  
✅ Leave request approval workflow  
✅ Comp-off request management  
✅ Holiday management  
✅ CORS-compatible API calls  
✅ Responsive design (Bootstrap 5)  

---

## API Endpoints Used

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | /login | User authentication |
| GET | /logout | User logout |
| GET | /test_session | Session verification |
| GET | /health | Health check |
| GET | /dashboard | Employee dashboard data |
| POST | /checkin | Record check-in |
| POST | /checkout | Record check-out |
| GET | /admin | Admin dashboard |
| GET | /admin/employees | List employees |
| POST | /admin/add_employee | Add employee |
| GET | /admin/attendance | All attendance |
| POST | /admin/review_leave/<id> | Approve/reject leave |
| GET | /admin/holidays | List holidays |
| POST | /admin/add_holiday | Add holiday |

---

## Performance Optimization

Netlify auto-optimizes:
- Minification
- Image optimization
- CDN delivery
- Cache control headers

---

## Security Notes

- ✅ CORS configured
- ✅ Session cookies with HttpOnly flag
- ✅ Password hashing on backend (scrypt)
- ✅ No sensitive data in localStorage (only user ID/name/role)
- ✅ All API calls use credentials: "include"

For production:
- [ ] Enable SSL/TLS in backend
- [ ] Set SESSION_COOKIE_SECURE = True in Flask
- [ ] Use environment variables for API base URL
- [ ] Implement rate limiting on backend

---

## Support

For issues, check:
1. Browser console for errors
2. Netlify deployment logs
3. Backend server logs
4. CORS configuration

---

**Deployment Status:** Ready for production ✅
