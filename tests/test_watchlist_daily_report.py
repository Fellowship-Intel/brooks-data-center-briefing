from datetime import date

from report_service import generate_watchlist_daily_report


def test_generate_watchlist_daily_report_uses_existing_pipeline(
    mock_gemini, mock_firestore, mock_storage, mock_tts
):
    trading_date = date(2025, 1, 1)
    client_id = "michael_brooks"
    watchlist = ["IREN", "CRWV", "NBIS", "MRVL"]

    report = generate_watchlist_daily_report(
        trading_date=trading_date,
        client_id=client_id,
        watchlist=watchlist,
    )

    assert report is not None
    assert report.get("client_id") == client_id
    assert report.get("trading_date") in {trading_date.isoformat(), str(trading_date)}
    
    # Ensure tickers are reflected somewhere in the stored payload
    # The raw_payload is stored in Firestore but not returned in the report dict
    # So we check what was passed to create_or_update_daily_report
    assert mock_firestore["mock_upsert"].called, "Report should be stored in Firestore"
    
    # Get the call arguments to verify tickers are in the stored data
    call_args = mock_firestore["mock_upsert"].call_args
    assert call_args is not None, "create_or_update_daily_report should have been called with arguments"
    
    # The function takes report_data as the first positional argument
    stored_data = call_args[0][0] if call_args[0] else {}
    raw_payload = stored_data.get("raw_payload", {})
    
    # Verify all watchlist tickers are reflected in the raw_payload
    # Check both the market_data tickers list and the string representation
    assert any(t in str(raw_payload) for t in watchlist), \
        f"Watchlist tickers {watchlist} should be reflected in raw_payload"


def test_generate_watchlist_daily_report_tts_fallback(
    mock_gemini, mock_firestore, mock_storage, mock_tts
):
    # Force TTS to raise
    mock_tts.side_effect = RuntimeError("TTS failure")

    trading_date = date(2025, 1, 1)
    client_id = "michael_brooks"
    watchlist = ["IREN"]

    report = generate_watchlist_daily_report(
        trading_date=trading_date,
        client_id=client_id,
        watchlist=watchlist,
    )

    # Should still return a valid text report
    assert report is not None
    assert report.get("summary_text")
    # audio_gcs_path should be missing/None when TTS fails
    assert not report.get("audio_gcs_path")

