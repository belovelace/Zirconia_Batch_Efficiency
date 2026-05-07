from rq import Queue
from redis import Redis

from app.config import settings

redis_conn = Redis.from_url(settings.REDIS_URL)
queue = Queue("default", connection=redis_conn)


def enqueue(func, *args, **kwargs):
    """Enqueue a callable to the default queue."""
    return queue.enqueue(func, *args, **kwargs)
