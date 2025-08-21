# Sentry.io Integration Setup Guide

## 🎯 Overview

Sentry has been successfully integrated into your Analytics AI Dashboard project for comprehensive error tracking and performance monitoring across both frontend (Next.js) and backend (FastAPI).

## ✅ What's Been Configured

### Frontend (Next.js/React)

- ✅ `@sentry/nextjs` SDK installed
- ✅ Client-side configuration (`sentry.client.config.js`)
- ✅ Server-side configuration (`sentry.server.config.js`)
- ✅ Edge configuration (`sentry.edge.config.js`)
- ✅ Next.js config updated with Sentry webpack plugin
- ✅ Instrumentation file created for server-side monitoring
- ✅ React ErrorBoundary component created (`components/common/ErrorBoundary.tsx`)
- ✅ Environment variables template created

### Backend (FastAPI/Python)

- ✅ `sentry-sdk[fastapi]` installed and added to requirements.txt
- ✅ Sentry initialization configured in `app.py`
- ✅ FastAPI and Starlette integrations enabled
- ✅ Test endpoints created (`/api/sentry-test`, `/api/sentry-error-test`)
- ✅ Environment variables template created
- ✅ Logging integration configured

## 🚀 Next Steps

### 1. Create Sentry Account & Projects

1. Go to [sentry.io](https://sentry.io) and create an account
2. Create an organization
3. Create two projects:
   - **Frontend**: Platform "React", name: "analytics-ai-frontend"
   - **Backend**: Platform "Python", name: "image.png"

### 2. Update Environment Variables

**Frontend** (`frontend/.env.local`):

```env
NEXT_PUBLIC_SENTRY_DSN=https://your-frontend-dsn@sentry.io/project-id
SENTRY_DSN=https://your-frontend-dsn@sentry.io/project-id
SENTRY_ORG=your-org-name
SENTRY_PROJECT=analytics-ai-frontend
```

**Backend** (`backend/.env`):

```env
SENTRY_DSN=https://your-backend-dsn@sentry.io/project-id
SENTRY_ORG=your-org-name
SENTRY_PROJECT=analytics-ai-backend
ENVIRONMENT=development
APP_VERSION=1.0.0
```

### 3. Test the Integration

**Backend Test:**

```bash
# Start your FastAPI server
cd backend
python app.py

# Test endpoints:
GET http://localhost:8000/api/sentry-test        # Info/breadcrumb test
GET http://localhost:8000/api/sentry-error-test  # Error tracking test
```

**Frontend Test:**

```bash
# Start your Next.js app
cd frontend
npm run dev

# The app will now automatically:
# - Track JavaScript errors
# - Monitor performance
# - Capture user sessions (with replay)
# - Send unhandled exceptions to Sentry
```

## 🔧 Configuration Features

### Frontend Features

- **Error Tracking**: Automatic capture of JavaScript errors and unhandled promise rejections
- **Performance Monitoring**: Page load times, API calls, and user interactions
- **Session Replay**: Record user sessions for debugging (configurable)
- **Error Boundaries**: Graceful error handling with custom UI
- **Source Maps**: Upload source maps for better stack traces (production)

### Backend Features

- **Error Tracking**: Automatic capture of Python exceptions
- **Performance Monitoring**: API endpoint response times and database queries
- **Request Tracing**: Track requests across your application
- **Integration**: FastAPI, Starlette, and logging integration
- **Custom Tags**: Environment, release, and component tagging

## 📊 What You'll See in Sentry

Once configured, you'll get:

- **Real-time error alerts** via email/Slack/Discord
- **Performance insights** with slow endpoint detection
- **User impact analysis** showing how many users are affected
- **Release tracking** to see which deployments introduce issues
- **Custom dashboards** with your key metrics

## 🛡️ Security & Privacy

The configuration includes:

- **Development filtering**: Reduces noise in development
- **Sensitive data masking**: Automatically masks sensitive information
- **Rate limiting**: Prevents spam to your Sentry quota
- **Environment tagging**: Separate development from production issues

## 🎛️ Advanced Configuration (Optional)

### Custom Error Handling

```javascript
// Frontend - Custom error reporting
import * as Sentry from "@sentry/nextjs";

Sentry.captureException(new Error("Custom error"));
```

```python
# Backend - Custom error reporting
import sentry_sdk

sentry_sdk.capture_exception(Exception("Custom error"))
```

### Performance Monitoring

```javascript
// Frontend - Custom performance tracking
const transaction = Sentry.startTransaction({
	name: "Custom Operation",
});
// ... your code
transaction.finish();
```

## 🔍 Troubleshooting

### Common Issues:

1. **No events in Sentry**: Check DSN format and network connectivity
2. **Too many events**: Adjust sample rates in configuration
3. **Missing source maps**: Ensure build process uploads source maps
4. **Performance overhead**: Reduce traces_sample_rate for production

### Debug Commands:

```bash
# Check if Sentry SDK is working
curl http://localhost:8000/api/sentry-test
curl http://localhost:8000/api/sentry-error-test
```

## 📚 Resources

- [Sentry Next.js Documentation](https://docs.sentry.io/platforms/javascript/guides/nextjs/)
- [Sentry FastAPI Documentation](https://docs.sentry.io/platforms/python/integrations/fastapi/)
- [Sentry Dashboard](https://sentry.io/organizations/your-org/projects/)

---

**Ready to test?** Update your environment variables with real Sentry DSN keys and start your applications!
