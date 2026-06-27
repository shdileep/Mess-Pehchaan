# Mess-Pehchaan

A compact, production-ready system that identifies, analyzes, and automates improvements for mess (canteen) operations using data-driven analytics and AI. Mess-Pehchaan provides usage forecasting, anomaly detection, intelligent recommendations, and an autonomous agent to streamline reporting and user interactions.

## One-line intro
AI-driven insights and an autonomous assistant to optimize mess usage, menus, and feedback handling.

## Key Features
- Unified ingestion of attendance, menu, transaction and feedback data
- Short-term demand forecasting and anomaly detection
- Automated reports, alerting, and reply suggestions via an AI agent
- Personalized recommendations and searchable feedback retrieval

## Tools & Tech Stack
- Languages: Python (backend, ML), JavaScript/TypeScript (frontend, agent integration)
- Backend: FastAPI or Flask
- Frontend: React
- Database: PostgreSQL (or SQLite for small deployments)
- Caching / Queues: Redis, Celery or RQ
- ML & Data: pandas, NumPy, scikit-learn, XGBoost
- Deep learning / NLP: PyTorch or TensorFlow, Hugging Face Transformers
- Vector search / RAG: FAISS or Elasticsearch
- Containerization & CI: Docker, GitHub Actions

## Algorithms & AI Techniques
- Time-series forecasting: ARIMA / Prophet or LSTM/Transformer models for demand prediction
- Classification & detection: Random Forest / XGBoost, Isolation Forest or autoencoders for anomalies
- NLP: tokenization, transformer embeddings, intent classification, sentiment analysis
- Recommendations: embeddings-based similarity, collaborative/content-based filtering
- Feature engineering: time bucketing, seasonal decomposition, rolling statistics
- Evaluation: cross-validation, backtesting for forecasting, precision/recall for classification

## AI Agent — Design & How It Works
1. Input & Retrieval
   - Collects structured events (attendance, sales) and unstructured feedback/messages.
   - Retrieves context via a vector store (embeddings) for RAG-style lookups.

2. Preprocessing
   - Normalizes, aggregates and imputes data; converts text to embeddings for semantic search.

3. Model Pipeline
   - Lightweight models run for fast inference (forecasting, anomaly detection, intent classification).
   - For complex language responses or reasoning, the agent leverages an LLM with retrieved context.

4. Policy & Actions
   - A policy layer maps model outputs to concrete actions: notify staff, generate reports, suggest menu changes, or auto-respond to feedback.
   - Actions are executed via API calls, email, or push notifications; background workers handle retries and scheduling.

5. Continuous Improvement
   - All agent actions and outcomes are logged. Periodic retraining and label collection improve models over time.

## Quick Start (local)
1. Clone the repository.
2. Create a Python virtualenv and install requirements: `pip install -r requirements.txt`
3. Configure environment variables and a database (Postgres or SQLite).
4. Run backend: `uvicorn app.main:app --reload` (or `flask run`). Start frontend and any workers (Redis + Celery).
5. Load sample data and run model pipelines for initial forecasts and index building.
