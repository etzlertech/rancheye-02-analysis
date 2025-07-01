# Railway Deployment Lessons Learned

This document captures the challenges and solutions encountered while deploying a FastAPI + React application to Railway.

## Overview
Deploying a Python FastAPI backend with a React frontend to Railway presented several challenges. This document serves as a reference for future deployments.

## Key Issues and Solutions

### 1. Environment Variables Not Recognized
**Problem**: Railway wasn't picking up environment variables from the dashboard.
**Solution**: Manually paste raw ENV text into Railway Variables section rather than relying on auto-detection.

### 2. Dockerfile vs Nixpacks Confusion
**Problem**: Railway kept using Dockerfile when we wanted nixpacks, causing build failures.
**Solution**: Temporarily rename Dockerfile to force nixpacks usage, or ensure Dockerfile is properly configured for the full stack.

### 3. React Build Not Being Served
**Problem**: FastAPI was serving the old vanilla JS UI instead of the new React build.
**Root Causes**:
- React build files weren't being copied from Docker builder stage to production stage
- Vite was configured to output to `../static/dist` but Dockerfile was looking in `frontend/dist`

**Solution**: 
```dockerfile
# Copy React build from builder stage (correct path)
COPY --from=builder --chown=appuser:appgroup /app/static/dist /app/static/dist
```

### 4. PostCSS Configuration Syntax Error
**Problem**: PostCSS config used ES modules syntax which failed in production.
```
Error: Unexpected token 'export'
```
**Solution**: Convert from ES modules to CommonJS:
```javascript
// Wrong
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}

// Correct
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

### 5. Pip Installation Issues with Nixpacks
**Problem**: When trying to use nixpacks, pip wasn't available in the build environment.
**Errors**:
- `pip: command not found`
- `/usr/bin/python: No module named pip`

**Solution**: Stick with Dockerfile approach which properly manages Python environments.

### 6. Supabase Authentication Keys
**Problem**: API returning 401 Unauthorized errors.
**Solution**: Update FastAPI to use `SUPABASE_SERVICE_ROLE_KEY` instead of regular `SUPABASE_KEY`:
```python
supabase = SupabaseClient(
    url=os.getenv('SUPABASE_URL'),
    key=os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_KEY')
)
```

## Successful Dockerfile Configuration

```dockerfile
# Multi-stage build is crucial for proper React + Python deployment
FROM python:3.11-slim AS builder

# Install Node.js in builder stage
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc g++ build-essential libpq-dev curl \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Build Python venv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Build React app
COPY frontend/package*.json ./frontend/
WORKDIR /app/frontend
RUN npm install
COPY frontend/ .
RUN npm run build
WORKDIR /app

# Production stage
FROM python:3.11-slim AS production

# Copy venv and React build
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app/static/dist /app/static/dist
```

## Debugging Steps That Helped

1. **Add verbose logging to FastAPI**:
```python
print(f"Looking for React build at: {react_build_dir}")
print(f"React index exists: {(react_build_dir / 'index.html').exists()}")
```

2. **Check Railway build logs carefully** - the error messages are usually accurate but can be buried.

3. **Use git commits and pushes to trigger rebuilds** - Railway auto-deploys on push.

## Recommended Deployment Workflow

1. Ensure all config files use CommonJS syntax (not ES modules)
2. Test Docker build locally first: `docker build -t test .`
3. Verify Vite build output directory matches Dockerfile COPY commands
4. Use multi-stage Docker builds to keep production images small
5. Always copy React build files in Dockerfile production stage
6. Set all environment variables in Railway dashboard before deploying

## Common Pitfalls to Avoid

- Don't assume Railway will auto-detect all environment variables
- Don't mix ES modules and CommonJS syntax in config files
- Don't forget to copy React build from builder to production in Dockerfile
- Don't use relative paths without understanding where files actually end up
- Don't switch between Dockerfile and nixpacks without understanding the implications

## Final Working Setup

- **Backend**: FastAPI with proper static file mounting
- **Frontend**: React with Vite, building to `../static/dist`
- **Deployment**: Multi-stage Dockerfile that builds both Python and React
- **Hosting**: Railway with manual environment variable configuration

This setup successfully serves the React SPA with Supabase integration for image storage browsing.