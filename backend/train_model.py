import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import pickle
import os

def create_synthetic_data(n_samples=5000):
    np.random.seed(42)
    
    # Normal transactions
    amounts_normal = np.random.normal(500, 200, n_samples)
    distance_from_home_normal = np.random.exponential(5, n_samples)
    known_device_normal = np.random.choice([1, 0], n_samples, p=[0.95, 0.05])
    is_fraud_normal = np.zeros(n_samples)
    
    # Fraudulent transactions
    amounts_fraud = np.random.normal(5000, 2000, n_samples // 10)
    distance_from_home_fraud = np.random.exponential(100, n_samples // 10)
    known_device_fraud = np.random.choice([1, 0], n_samples // 10, p=[0.1, 0.9])
    is_fraud_fraud = np.ones(n_samples // 10)
    
    # Combine
    amounts = np.concatenate([amounts_normal, amounts_fraud])
    distances = np.concatenate([distance_from_home_normal, distance_from_home_fraud])
    known_devices = np.concatenate([known_device_normal, known_device_fraud])
    is_fraud = np.concatenate([is_fraud_normal, is_fraud_fraud])
    
    df = pd.DataFrame({
        'amount': amounts,
        'distance_from_home': distances,
        'known_device': known_devices,
        'is_fraud': is_fraud
    })
    
    # Keep amounts positive
    df['amount'] = df['amount'].abs()
    
    return df

def train_and_save_model():
    print("Generating synthetic data...")
    df = create_synthetic_data()
    
    X = df[['amount', 'distance_from_home', 'known_device']]
    y = df['is_fraud']
    
    print("Training Random Forest model...")
    clf = RandomForestClassifier(n_estimators=50, max_depth=10, random_state=42)
    clf.fit(X, y)
    
    model_path = os.path.join(os.path.dirname(__file__), 'model.pkl')
    with open(model_path, 'wb') as f:
        pickle.dump(clf, f)
        
    print(f"Model saved to {model_path}")

if __name__ == "__main__":
    train_and_save_model()
