# SOLARA | Smart Solar Farm Telemetry Portal

**SOLARA** is an original CleanTech prototype for monitoring a multi-vendor solar farm. It brings inverter status, power output, temperatures, firmware metadata, site weather, telemetry trends and equipment events into one operations view.

> **Data integrity note:** The built-in data is simulated for demonstration. It is not connected to physical inverters and must not be used for operational or safety decisions. The dashboard's *snapshot availability* is the share of currently online inverters, not a historical uptime SLA.

## Product capabilities
- Fleet overview with current output, snapshot availability and attention-needed counts.
- Inverter filtering by solar site and operational state.
- 24-hour simulated telemetry profile and manufacturer comparison.
- Nested vendor-specific metadata and error-event arrays.
- MongoDB document storage and manufacturer-level aggregation.
- FastAPI endpoints with a usable demo fallback when MongoDB is not configured.

## Technology
Python 3.11+, Streamlit, FastAPI, PyMongo, MongoDB Atlas, Pandas and Plotly.

## Project layout
\`\`\`text
solar-telemetry-portal/
├── app/
│   ├── __init__.py
│   ├── database.py
│   ├── demo_data.py
│   └── main.py
├── app.py
├── requirements.txt
├── Dockerfile
├── .env.example
└── .gitignore
\`\`\`

## Run locally (Windows PowerShell)
\`\`\`powershell
py -3.11 -m venv .venv
.venv\\Scripts\\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
\`\`\`
The Streamlit dashboard runs in demo mode without MongoDB.

## Run the API
In another terminal, activate the same environment:
\`\`\`powershell
uvicorn app.main:app --reload
\`\`\`
- API home: http://127.0.0.1:8000/
- Interactive API docs: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

## Connect MongoDB Atlas
1. Create a MongoDB Atlas cluster and database user.
2. Add your current IP address to Network Access.
3. Copy the Python connection string.
4. Copy \`.env.example\` to \`.env\` and set \`MONGODB_URI\` and \`DATABASE_NAME\`.
5. Keep \`USE_MONGODB=true\`.
6. Start the API and call \`POST /api/telemetry/seed\` once to insert the sample inverter documents.
7. Restart the dashboard. It will read the MongoDB \`inverters\` collection when records are present.

Never commit \`.env\` or expose your database password.

## API endpoints
| Method | Endpoint | Purpose |
|---|---|---|
| GET | \`/\` | API welcome |
| GET | \`/health\` | Service and MongoDB status |
| GET | \`/api/inverters\` | List and filter inverters |
| GET | \`/api/inverters/{inverter_id}\` | Read one inverter |
| GET | \`/api/fleet/summary\` | Fleet KPI summary |
| GET | \`/api/analytics/availability-by-manufacturer\` | MongoDB aggregation by manufacturer |
| GET | \`/api/telemetry/{inverter_id}\` | Inverter telemetry |
| POST | \`/api/telemetry/seed\` | Safely upsert sample inverter documents |

## MongoDB document design
Common fields are nested under \`status\`, \`firmware\` and \`weather\`. Vendor-specific fields stay under \`vendor_metadata\`; error events are stored as an array. This document approach accommodates different manufacturer payloads without forcing every vendor into identical columns.

## Deployment notes
Deploy the FastAPI API and Streamlit dashboard as separate services for a simple production topology. Set \`MONGODB_URI\`, \`DATABASE_NAME\` and \`USE_MONGODB\` in each service's environment. Do not deploy with demo credentials. Add authentication, input validation, role-based access, real telemetry ingestion and alert acknowledgement before using with a real solar plant.

## Assignment mapping
Pragyan AI Super 30, Phase 1, Project 5: Renewable Energy — Smart Solar Farm Multi-Inverter Telemetry Portal. The prototype demonstrates nested MongoDB documents and an aggregation pipeline that calculates **snapshot availability** by manufacturer.
