# SOLARA | Smart Solar Farm Telemetry Portal

A MongoDB-based solar inverter monitoring project built around the NoSQL assignment brief.

## Assignment alignment
- Python, PyMongo Async, FastAPI, Streamlit and MongoDB.
- Nested inverter status, firmware, weather and vendor error-log documents.
- MongoDB aggregation pipeline calculates uptime percentages by manufacturer.
- Render can be used for deployment; local development does not require Render.

## Project structure
```text
solar-telemetry-portal/
├── app/
│   └── main.py          # FastAPI backend
├── app.py               # Streamlit frontend
├── requirements.txt
├── README.md
├── .env.example
└── .gitignore
```

## 1. Setup
Python 3.11 or newer is recommended.

```bash
python -m venv venv
```
Windows:
```bash
venv\Scripts\activate
```
Install:
```bash
pip install -r requirements.txt
```

## 2. Configure MongoDB
Copy `.env.example` to `.env`, then add your MongoDB Atlas connection string.
Never upload `.env` to GitHub.

## 3. Run the backend
```bash
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000/docs

Use `POST /api/telemetry/seed` once to insert sample documents.
Then check `GET /api/telemetry` and `GET /api/analytics/uptime-by-manufacturer`.

## 4. Run the dashboard
Open a second terminal, activate the same virtual environment, then run:
```bash
streamlit run app.py
```
The dashboard can show a demo preview without a database URI. To connect to MongoDB, set `MONGODB_URI` in `.env`.

## 5. Deployment
Deploy the FastAPI backend and Streamlit frontend as separate services on a hosting platform that supports Python. Configure `MONGODB_URI` and `DATABASE_NAME` as environment variables for both services. Render is optional for local development and may have plan limits.

## Main API routes
- `GET /` API welcome
- `GET /health` MongoDB connection check
- `POST /api/telemetry/seed` insert sample inverter documents
- `GET /api/telemetry` read inverter documents
- `GET /api/analytics/uptime-by-manufacturer` aggregation result
