# Mess Pehchaan

High-tech face-recognition registration and meal-attendance system for VIT Chennai Non‑Veg Mess — client-side face extraction with secure embeddings, server-side matching, and Redis-backed caching & rate-limiting.

---

## Table of Contents
- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Environment Variables](#environment-variables)
  - [Local Setup](#local-setup)
- [Database Schema](#database-schema)
- [API Reference](#api-reference)
- [Client Behavior & Agents](#client-behavior--agents)
- [Face Recognition Details](#face-recognition-details)
- [Caching, Rate-Limiting & Performance](#caching-rate-limiting--performance)
- [Security & Privacy](#security--privacy)
- [Testing & Validation](#testing--validation)
- [Deployment Recommendations](#deployment-recommendations)
- [Contributing](#contributing)
- [License & Acknowledgments](#license--acknowledgments)

---

## Overview
Mess Pehchaan provides a frictionless, privacy-preserving way for students to register and check in for meals using in-browser face recognition. Raw images never leave the user's browser — only 128-dimensional biometric embeddings are transmitted and stored. The system performs real-time matching to mark attendance for defined meal slots (Breakfast, Lunch, Snacks, Dinner).

---

## Key Features
- Client-side face detection and 128‑dim embedding extraction via face-api.js.
- Euclidean-distance-based matching on a Node.js/Express backend.
- Redis cache for embeddings and short TTL rate-limits to avoid duplicate logs.
- Meal-slot mapping based on server time with personalized greetings.
- Smooth UX: 3s countdown on registration and 3s confirmation on successful check-in.
- Tailwind CSS and Framer Motion for modern, responsive UI.

---

## Architecture
- Frontend (React + Vite) runs face-api.js in the browser to:
  - Capture frames every 2.5s while scanning.
  - Extract 128‑dim embeddings and send embeddings (not images) to the server.
- Backend (Node.js + Express) does:
  - Query Redis cache (mess:users_cache) for user embeddings.
  - On cache miss, load embeddings from PostgreSQL (mess_users), populate Redis.
  - Compute Euclidean distances, pick best match, apply threshold (0.6).
  - Enforce per-user rate limiting via Redis: `rate_limit:<reg_no>` with TTL 30s.
  - Log attendance in PostgreSQL table mess_attendance_logs.
- Redis (ioredis) used for caching embeddings and enforcing rate-limits.
- PostgreSQL stores persistent user embeddings and attendance logs.

Diagram (conceptual):
Client (Webcam + face-api.js) → (embeddings only) → Backend (Redis → Postgres) → Attendance Logs

---

## Technology Stack
- Frontend: React (JSX, 100% JavaScript), Vite, Tailwind CSS, Framer Motion
- Face Processing: face-api.js (TinyFaceDetector, FaceLandmark68Net, FaceRecognitionNet)
- Backend: Node.js + Express (JavaScript)
- Database: PostgreSQL (embeddings as float8[] or using `pgvector`)
- Cache & Rate-Limit: Redis (ioredis)
- Other: Docker (recommended for deployment), Nginx (reverse proxy / TLS)

---

## Getting Started

### Prerequisites
- Node.js (16+ recommended)
- npm or yarn
- PostgreSQL (13+)
- Redis
- Optional: Docker & Docker Compose for local multi-service setup
- Browser with getUserMedia support (Chrome/Firefox/Edge)

### Environment Variables (example)
Create a file `.env` for backend and `.env.local` for frontend as appropriate.

Backend (.env)
```
PORT=4000
DATABASE_URL=postgresql://user:password@localhost:5432/mess_pehchaan
REDIS_URL=redis://localhost:6379
TRUST_PROXY=false
RATE_LIMIT_TTL_SECONDS=30
USERS_CACHE_KEY=mess:users_cache
USERS_CACHE_TTL_SECONDS=3600
MATCH_THRESHOLD=0.6
```

Frontend (.env.local)
```
VITE_API_BASE_URL=http://localhost:4000/api
VITE_FACE_MODELS_BASE_URL=/models
```

### Local Setup

Backend
1. Install dependencies:
   - npm install
2. Run migrations (see Database Schema below or use migration tool):
   - npm run migrate
3. Start server:
   - npm run dev or NODE_ENV=development node src/index.js

Frontend
1. Install dependencies:
   - npm install
2. Run dev server:
   - npm run dev
3. Open the app in the browser at the localhost URL provided by Vite.

Model files
- Place face-api.js model files (TinyFaceDetector, FaceLandmark68Net, FaceRecognitionNet) under `public/models` or serve from a CDN and set `VITE_FACE_MODELS_BASE_URL` accordingly.

---

## Database Schema

Recommended: use pgvector extension for efficient vector storage & similarity search.

Option A — using pgvector (recommended)
```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE mess_users (
  id SERIAL PRIMARY KEY,
  reg_no VARCHAR(32) UNIQUE NOT NULL,
  name TEXT NOT NULL,
  embedding vector(128) NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE mess_attendance_logs (
  id SERIAL PRIMARY KEY,
  reg_no VARCHAR(32) NOT NULL,
  meal_slot VARCHAR(32) NOT NULL,
  matched_confidence DOUBLE PRECISION,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

Option B — using float8[] (no extension)
```sql
CREATE TABLE mess_users (
  id SERIAL PRIMARY KEY,
  reg_no VARCHAR(32) UNIQUE NOT NULL,
  name TEXT NOT NULL,
  embedding double precision[] NOT NULL,  -- should be length 128
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE mess_attendance_logs (
  id SERIAL PRIMARY KEY,
  reg_no VARCHAR(32) NOT NULL,
  meal_slot VARCHAR(32) NOT NULL,
  matched_confidence DOUBLE PRECISION,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

Notes:
- If using pgvector, you can leverage `embedding <-> query_embedding` index for fast nearest neighbors.
- Ensure embeddings are normalized or consistent with the threshold used.

---

## API Reference

Base: POST to /api (example using VITE_API_BASE_URL)

1) POST /api/recognize
- Purpose: Accepts a 128-d embedding and returns matched user and meal-slot confirmation.
- Body:
```json
{
  "embedding": [0.012, -0.231, ..., 0.091]  // length 128
}
```
- Response (success):
```json
{
  "matched": true,
  "reg_no": "19BCS123",
  "name": "A Student",
  "distance": 0.492,
  "meal_slot": "Lunch",
  "greeting": "Good Afternoon, A Student!"
}
```
- Response (no match):
```json
{
  "matched": false,
  "reason": "no-close-match"
}
```

2) POST /api/register
- Purpose: Register a new user embedding.
- Body:
```json
{
  "reg_no": "19BCS123",
  "name": "A Student",
  "embedding": [ ... ]  // 128 floats
}
```
- Response:
```json
{
  "success": true,
  "message": "User registered",
  "reg_no": "19BCS123"
}
```

3) GET /api/meal-slot
- Purpose: Returns current meal slot based on server time and VIT Chennai schedule.
- Response:
```json
{
  "meal_slot": "Lunch",
  "greeting_prefix": "Good Afternoon"
}
```

Implementation notes:
- All endpoints must validate embedding length (128) and numeric types.
- Use HTTPS in production and apply CORS securely.

---

## Client Behavior & Agents

- Capture Agent (Client)
  - Continuously reads webcam stream.
  - Every 2.5 seconds grabs a frame, runs TinyFaceDetector + FaceLandmark68Net + FaceRecognitionNet.
  - If a face exists → extract 128-d embedding → POST to /api/recognize.

- Registration Agent (Client/Backend)
  - UI wizard collects Name + Reg No.
  - Plays a 3s countdown for the user to position themselves.
  - Captures an embedding and calls /api/register.
  - On backend success, invalidates `mess:users_cache` in Redis.

- Greeting/Display Agent (Client)
  - On successful match, show a 3s personalized confirmation overlay (interrupts scanning loop).
  - After 3s, resume continuous scanning.

- Meal-Time Agent (Backend)
  - Server-side mapping of current time to one of: Breakfast, Lunch, Snacks, Dinner (configurable schedule).
  - Returns a greeting prefix and meal-slot for logging.

---

## Face Recognition Details

- Models used (client-side):
  - TinyFaceDetector — fast face detection.
  - FaceLandmark68Net — facial alignment.
  - FaceRecognitionNet — outputs 128-dimensional embedding.

- Embedding matching (backend):
  - Compute Euclidean (L2) distance between captured vector A and stored vector B:
    d(A, B) = sqrt(Σ_{i=1..128} (A_i − B_i)^2)
  - If min distance < 0.6 → consider it a match (configurable via MATCH_THRESHOLD).
  - Note: If you use pgvector, consider `L2` search and tune threshold empirically.

- Practical tips:
  - Normalize input images and maintain consistent preprocessing between registration and scanning.
  - Collect multiple embeddings per user during registration (average or store multiple) to improve robustness.

---

## Caching, Rate-Limiting & Performance

- Embeddings cache:
  - Redis key: `mess:users_cache` (or per-key map)
  - TTL: 3600 seconds (1 hour) by default.
  - On cache miss: fetch from PostgreSQL and repopulate cache.

- Rate-limiter:
  - On successful scan, set `rate_limit:<reg_no>` with TTL 30 seconds.
  - If key exists, skip inserting duplicate attendance rows.
  - TTL configurable via RATE_LIMIT_TTL_SECONDS environment variable.

- Performance recommendations:
  - Use efficient data structure in Redis (hash / serialized JSON / RedisJSON) for fast in-memory lookup.
  - For large user bases, use approximate nearest neighbor indexes (pgvector or specialized vector DB).
  - Use connection pooling for Postgres and Redis to avoid resource spikes.

---

## Security & Privacy

- Raw images NEVER leave the browser — only embeddings are transmitted.
- Use HTTPS for all client-server communication.
- Store minimal PII (name, reg_no) and the embedding vector only as needed.
- Secure Redis and Postgres connections; do not expose database endpoints to public internet.
- Rate-limit API endpoints to prevent abuse (per-IP and per-reg_no).
- Log only necessary events and use appropriate retention policies.

---

## Testing & Validation
- Unit tests for:
  - Backend matching logic (distance calculation, threshold edge-cases).
  - Redis cache & rate-limiter behavior.
  - API input validation and error handling.
- End-to-end tests:
  - Browser-based capture flow e2e using Playwright or Cypress (mock face-api.js in CI where camera isn't available).
- Performance tests:
  - Load-test recognition endpoint with cached and cache-miss scenarios.

---

## Deployment Recommendations
- Containerize backend and frontend; provide Docker Compose for local development (Postgres + Redis + backend + frontend).
- Use environment secrets management (e.g., Vault, cloud secret manager) for DB and Redis credentials.
- Scale Redis using clustering for high throughput.
- Use pgvector for vector search or integrate a dedicated vector DB for very large scale.
- TLS termination at load balancer (Nginx / Cloud LB).
- Run models client-side; reduce backend complexity / cost by not hosting models.

---

## Contributing
1. Fork the repository.
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Add tests and update documentation.
4. Open a PR with a clear description of changes.

Please follow the repository's code style (JS only for app code, using Prettier/ESLint if configured).

---

## License & Acknowledgments
- License: MIT (update as needed)
- Acknowledgments:
  - face-api.js (for client-side face recognition)
  - Tailwind CSS, Framer Motion
  - pgvector for vector indexing (optional)

---

If you'd like, I can:
- Generate a ready-to-run Docker Compose file,
- Produce SQL migration scripts (pgvector and non-pgvector),
- Create a `.env.example` and a sample `nginx.conf`,
- Draft the registration React component (JSX) and backend route handlers (Express) for register/recognize.

Which of these would you like next?
```
