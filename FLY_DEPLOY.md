# 🚀 Marker Engine - Fly.io Deployment

## ✅ Konfiguration korrigiert!

Der Fehler in der `fly.toml` wurde behoben. Das Problem war die doppelte Definition von `http_checks`.

## 📋 Deployment Schritte

### 1. Fly CLI installieren (falls noch nicht vorhanden)
```bash
# macOS
brew install flyctl

# oder mit curl
curl -L https://fly.io/install.sh | sh
```

### 2. Bei Fly.io anmelden
```bash
fly auth login
```

### 3. App erstellen und deployen
```bash
# Im marker-engine Verzeichnis
cd /Users/benjaminpoersch/Projekte/XEXPERIMENTE/claude-flow/claude-flow/marker-engine

# App erstellen (nur beim ersten Mal)
fly launch --name marker-engine-prod --region fra --no-deploy

# Secrets setzen
fly secrets set MONGODB_URI="mongodb+srv://username:password@cluster.mongodb.net/marker_engine"
fly secrets set JWT_SECRET="your-secret-key-here"
fly secrets set REDIS_URL="redis://default:password@redis-server.upstash.io:6379"

# Deployen
fly deploy
```

### 4. Monitoring
```bash
# Logs anzeigen
fly logs

# App Status
fly status

# App öffnen
fly open
```

## 🔧 Umgebungsvariablen

Setzen Sie diese Secrets in Fly.io:
```bash
fly secrets set \
  MONGODB_URI="mongodb+srv://..." \
  JWT_SECRET="..." \
  OPENAI_API_KEY="sk-..." \
  ANTHROPIC_API_KEY="sk-ant-..." \
  REDIS_URL="redis://..." \
  SENTRY_DSN="https://..."
```

## 📊 Ressourcen

Fly.io Free Tier bietet:
- **3 shared-cpu-1x VMs** (256MB RAM each)
- **3GB persistent storage**
- **160GB outbound data transfer**

Für die Marker Engine empfohlen:
```bash
# Skalierung anpassen
fly scale vm shared-cpu-1x --memory 512

# Oder für Production
fly scale vm dedicated-cpu-1x --memory 2048
```

## 🐛 Fehlerbehebung

### Build-Fehler
```bash
# Lokalen Build testen
docker build -f docker/Dockerfile.production -t marker-engine .
docker run -p 8080:8080 marker-engine
```

### Connection Errors
```bash
# Health Check prüfen
curl https://marker-engine-prod.fly.dev/health

# Logs prüfen
fly logs --tail
```

## 🎯 Endpoints

Nach dem Deployment ist Ihre App erreichbar unter:
```
https://marker-engine-prod.fly.dev
```

**API Endpoints:**
- `GET /` - Status
- `GET /health` - Health Check
- `POST /api/analyze` - Text analysieren
- `POST /api/upload` - Datei hochladen
- `WS /ws` - WebSocket für Echtzeit

## 💰 Kosten

**Free Tier:**
- Kostenlos für kleine Apps
- Automatisches Sleep nach Inaktivität

**Hobby Plan ($5/Monat):**
- Keine Sleep-Zeit
- Bessere Performance
- Priority Support

**Production:**
- Ab $25/Monat für dedicated resources

## 🚀 Nächste Schritte

1. **Deploy starten:**
```bash
fly deploy
```

2. **Status prüfen:**
```bash
fly status
fly open
```

3. **Frontend verbinden:**
Update die API URL im Frontend zu `https://marker-engine-prod.fly.dev`

---

**Status**: ✅ Bereit für Deployment
**Region**: Frankfurt (fra)
**Fehler behoben**: fly.toml korrekt konfiguriert