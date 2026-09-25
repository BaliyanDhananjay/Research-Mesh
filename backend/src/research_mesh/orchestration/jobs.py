"""Lightweight in-process background execution for research runs.

This is intentionally simple for the MVP: a thread pool with a future per run.
A production deployment would replace this with a durable queue (e.g. Redis or
Celery) without changing the API surface that depends on it.
"""

from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from uuid import UUID


class RunJobManager:
    def __init__(self, *, max_workers: int = 2) -> None:
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._futures: dict[UUID, Future[object]] = {}

    def submit(self, run_id: UUID, task: Callable[[], object]) -> None:
        self._futures[run_id] = self._executor.submit(task)

    def is_running(self, run_id: UUID) -> bool:
        future = self._futures.get(run_id)
        return future is not None and not future.done()

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False)
