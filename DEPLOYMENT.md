# Deployment Guide for Render

This guide will help you deploy the Analytics AI Dashboard to Render with separate frontend and backend services.

## Prerequisites

1. **Render Account**: Sign up at [render.com](https://render.com)
2. **GitHub Repository**: Your code should be in a GitHub repository
3. **Required API Keys**:
   - Supabase credentials (URL, anon key, service key)
   - OpenAI API key for AI features

## Deployment Steps

### 1. Backend Deployment

1. **Create Web Service** in Render Dashboard:
   - **Name**: `analytics-ai-backend`
   - **Environment**: `Python 3`
   - **Build Command**: `cd backend && pip install -r requirements.txt`
   - **Start Command**: `cd backend && python -m uvicorn app:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path**: `/health`

2. **Environment Variables** (Add in Render Dashboard):
   ```
   SUPABASE_URL=your_supabase_project_url
   SUPABASE_KEY=your_supabase_anon_key  
   SUPABASE_SERVICE_KEY=your_supabase_service_role_key
   OPENAI_API_KEY=your_openai_api_key
   JWT_SECRET_KEY=generate_secure_random_string
   SUPERADMIN_USERNAME=admin
   SUPERADMIN_PASSWORD=secure_password
   ENVIRONMENT=production
   DEBUG=false
   FRONTEND_URL=https://your-frontend-name.onrender.com
   ```

### 2. Frontend Deployment

1. **Create Web Service** in Render Dashboard:
   - **Name**: `analytics-ai-frontend`
   - **Environment**: `Node`
   - **Build Command**: `cd frontend && npm ci && npm run build`
   - **Start Command**: `cd frontend && npm start`

2. **Environment Variables**:
   ```
   NEXT_PUBLIC_API_URL=https://your-backend-name.onrender.com
   ```

### 3. Update Backend CORS

After frontend is deployed, update the backend's `FRONTEND_URL` environment variable with your actual frontend URL.

## Security Checklist

- [ ] Change default superadmin password
- [ ] Generate secure JWT secret (64+ character random string)
- [ ] Set `DEBUG=false` in production
- [ ] Verify all API keys are set as secret environment variables
- [ ] Test API endpoints after deployment

## Database Setup

Your Supabase database should already be configured. If not:

1. Visit your deployed backend at: `https://your-backend-name.onrender.com/api/setup-schema`
2. Run the provided SQL commands in your Supabase SQL editor

## Testing Deployment

1. **Backend Health Check**: 
   - Visit: `https://your-backend-name.onrender.com/health`
   - Should return JSON with status "healthy"

2. **Frontend**: 
   - Visit: `https://your-frontend-name.onrender.com`
   - Should load the dashboard interface

3. **API Integration**:
   - Test login and data loading from frontend
   - Verify superadmin panel works

## Common Issues

### CORS Errors
- Ensure `FRONTEND_URL` is set correctly in backend
- Check that frontend URL matches exactly (with https://)

### Build Failures  
- Check build logs in Render dashboard
- Verify all environment variables are set
- Ensure requirements.txt includes all dependencies

### Database Connections
- Verify Supabase credentials are correct
- Check that Supabase allows connections from Render IPs

## Monitoring

- **Backend Logs**: Available in Render dashboard
- **Health Monitoring**: `/health` endpoint provides service status
- **Error Tracking**: Check application logs for any issues

## Cost Optimization

- **Starter Plans**: Both services can run on Render's free tier initially
- **Sleep Mode**: Free tier services sleep after inactivity
- **Upgrade**: Consider paid plans for production workloads

## Support

If you encounter issues:
1. Check Render service logs
2. Verify environment variables
3. Test API endpoints individually
4. Check database connectivity 