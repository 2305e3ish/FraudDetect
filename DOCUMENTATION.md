# Project Documentation
**Project Name:** Adaptive Fraud Response Engine

**Architecture:** Asynchronous FastAPI Backend, Vite React Frontend, Scikit-Learn ML

---

## 1. Executive Summary
The **Adaptive Fraud Response Engine** is a modern, real-time streaming platform designed to replace legacy, binary (block/allow) fraud detection systems. By dynamically assessing incoming transactions against behavioral baselines, the engine routes transactions into granular mitigation tiers (Approve, OTP Challenge, Manual Review, Block) using a machine learning risk score. This approach drastically reduces false positives, limits user friction, and optimizes analyst workloads.

---

## 2. The Business Problem
Traditional financial systems rely on rigid static rulesets (e.g., "Block all transactions > $5,000 outside of home country"). This binary approach creates two massive operational challenges:
1. **High False Positives:** Legitimate users traveling or making large purchases face account lockouts, leading to extreme customer dissatisfaction and churn.
2. **Analyst Fatigue:** Human analysts are overwhelmed by evaluating thousands of low-risk alerts that could have been handled by automated step-up authentication.

## 3. The Solution
Implemented a **Dynamic Mitigation Workflow** driven by a Machine Learning model. 
Instead of blocking or allowing, the engine predicts a probability score (0-100) and routes the transaction deterministically:
- Safe transactions stream through transparently.
- Mild anomalies trigger automated Friction (OTP Challenges).
- High-risk anomalies are pinned for Human Analysts.
- Guaranteed fraud is dropped instantly.

---

## 4. System Workflow & Data Flow

1. **Data Generation:** The `simulator.py` script continuously mocks transactions for various user profiles and pushes them via HTTP POST to the backend.
2. **Ingestion & Validation:** The FastAPI endpoint `/score_transaction` receives the payload. `Pydantic` validates the schema (e.g., ensuring `amount` is a positive number).
3. **ML Inference:** The payload is handed to the Scikit-Learn Random Forest model via an asynchronous thread (`asyncio.to_thread`). The model evaluates the transaction against historical distances and amounts.
4. **Logic Routing:** The system calculates explicit "Risk Factors" (e.g., "Location Mismatch") and maps the 0-100 score to an actionable mitigation tier.
5. **Real-Time Broadcast:** The resolved transaction is pushed over a persistent `WebSocket` connection to all connected React clients.
6. **UI Rendering:** The React dashboard routes the payload. Low-risk items enter the auto-scrolling `LiveFeed`, while actionable alerts are pinned to the `DecisionQueue`.

---

## 5. File Index & Directory Structure

```text
FraudDetect/
│
├── backend/
│   ├── requirements.txt      # Python dependencies (FastAPI, scikit-learn, etc.)
│   ├── train_model.py        # ML Script: Generates synthetic data, trains Random Forest, exports model.pkl
│   ├── model.pkl             # The serialized, trained Random Forest model
│   ├── app.py                # Core Engine: FastAPI server, REST endpoint, WebSocket broadcaster
│   ├── simulator.py          # Behavioral Generator: Infinite loop script pushing mock data to the API
│   └── test_api.py           # SDET Suite: Pytest scripts verifying edge cases and async concurrency
│
├── frontend/
│   ├── package.json          # Node dependencies (Vite, React, TailwindCSS)
│   ├── tailwind.config.js    # Tailwind configuration for utility-class styling
│   ├── src/
│   │   ├── index.css         # Global CSS containing Tailwind directives and scrollbar styling
│   │   ├── main.jsx          # React entry point
│   │   ├── App.jsx           # Main Dashboard Layout & WebSocket connection logic
│   │   └── components/
│   │       ├── LiveFeed.jsx        # Ticker component for incoming transactions
│   │       └── DecisionQueue.jsx   # Interactive queue for Analyst actions (Approve, Block, Step-up)
│
├── README.md                 # Recruiter-facing RFC overview
└── DOCUMENTATION.md          # Detailed engineering documentation (This file)
```

---

## 6. Business Logic: Mitigation Tiers

The routing engine inside `app.py` enforces the following deterministic bounds based on the ML Score (0-100):

| ML Score Range | Mitigation Action | UI Treatment | Description |
| :--- | :--- | :--- | :--- |
| **0 - 49** | `APPROVE` | Green (Auto-scrolls) | Standard behavior matching user baseline. Sent to straight-through processing. |
| **50 - 74** | `OTP_CHALLENGE` | Yellow (Pinned) | Mild anomaly (e.g., new device). UI flags for automated Step-Up Auth via SMS/Email. |
| **75 - 89** | `MANUAL_REVIEW` | Orange (Pinned) | High anomaly. Dropped into the human analyst queue for investigation. |
| **90 - 100**| `BLOCK` | Red (Pinned) | Extreme deviation from baseline. Transaction immediately dropped at the gateway. |

---

## 7. Technical Tradeoffs & Architectural Decisions

### A. Random Forest vs. Deep Neural Networks
For tabular financial data, tree-based models like Random Forest vastly outperform Deep Learning models in efficiency and require significantly less data to avoid overfitting. Crucially, tree models offer high "Explainability" (Feature Importance), which is heavily regulated and required in modern FinTech compliance.

### B. WebSockets vs. HTTP Polling
A live transaction feed built on HTTP Polling (e.g., requesting data every 250ms) creates massive TCP handshake overhead and chokes server bandwidth. Upgrading the architecture to a persistent WebSocket (`ws://`) allows the server to instantly "push" data to the client with sub-millisecond latency and minimal network payload.

### C. Async Event Loop Blocking
Python's `asyncio` runs on a single thread. Because `scikit-learn` model inference is a CPU-bound, synchronous operation, running it natively inside an `async def` FastAPI route would block the event loop, causing all concurrent API requests to freeze until the model finishes predicting.
**Solution:** The prediction logic is offloaded to a thread pool using `await asyncio.to_thread()`, keeping the main FastAPI web server perfectly responsive to incoming traffic.

---

## 8. Machine Learning Logic & Training

The machine learning logic is entirely self-contained within `backend/train_model.py`. Because proprietary banking data is highly restricted, the engine relies on a synthetic data generation script to learn behavioral boundaries.

1. **Synthetic Data Generation:** The script uses `numpy` to generate 5,000 mock transactions representing two classes:
   - **Normal Transactions:** Average amount of ~$500, average distance of ~5km from primary location, and happening on a known device 95% of the time.
   - **Fraudulent Transactions:** Average amount of ~$5,000, distance of ~100km, and happening on a new device 90% of the time.
2. **Model Training:** It extracts three features (`amount`, `distance_from_home`, `known_device`) and trains a `RandomForestClassifier` (Scikit-Learn) with 50 estimators and a max depth of 10.
3. **Serialization:** The trained model is exported as a binary `model.pkl` file.
4. **Inference:** When the FastAPI server starts (`app.py`), it loads `model.pkl` directly into memory. The `/score_transaction` endpoint passes incoming live data into the loaded model's `predict_proba()` function to output the 0-100 risk score instantly.

