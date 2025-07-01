# Railway Deployment Guide

## Prerequisites

1. Railway account (sign up at railway.app)
2. Railway CLI installed (optional but recommended)
3. GitHub repository connected

## Environment Variables

Set these in Railway dashboard:

### Required
```bash
# Supabase
SUPABASE_URL=https://enoyydytzcgejwmivshz.supabase.co
SUPABASE_KEY=your_service_role_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
SUPABASE_ANON_KEY=your_anon_key

# AI Providers (at least one required)
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GEMINI_API_KEY=your_gemini_key

# Railway sets these automatically
PORT=8080
RAILWAY_ENVIRONMENT=production
```

### Optional
```bash
# Alert Configuration
ALERT_WEBHOOK_URL=your_webhook_url
ALERT_EMAIL=your_email

# Performance
MAX_WORKERS=5
REQUEST_TIMEOUT=60
```

## Deployment Steps

### Method 1: GitHub Integration (Recommended)

1. Connect your GitHub repo to Railway
2. Railway will auto-deploy on every push to main
3. The build process will:
   - Install Python dependencies
   - Build the React frontend
   - Start the web server

### Method 2: Railway CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Create new project
railway new

# Deploy
railway up
```

### Method 3: Manual Deploy

1. Go to Railway dashboard
2. Create new project
3. Deploy from GitHub
4. Add environment variables
5. Railway will build and deploy automatically

## Post-Deployment

1. **Check deployment logs**:
   - Look for "Frontend build complete"
   - Verify "RanchEye Web Server Starting..."

2. **Access your app**:
   - Dashboard: https://your-app.railway.app
   - API Docs: https://your-app.railway.app/docs

3. **Verify functionality**:
   - Check WebSocket connection in browser console
   - Test image upload
   - Verify stats are updating

## Troubleshooting

### Frontend not loading
- Check build logs for npm errors
- Verify frontend/package.json exists
- Check static/dist folder was created

### API errors
- Verify all environment variables are set
- Check Supabase connection
- Ensure at least one AI API key is provided

### WebSocket issues
- Railway supports WebSockets by default
- Check browser console for connection errors
- Verify /ws endpoint is accessible

## Monitoring

Railway provides:
- Deployment logs
- Resource usage metrics
- Crash reporting
- Custom domains

## Scaling

Railway automatically handles:
- SSL certificates
- Load balancing
- Auto-scaling (based on plan)
- Zero-downtime deploys