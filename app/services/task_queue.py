import asyncio
import logging
from typing import Callable, Awaitable, Any, Dict, Optional

logger = logging.getLogger(__name__)

_SENTINEL: Dict[str, Any] = {"__stop__": True}

class TaskQueue:
    def __init__(self):
        self.queue: asyncio.Queue = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task] = None
        self._handler: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None

    async def start(self, handler: Callable[[Dict[str, Any]], Awaitable[None]]):
        # Idempotent start
        if self._worker_task and not self._worker_task.done():
            return
        self._handler = handler

        async def _worker():
            while True:
                job = await self.queue.get()
                try:
                    if job is _SENTINEL or (isinstance(job, dict) and job.get("__stop__")):
                        return
                    if self._handler:
                        await self._handler(job)
                except Exception as e:
                    logger.error(f"TaskQueue handler error: {e}")
                finally:
                    self.queue.task_done()

        self._worker_task = asyncio.create_task(_worker())

    async def stop(self):
        # Gracefully stop worker by unblocking queue.get()
        if self._worker_task and not self._worker_task.done():
            await self.queue.put(_SENTINEL)
            try:
                await self._worker_task
            finally:
                self._worker_task = None

    async def enqueue(self, payload: Dict[str, Any]):
        await self.queue.put(payload)

# Singleton instance
queue = TaskQueue()
