"""
HTTP client for Group Service communication.
"""
import httpx
import logging
from uuid import UUID
from typing import Optional

from app.config import config
from app.models import BroadcastRequest

logger = logging.getLogger(__name__)


class GroupClient:
    """Client for communicating with Group Service."""

    def __init__(self):
        self.base_url = config.group_service_url.rstrip('/')
        self.timeout = 10.0

    async def broadcast_alert(
        self,
        event_id: UUID,
        user_id: UUID,
        alert_id: UUID,
        message: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None
    ) -> bool:
        """
        Send alert broadcast request to Group Service.
        
        Group Service will broadcast this alert to all groups
        associated with the event via WebSocket.
        
        Args:
            event_id: Event ID
            user_id: User who triggered alert
            alert_id: Alert ID
            message: Alert message
            latitude: Optional user latitude
            longitude: Optional user longitude
            
        Returns:
            True if broadcast successful, False otherwise
        """
        url = f"{self.base_url}/api/v1/groups/internal/broadcast"
        
        payload = BroadcastRequest(
            event_id=event_id,
            user_id=user_id,
            alert_id=alert_id,
            message=message,
            latitude=latitude,
            longitude=longitude
        )
        
        try:
            logger.info(f"Broadcasting alert {alert_id} to event {event_id} groups")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    json=payload.model_dump(mode='json'),
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Alert broadcast successful: {result}")
                    return True
                else:
                    logger.error(f"Alert broadcast failed: {response.status_code} - {response.text}")
                    return False
                    
        except httpx.TimeoutException:
            logger.error(f"Timeout broadcasting alert {alert_id} to Group Service")
            return False
        except Exception as e:
            logger.error(f"Error broadcasting alert {alert_id}: {str(e)}")
            return False
