# LuminaBI Architecture Overview

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT BROWSER                          │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  HTML Pages with JavaScript/HTMX                          │ │
│  │  - Dashboard UI                                           │ │
│  │  - Data Upload Form                                       │ │
│  │  - Visualization Display                                  │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
         │                            │
         │ HTTP Requests             │ WebSocket Connections
         │ (HTML Views)              │ (Real-time Updates)
         ▼                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DJANGO ASGI APPLICATION                      │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ ProtocolTypeRouter (HTTP + WebSocket)                     │ │
│  │                                                            │ │
│  │  HTTP: Django Views (HTML responses)                      │ │
│  │  ├── accounts/ (Login, Register, Profile)               │ │
│  │  ├── core/ (Dashboard, Upload)                          │ │
│  │  ├── datasets/ (Dataset Management)                     │ │
│  │  └── visualizations/ (Chart Display)                    │ │
│  │                                                            │ │
│  │  WebSocket: Channel Consumers (Real-time)               │ │
│  │  ├── DataCleaningConsumer (progress updates)            │ │
│  │  ├── InsightsConsumer (insight discovery)               │ │
│  │  ├── DashboardConsumer (collaborative updates)          │ │
│  │  └── UploadProgressConsumer (file upload progress)      │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
         │                            │
         │ ORM                        │ Channel Groups
         │ Queries                    │ (In-Memory)
         ▼                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DATABASE (PostgreSQL/SQLite)               │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Tables:                                                   │ │
│  │  - User (auth)                                            │ │
│  │  - Dataset (uploaded files)                              │ │
│  │  - Dashboard (user dashboards)                           │ │
│  │  - Visualization (charts)                                │ │
│  │  - Insight (generated insights)                          │ │
│  │  - ScheduledReport (automated reports)                   │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
         ▲
         │
         │ Read/Write
         │
┌─────────────────────────────────────────────────────────────────┐
│                   APScheduler (Background Tasks)                │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Scheduled Jobs (Background Thread)                       │ │
│  │                                                            │ │
│  │  ┌─────────────────────────────────────────────────────┐  │ │
│  │  │ Every 1 Hour: Data Cleaning                        │  │ │
│  │  │  - Find pending datasets                           │  │ │
│  │  │  - Clean: remove duplicates, handle missing values │  │ │
│  │  │  - Emit progress via WebSocket                     │  │ │
│  │  └─────────────────────────────────────────────────────┘  │ │
│  │                                                            │ │
│  │  ┌─────────────────────────────────────────────────────┐  │ │
│  │  │ Every 2 Hours: Insights Generation                 │  │ │
│  │  │  - Analyze cleaned datasets                        │  │ │
│  │  │  - Detect trends, correlations, anomalies         │  │ │
│  │  │  - Emit insights via WebSocket                     │  │ │
│  │  └─────────────────────────────────────────────────────┘  │ │
│  │                                                            │ │
│  │  ┌─────────────────────────────────────────────────────┐  │ │
│  │  │ Every 24 Hours: Report Generation                  │  │ │
│  │  │  - Generate PDF reports                            │  │ │
│  │  │  - Send scheduled emails                           │  │ │
│  │  │  - Archive for history                             │  │ │
│  │  └─────────────────────────────────────────────────────┘  │ │
│  │                                                            │ │
│  │  Runs continuously in background (no blocking)           │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Request Flow Examples

### Example 1: User Uploads a Dataset

```
1. User opens upload form (HTTP GET)
   ├─ Django renders HTML template
   └─ Returns form page

2. User selects file and submits (HTTP POST)
   ├─ Django validates and saves file
   ├─ Creates WebSocket connection
   └─ Returns upload page with WS endpoint

3. File upload starts (WebSocket)
   ├─ Client streams file data
   ├─ Server tracks progress
   ├─ Emits progress events: 10%, 25%, 50%, 75%, 100%
   └─ Client updates progress bar in real-time

4. Upload complete
   ├─ Server creates Dataset record in DB
   ├─ Marks as "pending" for cleaning
   └─ Sends completion event

5. APScheduler detects pending dataset (next hour)
   ├─ Starts data cleaning task
   ├─ Emits progress via WebSocket: "Removing duplicates...", "Handling nulls..."
   ├─ Saves cleaned dataset to DB
   └─ User sees cleaning progress in real-time UI
```

### Example 2: Dashboard View with Real-Time Updates

