# LuminaBI Settings & Architecture Documentation

## Overview

The LuminaBI project is configured to use:
- **WebSocket** (via Django Channels) for real-time updates
- **APScheduler** for background tasks
- **In-Memory Channel Layer** for local development
- **Session-based authentication** (no JWT for HTML views)

This configuration avoids Redis and Celery, making the project lighter and easier to deploy.

---

## Settings Configuration

### Key Settings Files

1. **Luminabi/settings.py** - Main Django settings
2. **.env** - Environment variables (create from .env.example)

### Environment Variables

```bash
# Create .env from example
cp .env.example .env
```

Key variables:
- `DEBUG=True/False` - Development mode
- `SECRET_KEY` - Django secret key (change for production)
- `ALLOWED_HOSTS` - Comma-separated list of allowed domains
- `DATABASE_URL` - Database connection string

---

## WebSocket Configuration (Channels)

### What is WebSocket?

WebSocket enables real-time, bidirectional communication between client and server.

### Real-Time Features

**Data Cleaning Progress**
- Endpoint: `ws://localhost:8000/ws/data-cleaning/<dataset_id>/`
- Updates: Cleaning progress, current step, errors

**Insights Generation**
- Endpoint: `ws://localhost:8000/ws/insights/<dataset_id>/`
- Updates: Discovered insights, trends, correlations

**Dashboard Updates**
- Endpoint: `ws://localhost:8000/ws/dashboard/<dashboard_id>/`
- Updates: Filter changes, widget updates, collaborative edits

**File Upload Progress**
- Endpoint: `ws://localhost:8000/ws/upload-progress/<upload_id>/`
- Updates: Upload percentage, speed, ETA

### Files

- **core/consumers.py** - WebSocket consumer implementations
- **core/routing.py** - WebSocket URL routing
- **Luminabi/asgi.py** - ASGI application configuration

---

## APScheduler Configuration

### What is APScheduler?

APScheduler (Advanced Python Scheduler) runs background tasks on a schedule without needing Redis/Celery.

### Scheduled Tasks

Configured in `settings.SCHEDULED_TASKS`:

1. **Data Cleaning** (every 1 hour)
   - Finds pending datasets
   - Automatically cleans them
   - Updates via WebSocket

2. **Insights Generation** (every 2 hours)
   - Analyzes cleaned datasets
   - Generates trends, correlations, anomalies
   - Broadcasts via WebSocket

3. **Report Generation** (daily)
   - Creates scheduled reports
   - Sends email deliveries
   - Archives for historical tracking

### Files

- **core/scheduler.py** - Scheduler initialization and management
- **core/tasks.py** - Scheduled task implementations
- **core/apps.py** - Starts scheduler on app startup

### Modifying Scheduled Tasks

Edit `Luminabi/settings.py`:

```python
SCHEDULED_TASKS = {
    'task-name': {
        'task': 'app.module.function_name',
        'schedule': timedelta(hours=1),  # or minutes, seconds, days
    },
}
```

---

## Running LuminaBI

### Development Server

```bash
# Install dependencies
pip install -r requirements.txt

# Apply migrations
python manage.py migrate

# Run development server (ASGI)
daphne -b 0.0.0.0 -p 8000 Luminabi.asgi:application
```

Or use runserver (HTTP only, no WebSocket):
```bash
python manage.py runserver
```

### Production Server

```bash
# Using Daphne (ASGI server)
daphne -b 0.0.0.0 -p 8000 Luminabi.asgi:application

# Or using Uvicorn
pip install uvicorn
uvicorn Luminabi.asgi:application --host 0.0.0.0 --port 8000
```

---

## Architecture Overview

### Request Flow

```
Client (HTML/JS)
    ↓
Django Views (HTML responses)
    ↓
WebSocket Connections (real-time updates)
    ↓
APScheduler Tasks (background jobs)
    ↓
Database (persistence)
```

### Component Interaction

1. **User uploads dataset** → REST API
2. **Server starts WebSocket connection** → Consumer notifies client
3. **APScheduler starts cleaning task** → Emits progress via WebSocket
4. **Client receives updates** → UI updates in real-time
5. **Cleaning complete** → Insights generation scheduled

---

## Logging Configuration

Logs are written to both console and file.

### Log Files

- **logs/django.log** - Main application logs
- **logs/scheduler.log** - Scheduler debug logs

View logs:
```bash
# Real-time logs
tail -f logs/django.log

# Search for errors
grep ERROR logs/django.log
```

---

## Channel Layers

### Current Configuration: In-Memory

```python
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer'
    }
}
```

**Pros:**
- Simple, no Redis required
- Good for development and small deployments

**Cons:**
- Only works with single server
- Not persistent

### Production Alternative: Redis

If scaling to multiple servers, use Redis:

```python
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('redis_host', 6379)],
        },
    },
}
```

---

## Authentication & Sessions

### Session Configuration

- **Engine:** Database-backed sessions
- **Cookie Age:** 2 weeks
- **Security:** HTTPOnly, Secure in production
- **CSRF Protection:** Enabled

### User Login Flow

1. User provides credentials
2. Django validates and creates session
3. Session ID stored in cookie
4. Subsequent requests authenticated via session

---

## Database Models

The following models are used for scheduling and tracking:

- **Dataset** - Uploaded data files
- **Dashboard** - User dashboards
- **Visualization** - Charts and graphs
- **Insight** - Generated insights
- **ScheduledReport** - Automated report configuration

---

## Troubleshooting

### Scheduler not starting?

```python
# In Django shell
from core.scheduler import get_scheduler_jobs
print(get_scheduler_jobs())
```

### WebSocket not connecting?

1. Check ASGI server is running (Daphne, not runserver)
2. Verify client WebSocket URL matches routing
3. Check browser console for connection errors

### Logs not appearing?

Create logs directory:
```bash
mkdir -p logs
```

---

## Next Steps

1. ✅ Settings configured
2. Next: Implement core HTML views for class-based views
3. Then: Build dashboard UI with WebSocket integration
4. Finally: Connect to task scheduler for automations

See the project README.md for full feature documentation.
