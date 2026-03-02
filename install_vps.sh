#!/bin/bash

# agenticSeek Installatiescript voor Ubuntu 24.04 VPS
# VPS: 187.77.64.137, 2 vCPU, 8GB RAM, 100GB SSD

set -e

echo "=== agenticSeek Installatie Start ==="
echo "Tijd: $(date)"
echo "VPS: $(hostname)"
echo "OS: $(cat /etc/os-release | grep PRETTY_NAME)"
echo ""

# Stap 1: Systeem update
echo "[1/10] Systeem update uitvoeren..."
apt update && apt upgrade -y

# Stap 2: Git installeren
echo "[2/10] Git installeren..."
apt install -y git

# Stap 3: Docker Compose installeren (Docker is al geïnstalleerd)
echo "[3/10] Docker Compose installeren..."
apt install -y docker-compose-plugin

# Stap 4: Python 3.10 en vereiste packages installeren
echo "[4/10] Python 3.10 en vereiste packages installeren..."
apt install -y python3.10 python3.10-dev python3-pip python3-venv build-essential

# Stap 5: agenticSeek repository klonen
echo "[5/10] agenticSeek repository klonen..."
cd /opt
if [ -d "agenticSeek" ]; then
    echo "Directory bestaat al, verwijderen..."
    rm -rf agenticSeek
fi
git clone https://github.com/Fosowl/agenticSeek.git
cd agenticSeek

# Stap 6: .env bestand aanmaken en configureren
echo "[6/10] .env bestand aanmaken en configureren..."
cat > .env << 'EOF'
SEARXNG_BASE_URL="http://searxng:8080"
REDIS_BASE_URL="redis://redis:6379/0"
WORK_DIR="/opt/workspace"
OLLAMA_PORT="11434"
LM_STUDIO_PORT="1234"
BACKEND_PORT="7777"
CUSTOM_ADDITIONAL_LLM_PORT="11435"
DEEPSEEK_API_KEY='opx3G1MSykY7aeJBhthZqfTpGgdtqRNQ4gKb55Fb33398151'
EOF

# Stap 7: Workspace directory aanmaken
echo "[7/10] Workspace directory aanmaken..."
mkdir -p /opt/workspace

# Stap 8: config.ini bestand configureren voor Deepseek API
echo "[8/10] config.ini bestand configureren voor Deepseek API..."
cat > config.ini << 'EOF'
[MAIN]
is_local = False
provider_name = deepseek
provider_model = deepseek-chat
provider_server_address = 
agent_name = Jarvis
recover_last_session = False
save_session = False
speak = False
listen = False
jarvis_personality = False
languages = en
[BROWSER]
headless_browser = True
stealth_mode = False
EOF

# Stap 9: Firewall instellen
echo "[9/10] Firewall instellen voor poorten 3000, 7777, 8080..."
if command -v ufw &> /dev/null; then
    ufw allow 3000/tcp
    ufw allow 7777/tcp
    ufw allow 8080/tcp
    echo "Firewall regels toegevoegd."
else
    echo "UFW niet geïnstalleerd, firewall regels overgeslagen."
fi

# Stap 10: Docker services starten
echo "[10/10] Docker services starten..."
chmod +x start_services.sh
./start_services.sh full

echo ""
echo "=== Installatie Voltooid ==="
echo "Wacht 5-10 minuten voordat de backend service volledig is gestart."
echo "U kunt de web interface bereiken op: http://187.77.64.137:3000"
echo ""
echo "Om de status te controleren:"
echo "  - Docker containers: docker ps"
echo "  - Backend logs: docker logs backend"
echo "  - Frontend logs: docker logs frontend"
echo ""
