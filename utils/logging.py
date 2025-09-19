import json
import sys
import time
import uuid
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional


@dataclass
class LogEvent:
    run_id: str
    step: str
    tool: str
    outcome: str
    duration_ms: int
    extra: Optional[Dict[str, Any]] = None


class EventLogger:
    """Simple structured logger that emits JSON lines to stdout.

    Fields: step, tool, outcome, ms. Optional extra metadata.
    """

    def __init__(self, sink=None, run_id: Optional[str] = None):
        self.sink = sink or sys.stdout
        self.run_id = run_id or str(uuid.uuid4())

    def log(self, step: str, tool: str, outcome: str, duration_ms: int, extra: Optional[Dict[str, Any]] = None):
        evt = LogEvent(run_id=self.run_id, step=step, tool=tool, outcome=outcome, duration_ms=duration_ms, extra=extra)
        self.sink.write(json.dumps(asdict(evt), ensure_ascii=False) + "\n")
        self.sink.flush()

    def timed(self, step: str, tool: str):
        """Context manager to time and log an operation. Use with .result(outcome, extra)."""
        logger = self

        class _Timer:
            def __init__(self):
                self._start = None
                self._duration_ms = 0

            def __enter__(self):
                self._start = time.perf_counter()
                return self

            def __exit__(self, exc_type, exc, tb):
                end = time.perf_counter()
                self._duration_ms = int((end - self._start) * 1000)
                # If exception and no explicit result logged, log failure
                if exc_type is not None:
                    logger.log(step, tool, outcome=f"error:{exc_type.__name__}", duration_ms=self._duration_ms, extra={"error": str(exc)})
                # suppress? no
                return False

            def result(self, outcome: str, extra: Optional[Dict[str, Any]] = None):
                end = time.perf_counter()
                self._duration_ms = int((end - self._start) * 1000)
                logger.log(step, tool, outcome=outcome, duration_ms=self._duration_ms, extra=extra)

        return _Timer()
