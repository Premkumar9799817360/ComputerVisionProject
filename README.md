# 👁 SightFlow – AI Proctoring & Visual Monitoring System

Real-time vision-powered AI for intelligent proctoring. Verify identities, detect spoofing, monitor suspicious behavior, and generate AI-powered compliance reports.

---

## 🚀 Quick Start (3 Steps)

### Step 1: Install Dependencies

**Install CMake (required for face_recognition):**

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y cmake libopenblas-dev liblapack-dev libx11-dev python3-dev
```

**macOS:**
```bash
brew install cmake
```

**Windows:**
- Install [CMake](https://cmake.org/download/) and [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)

**Then install Python packages:**
```bash
pip install -r requirements.txt
```

> ⚠️ If `face_recognition` fails to install, the system automatically falls back to OpenCV-only mode (still fully functional).

### Step 2: Configure (Optional - for AI summaries)

Edit `.env` file:
```
GROQ_API_KEY=your_free_key_here
```

Get a **free** API key at [console.groq.com](https://console.groq.com) (no credit card required).

Without this key, the system still works — risk scoring, detection, and PDF reports all function. AI text summaries will show a placeholder message.

### Step 3: Run

```bash
python run.py
```

Open your browser: **http://localhost:8000**

---

## 📁 Project Structure

```
sightflow/
├── main.py                          # FastAPI app entry point
├── run.py                           # Startup script
├── requirements.txt                 # Python dependencies
├── .env                             # Configuration (API keys, settings)
│
├── backend/
│   ├── config.py                    # Config loader
│   ├── models/
│   │   └── session.py               # Session & Event data models
│   ├── services/
│   │   ├── vision.py                # Face detection, verification, liveness
│   │   ├── risk_engine.py           # Risk scoring engine
│   │   ├── llm_analysis.py          # Groq LLM integration
│   │   ├── report_generator.py      # PDF report generation
│   │   └── session_store.py         # In-memory session management
│   └── routers/
│       ├── session_router.py        # REST API endpoints
│       └── ws_router.py             # WebSocket real-time endpoint
│
├── frontend/
│   ├── templates/
│   │   ├── index.html               # Landing page
│   │   ├── monitor.html             # Live monitoring page
│   │   └── dashboard.html           # Sessions dashboard
│   └── static/
│       ├── css/style.css            # All styles
│       └── js/
│           ├── utils.js             # Shared utilities
│           ├── monitor.js           # Monitor page logic
│           └── dashboard.js         # Dashboard logic
│
└── reports/                         # Generated PDF reports saved here
```

---

## 🔬 Features

### Feature 1: Real-Time Face Verification
- Extracts face embeddings using `face_recognition` library (dlib-based)
- Compares live frame embedding vs registered embedding using cosine similarity
- Returns identity match percentage (0-100%)
- Threshold: 50% = match

### Feature 2: Liveness Detection (Anti-Spoofing)
- Frame-to-frame pixel variation analysis
- OpenCV eye cascade detection
- Flags static images (photo spoofing) when motion < threshold and no eyes detected

### Feature 3: Multi-Face Detection
- Uses `face_recognition.face_locations()` or OpenCV Haar cascade fallback
- Triggers alert when 2+ faces detected in frame
- Throttled to avoid spam (once per 8 seconds)

### Feature 4: Absence Detection
- Tracks timestamp of last detected face
- Triggers alert after 5 seconds of no face (configurable via `.env`)
- Throttled to alert once per 10 seconds

### Feature 5: Risk Scoring Engine
| Event | Points |
|-------|--------|
| Face Mismatch | +50 per incident |
| Liveness Fail | +40 per incident |
| Multiple Faces | +30 per incident |
| Absence | +20 per incident |

- **0-29**: 🟢 SAFE
- **30-59**: 🟡 WARNING  
- **60+**: 🔴 HIGH RISK

### Feature 6: AI Session Summary (LLM)
- After session ends, all events are structured into a prompt
- Groq LLM (llama3-8b) generates natural language summary
- Falls back to rule-based text if no API key

### Feature 7: Explainable AI
- Converts risk breakdown into structured prompt
- LLM explains WHY each factor contributed to risk score
- Actionable, human-readable output

### Feature 8: AI Compliance PDF Report
- Risk bar chart (matplotlib)
- Event timeline chart
- AI-generated summary, explanation, recommendation
- Event log table
- Download as PDF via dashboard or monitor page

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/session/create` | Create new session |
| GET | `/api/session/list` | List all sessions |
| GET | `/api/session/{id}/status` | Get session status + risk |
| GET | `/api/session/{id}/analysis` | Get AI analysis |
| GET | `/api/session/{id}/report` | Download PDF report |
| POST | `/api/session/{id}/end` | End session |
| DELETE | `/api/session/{id}` | Delete session |
| WS | `/ws/{session_id}` | Real-time frame stream |

### WebSocket Messages

**Register face:**
```json
{ "action": "register", "frame": "<base64_image>" }
```

**Send frame:**
```json
{ "action": "frame", "frame": "<base64_image>" }
```

**Response:**
```json
{
  "status": "ok|alert|error",
  "face_count": 1,
  "identity_score": 87.3,
  "identity_match": true,
  "liveness": true,
  "alerts": ["multi_face"],
  "risk_score": 30,
  "risk_level": "WARNING"
}
```

---

## ⚙️ Configuration (.env)

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_API_KEY` | — | Free Groq API key for AI summaries |
| `APP_HOST` | `0.0.0.0` | Server host |
| `APP_PORT` | `8000` | Server port |
| `ABSENCE_THRESHOLD_SECONDS` | `5` | Seconds before absence alert |
| `RISK_HIGH_THRESHOLD` | `60` | Score for HIGH RISK classification |
| `RISK_WARNING_THRESHOLD` | `30` | Score for WARNING classification |

---

## 🔧 Troubleshooting

**`face_recognition` install fails:**
```bash
# Install dlib manually first
pip install dlib
pip install face_recognition
```
If dlib fails, the system uses OpenCV-only mode automatically.

**Camera not detected:**
- Ensure browser has camera permissions
- Try a different browser (Chrome recommended)

**WebSocket connection fails:**
- Ensure the server is running on correct port
- Check firewall isn't blocking WebSocket connections

**PDF report fails:**
- Ensure `reports/` directory exists (created automatically)
- Check matplotlib is installed: `pip install matplotlib`

---

## 📦 Dependencies Summary

| Package | Purpose |
|---------|---------|
| `fastapi` | Web framework |
| `uvicorn` | ASGI server |
| `websockets` | WebSocket support |
| `opencv-python-headless` | Computer vision |
| `face-recognition` | Face embeddings (optional) |
| `numpy` | Array operations |
| `Pillow` | Image processing |
| `groq` | Free LLM API |
| `fpdf2` | PDF generation |
| `matplotlib` | Chart generation |
| `jinja2` | HTML templates |

---

## 📝 Notes

- **Data Privacy**: All session data is stored in-memory and cleared on server restart. No data is sent to external servers except the Groq LLM API (when configured).
- **Production**: For production use, replace in-memory store with a database (PostgreSQL/SQLite).
- **Performance**: Sends 1 frame/second to backend for analysis. Adjust in `monitor.js` `captureInterval` if needed.
