# Mess-Pehchaan

A compact, production-ready system for identifying and managing mess (canteen) usage patterns and feedback using AI-assisted analytics and an autonomous agent. Mess-Pehchaan provides data-driven insights, intelligent recommendations, and automated assistance to improve operational efficiency and user experience.

## Key Features

- Unified ingestion of attendance, menu, and feedback data.
- AI-powered anomaly detection and usage forecasting.
- Personalized recommendations and smart notifications.
- Lightweight agent for automating common tasks (reports, alerts, replies).

## Tools & Tech Stack

- Languages: Python (backend/ML), JavaScript/TypeScript (frontend/agent glue)
- Backend & APIs: FastAPI or Flask
- Frontend: React
- Data storage: PostgreSQL or SQLite for easy deployment
- ML libraries: scikit-learn, pandas, NumPy
- Deep learning & NLP: PyTorch or TensorFlow, Hugging Face Transformers
- Search & retrieval: FAISS or elasticsearch (for embeddings/RAG)
- Containerization & infra: Docker, GitHub Actions (CI)
- Other: Redis (caching/queues), Celery or RQ (background jobs)

## Algorithms & AI Techniques

- Data processing: feature engineering, normalization, time-series windowing.
- Forecasting: ARIMA / Prophet or LSTM-based models for short-term demand prediction.
- Classification & detection: supervised classifiers (XGBoost / Random Forest) for identifying anomalous usage or feedback categories.
- NLP: tokenization, embeddings (transformers), intent classification, and sentiment analysis to process feedback and messages.
- Recommendation: collaborative filtering or content-based similarity using embeddings to surface menu/item suggestions.
- Anomaly detection: isolation forest, autoencoders, or statistical control charts for outlier detection.

## AI Agent — Design & How It Works

The AI agent is a modular controller that automates monitoring, decision-making, and user interactions:

1. Input & Retrieval
- Collects structured events (attendance, transactions) and unstructured feedback.
- Retrieves relevant context and historical records using a vector index (embeddings + FAISS/Elasticsearch).

2. Preprocessing
- Normalizes and aggregates inputs (time bucketing, missing-value handling).
- Encodes text inputs into embeddings for semantic search and downstream models.

3. Model Pipeline
- Uses lightweight models for fast inference: classification for intent, forecasting for load prediction, and anomaly detection for alerts.
- For complex reasoning and natural-language responses, it can call a pretrained LLM (locally hosted or API-based) with retrieved context (RAG pattern).

4. Decision & Action
- A policy layer maps model outputs to actions: notify admins, generate a daily report, suggest menu changes, or reply to user feedback.
- Actions are executed via APIs, emails, or push notifications; queued jobs handle retries and throttling.

5. Continuous Learning
- Agent logs outcomes and collects user feedback to retrain models periodically, improving accuracy over time.

## Deployment & Running Locally (Quick Start)

1. Clone the repository.
2. Create a Python virtual environment and install dependencies (requirements.txt).
3. Configure the database and environment variables.
4. Start the backend: `uvicorn app.main:app --reload` (or `flask run`).
5. Start the frontend and any background workers (Redis + Celery).

## Contribution

Contributions are welcome. Open an issue for discussion or submit a PR with small, well-scoped changes and tests.

---

For implementation-specific details (model checkpoints, data schema, and agent policies), see the docs/ directory or the relevant modules in the codebase.