"""
Circuit Breaker Pattern.

Protects against cascading failures when external APIs (Petpooja, Razorpay) are down.
"""

import time
from typing import Callable, Any
import functools
from app.utils.logger import get_logger

logger = get_logger(__name__)

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "CLOSED" # "CLOSED", "OPEN", "HALF_OPEN"
        
    def __call__(self, func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            if self.state == "OPEN":
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    logger.info(f"CircuitBreaker [{func.__name__}]: Half-open mode.")
                    self.state = "HALF_OPEN"
                else:
                    raise Exception(f"Circuit is OPEN. Fast failing call to {func.__name__}")
                    
            try:
                result = await func(*args, **kwargs)
                # Success -> reset
                if self.state == "HALF_OPEN":
                    logger.info(f"CircuitBreaker [{func.__name__}]: Recovery success, circuit closed.")
                    self.state = "CLOSED"
                    self.failure_count = 0
                return result
                
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                if self.failure_count >= self.failure_threshold:
                    logger.warning(f"CircuitBreaker [{func.__name__}]: TRIPPED! Circuit OPEN.")
                    self.state = "OPEN"
                    
                raise e
                
        return wrapper
