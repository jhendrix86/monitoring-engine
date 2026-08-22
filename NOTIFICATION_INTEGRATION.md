# Monitoring-Engine → Notification-Engine Integration

## Implementation Status
✅ **Code Integration Complete** - monitoring-engine now calls notification-engine when alerts are created
⏳ **Infrastructure Setup Required** - end-to-end testing requires Docker/PostgreSQL setup

## Changes Made

### 1. New Notification Client Service
- **File**: `app/services/notification_client.py`
- **Function**: `send_alert_notification()`
- **Purpose**: Sends HTTP POST requests to notification-engine's `/notifications/send` endpoint
- **Features**:
  - Async HTTP client using httpx
  - Configurable recipient and channels
  - Graceful error handling (notification failures don't fail alert creation)
  - Includes alert metadata (id, severity, title, message)

### 2. Alert Router Integration
- **File**: `app/routers/alerts.py`
- **Change**: Modified `create_alert()` endpoint to call notification service after alert creation
- **Behavior**:
  - Alert is created and committed to database first
  - Notification is sent asynchronously
  - Notification failures are logged but don't fail the alert creation
  - Ensures reliable alert storage even if notification is unavailable

### 3. Configuration
- **Environment Variable**: `NOTIFICATION_ENGINE_URL` (default: `http://localhost:8037`)
- **Default Recipient**: `admin@company.com` (configurable in notification_client)
- **Default Channel**: Email (configurable to include SMS, Slack, Discord)

## Testing Requirements

### Infrastructure Needed
1. **PostgreSQL**: Running on localhost:5432
   - Database: `monitoring` (for monitoring-engine)
   - Database: `notifications` (for notification-engine)
2. **Redis**: Running on localhost:6379
3. **Docker**: Required for containerized deployment

### Manual Testing Steps
1. Start infrastructure services:
   ```bash
   cd C:\Users\Jonat\CascadeProjects\deploy
   docker-compose -f docker-compose.infra.yml up -d
   ```

2. Start notification-engine:
   ```bash
   cd C:\Users\Jonat\CascadeProjects\notification-engine
   # Install dependencies and start service
   uvicorn app.main:app --host 0.0.0.0 --port 8037
   ```

3. Start monitoring-engine:
   ```bash
   cd C:\Users\Jonat\CascadeProjects\monitoring-engine
   # Install dependencies and start service
   uvicorn app.main:app --host 0.0.0.0 --port 8036
   ```

4. Create a test alert:
   ```bash
   curl -X POST http://localhost:8036/alerts/create \
     -H "Content-Type: application/json" \
     -d '{
       "alert_type": "system_health",
       "severity": "critical",
       "title": "Test Alert",
       "message": "This is a test alert to verify notification integration"
     }'
   ```

5. Verify notification was created:
   ```bash
   curl http://localhost:8037/notifications/
   ```

## Next Steps
- Set up Docker infrastructure on Acer laptop
- Run end-to-end integration test
- Verify notification delivery to actual email/SMS/etc. (requires SendGrid/Twilio credentials)
- Update HANDOFF.md with test results