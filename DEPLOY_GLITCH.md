# 🚀 Marker Engine - Glitch.com Deployment Guide

## Überblick
Diese Anleitung zeigt, wie Sie die Lean-Deep 3.2 Marker Engine auf Glitch.com deployen.

## 📋 Voraussetzungen

1. **Glitch Account**: https://glitch.com
2. **MongoDB Atlas** (kostenlos): https://www.mongodb.com/cloud/atlas
3. **GitHub Repository**: https://github.com/DYAI2025/ME_LD3.2_Backend_deploy

## 🔧 Deployment-Schritte

### 1. MongoDB Atlas Setup (Kostenlose Datenbank)

1. Account erstellen auf [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Kostenlosen M0 Cluster erstellen:
   - Cloud Provider: AWS
   - Region: Nähe zu Glitch (US-East empfohlen)
3. Database User erstellen:
   - Username: `marker_engine`
   - Passwort: Sicheres Passwort generieren
4. Network Access konfigurieren:
   - IP Whitelist: `0.0.0.0/0` (für Glitch erforderlich)
5. Connection String kopieren:
   ```
   mongodb+srv://marker_engine:PASSWORD@cluster.mongodb.net/marker_engine?retryWrites=true&w=majority
   ```

### 2. Glitch Projekt erstellen

#### Option A: Import von GitHub (Empfohlen)

1. Auf [Glitch.com](https://glitch.com) einloggen
2. "New Project" → "Import from GitHub"
3. Repository URL eingeben:
   ```
   https://github.com/DYAI2025/ME_LD3.2_Backend_deploy
   ```

#### Option B: Manuell erstellen

1. "New Project" → "hello-express"
2. Alle Standard-Dateien löschen
3. Folgende Dateien hochladen:
   - `glitch.json`
   - `package.json`
   - `backend/main_glitch.py`
   - `backend/requirements-glitch.txt`

### 3. Environment Variables konfigurieren

In Glitch:
1. Links auf "Tools" → "Terminal" klicken
2. `.env` Datei erstellen:
   ```bash
   cp .env.glitch .env
   ```
3. In der Glitch UI auf `.env` klicken und ausfüllen:
   ```env
   # MongoDB Connection (von Atlas)
   MONGODB_URI=mongodb+srv://marker_engine:IHR_PASSWORT@cluster.mongodb.net/marker_engine?retryWrites=true&w=majority
   
   # Server Settings
   PORT=3000
   HOST=0.0.0.0
   
   # Features
   ENABLE_WEBSOCKET=true
   ENABLE_CACHE=false
   
   # Security
   JWT_SECRET=ihr-geheimer-schluessel-hier
   CORS_ORIGINS=https://ihr-projekt.glitch.me
   ```

### 4. Dependencies installieren

Im Glitch Terminal:
```bash
# Python dependencies installieren
pip3 install --user -r backend/requirements-glitch.txt

# Spacy Sprachmodell herunterladen (optional)
python3 -m spacy download en_core_web_sm
```

### 5. Anwendung starten

Glitch startet automatisch, aber Sie können manuell starten:
```bash
# Im Terminal
cd backend
python3 main_glitch.py
```

## 🎯 Verwendung

### API Endpoints

Ihre Glitch App ist erreichbar unter:
```
https://ihr-projekt-name.glitch.me
```

**Endpoints:**
- `GET /` - Status-Seite
- `GET /health` - Health Check
- `POST /api/analyze` - Text analysieren
- `POST /api/upload` - Datei hochladen
- `GET /api/markers` - Gespeicherte Marker abrufen
- `WS /ws` - WebSocket für Echtzeit-Analyse

### Beispiel-Requests

**Text analysieren:**
```bash
curl -X POST https://ihr-projekt.glitch.me/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Ich fühle mich heute sehr gut!",
    "context": {}
  }'
```

**Health Check:**
```bash
curl https://ihr-projekt.glitch.me/health
```

## ⚡ Performance-Optimierungen

### Glitch Einschränkungen
- **RAM**: 512MB
- **CPU**: Shared
- **Disk**: 200MB
- **Sleep**: Nach 5 Minuten Inaktivität

### Optimierungen

1. **Lightweight Dependencies**: 
   - Keine schweren ML-Libraries (torch, transformers)
   - Einfache Pattern-Matching statt Deep Learning

2. **Caching deaktiviert**:
   - Redis nicht verwendet (spart RAM)

3. **Batch-Größe reduziert**:
   - Max 50 Marker pro Batch

4. **Keep-Alive** (Optional):
   - Verwenden Sie [UptimeRobot](https://uptimerobot.com) um die App aktiv zu halten

## 🔍 Monitoring

### Logs anzeigen
In Glitch:
- "Tools" → "Logs" für Echtzeit-Logs

### Speichernutzung prüfen
```bash
# Im Terminal
curl https://ihr-projekt.glitch.me/api/stats
```

## 🐛 Fehlerbehebung

### "Module not found" Fehler
```bash
pip3 install --user -r backend/requirements-glitch.txt
```

### MongoDB Verbindungsfehler
- Prüfen Sie die IP Whitelist in Atlas (muss 0.0.0.0/0 sein)
- Prüfen Sie Username/Passwort in der Connection URL

### Out of Memory
- Reduzieren Sie BATCH_SIZE in .env
- Deaktivieren Sie nicht benötigte Features

## 🚀 Nächste Schritte

1. **Frontend deployen**: 
   - Separates Glitch-Projekt für Next.js Frontend
   - Oder nutzen Sie Vercel/Netlify für das Frontend

2. **Erweiterte Features**:
   - Upstash Redis für Caching (kostenlose Tier)
   - Sentry für Error Tracking

3. **Skalierung**:
   - Upgrade zu Glitch Pro für mehr Ressourcen
   - Oder Migration zu Railway/Render für Production

## 📝 Wichtige Hinweise

- **Kostenlos**: Glitch Free Tier ist komplett kostenlos
- **Limits**: App schläft nach 5 Min Inaktivität
- **Wakeup**: Erster Request nach Sleep dauert ~10 Sekunden
- **Daten**: MongoDB Atlas Free Tier: 512MB Storage

## 🆘 Support

Bei Problemen:
1. Glitch Support: https://support.glitch.com
2. MongoDB Atlas Docs: https://docs.atlas.mongodb.com
3. GitHub Issues: https://github.com/DYAI2025/ME_LD3.2_Backend_deploy/issues

---

**Status**: ✅ Bereit für Deployment
**Optimiert für**: Glitch.com Free Tier
**Speichernutzung**: < 300MB RAM
**Performance**: ~100-200 Requests/Minute