# Frontend — Mutual Fund FAQ Assistant

Stitch-themed chat UI (Obsidian Finance Assistant) for the Tata Mutual Fund facts-only FAQ assistant.

## Setup

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Open http://localhost:5173 — ensure the backend is running on port 8000.

## Environment

| Variable | Example | Purpose |
|----------|---------|---------|
| `VITE_API_BASE_URL` | `http://localhost:8000` | FastAPI backend (leave empty to use Vite proxy) |

## Features (Phase 4 + bugsfile fixes)

- Stitch dark theme from `stitch_tata_fund_fact_assistant/`
- **Powered by Groww** subheading
- Multiple chat sessions (new + delete)
- Highlighted factual answers; **source link below** the answer body
- Refusal / clarification / error states per Stitch designs
- Example question chips wired to `/api/chat`

## Structure

```
frontend/src/
├── api/client.ts
├── components/
│   ├── Chat.tsx
│   ├── ChatSidebar.tsx
│   ├── Disclaimer.tsx
│   ├── ExampleChips.tsx
│   ├── Header.tsx
│   ├── InputBar.tsx
│   ├── MessageBubble.tsx
│   └── Welcome.tsx
├── hooks/useChatSessions.ts
├── utils/parseAnswer.ts
├── App.tsx
└── main.tsx
```

Backend: [backend/README.md](../backend/README.md)
