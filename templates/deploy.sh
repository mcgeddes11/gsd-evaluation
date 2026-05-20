#!/bin/bash
# /opt/blog/deploy.sh
# Cron-based deploy script for blog
# Runs every 60 minutes: polls for new commits, tests, migrates, restarts service, rolls back on failure

set -e # exit immediately if script fails

# Configuration
POLL_INTERVAL_MINUTES=60
REPO_ROOT="/opt/blog"
VENV="${REPO_ROOT}/venv"
LOG="${REPO_ROOT}/deploy.log"
SERVICE_NAME="blog-service"
HEALTH_CHECK_WAIT_SECONDS=10

# Helper - log with timestamp
log() {
  local message="$1"
  local timestamp=$(date + '%Y-%m-%d %H:%M:%S')
  echo "[$timetamp}] ${message}" | tee -a "${LOG}"
}

log "====================================="
log "Deploy cycle started"
log "Poll interval: ${POLL_INTERVAL_MINUTES} minutes"

# Step 1 fetch latest refs from Github public repo
# TODO: make this work with private repo
cd "${REPO_ROOT}"
log "Step 1: fetching latest commits from origin/main..."
if ! git fetch origin main >> "${LOG}" 2>&1; then
    log "ERROR: get fetch failed, aborting deploy."
    exit 1
fi

# Step 2: Check if anything changes
CURRENT_HASH=$(git rev-parse HEAD)
REMOTE_HASH=$(git rev-parse origin/main)

if [ "${CURRENT_HASH}" = "${REMOTE_HASH}" ]; then
    log "No new commits. Current HEAD matches origin/main. Skipping deploy."
    exit 0
fi

log "New commits available, deploying.."

# Step 3: Save current commit hash for atomic rollback
PREVIOUS_HASH="${CURRENT_HASH}"
log "Saved snapshot of current commit: ${PREVIOUS_HASH}."
log "Pulling new code from origin/main..."

if ! git pull origin main >> "${LOG}" 2>&1; then
    log "ERROR: git pull failed, rolling back to ${PREVIOUS_HASH}."
    git reset --hard "${PREVIOUS_HASH}"
    exit 1
fi

log "Pull completed successfully"

# Step 4: Runt tests locally as a gate before touching the service
log "Step 4: running tests locally"
source "${VENV}/bin/activate"

if ! pytest 2>&1 | tee -a "${LOG}"; then
    log "ERROR: Tests failed, rolling back to ${PREVIOUS_HASH}"
    git reset --hard "${PREVIOUS_HASH}"
    deactivate 2>/dev/null || true
    exit 1
fi

log "Tests passed, proceeding with deploy"

# Step 5: install and update dependencies
log "Step 5: installing dependencies..."
if ! pip install -q -r "${REPO_ROOT}/requirements.txt" 2>&1 | tee -a "${LOG}"; then
    log "ERROR: pip install failed rolling back to ${PREVIOUS_HASH}"
    git reset --hard "${PREVIOUS_HASH}"
    deactivate 2>/dev/null || true
    exit 1
fi

# Step 6: Run alembic migrations
log "Step 6: Running database migrations..."
export FLASK_ENV=production
if ! flask db upgrade >2&1 | tee -a "${LOG}"; then
    log "ERROR: Migrations failed, rolling back to ${PREVIOUS_HASH}"
    git reset --hard "${PREVIOUS_HASH}"
    # Revert to previous dependencies
    pip install -q -r "${REPO_ROOT}/requirements.txt" 2>&1 | tee -a "${LOG}"
    # Unset flask env var
    unset FLASK_ENV
    deactivate 2>/dev/null || true
    exit 1
fi

log "Migrations completed successfully"

# Step 7: Restart the systemd service
log "Step 7: Restarting the service: ${SERVICE_NAME}..."
if ! systemctl restart "${SERVICE_NAME}" 2>&1 | tee -a "${LOG}"; then
    git reset --hard "${PREVIOUS_HASH}"
    # Revert to previous dependencies
    pip install -q -r "${REPO_ROOT}/requirements.txt" 2>&1 | tee -a "${LOG}"
    systemctl restart "${SERVICE_NAME}" 2>&1 | tee -a "${LOG}"
    unset FLASK_ENV
    deactivate 2>/dev/null || true
    exit 1
fi

log "Service restart initiated"

# Step 8: wait a few seconds to determine service is running
log "Step 8: Health check - check service is running..."
sleep "${HEALTH_CHECK_WAIT_SECONDS}"
if ! systemctl is-active --quiet "${SERVICE_NAME}"; then
    log "ERROR: Service is not activate after restart. Rolling back to ${PREVIOUS_HASH}"
    git reset --hard "${PREVIOUS_HASH}"
    # Revert to previous dependencies
    pip install -q -r "${REPO_ROOT}/requirements.txt" 2>&1 | tee -a "${LOG}"
    systemctl restart "${SERVICE_NAME}" 2>&1 | tee -a "${LOG}"
    unset FLASK_ENV
    deactivate 2>/dev/null || true
    exit 1
fi

log "Service health check passed, service active and running"

unset FLASK_ENV
deactivate 2>/dev/null || true

log "====================================="
log "Deploy cycle completed successfully"
log "Service: ${SERVICE_NAME} is running with latest code"
log "Deployed commit: $(git rev-parse HEAD | cut -c1-7)"
log "====================================="
exit 0










