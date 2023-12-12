"""Module that contains logic to build reference objects for component parsing."""

import types
import typing

import disnake
from disnake.ext import commands

__all__: typing.Sequence[str] = ("create_reference",)

_BOTS = (
    commands.Bot,
    commands.InteractionBot,
    commands.AutoShardedBot,
    commands.AutoShardedInteractionBot,
)

_CHANNELS = (
    disnake.TextChannel,
    disnake.Thread,
    disnake.VoiceChannel,
    disnake.DMChannel,
    disnake.PartialMessageable,
)


def _maybe_make_ref(ns: types.SimpleNamespace, *, source: object, key: str) -> None:
    obj = getattr(source, key, None)
    if obj is not None and not hasattr(ns, key):
        setattr(ns, key, obj)


def create_reference(*reference_objects: object) -> object:
    """Aggregate multiple reference objects into one.

    Interaction objects are returned as-is to speed up automatic component
    parsing from incoming interactions.
    """
    # Special-case to speed up automatic component parsing and reusing references:
    if len(reference_objects) == 1:
        obj = reference_objects[0]
        if isinstance(obj, (disnake.Interaction, types.SimpleNamespace)):
            return obj

    reference = types.SimpleNamespace()
    for obj in reference_objects:
        # Special-case priority objects
        if isinstance(obj, _BOTS):
            reference.bot = obj

        elif isinstance(obj, _CHANNELS):
            reference.channel = obj

        elif isinstance(obj, disnake.Guild):
            reference.guild = obj

        elif isinstance(obj, disnake.Message):
            reference.message = obj

        # Anything goes
        _maybe_make_ref(reference, source=obj, key="bot")
        _maybe_make_ref(reference, source=obj, key="guild")
        _maybe_make_ref(reference, source=obj, key="channel")
        _maybe_make_ref(reference, source=obj, key="message")

    return reference
