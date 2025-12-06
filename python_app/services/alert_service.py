"""
Service for managing market alerts and sending SMS notifications via Twilio.
"""
import os
import logging
from enum import Enum
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from google.cloud import firestore
from utils.email_service import get_email_service
from gcp_clients import get_firestore_client

logger = logging.getLogger(__name__)

class ConditionType(str, Enum):
    PRICE_ABOVE = "price_above"
    PRICE_BELOW = "price_below"
    CHANGE_PCT_ABOVE = "change_pct_above"
    CHANGE_PCT_BELOW = "change_pct_below"

@dataclass
class Alert:
    user_id: str
    ticker: str
    condition_type: ConditionType
    target_value: float
    email: str
    id: str = ""
    created_at: str = ""
    last_triggered: Optional[str] = None
    active: bool = True

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if not data["id"]:
            del data["id"]
        return data

class AlertService:
    def __init__(self):
        self.db = get_firestore_client()
        self.collection = self.db.collection("alerts")
        self.email_service = get_email_service()

    def create_alert(self, user_id: str, ticker: str, condition: ConditionType, value: float, email: str) -> str:
        """Create a new alert."""
        alert_id = str(uuid.uuid4())
        alert = Alert(
            id=alert_id,
            user_id=user_id,
            ticker=ticker.upper(),
            condition_type=condition,
            target_value=value,
            email=email,
            created_at=datetime.utcnow().isoformat()
        )
        
        self.collection.document(alert_id).set(alert.to_dict())
        logger.info(f"Created alert {alert_id} for user {user_id}")
        return alert_id

    def get_user_alerts(self, user_id: str) -> List[Alert]:
        """Get all alerts for a user."""
        docs = self.collection.where("user_id", "==", user_id).stream()
        alerts = []
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            alerts.append(Alert(**data))
        return alerts

    def delete_alert(self, alert_id: str) -> bool:
        """Delete an alert."""
        try:
            self.collection.document(alert_id).delete()
            return True
        except Exception as e:
            logger.error(f"Error deleting alert {alert_id}: {e}")
            return False

    def check_market_data(self, market_data_df) -> List[str]:
        """
        Check provided market data against all active alerts.
        Returns a list of triggered alert IDs.
        """
        if market_data_df.empty:
            return []

        triggered_ids = []
        
        # In a real high-scale app, we'd query by ticker. 
        # For now, fetching all active alerts is manageable.
        active_alerts = self.collection.where("active", "==", True).stream()
        
        for doc in active_alerts:
            data = doc.to_dict()
            alert = Alert(**{**data, "id": doc.id})
            
            # Find data for this ticker
            row = market_data_df[market_data_df['ticker'] == alert.ticker]
            if row.empty:
                continue
            
            price = row.iloc[0]['last_price']
            change = row.iloc[0]['change_pct']
            
            trigger = False
            msg = ""
            
            # Check conditions
            if alert.condition_type == ConditionType.PRICE_ABOVE and price > alert.target_value:
                trigger = True
                msg = f"{alert.ticker} is above ${alert.target_value} (Current: ${price:.2f})"
            elif alert.condition_type == ConditionType.PRICE_BELOW and price < alert.target_value:
                trigger = True
                msg = f"{alert.ticker} is below ${alert.target_value} (Current: ${price:.2f})"
            elif alert.condition_type == ConditionType.CHANGE_PCT_ABOVE and change > alert.target_value:
                trigger = True
                msg = f"{alert.ticker} is up {change:.2f}% (Target: >{alert.target_value}%)"
            elif alert.condition_type == ConditionType.CHANGE_PCT_BELOW and change < alert.target_value:
                # change < -5% means it dropped more than 5%
                trigger = True
                msg = f"{alert.ticker} dropped {change:.2f}% (Target: <{alert.target_value}%)"
            
            # Dedup: don't trigger if already triggered recently?
            # For simplicity, we trigger and then maybe disable or update timestamp
            # Let's just update 'last_triggered' and implement a cooldown in future if needed.
            
            if trigger:
                self._send_email_alert(alert, msg)
                self._mark_triggered(alert.id)
                triggered_ids.append(alert.id)
                
        return triggered_ids

    def _mark_triggered(self, alert_id: str):
        """Update last_triggered timestamp."""
        self.collection.document(alert_id).update({
            "last_triggered": datetime.utcnow().isoformat()
        })

    def _send_email_alert(self, alert: Alert, message: str):
        """Send Alert Email."""
        subject = f"🔔 Market Alert: {alert.ticker}"
        self.email_service.send_email(
            to_emails=[alert.email],
            subject=subject,
            body_text=message,
            body_html=f"<h3>{message}</h3><p>Sent from Brooks Data Center Daily Briefing</p>"
        )
