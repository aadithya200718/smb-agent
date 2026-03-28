"""
SLA & Performance Monitoring Decorator.

Decorate functions with @track_performance("operation_name")
to automatically log their latency and check against SLAs.
"""

import time
import functools
from typing import Callable, Any

from app.utils.logger import get_logger

logger = get_logger(__name__)

# Configured SLAs in milliseconds limit
SLA_TARGETS_MS = {
    "faq_response": 2000,
    "tool_call": 4000,
    "create_order": 5000,
    "agent_full_run": 8000,
}


def track_performance(operation: str) -> Callable:
    """
    Decorator to wrap async functions, track latency, 
    and alert if SLA is breached.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration_ms = (time.perf_counter() - start_time) * 1000
                logger.info(f"PERFORMANCE [{operation}]: {duration_ms:.2f}ms")
                
                # Check against SLA
                sla_limit = SLA_TARGETS_MS.get(operation, None)
                if sla_limit and duration_ms > sla_limit:
                    logger.warning(
                        f"SLA BREACH [{operation}]: "
                        f"Took {duration_ms:.2f}ms > limit {sla_limit}ms"
                    )
        return wrapper
    return decorator
