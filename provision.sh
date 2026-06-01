#!/bin/bash
# provision.sh - one time server setup for blog application
# Run this once on a fresh ubuntu server installation
# re-running should be safe - each step checks for completion before acting
#
# Usage:
# chmod +x provision.sh
# sudo ./provision.sh

set -euo pipefail

# Colors
RED='\033[0;31m'; GREEN='\033[032m'; YELLOW='\033[1;33m' BOLD='\033[1m' NC='\033[0m'

ok()     { echo -e "${GREEN}  ✓ $*${NC}"; }
info()   { echo -e "${BOLD}  -> $*${NC}"; }
warn()   { echo -e "${YELLOW}  i $*${NC}"; }
die()    { echo -e "${RED}  X ERROR: $*${NC}"; }

# ROOT check
[[ $EUID -eq 0 ]] || die "This script must be run with sudo"

# Helper: prompt for a value
prompt() {
    local prompt_text="$1" default="${2:-}"
    local value
    if [[ -n "$default" ]]; then
      read -rp "  ${prompt_text} [${default}]: " value
      echo "${value:-$default}"
    else
      while true; do
        read -rp "  ${prompt_text}: " value
        [[ -n "$value" ]] && break
        warn "This field is required"
      done
      echo "$value"
    fi
}

prompt_secret() {
  local prompt_text="$1"
  loval value
  while true; do
    read -rsp "  ${prompt_text}: " value
    echo ""
    [[ -n "$value" ]] && break
    warn "This field is required"
  done
  echo "$value"
}

# ===============================================
echo ""
echo -e "${BOLD}BLOG APPLICATION PROVISIONING"${NC}
echo ""
echo "This script sets up the blog as s docker container on this server"
echo "It is sage to re-run - completed steps are skipped"

# Gather config
echo -e "${BOLD}-----Configuration-----${NC}"

DOMAIN=$(prompt   "Blog subdomain (e.g. blog.mydomain.com)")
REPO_URL=$(prompt  "Git repo URL" "$(git remote get-url origin 2>/dev/null || echo '')")

echo ""
echo "Mail settings used for password reset and invite emails"
MAIL_SERVER=$(prompt  "SMTP server"  "smtp.gmail.com")
MAIL_PORT=$(prompt  "SMTP port"  "587")
MAIL_USERNAME=$(prompt  "SMTP username (email address)")
MAIL_PASSWORD=$(prompt_secret  "SMTP password or app password")
MAIL_DEFAULT_SENDER=$(prompt  "From address"  "noreply@${DOMAIN}")

echo ""
info "Generating SECRET_KEY..."
SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
ok "SECRET_KEY generated"

echo ""
echo -e "${BOLD}----- Starting provisioning ---------${NC}"
echo ""

# Step 1: install Git and Docker
echo -e "${BOLD}[1/8] Installing Git and Docker...${NC}"
# Git
if command -v git &>/dev/null; then
  ok "Git already installed ($(git --version))"
else
  apt-get update -q
  apt-get install -y -q git
  ok "Git installed"

# Docker
if command -v docker &>/dev/null; then
  ok "Docker already installed ($(docker --version))."
else
  apt-get update -q
  apt-get install -y -q ca-certificates curl gnupg
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  > /etc/apt/sources.list.d/docker.list
  apt-get update -q
  apt-get install -y -q docker-ce docker-ce-cli containerd.io docker-compose-plugin
  systemctl enable docker
  systemctl start docker
  ok "Docker installed."
fi

# Step 2: Directory structure
echo -e "${BOLD}[2/8] Creating application directories...${NC}"
APP_DIR="/srv/blog"
mkdir -p "${APP_DIR}/data" "${APP_DIR}/uploads"
ok "Directories created at ${APP_DIR}."

# Step 3: Clone repo
echo -e "${BOLD}[3/8] Cloning repository...${NC}"
if [[ -f "${APP_DIR}/wsgi.py" ]]; then
  ok "Repository already cloned"
