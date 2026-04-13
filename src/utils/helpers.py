"""Utility helpers for retries and timing."""

from __future__ import annotations

import functools
import inspect
import time
from typing import Any, Callable, ParamSpec, TypeVar

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.core.logger import logger
from src.exceptions import ResearchError


R = TypeVar("R")
P = ParamSpec("P")


def retry_on_error(
    max_attempts: int = 3,
    wait_exp_min: float = 1,
    wait_exp_max: float = 10,
    exceptions: tuple[type[BaseException], ...] = (ResearchError,),
) -> Callable[[Callable[P, Any]], Callable[P, Any]]:
    """Retry sync or async functions for configured exception types."""

    def decorator(func: Callable[P, Any]) -> Callable[P, Any]:
        if inspect.iscoroutinefunction(func):

            @retry(
                stop=stop_after_attempt(max_attempts),
                wait=wait_exponential(multiplier=1, min=wait_exp_min, max=wait_exp_max),
                retry=retry_if_exception_type(exceptions),
                reraise=True,
            )
            @functools.wraps(func)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                try:
                    return await func(*args, **kwargs)
                except exceptions as exc:
                    logger.warning("Retryable async error in {}: {}", func.__name__, exc)
                    raise

            return async_wrapper

        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=wait_exp_min, max=wait_exp_max),
            retry=retry_if_exception_type(exceptions),
            reraise=True,
        )
        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                return func(*args, **kwargs)
            except exceptions as exc:
                logger.warning("Retryable sync error in {}: {}", func.__name__, exc)
                raise

        return sync_wrapper

    return decorator


def time_execution(func: Callable[P, Any]) -> Callable[P, Any]:
    """Log execution time for sync and async callables."""

    if inspect.iscoroutinefunction(func):

        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            start = time.perf_counter()
            result = await func(*args, **kwargs)
            duration = time.perf_counter() - start
            logger.info("{} took {:.2f}s", func.__name__, duration)
            return result

        return async_wrapper

    @functools.wraps(func)
    def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        duration = time.perf_counter() - start
        logger.info("{} took {:.2f}s", func.__name__, duration)
        return result

    return sync_wrapper


__all__ = ["retry_on_error", "time_execution"]
