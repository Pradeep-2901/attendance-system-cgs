#!/bin/bash
# Quick Start Script for CGS Attendance Frontend Deployment

echo "======================================"
echo "CGS Attendance - Frontend Setup"
echo "======================================"
echo ""

# Check if in frontend directory
if [ ! -f "index.html" ]; then
    echo "❌ Error: Run this script from the frontend directory"
    exit 1
fi

echo "✅ Frontend directory detected"
echo ""

# Check if netlify.toml exists
if [ -f "netlify.toml" ]; then
    echo "✅ netlify.toml found"
else
    echo "⚠️  netlify.toml missing"
fi

# Check API files
for file in js/api.js js/auth.js js/common.js js/dashboard.js js/admin.js; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ Missing: $file"
    fi
done

echo ""
echo "======================================"
echo "Deployment Options"
echo "======================================"
echo ""
echo "1️⃣  Netlify CLI (Recommended):"
echo "   npm install -g netlify-cli"
echo "   netlify deploy --prod --dir=."
echo ""
echo "2️⃣  Drag & Drop:"
echo "   Go to app.netlify.com and drag this folder"
echo ""
echo "3️⃣  GitHub + Netlify:"
echo "   Push to GitHub, connect to Netlify"
echo ""
echo "======================================"
echo "Important: Update Backend URL"
echo "======================================"
echo ""
echo "Edit: js/api.js"
echo "Line 6-7: Update the API_BASE URL with your Render backend"
echo ""
echo "Current: https://cgs-attendance-backend.onrender.com"
echo "Change to: https://YOUR-ACTUAL-RENDER-APP.onrender.com"
echo ""
echo "======================================"
echo "Test Credentials"
echo "======================================"
echo ""
echo "Employee:"
echo "  Username: pradeep"
echo "  Password: pradeep123"
echo ""
echo "Admin:"
echo "  Username: francis"
echo "  Password: francis123"
echo ""
