import pytest
import asyncio
import time
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch
from app import app

# 1. Threshold Boundary Testing
@pytest.mark.asyncio
@pytest.mark.parametrize("mock_score, expected_action", [
    (49.99, "APPROVE"),
    (50.0, "OTP_CHALLENGE"),
    (74.99, "OTP_CHALLENGE"),
    (75.0, "MANUAL_REVIEW"),
    (89.99, "MANUAL_REVIEW"),
    (90.0, "BLOCK"),
    (99.9, "BLOCK")
])
async def test_threshold_boundaries(mock_score, expected_action):
    """
    Force the mocked ML model to return exactly boundary values to ensure
    the routing logic correctly handles inclusive/exclusive bounds.
    """
    with patch('app.predict_score', return_value=mock_score):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/score_transaction", json={
                "user_id": "test_user",
                "amount": 100.0,
                "distance_from_home": 10.0,
                "known_device": 1
            })
            assert response.status_code == 200
            data = response.json()
            assert data["action"] == expected_action
            assert data["score"] == mock_score

# 2. The 'Fat Finger' & Type Failure
@pytest.mark.asyncio
async def test_fat_finger_massive_integer():
    """Submit a transaction where amount is a massive integer."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/score_transaction", json={
            "user_id": "test_user",
            "amount": 99999999999999,
            "distance_from_home": 10.0,
            "known_device": 1
        })
        assert response.status_code == 200
        data = response.json()
        assert "Amount exceeds historical baseline" in data["risk_factors"]

@pytest.mark.asyncio
async def test_fat_finger_string_amount():
    """Submit a transaction where amount is a string 'five hundred'."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/score_transaction", json={
            "user_id": "test_user",
            "amount": "five hundred",
            "distance_from_home": 10.0,
            "known_device": 1
        })
        assert response.status_code == 422 # Unprocessable Entity

@pytest.mark.asyncio
async def test_missing_device_id_field():
    """Submit a transaction missing the known_device field entirely."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/score_transaction", json={
            "user_id": "test_user",
            "amount": 100.0,
            "distance_from_home": 10.0
        })
        assert response.status_code == 422 # Unprocessable Entity

# 3. The Asynchronous Blocking Trap
@pytest.mark.asyncio
async def test_asynchronous_blocking():
    """
    Fire 100 concurrent requests using asyncio.gather.
    Assertion: The average response time must not degrade linearly. 
    It ensures the ML inference isn't blocking the event loop.
    """
    async def make_request(ac):
        return await ac.post("/score_transaction", json={
            "user_id": "test_user",
            "amount": 100.0,
            "distance_from_home": 10.0,
            "known_device": 1
        })

    # We mock predict_score to simulate a model taking e.g., 50ms per inference
    # If the event loop is blocked, 100 requests * 50ms = 5 seconds.
    # If it's correctly threaded, it should be much faster.
    def mock_slow_predict(*args, **kwargs):
        time.sleep(0.05)
        return 50.0

    with patch('app.predict_score', side_effect=mock_slow_predict):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            start_time = time.time()
            tasks = [make_request(ac) for _ in range(100)]
            responses = await asyncio.gather(*tasks)
            end_time = time.time()
            
            total_time = end_time - start_time
            
            assert all(r.status_code == 200 for r in responses)
            
            # 100 * 50ms = 5s. With threading, it should be significantly less than 5s
            # depending on the thread pool size (default in asyncio is min(32, os.cpu_count()+4)).
            # We assert that it didn't strictly serialize (total_time < 5.0)
            assert total_time < 4.5, f"Requests seem to be blocking the event loop. Total time: {total_time}s"

