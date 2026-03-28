"""
SLA Monitor Service.

Consolidates SLA alerting mechanisms.
"""

from app.utils.logger import get_logger

logger = get_logger(__name__)


class SLAMonitor:
    """Centralizes alerting logic for performance regressions."""
    
    @staticmethod
    def alert_sla_breach(operation: str, duration_ms: float, limit_ms: float):
        """Send an alert to a monitoring service like PagerDuty or Slack (mocked)."""
        logger.error(
            f"SLA_ALERT: Operation '{operation}' exceeded limit! "
            f"({duration_ms:.2f}ms vs {limit_ms}ms)"
        )
        # In a real system, send off a webhook here

sla_monitor = SLAMonitor()
