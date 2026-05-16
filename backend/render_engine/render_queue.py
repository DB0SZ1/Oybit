"""
Render Queue — Semaphore-based concurrency control for Playwright/Remotion renders.
Prevents OOM on Railway by limiting concurrent renders to 1.
"""

import asyncio
from backend.logger import get_logger

logger = get_logger("render_engine.queue")

# Global semaphore — max 1 concurrent render to prevent OOM on Railway (512MB-1GB)
_render_semaphore = asyncio.Semaphore(1)

# Track queue depth for monitoring
_queue_depth = 0


async def enqueue_render(render_fn, *args, **kwargs):
    """
    Execute a render function with concurrency control.

    Args:
        render_fn: async callable (e.g., carousel.render, video.render)
        *args, **kwargs: passed to render_fn

    Returns:
        Result of render_fn
    """
    global _queue_depth
    _queue_depth += 1

    logger.info("Render queued", extra={
        "queue_depth": _queue_depth,
        "render_fn": render_fn.__name__ if hasattr(render_fn, '__name__') else str(render_fn),
    })

    try:
        async with _render_semaphore:
            logger.info("Render started", extra={"fn": render_fn.__name__ if hasattr(render_fn, '__name__') else "unknown"})
            result = await render_fn(*args, **kwargs)
            return result
    except Exception as e:
        logger.error("Render failed", extra={"error": str(e)})
        raise
    finally:
        _queue_depth -= 1
        logger.info("Render complete", extra={"remaining_queue": _queue_depth})


def get_queue_depth() -> int:
    """Return current queue depth for health monitoring."""
    return _queue_depth
