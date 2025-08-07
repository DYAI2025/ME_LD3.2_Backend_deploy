# 📊 Marker Import Guide - 127 Validated Markers

## 🎯 Überblick

Dieses Dokument erklärt, wie Sie die 127 validierten Marker in MongoDB importieren.

## 📋 Voraussetzungen

1. **MongoDB Connection String** (z.B. MongoDB Atlas)
2. **Python 3.9+** mit pymongo installiert
3. **Ihre Marker-Datei** (JSON oder YAML Format)

## 🚀 Quick Start

### 1. Dependencies installieren

```bash
pip install pymongo pyyaml
```

### 2. Marker-Datei vorbereiten

Ihre 127 Marker sollten in einem dieser Formate vorliegen:

**JSON Format:**
```json
[
  {
    "marker_id": "A_TE_",
    "level": "ATO",
    "pattern": "\\b(test|testing|tested)\\b",
    "description": "Test/Testing marker",
    "category": "action",
    "confidence_threshold": 0.8,
    "dependencies": []
  },
  // ... weitere 126 Marker
]
```

**YAML Format:**
```yaml
- marker_id: A_TE_
  level: ATO
  pattern: '\b(test|testing|tested)\b'
  description: Test/Testing marker
  category: action
  confidence_threshold: 0.8
  dependencies: []
# ... weitere 126 Marker
```

### 3. Import durchführen

#### Dry Run (Test ohne Schreiben):
```bash
python scripts/import_markers.py --file ihre_127_marker.json --dry-run
```

#### Echter Import:
```bash
# Mit MongoDB URI
python scripts/import_markers.py \
  --file ihre_127_marker.json \
  --mongodb-uri "mongodb+srv://user:pass@cluster.mongodb.net/marker_engine"

# Oder mit Environment Variable
export MONGODB_URI="mongodb+srv://user:pass@cluster.mongodb.net/marker_engine"
python scripts/import_markers.py --file ihre_127_marker.json
```

## 📝 Marker-Struktur

Jeder Marker muss mindestens diese Felder haben:

### Pflichtfelder:
- `marker_id`: Eindeutige ID (z.B. "A_TE_", "S_QU_")
- `level`: Marker-Level ("ATO", "SEM", "CLU", "MEMA")
- `pattern`: Regex-Pattern oder Erkennungsmuster

### Optionale Felder:
- `description`: Beschreibung des Markers
- `category`: Kategorie (action, cognitive, emotion, etc.)
- `confidence_threshold`: Schwellwert (0.0 - 1.0)
- `dependencies`: Array von abhängigen Marker-IDs
- `metadata`: Zusätzliche Metadaten
- `dsl_rules`: DSL-Aktivierungsregeln
- `examples`: Beispiele für Matches

## 🔄 Update bestehender Marker

Das Script verwendet **upsert** - das bedeutet:
- **Neue Marker** werden hinzugefügt
- **Bestehende Marker** werden aktualisiert (basierend auf marker_id)
- **Keine Marker** werden gelöscht

## 🧪 Test mit Sample-Daten

Erstellen Sie eine Test-Datei:
```bash
python scripts/import_markers.py --sample
```

Dies erstellt `sample_markers.json` mit Beispiel-Markern.

## 🔍 Validierung

Das Script validiert automatisch:
- ✅ Pflichtfelder vorhanden
- ✅ Level ist gültig (ATO/SEM/CLU/MEMA)
- ✅ Pattern ist nicht leer
- ✅ marker_id ist eindeutig

## 📊 Import-Statistiken

Nach dem Import sehen Sie:
```
✅ Valid markers: 127
❌ Invalid markers: 0

📊 Import Results:
  - Inserted: 127
  - Modified: 0
  - Total processed: 127
  - Total markers in DB: 127

✅ Import completed successfully!
```

## 🔗 MongoDB Atlas Setup

Falls Sie noch keine MongoDB haben:

1. **Kostenloser Account**: https://www.mongodb.com/cloud/atlas
2. **M0 Cluster erstellen** (kostenlos, 512MB)
3. **Database User** anlegen
4. **Network Access**: 0.0.0.0/0 für Fly.io
5. **Connection String** kopieren

## 🐛 Troubleshooting

### "Connection refused"
- Prüfen Sie die MongoDB URI
- Prüfen Sie Network Access in Atlas

### "Invalid marker structure"
- Prüfen Sie die Pflichtfelder
- Nutzen Sie --dry-run zum Testen

### "Duplicate key error"
- marker_id muss eindeutig sein
- Script nutzt upsert (sollte nicht passieren)

## 🎯 Nächste Schritte

Nach dem Import:

1. **Testen Sie beide Backends:**
   - Backend 1: https://[ihre-app-1].fly.dev/api/analyze
   - Backend 2: https://me-ld3-2-backend-deploy.fly.dev/api/analyze

2. **Vergleichen Sie Performance:**
   - Marker-Erkennungsrate
   - Response-Zeit
   - Accuracy

3. **A/B Testing:**
   - Gleiche Texte an beide Backends
   - Vergleichen Sie Ergebnisse
   - Optimieren Sie basierend auf Erkenntnissen

## 📞 Support

Bei Fragen oder Problemen:
- Check die Logs: `fly logs --tail`
- MongoDB Atlas Dashboard für DB-Status
- GitHub Issues für Bug Reports

---

**Status**: ✅ Bereit für Import
**Marker**: 127 validierte Marker
**Backends**: 2 parallel auf Fly.io