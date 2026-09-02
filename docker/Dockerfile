FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Sibling package this engine depends on via an editable install (see
# requirements.txt's "-e ../autonomy-events" line, added 2026-08-14 for
# the canonical Severity scale - app/severity_mapping.py). The build
# context is the workspace root (see docker-compose.yml's
# `context: ../..`) specifically so this is reachable - COPY can't reach
# outside its build context. Copied to /app/autonomy-events so it sits
# exactly one level up from WORKDIR below, matching pip's real
# resolution rule for "-e ../X": relative to the process's cwd at
# install time, not to requirements.txt's own location (verified
# empirically - see content-engine's 2026-08-12 Docker-build-fix commit
# for the full writeup, same pattern applied here).
COPY autonomy-events/ /app/autonomy-events/

# Second sibling package, same rule as autonomy-events above - see
# requirements.txt's "-e ../empire-operators" line (app/drift_monitor.py
# depends on its DriftMonitor operator).
COPY empire-operators/ /app/empire-operators/

WORKDIR /app/monitoring-engine
COPY monitoring-engine/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY monitoring-engine/app/ ./app/

# Expose port
EXPOSE 8043

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8043"]
