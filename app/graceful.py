import asyncio
import logging
from app.config import settings

logger = logging.getLogger(__name__)


async def _close_all(app):
    # Hook to close DB pools, workers, etc. Replace placeholders with real cleanup.
    if getattr(app.state, "db", None):
        try:
            await app.state.db.close()
        except Exception:
            logger.exception("Error closing DB")
    # Add other shutdown tasks here
    await asyncio.sleep(0.01)


async def on_shutdown(app):
    try:
        await asyncio.wait_for(_close_all(app), timeout=settings.GRACEFUL_TIMEOUT)
    except asyncio.TimeoutError:
        logger.warning("Graceful shutdown timed out")
