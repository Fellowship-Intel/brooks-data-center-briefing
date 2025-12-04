from datetime import date

from report_service import generate_and_store_daily_report


def test_generate_report_tts_failure(mock_gemini, mock_firestore, mock_storage):
    """Ensure pipeline does NOT break if TTS fails."""

    # Mock synthesize_speech to raise an error
    from unittest.mock import patch
    
    with patch("report_service.synthesize_speech") as mock_tts:
        mock_tts.side_effect = Exception("TTS DOWN")

        result = generate_and_store_daily_report(
            trading_date=date(2025, 12, 4),
            client_id="michael_brooks",
            market_data={"tickers": ["SMCI"]},
            news_items={},
            macro_context={},
        )

        # Should still return text report
        assert result["summary_text"] is not None
        assert result["audio_gcs_path"] is None, "Audio should be None when TTS fails"

        # Firestore upsert still called (text report was saved)
        assert mock_firestore["mock_upsert"].called
        
        # Audio update should NOT be called when TTS fails
        assert not mock_firestore["mock_audio_update"].called, "Audio update should not be called when TTS fails"

