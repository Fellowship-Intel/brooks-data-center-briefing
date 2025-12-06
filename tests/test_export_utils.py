"""Tests for export utilities."""
import pytest
from utils.export_utils import export_report_to_csv, export_market_data_to_csv


class TestExportUtils:
    """Test export utilities."""
    
    def test_export_report_to_csv(self):
        """Test exporting report to CSV."""
        report_data = {
            "trading_date": "2025-01-15",
            "client_id": "test_client",
            "summary_text": "Test summary",
            "key_insights": ["Insight 1", "Insight 2"],
            "tickers": ["AAPL", "MSFT"]
        }
        
        csv_bytes = export_report_to_csv(report_data)
        assert csv_bytes is not None
        assert len(csv_bytes) > 0
        
        # Verify CSV contains expected data
        csv_str = csv_bytes.decode('utf-8')
        assert "Trading Date" in csv_str
        assert "2025-01-15" in csv_str
        assert "Test summary" in csv_str
    
    def test_export_market_data_to_csv(self):
        """Test exporting market data to CSV."""
        market_data = [
            {"ticker": "AAPL", "price": 150.0, "volume": 1000000},
            {"ticker": "MSFT", "price": 300.0, "volume": 2000000}
        ]
        
        csv_bytes = export_market_data_to_csv(market_data)
        assert csv_bytes is not None
        assert len(csv_bytes) > 0
        
        # Verify CSV contains expected data
        csv_str = csv_bytes.decode('utf-8')
        assert "ticker" in csv_str
        assert "AAPL" in csv_str
        assert "MSFT" in csv_str
    
    def test_export_empty_market_data(self):
        """Test exporting empty market data raises error."""
        with pytest.raises(ValueError):
            export_market_data_to_csv([])

