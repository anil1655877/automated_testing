"""
============================================================
AI-Enhanced Enterprise Test Automation Framework
Retry Utilities
============================================================
Decorators and helpers for retrying flaky tests and
unreliable operations with configurable backoff strategies.
============================================================
"""
import time
import functools
from typing import Callable, Type, Tuple, Any, Optional
from utilities.logger import get_logger
from config.config import MAX_RETRIES, RETRY_DELAY

logger = get_logger(__name__)


def retry(
    max_attempts: int = MAX_RETRIES,
    delay: float = RETRY_DELAY,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    backoff: float = 1.0,
    on_retry: Optional[Callable] = None,
) -> Callable:
    """
    Decorator to retry a function on failure with configurable backoff.

    DESIGN PATTERN: Decorator Pattern
        Wraps any function/method with retry logic without
        modifying its implementation.

    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        exceptions: Tuple of exception types to catch and retry
        backoff: Multiplier applied to delay after each attempt
                 1.0 = constant delay, 2.0 = exponential backoff
        on_retry: Optional callback called on each retry with
                  (attempt_number, exception) arguments

    Returns:
        Decorated function with retry logic

    USAGE:
        @retry(max_attempts=3, delay=2, backoff=2.0)
        def click_unstable_button(driver):
            driver.find_element(By.ID, "btn").click()

        # Custom exception handling
        @retry(exceptions=(TimeoutException, StaleElementReferenceException))
        def find_dynamic_element(driver, locator):
            return driver.find_element(*locator)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            last_exception = None

            for attempt in range(1, max_attempts + 2):  # +2 = original + retries
                try:
                    result = func(*args, **kwargs)
                    if attempt > 1:
                        logger.info("✓ Succeeded on attempt %d: %s", attempt, func.__name__)
                    return result

                except exceptions as e:
                    last_exception = e
                    if attempt <= max_attempts:
                        logger.warning(
                            "Attempt %d/%d failed for '%s': %s. Retrying in %.1fs...",
                            attempt, max_attempts + 1, func.__name__, str(e)[:100], current_delay
                        )
                        if on_retry:
                            try:
                                on_retry(attempt, e)
                            except Exception as callback_err:
                                logger.debug("on_retry callback error: %s", callback_err)
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            "All %d attempts failed for '%s'. Last error: %s",
                            max_attempts + 1, func.__name__, str(e)
                        )
                        raise

            raise last_exception  # Should not reach here, but satisfies type checker

        return wrapper
    return decorator


def retry_on_exception(
    exception_types: Tuple[Type[Exception], ...],
    max_attempts: int = MAX_RETRIES,
    delay: float = RETRY_DELAY,
) -> Callable:
    """
    Shorthand decorator: retry only on specific exception types.

    USAGE:
        from selenium.common.exceptions import StaleElementReferenceException

        @retry_on_exception((StaleElementReferenceException,), max_attempts=3)
        def get_element_text(element):
            return element.text
    """
    return retry(
        max_attempts=max_attempts,
        delay=delay,
        exceptions=exception_types,
    )


def retry_with_result(
    condition: Callable[[Any], bool],
    max_attempts: int = 5,
    delay: float = 1.0,
) -> Callable:
    """
    Retry a function until the result satisfies a condition.
    Unlike retry(), this retries based on RETURN VALUE, not exceptions.

    Args:
        condition: Function that takes the result and returns bool
        max_attempts: Max retry count
        delay: Delay between attempts

    USAGE:
        @retry_with_result(lambda r: r.status_code == 200, max_attempts=5)
        def poll_api_until_ready(client):
            return client.get("/status")
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            for attempt in range(1, max_attempts + 1):
                result = func(*args, **kwargs)
                if condition(result):
                    if attempt > 1:
                        logger.info("Condition met on attempt %d: %s", attempt, func.__name__)
                    return result
                if attempt < max_attempts:
                    logger.debug(
                        "Condition not met (attempt %d/%d), retrying %s in %.1fs",
                        attempt, max_attempts, func.__name__, delay
                    )
                    time.sleep(delay)
            logger.warning("Condition never met after %d attempts: %s", max_attempts, func.__name__)
            return result  # Return last result even if condition not met
        return wrapper
    return decorator


class RetryContext:
    """
    Context manager for retry logic — use when decorators aren't suitable.

    USAGE:
        with RetryContext(max_attempts=3, delay=1) as ctx:
            while ctx.should_retry:
                try:
                    result = some_risky_operation()
                    ctx.success()
                    break
                except Exception as e:
                    ctx.fail(e)
    """

    def __init__(self, max_attempts: int = MAX_RETRIES, delay: float = RETRY_DELAY):
        self.max_attempts = max_attempts
        self.delay = delay
        self._attempt = 0
        self._succeeded = False
        self._last_error: Optional[Exception] = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False  # Don't suppress exceptions

    @property
    def should_retry(self) -> bool:
        """Returns True if more attempts are available."""
        return self._attempt <= self.max_attempts and not self._succeeded

    def success(self) -> None:
        """Mark current attempt as successful."""
        self._succeeded = True
        logger.debug("RetryContext: succeeded on attempt %d", self._attempt)

    def fail(self, error: Exception) -> None:
        """Record failure and sleep before next attempt."""
        self._last_error = error
        self._attempt += 1
        if self._attempt <= self.max_attempts:
            logger.warning(
                "RetryContext: attempt %d failed: %s. Retrying...",
                self._attempt, str(error)[:100]
            )
            time.sleep(self.delay)
        else:
            logger.error("RetryContext: all %d attempts exhausted", self.max_attempts)
            raise error

    @property
    def attempt_number(self) -> int:
        """Current attempt number (1-indexed)."""
        return self._attempt + 1
