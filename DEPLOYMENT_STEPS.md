# 🚀 DEPLOYMENT GUIDE - PostgreSQL + Render + Netlify

## Quick Links
- 📋 [Migration Summary](MIGRATION_SUMMARY.md) - Overview of all changes
- ✅ [Deployment Checklist](DEPLOYMENT_CHECKLIST.md) - Verification items
- 📖 [PostgreSQL Migration Guide](POSTGRESQL_MIGRATION_GUIDE.md) - Detailed technical guide

---

## 🎯 What You're About to Deploy

Your Flask attendance system has been successfully migrated from SQLite to PostgreSQL. This guide will walk you through the 4-step deployment process to get your app live.

**Deployment Stack:**
- 🏃 **Backend:** Flask app on Render
- 💾 **Database:** PostgreSQL on Neon
- 🎨 **Frontend:** React/HTML on Netlify

**Estimated Time:** 30 minutes

---

## ⚡ STEP 1: Set Up Neon PostgreSQL (5 min)

### 1.1 Create Neon Account

1. Go to [neon.tech](https://neon.tech)
2. Click "Sign Up" → Create account
3. Verify email

### 1.2 Create Project

1. Click "New Project"
2. Choose region (pick closest to your users)
3. Click "Create Project"

### 1.3 Get Connection String

1. You'll see a connection string like:
```
postgresql://user:password@host.neon.tech:5432/dbname?sslmode=require
```

2. Copy this **entire** string (save it somewhere)
3. This is your `DATABASE_URL`

---

## ⚡ STEP 2: Deploy Backend to Render (10 min)

### 2.1 Prepare Code

```bash
# In your project directory
git add .
git commit -m "feat: PostgreSQL migration complete"
git push origin main
```

### 2.2 Create Render Web Service

1. Go to [render.com](https://render.com)
2. Click "New +" → "Web Service"
3. Click "Connect" next to your GitHub repo
4. Select the **cggs/CGS** branch

### 2.3 Configure Service

**Settings:**
- **Name:** `cgs-attendance` (or your choice)
- **Environment:** `Python 3`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn app:app`

### 2.4 Set Environment Variables

Click "Advanced" → "Add Environment Variable"

Add these:
```
FLASK_ENV          = production
SECRET_KEY          = <generate-random-string-32-chars>
DATABASE_URL        = <paste-your-neon-connection-string>
```

**To generate SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 2.5 Deploy

Click "Create Web Service" → Render deploys automatically

**Wait for:**
- ✅ Build succeeds
- ✅ Service running
- ✅ No errors in logs

Your backend is now live! 🎉

---

## ⚡ STEP 3: Initialize Database (2 min)

### 3.1 Option A: Via Render Shell (Recommended)

1. In Render dashboard, go to your service
2. Click "Shell" tab
3. Run:
```bash
python setup_postgres_db.py
```

4. Verify output:
```
✅ Connected to PostgreSQL
✅ All tables created successfully!
✅ Demo users inserted!
✅ Database setup complete!
```

### 3.2 Option B: Via API (Manual)

You can trigger setup via an API endpoint (if you added one):
```bash
curl https://your-service.onrender.com/init-db
```

### 3.3 Verify Database

1. Go to Neon dashboard
2. Click your project
3. Open "Branches" → Default branch
4. Should see tables: users, attendance, leaves, etc.

---

## ⚡ STEP 4: Deploy Frontend to Netlify (5 min)

### 4.1 Update API URL

Edit `frontend/js/api.js`:

**Find:**
```javascript
const API_BASE = 'http://localhost:5000';
```

**Replace with:**
```javascript
const API_BASE = 'https://your-render-service.onrender.com';
```

(Use your actual Render URL)

### 4.2 Deploy to Netlify

```bash
# Option A: Via GitHub (Recommended)
git add .
git commit -m "chore: update API URL for production"
git push origin main
# Netlify auto-deploys on push

# Option B: Via CLI
npm install -g netlify-cli
netlify deploy --prod --dir=frontend
```

### 4.3 Verify Frontend

1. Open your Netlify site URL
2. You should see the login page
3. Try logging in with demo credentials

---

## ✅ STEP 5: Verification (5 min)

### 5.1 Test Backend Health

```bash
curl https://your-render-service.onrender.com/health
```

Expected response:
```json
{
  "status": "ok",
  "database": "connected"
}
```

### 5.2 Test Login

1. Open frontend URL
2. Log in with:
   - Username: `francis`
   - Password: `francis123`
3. Should see admin dashboard

### 5.3 Test Employee Access

1. Log out
2. Log in with:
   - Username: `pradeep`
   - Password: `pradeep123`
3. Should see employee dashboard

### 5.4 Test Core Features

- [ ] Check-in button works
- [ ] Check-out button works
- [ ] Dashboard shows today's status
- [ ] Leave management works
- [ ] Admin dashboard accessible

### 5.5 Check Logs for Errors

**Render:**
1. Go to service → Logs tab
2. Look for any errors in red
3. Should see successful database queries

**Frontend (Netlify):**
1. Go to site → Deploys
2. Should show "Published"
3. Open browser DevTools → Console
4. Should have no red errors

---

## 🎊 You're Done!

Your attendance system is now live in production! 🚀

---

## 📱 Demo Users (Test with these)

| Role | Username | Password | Permissions |
|------|----------|----------|-------------|
| Admin | francis | francis123 | Full access |
| Employee | pradeep | pradeep123 | View/manage own data |
| Employee | sounthar | sounthar123 | View/manage own data |
| Employee | aadhi | aadhi123 | View/manage own data |

---

## 🐛 Troubleshooting

### "Cannot connect to database"
```bash
# Verify DATABASE_URL in Render
# 1. Go to Environment tab in Render
# 2. Confirm DATABASE_URL is set correctly
# 3. Restart service: Settings → Manual Deploy
```

### "Login doesn't work"
```bash
# Verify database initialization
# 1. Go to Render Shell
# 2. Run: python setup_postgres_db.py
# 3. Check for errors
```

### "Frontend can't reach backend"
```bash
# Verify API_BASE URL
# 1. Check frontend/js/api.js
# 2. Should match your Render URL exactly
# 3. Redeploy frontend
```

### "404 on endpoints"
```bash
# Check Render logs
# 1. Go to Service → Logs
# 2. Look for routing errors
# 3. Verify Flask app.py routes are intact
```

---

## 🔐 Security Checklist

After deployment, verify:

- [ ] `SECRET_KEY` is a random 32-character string
- [ ] `DATABASE_URL` is set in Render (not in code)
- [ ] `FLASK_ENV=production`
- [ ] Render service has auto-redeploys disabled (if preferred)
- [ ] No hardcoded credentials in repository
- [ ] HTTPS enabled on both Render and Netlify

---

## 📊 Monitoring & Maintenance

### Daily
- Check Render logs for errors
- Monitor database connection count
- Verify login functionality

### Weekly
- Review Render performance metrics
- Check Neon database size
- Test admin features

### Monthly
- Review and optimize slow queries
- Update dependencies if needed
- Check for security updates

---

## 🆘 Need Help?

### If deployment fails:

1. **Check Render logs** - most errors shown there
2. **Verify environment variables** - DATABASE_URL, SECRET_KEY
3. **Check database connection** - run `python setup_postgres_db.py`
4. **Review requirements.txt** - ensure psycopg2-binary is included

### Documentation
- [MIGRATION_SUMMARY.md](MIGRATION_SUMMARY.md) - What was changed
- [POSTGRESQL_MIGRATION_GUIDE.md](POSTGRESQL_MIGRATION_GUIDE.md) - Technical details
- [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) - Verification steps

### Useful Links
- Render Documentation: https://render.com/docs
- Neon Documentation: https://neon.tech/docs
- PostgreSQL Docs: https://www.postgresql.org/docs/

---

## 🎯 Next Steps

After deployment works:

1. **Monitor** for 24 hours
2. **Test thoroughly** with all users
3. **Set up backups** (Neon feature)
4. **Configure alerts** (Render feature)
5. **Document** any issues found

---

## 📝 Post-Deployment Checklist

- [ ] Health endpoint returns 200
- [ ] All demo users can login
- [ ] Dashboard loads correctly
- [ ] Check-in/out buttons work
- [ ] Attendance records save
- [ ] Leave requests work
- [ ] Admin features work
- [ ] No errors in logs
- [ ] Response times acceptable
- [ ] CORS working properly

---

**Deployed:** ✅ Date: ________  
**Verified:** ✅ Date: ________  
**Production Ready:** ✅ Status: LIVE

---

**Need updates?** See [MIGRATION_SUMMARY.md](MIGRATION_SUMMARY.md) for complete technical overview.