else
  git clone "$REPO_URL" "$APP_DIR"
  ok "Repository cloned"
fi

# Step 4: Write .env file
echo -e "${BOLD}[4/8] Writing .env file...${NC}"
ENV_FILE="${APP_DIR}/.env"
if [[ -f "$ENV_FILE" ]]; then
  warn ".env already exists, leaving it untouched."
else
  cat > "$ENV_FILE" << EOF
FLASK_ENV=production
SECRET_KEY=${SECRET_KEY}
DATABASE_URL=sqlite:////app/instance/blog.db
UPLOAD_FOLDER=/app/uploads

MAIL_SERVER=${MAIL_SERVER}
MAIL_PORT=${MAIL_PORT}
MAIL_USERNAME=${MAIL_USERNAME}
MAIL_PASSWORD=${MAIL_PASSWORD}
MAIL_DEFAULT_SENDER=${MAIL_DEFAULT_SENDER}
EOF
  chmod 600 "$ENV_FILE"
  ok ".env file written with 600 permissions"
fi

# STEP 5: Build and start container
echo -e "${BOLD}[5/8] Building and starting blog container...${NC}"
cd "$APP_DIR"
docker compose build --no-cache
docker compose up -d
ok "Container built and started"

# Step 6: Create admin account
echo -e "${BOLD}[6/8] Create admin account...${NC}"
docker compose exec blog flask create-admin
ok "Admin account created."

# Step 7: Install and configure nginx
echo -e "${BOLD}[7/8] Configuring NGINX...${NC}"
if ! command -v nginx &>/dev/null; then
  apt-get install -y -q nginx
  ok "nginx installed"
else
  ok "nginx already installed"
fi

NGINX_CONF="/etc/nginx/sites-available/blog"
cat > "$NGINX_CONF" << EOF
server {
    listen 80;
    server_name ${DOMAIN};

    client_max_body_size 16M;

    location / {
        proxy_pass              http://127.0.0.1:5000;
        proxy_set_header        Host \$host;
        proxy_set_header        X-Real-IP \$remote_addr;
        proxy_set_header        X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header        X-Forwarded-Proto \$scheme;
    }
}
EOF

ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/blog
[[ -f /etc/nginx/sites-enabled/default ]] && rm /etc/nginx/sites-enabled/default

nginx -t || die "nginx test config failed"
systemctl reload nginx
ok "nginx configured for ${DOMAIN}"

# Step 8: Firewall
echo -e "${BOLD}[8/8] Configuring Firewall...${NC}"
if ! command -v ufw &>/dev/null; then
  apt-get install ufw
  ok "UFW installed"
fi
ufw allow OpenSSH  -q
ufw allow 'Nginx Full' -q
ufw --force enable -q
ok "Firewall configured (SSH + HTTP/HTTPS allowed)"

# DONE
echo ""
echo -e "${GREEN}${BOLD}----- Provisioning complete!------${NC}"
echo ""
echo "Next steps:"
echo ""
echo "1. Set up HTTPS:"
echo "   apt-get install certbot python3-certbot-nginx"
echo "   certbot --nginx -d ${DOMAIN}"
echo ""
echo "2. Add SSH deploy hey to Github:"
echo "   ssh keygen -t ed25519 -C 'github-actions-deploy'"
echo "   Add public key to ~/.ssh/authorized_keys on this server"
echo "   Add private key as SSH_PRIVATE_KEY secret in Github repo settings"
echo "   Also add DEPLOY_HOST (${DOMAIN}) and DEPLOY_USER secrets"
echo ""
echo "3. Point your domain's A record ot this server's PUBLIC IP"
echo "   Visit https://${DOMAIN}/ to confirm everythign works"
echo ""
echo "   Container logs: docker compose -f /srv/blog/docker-compose.yml logs -f"