```
1. User navigates to dashboard (HTTP GET)
   ├─ Django fetches dashboard config
   ├─ Renders with existing widgets
   └─ Returns HTML page

2. JavaScript connects to WebSocket
   ├─ ws://localhost:8000/ws/dashboard/123/
   ├─ Server accepts connection
   └─ Adds client to "dashboard_123" channel group

3. Another user applies filter (edit mode)
   ├─ Sends filter change via WebSocket
   ├─ Server broadcasts to all connected clients
   └─ Your dashboard updates in real-time (no refresh needed!)

4. APScheduler runs insights generation
   ├─ Finds cleaned datasets
   ├─ Generates new insights
   ├─ Broadcasts via WebSocket to all dashboards
   └─ Dashboard widgets update with new data
```

### Example 3: Scheduled Report Generation

```
Daily at 00:00:
1. APScheduler triggers report task
   ├─ Finds all dashboards with scheduled reports
   └─ For each dashboard...

2. Generate PDF report
   ├─ Query all data for dashboard
   ├─ Render charts as images
   ├─ Create formatted PDF
   └─ Save to storage

3. Send email (if configured)
   ├─ Compose email with PDF attachment
   ├─ Send to subscribed users
   └─ Log delivery status

4. Archive for history
   ├─ Save report metadata to DB
   └─ Link to dashboard

5. Notify dashboard owner
   ├─ Check if online (has WebSocket connection)
   ├─ Send notification event
   └─ User sees "Report generated!" message
```

---

## Technology Stack

### Backend
- **Django 6.0** - Web framework
- **Django REST Framework** - API (optional, for mobile apps)
- **Channels 4.3** - WebSocket support
- **APScheduler 3.10** - Background task scheduling
- **Pandas** - Data processing
- **Scikit-learn** - Analysis & ML

### Frontend
- **HTML5** - Markup
- **TailwindCSS** - Styling
- **JavaScript/HTMX** - Interactivity
- **Chart.js** - Data visualization

### Database
- **PostgreSQL** (production)
- **SQLite** (development)

### Server
- **Daphne/Uvicorn** - ASGI server (WebSocket support)
- **Gunicorn** (production)

---

## Data Flow for Real-Time Features

### WebSocket Event Broadcasting

```python
# Task completes, sends update
channel_layer = get_channel_layer()
async_to_sync(channel_layer.group_send)(
    'datacleaning_123',  # Channel group name
    {
        'type': 'cleaning_progress',  # Consumer method name
        'progress': 100,
        'status': 'completed',
    }
)

# Server routes to all connected consumers in group
# Consumer's cleaning_progress() method called
# Message sent to all clients in channel group
```

### Consumer Message Handling

```javascript
// Client WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/data-cleaning/123/');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    
    // Update UI based on message type
    if (data.type === 'cleaning_progress') {
        updateProgressBar(data.progress);
        updateStatus(data.status);
    }
};
```

---

## Advantages of This Architecture

### vs Redis + Celery
- ✅ Simpler setup (no Redis required)
- ✅ Lower memory footprint
- ✅ Easier deployment
- ✅ Still provides real-time updates
- ✅ Perfect for small-to-medium datasets

### WebSocket Benefits
- ✅ Real-time bidirectional communication
- ✅ Lower latency than polling
- ✅ More efficient (fewer requests)
- ✅ Better user experience

### APScheduler Benefits
- ✅ In-process scheduling
- ✅ No message broker needed
- ✅ Easy to debug
- ✅ Sufficient for most workloads

---

## Scalability Considerations

### Current Setup (Single Server)
- Works great for development
- Suitable for small deployments (< 100 concurrent users)
- In-memory channel layer

### For Growth (Multiple Servers)
1. Switch to Redis channel layer
2. Use Celery for distributed tasks
3. Load balance with Nginx
4. Use PostgreSQL instead of SQLite

### Migration Path
```
Single Server (APScheduler + In-Memory)
    ↓
  Add Redis (Channel Layer)
    ↓
  Add Celery (Distributed Tasks)
    ↓
  Multi-Server Deployment
```

---

## Configuration & Deployment

### Development
```bash
daphne -b 0.0.0.0 -p 8000 Luminabi.asgi:application
```

### Production
```bash
# Systemd service
[Service]
ExecStart=/path/to/venv/bin/daphne -b 127.0.0.1 -p 8000 Luminabi.asgi:application

# Or behind Nginx
upstream daphne {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    location / {
        proxy_pass http://daphne;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## Next Steps

1. ✅ **Settings Configured** - WebSocket, APScheduler ready
2. ⏳ **Build Core Views** - Create HTML class-based views
3. ⏳ **Connect Frontend** - Integrate WebSocket in templates
4. ⏳ **Implement Tasks** - Wire up actual data processing
5. ⏳ **Deploy** - Production setup

All infrastructure is in place to support real-time, event-driven data processing!
