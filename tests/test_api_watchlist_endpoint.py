from datetime import date

from fastapi.testclient import TestClient

from app.main import app


def test_generate_watchlist_report_endpoint(mock_gemini, mock_firestore, mock_storage, mock_tts):
    client = TestClient(app)

    payload = {
        "client_id": "michael_brooks",
        "watchlist": ["IREN", "CRWV"],
        "trading_date": "2025-01-02",
    }

    resp = client.post("/reports/generate/watchlist", json=payload)
    assert resp.status_code == 200

    data = resp.json()
    assert data["client_id"] == "michael_brooks"
    assert data["trading_date"] == "2025-01-02"
    assert set(data["watchlist"]) == {"IREN", "CRWV"}
    assert "summary_text" in data
    assert "raw_payload" in data

