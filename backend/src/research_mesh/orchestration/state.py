"""Allowed research run state transitions."""

from research_mesh.domain.models import RunStatus

ALLOWED_TRANSITIONS: dict[RunStatus, frozenset[RunStatus]] = {
    RunStatus.QUEUED: frozenset({RunStatus.RUNNING, RunStatus.CANCELLED}),
    RunStatus.RUNNING: frozenset({RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED}),
    RunStatus.COMPLETED: frozenset(),
    RunStatus.FAILED: frozenset({RunStatus.QUEUED}),
    RunStatus.CANCELLED: frozenset({RunStatus.QUEUED}),
}


def transition_status(current: RunStatus, target: RunStatus) -> RunStatus:
    if target not in ALLOWED_TRANSITIONS[current]:
        raise ValueError(f"Invalid run transition: {current.value} -> {target.value}")
    return target
