# ============================================================
# PaySentinelIQ — Base Stage (Abstract)
# ============================================================

from __future__ import annotations

import time
from abc import ABC, abstractmethod

from app.core.contracts.pipeline_context import PipelineContext


class BaseStage(ABC):
    """Abstract base for all pipeline stages.

    Contract:
        - Receives PipelineContext
        - Modifies PipelineContext in place
        - Returns the SAME PipelineContext (never a new one)
        - Records execution time via context.record_stage_time()
        - Adds warnings/errors via context methods
        - NEVER returns dict, tuple, or any other type

    Subclasses implement:
        _execute(context: PipelineContext) -> None
    """

    def __init__(self, name: str | None = None):
        self.name = name or self.__class__.__name__

    def execute(self, context: PipelineContext) -> PipelineContext:
        """Execute the stage. Wraps _execute with timing and error handling."""
        start = time.monotonic()
        try:
            self._execute(context)
        except Exception as e:
            context.add_error(f"[{self.name}] {e}")
        finally:
            elapsed = time.monotonic() - start
            context.record_stage_time(self.name, round(elapsed, 3))
        return context

    @abstractmethod
    def _execute(self, context: PipelineContext) -> None:
        """Subclass implementation. Modifies context in place."""
        ...
