import logging
import httpx
import asyncio
from typing import Dict, Any

logger = logging.getLogger(__name__)

class EvaluationClient:
    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout

    async def notify(self, url: str, payload: Dict[str, Any], max_retries: int = 6) -> None:
        # Exponential backoff: 1, 2, 4, 8, 16, 32 seconds
        delay = 1
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(max_retries):
                try:
                    resp = await client.post(url, json=payload, headers={"Content-Type": "application/json"})
                    if resp.status_code == 200:
                        return
                    logger.warning(f"Evaluation notify non-200 ({resp.status_code}): {resp.text}")
                except Exception as e:
                    logger.warning(f"Evaluation notify error: {e}")
                await asyncio.sleep(delay)
                delay = min(delay * 2, 60)
        logger.error("Failed to notify evaluation URL after retries")


evaluation_client = EvaluationClient()
