#!/bin/bash
set -e

# ─── Load env ────────────────────────────────────────────────────────────────
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo "❌ .env file not found. Aborting."
    exit 1
fi

REMOTE_USER="root"
REMOTE_HOST="$VULTR_IP"
PROJECT_DIR="/opt/vanguard-milano"

echo "🚀 Deploying VANGUARD MILANO to Vultr @ $REMOTE_HOST ..."

# ─── 1. Prepare remote — install Docker if needed ────────────────────────────
ssh -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_HOST" << 'ENDSSH'
    echo "--- Checking Docker ---"
    if ! command -v docker &> /dev/null; then
        echo "Installing Docker..."
        apt-get update -qq
        apt-get install -y -qq apt-transport-https ca-certificates curl software-properties-common
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
        add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
        apt-get update -qq
        apt-get install -y -qq docker-ce
        systemctl start docker
        systemctl enable docker
        echo "✅ Docker installed."
    else
        echo "✅ Docker already present."
    fi
    mkdir -p /opt/vanguard-milano
ENDSSH

# ─── 2. Sync project files ───────────────────────────────────────────────────
echo "📦 Syncing project files..."
# Exclude local dev artefacts
rsync -az --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' \
    ./ "$REMOTE_USER@$REMOTE_HOST:$PROJECT_DIR/"

# ─── 3. Build and start container ────────────────────────────────────────────
echo "🏗️  Building Docker image..."
ssh "$REMOTE_USER@$REMOTE_HOST" << ENDSSH
    cd $PROJECT_DIR

    docker build -t vanguard-milano .

    # Stop existing container gracefully
    docker stop vanguard-milano-app 2>/dev/null || true
    docker rm   vanguard-milano-app 2>/dev/null || true

    # Run with both ports exposed:
    # Port 80  → Streamlit frontend (main public UI)
    # Port 8000 → FastAPI backend   (API / judges testing)
    docker run -d \
        --name vanguard-milano-app \
        -p 80:8501 \
        -p 8000:8000 \
        --restart always \
        --env-file .env \
        -e BACKEND_URL=http://localhost:8000 \
        vanguard-milano

    echo "✅ Container running."
    docker ps | grep vanguard-milano-app
ENDSSH

echo ""
echo "═══════════════════════════════════════════════════════"
echo "✅  VANGUARD MILANO is live!"
echo "   🖥️  UI  → http://$REMOTE_HOST"
echo "   🔌  API → http://$REMOTE_HOST:8000"
echo "   📖  Docs→ http://$REMOTE_HOST:8000/docs"
echo "═══════════════════════════════════════════════════════"