import asyncio
import pickle
import os
import time
import random
from typing import List, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel, Field
from sklearn.ensemble import RandomForestClassifier
import pandas as pd

# Load model
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'model.pkl')
model: Optional[RandomForestClassifier] = None

# Baseline configurations for risk factor logic
# (In a real app, this would be fetched per-user from a database)
USER_BASELINES = {
    "amount_threshold": 1500.0,
    "distance_threshold": 50.0
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    # Initialize a dummy model if file is not found (useful for early testing)
    if os.path.exists(MODEL_PATH):
        with open(MODEL_PATH, 'rb') as f:
            model = pickle.load(f)
    else:
        print("Warning: model.pkl not found! Please run train_model.py first.")
        
    # Start the autonomous background simulator for the live demo!
    simulator_task = asyncio.create_task(background_simulator())
    
    yield
    
    # Cleanup
    simulator_task.cancel()

app = FastAPI(title="Adaptive Fraud Response Engine", lifespan=lifespan)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()

class Transaction(BaseModel):
    user_id: str
    amount: float = Field(..., gt=0, description="Transaction amount")
    distance_from_home: float = Field(..., ge=0, description="Distance from primary location in km")
    known_device: int = Field(..., ge=0, le=1, description="1 if known device, 0 otherwise")

class ScoreResponse(BaseModel):
    user_id: str
    amount: float
    score: float
    action: str
    risk_factors: List[str]
    latency_ms: float

def predict_score(amount: float, distance_from_home: float, known_device: int) -> float:
    """Predicts fraud probability score (0 to 100)."""
    if model is None:
        return 0.0 # Fallback
    
    # Use pandas DataFrame to avoid scikit-learn warnings about missing feature names
    df = pd.DataFrame([{
        'amount': amount,
        'distance_from_home': distance_from_home,
        'known_device': known_device
    }])
    proba = model.predict_proba(df)
    # Assuming class 1 is fraud
    score = proba[0][1] * 100
    return score

@app.post("/score_transaction", response_model=ScoreResponse)
async def score_transaction(tx: Transaction):
    start_time = time.time()
    
    # Run ML prediction in a separate thread to prevent blocking the async event loop
    score = await asyncio.to_thread(
        predict_score, 
        tx.amount, 
        tx.distance_from_home, 
        tx.known_device
    )
    
    # Extract deterministic Risk Factors
    risk_factors = []
    if tx.amount > USER_BASELINES["amount_threshold"]:
        risk_factors.append("Amount exceeds historical baseline")
    if tx.distance_from_home > USER_BASELINES["distance_threshold"]:
        risk_factors.append("Location mismatch")
    if tx.known_device == 0:
        risk_factors.append("Unrecognized device")
        
    # Map score to mitigation action
    if score < 50:
        action = "APPROVE"
    elif score < 75:
        action = "OTP_CHALLENGE"
    elif score < 90:
        action = "MANUAL_REVIEW"
    else:
        action = "BLOCK"
        
    latency_ms = (time.time() - start_time) * 1000
    
    response = ScoreResponse(
        user_id=tx.user_id,
        amount=tx.amount,
        score=round(score, 2),
        action=action,
        risk_factors=risk_factors,
        latency_ms=round(latency_ms, 2)
    )
    
    # Broadcast to connected WebSocket clients
    await manager.broadcast(response.model_dump())
    
    return response

@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # We don't expect messages from the client, just keep connection open
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# ---------------------------------------------------------
# AUTONOMOUS BACKGROUND SIMULATOR (FOR LIVE DEMO)
# ---------------------------------------------------------

PROFILES = [
    {"user_id": "U1_AvgSpender", "avg_amount": 50, "known_device_prob": 0.95, "avg_distance": 2},
    {"user_id": "U2_HighRoller", "avg_amount": 800, "known_device_prob": 0.90, "avg_distance": 10},
    {"user_id": "U3_Traveler", "avg_amount": 200, "known_device_prob": 0.60, "avg_distance": 500},
]

async def background_simulator():
    """Continuously generates transactions so the live demo never sits empty."""
    while True:
        profile = random.choice(PROFILES)
        
        # Inject fraud anomalies 10% of the time
        if random.random() < 0.10:
            amount = random.uniform(profile["avg_amount"] * 5, profile["avg_amount"] * 20)
            distance = random.uniform(100, 1000)
            device = 0 # unknown device
        else:
            amount = max(1.0, random.gauss(profile["avg_amount"], profile["avg_amount"] * 0.2))
            distance = max(0.0, random.gauss(profile["avg_distance"], profile["avg_distance"] * 0.5))
            device = 1 if random.random() < profile["known_device_prob"] else 0
            
        tx = Transaction(
            user_id=profile["user_id"],
            amount=round(amount, 2),
            distance_from_home=round(distance, 2),
            known_device=device
        )
        
        # Process the transaction internally
        try:
            await score_transaction(tx)
        except Exception as e:
            print(f"Simulator error: {e}")
            
        # Wait before generating the next one
        await asyncio.sleep(random.uniform(0.5, 2.0))

