# Monitoring Engine

System monitoring and alerting system for the Autonomous Company OS. This engine handles system health checks, performance tracking, uptime monitoring, alert management, and infrastructure monitoring.

## Features

- **System Health Checks** - Comprehensive health monitoring
- **Performance Tracking** - CPU, memory, disk, network metrics
- **Uptime Monitoring** - Service availability tracking
- **Alert Management** - Intelligent alerting and escalation
- **Log Aggregation** - Centralized log collection
- **Infrastructure Monitoring** - Server and service monitoring
- **Custom Metrics** - Custom metric collection
- **Dashboard** - Real-time monitoring dashboard

## Architecture

```
┌─────────────┐    Metrics   ┌──────────────┐
│   All       │ ────────────> │  Metric      │
│  Services   │               │  Collector   │
└─────────────┘               └──────┬───────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
            ┌───────▼──────┐ ┌────▼────┐ ┌────▼──────┐
            │   Health     │ │ Perf    │ │ Alert      │
            │   Checker    │ │ Monitor │ │  Engine    │
            └──────────────┘ └─────────┘ └───────────┘
                    │                │                │
                    └────────────────┼────────────────┘
                                     │
                    ┌────────────────▼────────────────┐
                    │      Monitoring Dashboard       │
                    │  (Real-time system monitoring)   │
                    └─────────────────────────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
            ┌───────▼──────┐ ┌────▼────┐ ┌────▼──────┐
            │   Log        │ │ Custom  │ │ Incident   │
            │   Aggregator │ │ Metrics │ │  Manager   │
            └──────────────┘ └─────────┘ └───────────┘
```

## Installation

### Prerequisites

- Python 3.9+
- PostgreSQL (for monitoring data)
- Redis (for caching and real-time data)
- Prometheus (optional, for metrics)

### Local Development

```bash
# Clone repository
git clone https://github.com/autonomous-company/monitoring-engine.git
cd monitoring-engine

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your configuration

# Run the service
uvicorn app.main:app --reload --port 8043
```

### Docker Deployment

```bash
# Build and start all services
cd docker
docker-compose up -d

# View logs
docker-compose logs -f monitoring-engine

# Stop services
docker-compose down
```

## Configuration

Configuration is managed via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://localhost/monitoring` | PostgreSQL connection URL |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection URL |
| `PROMETHEUS_URL` | - | Prometheus URL (optional) |

## API Endpoints

### Health & Info
- `GET /health` - Health check
- `GET /` - Service information

### System Health
- `GET /health/system` - Get system health
- `GET /health/services` - Get service health
- `GET /health/{service_id}` - Get specific service health

### Performance
- `GET /performance/cpu` - Get CPU metrics
- `GET /performance/memory` - Get memory metrics
- `GET /performance/disk` - Get disk metrics
- `GET /performance/network` - Get network metrics

### Alerts
- `POST /alerts/create` - Create alert
- `GET /alerts` - List alerts
- `POST /alerts/{alert_id}/acknowledge` - Acknowledge alert

### Logs
- `GET /logs/recent` - Get recent logs
- `POST /logs/query` - Query logs
- `GET /logs/{log_id}` - Get specific log

### Incidents
- `POST /incidents/create` - Create incident
- `GET /incidents/{incident_id}` - Get incident details
- `POST /incidents/{incident_id}/resolve` - Resolve incident

## Usage Examples

### Get System Health

```python
import httpx

async def get_system_health():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8043/health/system"
        )
        return response.json()
```

### Get Performance Metrics

```python
async def get_performance_metrics():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8043/performance/cpu"
        )
        return response.json()
```

### Create Alert

```python
async def create_alert():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8043/alerts/create",
            json={
                "type": "cpu_high",
                "severity": "warning",
                "message": "CPU usage above 80%",
                "threshold": 80,
                "current_value": 85
            }
        )
        return response.json()
```

## Alert Types

- **CPU Alerts** - High CPU usage
- **Memory Alerts** - High memory usage
- **Disk Alerts** - Disk space running low
- **Network Alerts** - Network issues
- **Service Alerts** - Service downtime
- **Custom Alerts** - Custom threshold alerts

## Integration with Other Engines

### All Engines
- Monitors health of all engines
- Provides performance data
- Alerts on system issues

### Notification Engine
- Sends alerts through notification channels
- Escalates critical alerts
- Manages alert notifications

## Monitoring

### Metrics
- System uptime
- Response times
- Error rates
- Resource utilization
- Alert response time

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request
