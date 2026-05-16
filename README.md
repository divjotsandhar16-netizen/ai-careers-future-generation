# Ai Careers for Future Generation

An advanced full-stack rebuild of the Adaptive AI Career Clone Phase.

## What is included

1. Project planning and architecture
2. React frontend setup
3. FastAPI backend setup
4. SQLite database setup
5. ML model training script
6. API integration
7. AI career chatbot
8. Resume analyzer
9. Interview practice system
10. Local deployment workflow

## Folder structure

```text
ai-careers-future-generation/
  backend/
    app/
      api/
      core/
      db/
      models/
      schemas/
      services/
    data/
    scripts/
    requirements.txt
  frontend/
    src/
      api/
      components/
      types/
    package.json
```

## Run backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python scripts/train_readiness_model.py
uvicorn app.main:app --reload
```

Backend API: `http://localhost:8000/api/health`

## Run frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend app: `http://localhost:5173`

## Run on phone

Make sure your phone and laptop are on the same Wi-Fi or hotspot.

Terminal 1:

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8010
```

Terminal 2:

```bash
cd frontend
npm run dev:phone
```

Then open this on your phone, replacing the IP with your laptop IP:

```text
http://172.20.10.3:5173
```

## Deployment idea

- Frontend: Vercel or Netlify
- Backend: Render, Railway, Fly.io, or a VPS
- Database: PostgreSQL in production
- ML model: train offline, save `readiness_model.json`, load it in the backend service

## Next production upgrades

- Add authentication
- Replace SQLite with PostgreSQL
- Add Alembic migrations
- Add OpenAI/Gemini powered chatbot responses
- Add PDF/DOCX resume upload parsing
- Add real user dashboards and analytics
