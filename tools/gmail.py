from typing import Any, Dict, List, Optional

from utils.logging import EventLogger
from .executor import ArcadeToolExecutor


class GmailTool:
    def __init__(self, executor: ArcadeToolExecutor, logger: Optional[EventLogger] = None):
        self.exec = executor
        self.logger = logger or EventLogger()

    async def search_threads(self, domain: str, user_id: str, max_results: int = 20) -> List[Dict[str, Any]]:
        payload = await self.exec.execute(
            step="act:search_gmail",
            tool_name="Gmail.SearchThreads",
            input={"sender": f"@{domain}", "max_results": max_results},
            user_id=user_id,
        )
        threads = []
        if isinstance(payload, dict):
            threads = payload.get("threads", []) or []
        return threads

    async def get_thread(self, thread_id: str, user_id: str) -> Dict[str, Any]:
        payload = await self.exec.execute(
            step="act:get_thread",
            tool_name="Gmail.GetThread",
            input={"thread_id": thread_id},
            user_id=user_id,
        )
        if isinstance(payload, dict):
            return payload
        return {}
