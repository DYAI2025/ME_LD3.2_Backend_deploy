# 🚀 Marker Engine - Deployment Guide

Das Marker Engine Projekt ist **deployment-ready** für verschiedene Cloud-Plattformen. Hier sind die Anleitungen für die beliebtesten Deployment-Optionen.

## 📦 Vorbereitung

```bash
# Repository klonen
git clone https://github.com/DYAI2025/ME_LD3.2_Backend_deploy.git
cd ME_LD3.2_Backend_deploy

# Environment Variables vorbereiten
cp .env.example .env
# Editiere .env mit deinen Werten
```

## 🚄 Railway

Railway ist die **einfachste Option** mit automatischer Erkennung und One-Click-Deploy.

### Option 1: One-Click Deploy (Empfohlen)
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/marker-engine)

### Option 2: CLI Deploy
```bash
# Railway CLI installieren
npm install -g @railway/cli

# Login und Deploy
railway login
railway up

# Services werden automatisch erkannt durch railway.json
```

### Option 3: GitHub Integration
1. Gehe zu [Railway Dashboard](https://railway.app/dashboard)
2. "New Project" → "Deploy from GitHub repo"
3. Wähle `DYAI2025/ME_LD3.2_Backend_deploy`
4. Railway erkennt automatisch alle Services

**Services werden automatisch provisioniert:**
- MongoDB Atlas
- Redis
- Backend API
- Frontend
- Worker Services

## 🎨 Render

Render bietet kostenlose Tier für Prototyping.

### One-Click Deploy
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/DYAI2025/ME_LD3.2_Backend_deploy)

### Manual Deploy
```bash
# Die render.yaml definiert alle Services
# Einfach Repository in Render Dashboard verbinden
```

**Render Blueprint Features:**
- Auto-scaling
- Persistent Disks
- Background Workers
- Managed Databases

## ✈️ Fly.io

Fly.io ist optimal für global verteilte Apps.

```bash
# Fly CLI installieren
curl -L https://fly.io/install.sh | sh

# Login und Launch
fly auth login
fly launch --config fly.toml

# Deploy
fly deploy

# Secrets setzen
fly secrets set MONGODB_URL="..."
fly secrets set JWT_SECRET="..."

# Scaling
fly scale count 2 --region fra
```

## 🔺 Vercel (Frontend Only)

Für das Frontend kannst du Vercel nutzen:

```bash
# Vercel CLI
npm i -g vercel

# Deploy Frontend
cd frontend
vercel

# Environment Variables in Vercel Dashboard setzen:
# NEXT_PUBLIC_API_URL = https://your-backend.railway.app
# NEXT_PUBLIC_WS_URL = wss://your-backend.railway.app
```

## 🐳 Docker Compose (Self-Hosted)

Für Self-Hosting oder lokale Entwicklung:

```bash
# Alle Services starten
docker-compose up -d

# Mit Production Profile
docker-compose --profile production up -d

# Mit Monitoring
docker-compose --profile monitoring up -d
```

## 🔧 Heroku

```bash
# Heroku CLI
heroku create marker-engine

# Addons hinzufügen
heroku addons:create heroku-postgresql:mini
heroku addons:create heroku-redis:mini
heroku addons:create mongolab:sandbox

# Deploy
git push heroku main

# Oder mit Container Registry
heroku container:push web
heroku container:release web
```

## 🌍 DigitalOcean App Platform

```yaml
# .do/app.yaml
name: marker-engine
region: fra
services:
  - name: backend
    github:
      repo: DYAI2025/ME_LD3.2_Backend_deploy
      branch: main
      deploy_on_push: true
    dockerfile_path: docker/Dockerfile.production
    http_port: 8000
    
  - name: frontend
    github:
      repo: DYAI2025/ME_LD3.2_Backend_deploy
      branch: main
    build_command: cd frontend && npm run build
    run_command: cd frontend && npm start

databases:
  - name: mongodb
    engine: MONGODB
    version: "7"
    
  - name: redis
    engine: REDIS
    version: "7"
```

```bash
doctl apps create --spec .do/app.yaml
```

## 🔑 Environment Variables

Alle Plattformen benötigen diese Environment Variables:

```env
# Backend
MONGODB_URL=mongodb://...
REDIS_URL=redis://...
JWT_SECRET=your-secret-key
CORS_ORIGINS=https://your-frontend.com
ENVIRONMENT=production

# Frontend
NEXT_PUBLIC_API_URL=https://your-backend.com
NEXT_PUBLIC_WS_URL=wss://your-backend.com

# Optional für GPU/Whisper
CUDA_AVAILABLE=false
WHISPER_MODEL=base
```

## 📊 Monitoring & Logging

### Sentry Integration
```bash
# In .env hinzufügen
SENTRY_DSN=https://...@sentry.io/...
```

### Datadog
```yaml
# docker-compose.yml
services:
  datadog:
    image: datadog/agent:latest
    environment:
      - DD_API_KEY=${DD_API_KEY}
      - DD_SITE=datadoghq.eu
```

## 🚨 Production Checklist

- [ ] Environment Variables gesetzt
- [ ] MongoDB Indexes erstellt
- [ ] Redis Cache konfiguriert
- [ ] SSL/TLS aktiviert
- [ ] CORS richtig konfiguriert
- [ ] Health Checks funktionieren
- [ ] Monitoring eingerichtet
- [ ] Backup-Strategie definiert
- [ ] Rate Limiting aktiviert
- [ ] Security Headers gesetzt

## 💡 Tipps

### Kostenoptimierung
- **Railway**: $5 Credit für Start
- **Render**: Free Tier für Static Sites
- **Fly.io**: Free Tier mit 3 shared VMs
- **MongoDB Atlas**: 512MB free cluster
- **Redis Cloud**: 30MB free

### Performance
- Nutze CDN für Frontend Assets (Cloudflare)
- Enable Caching Headers
- Verwende MongoDB Atlas für managed DB
- Redis für Session Storage

### Scaling
```bash
# Railway
railway scale --replicas 3

# Fly.io
fly scale count 3 --region fra

# Render
# Auto-scaling in Dashboard konfigurieren
```

## 🆘 Support

Bei Problemen:
1. Check die Logs: `railway logs` / `fly logs` / `render logs`
2. GitHub Issues: https://github.com/DYAI2025/ME_LD3.2_Backend_deploy/issues
3. Discord Community: [Link]

---

**🎉 Das Marker Engine System ist vollständig deployment-ready!**

Wähle einfach deine bevorzugte Plattform und deploye mit wenigen Klicks oder Commands.