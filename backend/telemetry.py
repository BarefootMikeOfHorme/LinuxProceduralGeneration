"""
VaultMind Forge - Telemetry Service

Optional telemetry service for sending anonymized usage data to remote endpoint.
Fully opt-in, respects user privacy, and can be completely disabled.
"""

import os
import logging
import hashlib
import platform
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
import json
import asyncio
import aiohttp

from backend.analytics import ANALYTICS_ENABLED, TELEMETRY_ENABLED, TELEMETRY_ENDPOINT

logger = logging.getLogger(__name__)


class TelemetryService:
    """
    Privacy-first telemetry service.

    Features:
    - Fully opt-in (disabled by default)
    - Anonymous device ID (no PII collected)
    - Aggregated metrics only
    - User can disable at any time
    - Local analytics always available even if telemetry is off
    """

    def __init__(self):
        self.enabled = TELEMETRY_ENABLED and ANALYTICS_ENABLED
        self.endpoint = TELEMETRY_ENDPOINT
        self.device_id = self._get_or_create_device_id()
        self.session_id = str(uuid.uuid4())

        if self.enabled and not self.endpoint:
            logger.warning("Telemetry enabled but no endpoint configured. Disabling telemetry.")
            self.enabled = False

    def _get_or_create_device_id(self) -> str:
        """
        Generate anonymous device ID.
        Uses machine-specific hash (not personally identifiable).
        """
        device_id_file = "./data/.device_id"

        try:
            if os.path.exists(device_id_file):
                with open(device_id_file, 'r') as f:
                    return f.read().strip()
        except Exception as e:
            logger.warning(f"Could not read device ID: {e}")

        # Generate new anonymous ID
        machine_info = f"{platform.node()}-{platform.machine()}-{platform.system()}"
        device_id = hashlib.sha256(machine_info.encode()).hexdigest()[:16]

        try:
            os.makedirs(os.path.dirname(device_id_file) if os.path.dirname(device_id_file) else ".", exist_ok=True)
            with open(device_id_file, 'w') as f:
                f.write(device_id)
        except Exception as e:
            logger.warning(f"Could not save device ID: {e}")

        return device_id

    def _anonymize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove or hash any potentially identifying information"""
        anonymized = data.copy()

        # Remove PII fields
        pii_fields = ['user_id', 'username', 'email', 'ip_address', 'api_key']
        for field in pii_fields:
            if field in anonymized:
                del anonymized[field]

        # Replace paths with generic indicators
        if 'file_path' in anonymized:
            anonymized['file_path'] = '<redacted>'

        if 'workflow_id' in anonymized:
            # Hash workflow IDs to prevent correlation
            anonymized['workflow_id'] = hashlib.md5(
                str(anonymized['workflow_id']).encode()
            ).hexdigest()[:8]

        return anonymized

    async def send_telemetry(self, event_type: str, data: Dict[str, Any]):
        """Send anonymized telemetry data to remote endpoint"""
        if not self.enabled:
            return

        try:
            # Anonymize data
            anonymized_data = self._anonymize_data(data)

            # Build telemetry payload
            payload = {
                "device_id": self.device_id,
                "session_id": self.session_id,
                "event_type": event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "version": "1.0.0",  # VaultMind Forge version
                "platform": {
                    "system": platform.system(),
                    "python_version": platform.python_version(),
                },
                "data": anonymized_data
            }

            # Send async (don't block main thread)
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.endpoint,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=5),
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status != 200:
                        logger.warning(f"Telemetry send failed: HTTP {response.status}")
                    else:
                        logger.debug(f"Telemetry sent: {event_type}")

        except asyncio.TimeoutError:
            logger.debug("Telemetry send timed out (non-critical)")
        except Exception as e:
            logger.debug(f"Telemetry send failed (non-critical): {e}")

    async def track_workflow_execution(self, node_count: int, duration_ms: float, success: bool):
        """Track workflow execution metrics"""
        await self.send_telemetry("workflow_executed", {
            "node_count": node_count,
            "duration_ms": duration_ms,
            "success": success
        })

    async def track_node_usage(self, node_type: str, duration_ms: float, success: bool):
        """Track node usage metrics"""
        await self.send_telemetry("node_used", {
            "node_type": node_type,
            "duration_ms": duration_ms,
            "success": success
        })

    async def track_error(self, error_code: str, error_category: str):
        """Track error occurrence (no error messages sent for privacy)"""
        await self.send_telemetry("error_occurred", {
            "error_code": error_code,
            "error_category": error_category
        })

    async def track_feature_usage(self, feature_name: str):
        """Track feature usage"""
        await self.send_telemetry("feature_used", {
            "feature": feature_name
        })

    def get_telemetry_status(self) -> Dict[str, Any]:
        """Get current telemetry status"""
        return {
            "enabled": self.enabled,
            "endpoint": self.endpoint if self.enabled else None,
            "device_id": self.device_id if self.enabled else None,
            "session_id": self.session_id if self.enabled else None,
            "notice": "Telemetry is fully opt-in. No personally identifiable information is collected."
        }


# Global telemetry service instance
_telemetry_service: Optional[TelemetryService] = None


def get_telemetry_service() -> TelemetryService:
    """Get or create the global telemetry service"""
    global _telemetry_service
    if _telemetry_service is None:
        _telemetry_service = TelemetryService()
    return _telemetry_service


# Convenience functions (async)
async def track_workflow_execution(node_count: int, duration_ms: float, success: bool):
    """Track workflow execution (async)"""
    service = get_telemetry_service()
    if service.enabled:
        await service.track_workflow_execution(node_count, duration_ms, success)


async def track_node_usage(node_type: str, duration_ms: float, success: bool):
    """Track node usage (async)"""
    service = get_telemetry_service()
    if service.enabled:
        await service.track_node_usage(node_type, duration_ms, success)


async def track_error(error_code: str, error_category: str = "general"):
    """Track error occurrence (async)"""
    service = get_telemetry_service()
    if service.enabled:
        await service.track_error(error_code, error_category)


async def track_feature_usage(feature_name: str):
    """Track feature usage (async)"""
    service = get_telemetry_service()
    if service.enabled:
        await service.track_feature_usage(feature_name)
