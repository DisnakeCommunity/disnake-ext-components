"""Asyncio utility functions."""

import asyncio
import typing

__all__: typing.Sequence[str] = ("MaybeCoroutine", "eval_maybe_coro")


_T = typing.TypeVar("_T")

MaybeCoroutine = typing.Union[
    typing.Coroutine[typing.Any, typing.Any, _T],
    _T,
]


async def eval_maybe_coro(maybe_coro: MaybeCoroutine[_T]) -> _T:
    """Evaluate a function and automatically await it if it returns a coroutine."""
    if asyncio.iscoroutine(maybe_coro):
        return await maybe_coro

    return typing.cast(_T, maybe_coro)
