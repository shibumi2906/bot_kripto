# File: app/utils/risk_management.py
import time
from app.core.logger import logger

class CircuitBreaker:
    """
    Simple circuit breaker to halt operations after repeated failures.
    """
    def __init__(self, failure_threshold: int = 3, reset_timeout: int = 1800):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout  # seconds
        self.failure_count = 0
        self.opened_at: float | None = None

    def record_success(self) -> None:
        """Reset failure count and close the circuit."""
        self.failure_count = 0
        self.opened_at = None
        logger.debug("Circuit breaker reset")

    def record_failure(self) -> None:
        """Increment failure count and open circuit if threshold reached."""
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.opened_at = time.time()
            logger.warning("Circuit breaker opened due to failures")

    def allow_request(self) -> bool:
        """
        Return False if circuit is open and reset_timeout not passed.
        Else, return True and reset if timeout expired.
        """
        if self.opened_at:
            elapsed = time.time() - self.opened_at
            if elapsed >= self.reset_timeout:
                self.record_success()
                return True
            logger.error("Circuit breaker is open; request blocked")
            return False
        return True


def fixed_position_size(balance: float, risk_percent: float) -> float:
    """
    Calculate fixed position size as a percentage of balance.
    """
    size = balance * risk_percent
    logger.debug(f"Calculated fixed position size: {size} for balance {balance} @ {risk_percent}")
    return size
