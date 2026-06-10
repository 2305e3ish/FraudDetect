import time
import random
import requests

API_URL = "http://127.0.0.1:8000/score_transaction"

PROFILES = [
    {"user_id": "U1_AvgSpender", "avg_amount": 50, "known_device_prob": 0.95, "avg_distance": 2},
    {"user_id": "U2_Traveler", "avg_amount": 800, "known_device_prob": 0.70, "avg_distance": 500},
    {"user_id": "U3_HighRoller", "avg_amount": 5000, "known_device_prob": 0.99, "avg_distance": 10},
]

def generate_transaction():
    profile = random.choice(PROFILES)
    
    # 85% normal behavior, 15% anomalous
    is_anomaly = random.random() < 0.15
    
    if not is_anomaly:
        amount = max(1.0, random.gauss(profile["avg_amount"], profile["avg_amount"] * 0.2))
        distance = max(0.0, random.gauss(profile["avg_distance"], profile["avg_distance"] * 0.2))
        device = 1 if random.random() < profile["known_device_prob"] else 0
    else:
        # Anomaly logic
        anomaly_type = random.choice(["high_amount", "far_location", "new_device"])
        if anomaly_type == "high_amount":
            amount = profile["avg_amount"] * random.uniform(5, 20)
            distance = profile["avg_distance"]
            device = 1
        elif anomaly_type == "far_location":
            amount = profile["avg_amount"]
            distance = profile["avg_distance"] + random.uniform(1000, 5000)
            device = 1
        else: # new_device
            amount = profile["avg_amount"]
            distance = profile["avg_distance"]
            device = 0
            
    return {
        "user_id": profile["user_id"],
        "amount": round(amount, 2),
        "distance_from_home": round(distance, 2),
        "known_device": device
    }

def main():
    print("Starting Behavioral Simulator... (Press Ctrl+C to stop)")
    while True:
        tx = generate_transaction()
        try:
            resp = requests.post(API_URL, json=tx, timeout=5)
            if resp.status_code == 200:
                res_data = resp.json()
                action = res_data['action']
                score = res_data['score']
                amount = tx['amount']
                color = "\033[92m" if action == "APPROVE" else ("\033[93m" if action == "OTP_CHALLENGE" else ("\033[93m" if action == "MANUAL_REVIEW" else "\033[91m"))
                reset = "\033[0m"
                print(f"Sent: ${amount:7.2f} | Score: {score:5.2f} | Action: {color}{action}{reset} | Latency: {res_data['latency_ms']}ms")
            else:
                print(f"Error {resp.status_code}: {resp.text}")
        except requests.exceptions.RequestException as e:
            print(f"Connection failed: {e}")
            
        # Realistic stagger
        time.sleep(random.uniform(0.1, 1.5))

if __name__ == "__main__":
    main()
