# agenticSeek Installatiehandleiding voor Ubuntu 24.04 VPS

## VPS Specificaties
- **IP**: 187.77.64.137
- **CPU**: 2 vCPU
- **RAM**: 8 GB
- **Schijf**: 100 GB
- **OS**: Ubuntu 24.04
- **Docker**: Al geïnstalleerd

## Benodigdheden
- SSH toegang tot de VPS (root@187.77.64.137)
- Deepseek API key: `opx3G1MSykY7aeJBhthZqfTpGgdtqRNQ4gKb55Fb33398151`

## Stap-voor-stap Installatie

### Stap 1: Verbinding maken met VPS
```bash
ssh root@187.77.64.137
```

### Stap 2: Systeem update
```bash
apt update && apt upgrade -y
```

### Stap 3: Git installeren
```bash
apt install -y git
```

### Stap 4: Docker Compose installeren
```bash
apt install -y docker-compose-plugin
```

### Stap 5: Python 3.10 installeren
```bash
apt install -y python3.10 python3.10-dev python3-pip python3-venv build-essential
```

### Stap 6: agenticSeek repository klonen
```bash
cd /opt
rm -rf agenticSeek
git clone https://github.com/Fosowl/agenticSeek.git
cd agenticSeek
```

### Stap 7: .env bestand aanmaken
```bash
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
```

### Stap 8: Workspace directory aanmaken
```bash
mkdir -p /opt/workspace
```

### Stap 9: config.ini bestand configureren
```bash
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
```

### Stap 10: Firewall instellen
```bash
ufw allow 3000/tcp
ufw allow 7777/tcp
ufw allow 8080/tcp
```

### Stap 11: Docker services starten
```bash
chmod +x start_services.sh
./start_services.sh full
```

**BELANGRIJK**: Wacht 5-10 minuten voordat de backend service volledig is gestart. U ziet "backend: 'GET /health HTTP/1.1' 200 OK" in de logs wanneer de backend klaar is.

## Controleer de installatie

### Docker containers controleren
```bash
docker ps
```

### Backend logs bekijken
```bash
docker logs backend
```

### Frontend logs bekijken
```bash
docker logs frontend
```

## Toegang tot de applicatie

Nadat de installatie voltooid is, kunt u de web interface bereiken op:
```
http://187.77.64.137:3000
```

## Probleemoplossing

### Backend start niet
- Controleer de logs: `docker logs backend`
- Controleer of de API key correct is in .env
- Controleer of Docker draait: `docker ps`

### Frontend niet bereikbaar
- Controleer of poort 3000 open is: `ufw status`
- Controleer frontend logs: `docker logs frontend`

### Firewall problemen
```bash
ufw status
ufw allow 3000/tcp
ufw allow 7777/tcp
ufw allow 8080/tcp
```

### Services herstarten
```bash
cd /opt/agenticSeek
docker compose down
./start_services.sh full
```

## Beveiliging

Voor productiegebruik wordt aangeraden om:
1. Een domeinnaam te koppelen aan de VPS
2. Nginx reverse proxy te configureren met HTTPS
3. De firewall te configureren om alleen noodzakelijke poorten open te zetten
4. Regelmatige updates uit te voeren

## Volgende stappen

Na succesvolle installatie:
1. Test de web interface op http://187.77.64.137:3000
2. Configureer eventueel een domeinnaam en HTTPS
3. Maak back-ups van belangrijke bestanden in /opt/workspace
