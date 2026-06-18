# Frontend — Mutual Fund FAQ Assistant

Stitch-exported chat UI for the Tata Mutual Fund FAQ assistant.

## Setup (Phase 4)

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

## Environment

| Variable | Example | Purpose |
|----------|---------|---------|
| `VITE_API_BASE_URL` | `http://localhost:8000` | FastAPI backend (Phase 2c) |

## API endpoints consumed

| Method | Path | Used by |
|--------|------|---------|
| `POST` | `/api/chat` | Chat submit |
| `GET` | `/api/schemes` | Scheme hints (optional) |
| `GET` | `/api/health` | Startup health check |

## Structure (to implement)

```
frontend/src/
├── api/client.ts          # fetch wrappers
├── components/
│   ├── Chat.tsx
│   ├── Disclaimer.tsx
│   ├── ExampleChips.tsx
│   └── MessageBubble.tsx
├── App.tsx
└── main.tsx
```

Backend lives in `backend/` (Python / FastAPI). See [backend/README.md](../backend/README.md) and [implementation.md](../Docs%20folder/implementation.md) Phase 2 & 4.
