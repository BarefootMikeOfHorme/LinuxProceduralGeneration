# VaultMind Forge - Deployment Guide

This guide covers deployment options for VaultMind Forge.

## Quick Start (Docker)

The fastest way to deploy VaultMind Forge:

```bash
# 1. Clone repository
git clone https://github.com/BarefootMikeOfHorme/LinuxProceduralGeneration.git
cd LinuxProceduralGeneration

# 2. Copy environment template
cp .env.example .env

# 3. Generate API key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 4. Edit .env and set your API key
nano .env  # or your preferred editor

# 5. Start with Docker Compose
docker-compose up -d

# 6. Check health
curl http://localhost:8000/api/health
```

---

## Deployment Options

### Option 1: Docker (Recommended for Production)

**Pros:**
- Isolated environment
- Easy updates
- Consistent across platforms
- Automatic restarts

**Requirements:**
- Docker 20.10+
- Docker Compose 2.0+
- 8GB RAM minimum (16GB recommended)
- 20GB disk space

**Steps:**

1. **Configure environment:**
   ```bash
   cp .env.example .env
   ```

2. **Set required variables in `.env`:**
   ```bash
   VAULTMIND_AUTH_ENABLED=true
   VAULTMIND_API_KEY=your-generated-key-here
   VAULTMIND_LOG_LEVEL=INFO
   ```

3. **Build and start:**
   ```bash
   docker-compose up -d
   ```

4. **View logs:**
   ```bash
   docker-compose logs -f vaultmind-forge
   ```

5. **Stop:**
   ```bash
   docker-compose down
   ```

6. **Update:**
   ```bash
   git pull
   docker-compose build
   docker-compose up -d
   ```

---

### Option 2: Systemd Service (Linux)

**Pros:**
- Native Linux integration
- Automatic startup on boot
- System-level logging

**Requirements:**
- Linux with systemd
- Python 3.10+
- Node.js 18+

**Steps:**

1. **Install dependencies:**
   ```bash
   # Python dependencies
   python3 -m venv .venv312
   source .venv312/bin/activate
   pip install -r requirements.txt

   # Web UI dependencies
   cd web_ui
   npm install
   npm run build
   cd ..
   ```

2. **Create systemd service:**
   ```bash
   sudo nano /etc/systemd/system/vaultmind-forge.service
   ```

   ```ini
   [Unit]
   Description=VaultMind Forge API Server
   After=network.target

   [Service]
   Type=simple
   User=your-username
   WorkingDirectory=/path/to/VaultMind-Forge
   Environment="PATH=/path/to/VaultMind-Forge/.venv312/bin"
   EnvironmentFile=/path/to/VaultMind-Forge/.env
   ExecStart=/path/to/VaultMind-Forge/.venv312/bin/uvicorn backend.api:app --host 0.0.0.0 --port 8000
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

3. **Enable and start:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable vaultmind-forge
   sudo systemctl start vaultmind-forge
   ```

4. **Check status:**
   ```bash
   sudo systemctl status vaultmind-forge
   sudo journalctl -u vaultmind-forge -f
   ```

---

### Option 3: Manual Development Setup

**For local development only:**

1. **Backend:**
   ```bash
   python3 -m venv .venv312
   source .venv312/bin/activate  # Windows: .venv312\Scripts\activate
   pip install -r requirements.txt

   # Set environment variables
   export VAULTMIND_AUTH_ENABLED=false  # Dev mode
   export VAULTMIND_LOG_LEVEL=DEBUG

   # Start backend
   uvicorn backend.api:app --reload --port 8000
   ```

2. **Frontend (separate terminal):**
   ```bash
   cd web_ui
   npm install
   npm run dev  # Runs on port 5173 by default
   ```

---

## Production Checklist

Before deploying to production:

### Security
- [ ] Set `VAULTMIND_AUTH_ENABLED=true`
- [ ] Generate strong API key (32+ characters)
- [ ] Never commit `.env` file
- [ ] Use HTTPS (nginx/traefik reverse proxy)
- [ ] Configure firewall (only expose necessary ports)
- [ ] Set up SSL certificates (Let's Encrypt)

### Performance
- [ ] Allocate sufficient RAM (8GB minimum, 16GB+ recommended)
- [ ] Configure rate limits appropriately
- [ ] Set up Redis for distributed rate limiting (if running multiple instances)
- [ ] Mount persistent volumes for logs, data, models

### Monitoring
- [ ] Check `/api/health` endpoint works
- [ ] Set up log rotation
- [ ] Configure alerts for errors
- [ ] Monitor disk space (models/output can be large)

### Backup
- [ ] Backup `./data/` directory (SQLite database)
- [ ] Backup `.env` file (securely!)
- [ ] Backup workflow definitions

---

## Environment Variables Reference

See `.env.example` for all available options.

**Required:**
- `VAULTMIND_API_KEY` - API authentication key

**Security:**
- `VAULTMIND_AUTH_ENABLED` - Enable/disable auth (default: true)

**Logging:**
- `VAULTMIND_LOG_LEVEL` - DEBUG, INFO, WARNING, ERROR, CRITICAL

**Paths:**
- `VAULTMIND_MODELS_DIR` - Model storage location
- `VAULTMIND_OUTPUT_DIR` - Generated output location
- `VAULTMIND_CHECKPOINTS_DIR` - Checkpoint storage

**Rate Limiting:**
- `RATE_LIMIT_STORAGE` - `memory://` or `redis://localhost:6379`

---

## Reverse Proxy Setup (Nginx)

For HTTPS and domain setup:

```nginx
server {
    listen 80;
    server_name vaultmind.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name vaultmind.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/vaultmind.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/vaultmind.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## Troubleshooting

### Docker container won't start

```bash
# Check logs
docker-compose logs vaultmind-forge

# Common issues:
# 1. Port already in use - change PORT in .env
# 2. Missing API key - set VAULTMIND_API_KEY in .env
# 3. Insufficient resources - increase Docker limits
```

### API returns 401 Unauthorized

```bash
# Check auth is enabled and key is correct
curl -H "X-API-Key: your-key-here" http://localhost:8000/api/health
```

### Can't access from another machine

```bash
# Check firewall allows port 8000
sudo ufw allow 8000/tcp  # Ubuntu
sudo firewall-cmd --add-port=8000/tcp --permanent  # CentOS
```

### Logs filling up disk

```bash
# Logs auto-rotate at 10MB, but you can manually clean:
rm -f logs/*.log.*

# Or adjust rotation in backend/logging_config.py
```

---

## Updating

### Docker:
```bash
git pull
docker-compose down
docker-compose build
docker-compose up -d
```

### Systemd:
```bash
git pull
source .venv312/bin/activate
pip install -r requirements.txt
cd web_ui && npm install && npm run build && cd ..
sudo systemctl restart vaultmind-forge
```

---

## Support

- Documentation: `./docs/`
- Issues: https://github.com/BarefootMikeOfHorme/LinuxProceduralGeneration/issues
- License: See LICENSE.md (Michael Sovereign License v1.0)

---

**Last Updated:** December 9, 2025
