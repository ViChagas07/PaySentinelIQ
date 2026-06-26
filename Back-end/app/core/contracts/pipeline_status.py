# ============================================================
# PaySentinelIQ — Pipeline Status Enum
# ============================================================

from enum import Enum


class PipelineStatus(str, Enum):
    """Explicit pipeline execution states.

    Replaces ad-hoc strings ("completed", "failed", "processing")
    with a typed contract that downstream consumers can rely on.

    NEVER return "LOW RISK" when status is not SUCCESS.
    """

    SUCCESS = "success"              # All stages completed normally
    PARTIAL = "partial"              # >= 5 stages completed, some skipped
    FAILED = "failed"                # < 5 stages completed, insufficient
    INCONCLUSIVE = "inconclusive"    # Evidence conflicts, needs human review
