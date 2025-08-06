# 🎯 Lean-Deep 3.2 Marker Engine

**End-to-End Semantic Analysis System for Messenger, Email & Audio Dialogs**

## 🚀 Executive Summary

The Marker Engine is a comprehensive system for live and batch-based semantic analysis of communication data. It processes raw media (text & Opus voice messages) through a four-tier Lean-Deep marker hierarchy (ATO→SEM→CLU→MEMA) to deliver visually rich insights via a modern web frontend.

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Next.js Frontend                         │
│  (Timeline, Heat-Map, Markers, WebGPU Charts, YAML Export)  │
└──────────────────────┬──────────────────────────────────────┘
                       │ WebSocket + REST
┌──────────────────────▼──────────────────────────────────────┐
│                  FastAPI Gateway                             │
│              /upload  /analyze  /stream                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                   Core Services                              │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐    │
│  │STT & Emotion│  │Marker Engine │  │  Spark NLP      │    │
│  │(Whisper L3) │  │(ATO→SEM→CLU) │  │(Sentiment, NER) │    │
│  └─────────────┘  └──────────────┘  └─────────────────┘    │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐    │
│  │   Chunker   │  │EmotionDynamics│ │Profile Generator│    │
│  │  (Merger)   │  │(Drift Calc)   │  │   (YAML/JSON)   │    │
│  └─────────────┘  └──────────────┘  └─────────────────┘    │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              Data Layer (MongoDB + File Storage)             │
│   markers_* collections | events_* collections | .opus files │
└──────────────────────────────────────────────────────────────┘
```

## 🎯 Four-Tier Lean-Deep Marker Hierarchy

### ATO (Atomic) → SEM (Semantic) → CLU (Cluster) → MEMA (Meta-Marker)

1. **ATO (Atomic)**: Basic pattern recognition (keywords, phrases)
2. **SEM (Semantic)**: Context-aware semantic analysis
3. **CLU (Cluster)**: Pattern clustering and relationships
4. **MEMA (Meta-Marker)**: High-level behavioral insights

## 📦 Project Structure

```
marker-engine/
├── backend/
│   ├── api/                 # FastAPI gateway
│   ├── services/            # Core business logic
│   │   ├── marker_engine.py
│   │   ├── stt_service.py
│   │   ├── nlp_service.py
│   │   └── emotion_dynamics.py
│   ├── models/              # Data models
│   └── utils/               # Helper utilities
├── frontend/
│   ├── app/                 # Next.js 14 app
│   ├── components/          # React components
│   ├── lib/                 # Client utilities
│   └── public/              # Static assets
├── docker/
│   ├── docker-compose.yml
│   └── services/            # Service Dockerfiles
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
└── docs/
    ├── architecture.md
    ├── api.md
    └── deployment.md
```

## 🔧 Tech Stack

- **Backend**: FastAPI, MongoDB, Whisper, Spark NLP
- **Frontend**: Next.js 14, React, WebGPU (deck.gl)
- **Infrastructure**: Docker, Fly.io, GitHub Actions
- **Real-time**: WebSocket, Socket.io
- **ML/NLP**: Whisper-L-v3, Spark LightPipeline

## 🚀 Quick Start

```bash
# Clone repository
git clone https://github.com/yourusername/marker-engine.git
cd marker-engine

# Start with Docker
docker-compose up

# Or run services individually
cd backend && uvicorn main:app --reload
cd frontend && npm run dev
```

## 📈 Performance Targets

- End-to-end analysis: ≤5s for 10k tokens
- STT real-time factor: ≤1
- Frontend: 60fps @ 50k messages on M1 Mac
- Marker import: <5s with duplicate rejection
- Spark NLP latency: <120ms per 1k tokens

## 🛡️ Security & Compliance

- JWT authentication
- GDPR compliance with data retention controls
- Local processing mode available
- End-to-end encryption option
- OWASP ZAP validated (0 high-risk findings)

## 📋 Sprint Backlog

| Sprint | Focus | Status |
|--------|-------|--------|
| 0 | Infrastructure Bootstrap | 🟢 Complete |
| 1 | Core Data Layer | 🔄 In Progress |
| 2 | STT Pipeline | ⏳ Pending |
| 3 | Merge & Chunker | ⏳ Pending |
| 4 | Marker Engine MVP | ⏳ Pending |
| 5 | Spark NLP Integration | ⏳ Pending |
| 6 | CLU/MEMA & Drift | ⏳ Pending |
| 7 | API Gateway | ⏳ Pending |
| 8 | Frontend Alpha | ⏳ Pending |
| 9 | Profile Service | ⏳ Pending |
| 10 | Security & GDPR | ⏳ Pending |
| 11 | Load & UX Polish | ⏳ Pending |
| 12 | Beta Release | ⏳ Pending |

## 📚 Documentation

- [System Architecture](docs/architecture.md)
- [API Reference](docs/api.md)
- [Deployment Guide](docs/deployment.md)
- [Marker Schema](docs/marker-schema.md)

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

**🚀 Let's build.**