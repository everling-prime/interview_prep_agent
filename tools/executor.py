from typing import Any, Dict, Optional
import asyncio

from utils.logging import EventLogger


class ArcadeToolExecutor:
    """DRY helper to call Arcade tools with logging and error handling."""

    def __init__(self, arcade_client, logger: Optional[EventLogger] = None):
        self.client = arcade_client
        self.logger = logger or EventLogger()

    async def execute(self, step: str, tool_name: str, input: Dict[str, Any], user_id: Optional[str] = None) -> Any:
        with self.logger.timed(step=step, tool=tool_name) as t:
            try:
                result = await asyncio.to_thread(
                    self.client.tools.execute,
                    tool_name=tool_name,
                    input=input,
                    user_id=user_id,
                )
                # Normalize output for typical Arcade ExecuteToolResponse
                payload = None
                if hasattr(result, 'output') and hasattr(result.output, 'value'):
                    payload = result.output.value
                elif isinstance(result, dict):
                    payload = result
                else:
                    payload = getattr(result, 'result', result)
                t.result("ok", extra={"keys": list(payload.keys()) if isinstance(payload, dict) else None})
                return payload
            except Exception as e:
                t.result("error", extra={"error": str(e)})
                raise

