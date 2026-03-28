# AI WhatsApp Business Assistant — Backend

> AI-powered WhatsApp assistant that handles customer queries, takes orders, and processes payments 24/7 for SMBs in India.

---

## Prerequisites

| Tool       | Version  | Notes                                            |
|------------|----------|--------------------------------------------------|
| **Python** | 3.11+    | [python.org](https://www.python.org/downloads/)  |
| **MongoDB**| 7.x      | Local install **or** [Atlas free tier](https://www.mongodb.com/atlas)  |
| **Qdrant** | latest   | Docker: `docker run -p 6333:6333 qdrant/qdrant`  |

---

## Quick Start

### 1. Clone & enter the project

```bash
cd backend
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
# Copy the template and edit with your values
cp .env.example .env
```

### 5. Start external services

```bash
# MongoDB (if not already running)
mongod

# Qdrant via Docker
docker run -p 6333:6333 qdrant/qdrant
```

### 6. Run the server

```bash
python main.py
```

The server starts at **http://localhost:8000**.

---

## Testing

### Health check

```bash
curl http://localhost:8000/health
```

**Expected response:**

```json
{
  "status": "healthy",
  "mongodb": "connected",
  "qdrant": "connected",
  "timestamp": "2026-03-20T10:30:00+00:00",
  "environment": "development",
  "version": "0.1.0"
}
```

### API docs (development only)

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Project Structure

```
backend/
├── app/
│   ├── core/
│   │   ├── config.py        # Pydantic Settings configuration
│   │   ├── database.py      # Async MongoDB connection (Motor)
│   │   └── vector_db.py     # Qdrant vector database connection
│   ├── api/                 # API route handlers (Phase 2+)
│   ├── models/              # Pydantic / ODM models (Phase 2+)
│   ├── services/            # Business logic (Phase 2+)
│   └── utils/
│       └── logger.py        # Structured logging setup
├── logs/                    # Auto-created log files
├── main.py                  # FastAPI entry point
├── requirements.txt         # Pinned dependencies
├── .env.example             # Environment variable template
└── README.md                # ← You are here
```

---

## Environment Variables

| Variable                | Required | Default                      | Description                        |
|-------------------------|----------|------------------------------|------------------------------------|
| `ENVIRONMENT`           | No       | `development`                | Runtime env (development/production)|
| `DEBUG`                 | No       | `true`                       | Enable debug mode & docs           |
| `MONGODB_URI`           | Yes      | `mongodb://localhost:27017`  | MongoDB connection string          |
| `MONGODB_DB_NAME`       | No       | `whatsapp_business_agent`    | Database name                      |
| `QDRANT_URL`            | Yes      | `http://localhost:6333`      | Qdrant server URL                  |
| `QDRANT_API_KEY`        | No       | —                            | Qdrant API key (cloud only)        |
| `GEMINI_API_KEY`        | No*      | —                            | Google Gemini key (Phase 2+)       |
| `TWILIO_ACCOUNT_SID`    | No*      | —                            | Twilio SID (Phase 3+)             |
| `TWILIO_AUTH_TOKEN`     | No*      | —                            | Twilio token (Phase 3+)           |
| `RAZORPAY_KEY_ID`       | No*      | —                            | Razorpay key (Phase 4+)           |
| `RAZORPAY_KEY_SECRET`   | No*      | —                            | Razorpay secret (Phase 4+)        |
| `JWT_SECRET_KEY`        | Yes      | `change-me-in-production`    | JWT signing secret                 |
| `JWT_ALGORITHM`         | No       | `HS256`                      | JWT algorithm                      |
| `JWT_EXPIRATION_MINUTES`| No       | `1440`                       | JWT token TTL (minutes)            |

\* Required in later phases.

---

## Troubleshooting

| Issue                          | Fix                                                     |
|-------------------------------------------|-------------------------------------------------|
| Port 8000 in use               | Change `PORT` in `.env`                                  |
| MongoDB connection failed      | Ensure `mongod` is running or Atlas URI is correct       |
| Qdrant connection failed       | Ensure Qdrant container is running on port 6333          |
| `ModuleNotFoundError`          | Activate virtualenv and re-run `pip install -r …`        |

---

## License

Private — All rights reserved.
