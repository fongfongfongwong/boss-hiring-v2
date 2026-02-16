"""Task lifecycle management.

Tracks running tasks and provides pause / resume / stop controls.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Callable, Coroutine

from sqlalchemy.orm import Session

from database.models import RecruitTask

logger = logging.getLogger(__name__)


class TaskControl:
    """Per-task control flags (shared with the running pipeline coroutine)."""

    def __init__(self, task_id: int) -> None:
        self.task_id = task_id
        self._paused = asyncio.Event()
        self._paused.set()  # Not paused by default
        self._stop_requested = False

    def pause(self) -> None:
        self._paused.clear()
        logger.info("Task %d paused", self.task_id)

    def resume(self) -> None:
        self._paused.set()
        logger.info("Task %d resumed", self.task_id)

    def stop(self) -> None:
        self._stop_requested = True
        self._paused.set()  # Unblock if paused
        logger.info("Task %d stop requested", self.task_id)

    @property
    def should_stop(self) -> bool:
        return self._stop_requested

    async def wait_if_paused(self) -> None:
        """Block until un-paused (or stop-requested)."""
        await self._paused.wait()


class TaskManager:
    """Manages all active recruitment tasks."""

    def __init__(self) -> None:
        self._controls: dict[int, TaskControl] = {}
        self._tasks: dict[int, asyncio.Task] = {}  # type: ignore[type-arg]

    def start_task(
        self,
        task_id: int,
        coroutine: Coroutine,  # type: ignore[type-arg]
    ) -> TaskControl:
        """Register and start a new pipeline coroutine."""
        ctrl = TaskControl(task_id)
        self._controls[task_id] = ctrl
        self._tasks[task_id] = asyncio.create_task(coroutine)
        logger.info("Task %d started", task_id)
        return ctrl

    def register_task(
        self,
        task_id: int,
        ctrl: TaskControl,
        async_task: asyncio.Task,  # type: ignore[type-arg]
    ) -> None:
        """Register an already-created control and asyncio.Task."""
        self._controls[task_id] = ctrl
        self._tasks[task_id] = async_task
        logger.info("Task %d registered", task_id)

    def get_control(self, task_id: int) -> TaskControl | None:
        return self._controls.get(task_id)

    def pause_task(self, task_id: int) -> bool:
        ctrl = self._controls.get(task_id)
        if ctrl:
            ctrl.pause()
            return True
        return False

    def resume_task(self, task_id: int) -> bool:
        ctrl = self._controls.get(task_id)
        if ctrl:
            ctrl.resume()
            return True
        return False

    def stop_task(self, task_id: int) -> bool:
        ctrl = self._controls.get(task_id)
        if ctrl:
            ctrl.stop()
            return True
        return False

    def is_running(self, task_id: int) -> bool:
        t = self._tasks.get(task_id)
        return t is not None and not t.done()

    def cleanup(self, task_id: int) -> None:
        self._controls.pop(task_id, None)
        self._tasks.pop(task_id, None)


# Singleton
task_manager = TaskManager()
