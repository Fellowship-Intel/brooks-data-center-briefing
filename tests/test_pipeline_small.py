from datetime import date

from report_service import generate_and_store_daily_report


def test_generate_report_minimal(mock_gemini, mock_firestore, mock_storage, mock_tts):
    """Tiny test: validates pipeline shape without calling GCP or Gemini."""

    trading_date = date(2025, 12, 4)

    result = generate_and_store_daily_report(
        trading_date=trading_date,
        client_id="michael_brooks",
        market_data={"tickers": ["SMCI"]},
        news_items={},
        macro_context={},
    )

    # -----------------------
    # Validate result shape
    # -----------------------
    assert result["client_id"] == "michael_brooks"
    assert result["trading_date"] == "2025-12-04"
    assert "summary_text" in result
    assert "key_insights" in result
    assert "market_context" in result

    # audio_gcs_path should exist because we mocked TTS + upload
    assert result["audio_gcs_path"].startswith("gs://")

    # -----------------------
    # Validate Firestore interactions
    # -----------------------
    assert mock_firestore["mock_upsert"].called, "Report should be inserted/updated"
    assert mock_firestore["mock_audio_update"].called, "Audio path should update Firestore"

    # -----------------------
    # Validate Storage upload
    # -----------------------
    assert mock_storage["bucket"].blob.called, "Blob should be created"
    assert mock_storage["blob"].upload_from_string.called, "Audio should be uploaded"

    # -----------------------
    # Validate TTS was called
    # -----------------------
    mock_tts.assert_called_once()

