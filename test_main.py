import json
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "<title>Building Energy Efficiency Dashboard</title>" in response.text

def test_get_dashboard():
    response = client.get("/dashboard/")
    assert response.status_code == 200
    assert "Interactive Dashboard" in response.text
    assert "Distribution of Building Types" in response.text
    assert "Distribution of Total GHG Emissions" in response.text

def test_get_predictions():
    response = client.get("/predictions/")
    assert response.status_code == 200
    assert "Building Energy Efficiency Predictions" in response.text
    assert "Upload a CSV file with building data to get energy efficiency predictions." in response.text

