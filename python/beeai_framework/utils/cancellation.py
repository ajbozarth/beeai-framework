# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import asyncio
import contextlib
from collections.abc import Awaitable, Callable
from typing import TypeVar

from pydantic import BaseModel

from beeai_framework.errors import AbortError
from beeai_framework.logger import Logger

logger = Logger(__name__)

T = TypeVar("T")


class AbortSignal(BaseModel):
    def __init__(self) -> None:
        super().__init__()
        self._aborted = False
        self._reason: str | None = None
        self._listeners: list[Callable[[], None]] = []

    @property
    def aborted(self) -> bool:
        return self._aborted

    @property
    def reason(self) -> str:
        return self._reason or "Action has been aborted"

    def add_event_listener(self, callback: Callable[[], None]) -> None:
        self._listeners.append(callback)

    def remove_event_listener(self, callback: Callable[[], None]) -> None:
        with contextlib.suppress(ValueError):
            self._listeners.remove(callback)

    def _abort(self, reason: str | None = None) -> None:
        self._aborted = True
        self._reason = reason
        for callback in self._listeners:
            callback()

    @classmethod
    def timeout(cls, duration: float) -> "AbortSignal":
        signal = cls()

        loop = asyncio.get_event_loop()
        loop.call_later(duration, lambda *args: signal._abort(f"Operation timed out after {duration} ms"))

        return signal

    def throw_if_aborted(self) -> None:
        if self._aborted:
            raise AbortError(self.reason)


class AbortController:
    def __init__(self) -> None:
        self._signal = AbortSignal()

    @property
    def signal(self) -> AbortSignal:
        return self._signal

    def abort(self, reason: str | None = None) -> None:
        self._signal._abort(reason)

    async def clone(self) -> "AbortController":
        cloned = AbortController()
        cloned._signal = cloned._signal.model_copy()
        return cloned


def register_signals(controller: AbortController, signals: list[AbortSignal]) -> None:
    def register(signal: AbortSignal) -> None:
        if signal.aborted:
            controller.abort(signal.reason)
        else:
            signal.add_event_listener(lambda: controller.abort(signal.reason))

    for signal in filter(lambda x: x is not None, signals):
        register(signal)


async def abort_signal_handler(
    fn: Callable[[], Awaitable[T]], signal: AbortSignal | None = None, on_abort: Callable[[], None] | None = None
) -> T:
    def abort_handler() -> None:
        if on_abort:
            on_abort()

    if signal:
        if signal.aborted:
            raise AbortError(signal.reason)
        else:
            signal.add_event_listener(abort_handler)

    try:
        return await fn()
    finally:
        if signal:
            signal.remove_event_listener(abort_handler)
