"""Interaction implementations extending disnake interactions."""

from __future__ import annotations

import typing

import disnake
from disnake.ext.components.api import component as component_api

__all__: typing.Sequence[str] = ("MessageInteraction", "wrap_interaction")


ComponentT = typing.TypeVar(
    "ComponentT",
    bound=typing.Union[component_api.RichComponent, disnake.ui.WrappedComponent],
)

Components = typing.Union[
    # ActionRow[ComponentT],
    ComponentT,
    typing.Sequence[
        typing.Union[
            # "ActionRow[ComponentT]",
            ComponentT,
            typing.Sequence[ComponentT],
        ]
    ],
]
# TODO: Custom action rows?

MessageComponents = typing.Union[
    component_api.RichButton,
    disnake.ui.Button[typing.Any],
    component_api.RichSelect,
    disnake.ui.StringSelect[typing.Any],
    disnake.ui.ChannelSelect[typing.Any],
    disnake.ui.RoleSelect[typing.Any],
    disnake.ui.UserSelect[typing.Any],
    disnake.ui.MentionableSelect[typing.Any],
]


MISSING = disnake.utils.MISSING


async def _prepare(component: MessageComponents) -> disnake.ui.MessageUIComponent:
    if isinstance(
        component, (component_api.RichButton, component_api.RichSelect)
    ):  # TODO: add select
        return await component.as_ui_component()  # pyright: ignore

    return component


@typing.overload
async def _to_ui_components(
    components: Components[MessageComponents] = MISSING,
    *,
    allow_none: typing.Literal[False] = False,
) -> disnake.ui.Components[disnake.ui.MessageUIComponent]:
    ...


@typing.overload
async def _to_ui_components(
    components: typing.Optional[Components[MessageComponents]] = MISSING,
    *,
    allow_none: typing.Literal[True],
) -> typing.Optional[disnake.ui.Components[disnake.ui.MessageUIComponent]]:
    ...


async def _to_ui_components(
    components: typing.Optional[Components[MessageComponents]] = MISSING,
    *,
    allow_none: bool = False,
) -> typing.Optional[disnake.ui.Components[disnake.ui.MessageUIComponent]]:
    if components is None:
        if not allow_none:
            msg = "Components cannot be None in this method."
            raise TypeError(msg)
        return components

    if components is MISSING:
        return MISSING

    if not isinstance(components, typing.Sequence):
        return await _prepare(components)

    finalised: disnake.ui.Components[disnake.ui.MessageUIComponent] = []
    for component in components:
        if not isinstance(component, typing.Sequence):
            finalised.append(await _prepare(component))
            continue

        finalised.append([await _prepare(nested) for nested in component])

    return finalised


class WrappedInteraction(disnake.Interaction):
    """Interaction implementation that wraps :class:`disnake.Interaction`.

    This wrapped interaction class natively supports disnake-ext-components'
    specialised components classes and -- unlike vanilla disnake interactions --
    can send them without manually having to convert them to native disnake
    components first.

    Attribute access is simply proxied to the wrapped interaction object by
    means of a custom :meth:`__getattr__` implementation.
    """

    __slots__ = ("_wrapped",)

    def __init__(self, wrapped: disnake.Interaction):
        self._wrapped = wrapped

    def __getattribute__(self, name: str) -> typing.Any:  # noqa: ANN401
        """Get an attribute of this class or the wrapped interaction."""
        try:
            return super().__getattribute__(name)
        except AttributeError:
            return getattr(self._wrapped, name)

    @disnake.utils.cached_slot_property("_cs_response")
    def response(self) -> WrappedInteractionResponse:  # noqa: D102
        # <<docstring inherited from disnake.Interaction>>

        return WrappedInteractionResponse(super().response)

    @disnake.utils.cached_slot_property("_cs_followup")
    def followup(self) -> disnake.Webhook:  # noqa: D102
        # <<docstring inherited from disnake.Interaction>>

        return self._wrapped.followup  # TODO: custom followup object

    async def edit_original_response(  # pyright: ignore[reportIncompatibleMethodOverride]  # noqa: D102, E501
        self,
        content: typing.Optional[str] = MISSING,
        *,
        embed: typing.Optional[disnake.Embed] = MISSING,
        embeds: typing.List[disnake.Embed] = MISSING,
        file: disnake.File = MISSING,
        files: typing.List[disnake.File] = MISSING,
        attachments: typing.Optional[typing.List[disnake.Attachment]] = MISSING,
        view: typing.Optional[disnake.ui.View] = MISSING,
        components: typing.Optional[Components[MessageComponents]] = MISSING,
        suppress_embeds: bool = MISSING,
        allowed_mentions: typing.Optional[disnake.AllowedMentions] = None,
    ) -> disnake.InteractionMessage:
        # <<docstring inherited from disnake.Interaction>>

        return await self._wrapped.edit_original_response(
            content=content,
            embed=embed,
            embeds=embeds,
            file=file,
            files=files,
            attachments=attachments,
            view=view,
            components=await _to_ui_components(components, allow_none=True),
            suppress_embeds=suppress_embeds,
            allowed_mentions=allowed_mentions,
        )

    edit_original_message = edit_original_response

    async def send(  # pyright: ignore[reportIncompatibleMethodOverride]  # noqa: D102
        self,
        content: typing.Optional[str] = None,
        *,
        embed: disnake.Embed = MISSING,
        embeds: typing.List[disnake.Embed] = MISSING,
        file: disnake.File = MISSING,
        files: typing.List[disnake.File] = MISSING,
        allowed_mentions: disnake.AllowedMentions = MISSING,
        view: disnake.ui.View = MISSING,
        components: Components[MessageComponents] = MISSING,
        tts: bool = False,
        ephemeral: bool = False,
        suppress_embeds: bool = False,
        delete_after: float = MISSING,
    ) -> None:
        # <<docstring inherited from disnake.Interaction>>

        return await self._wrapped.send(
            content=content,
            embed=embed,
            embeds=embeds,
            file=file,
            files=files,
            allowed_mentions=allowed_mentions,
            view=view,
            components=await _to_ui_components(components),
            tts=tts,
            ephemeral=ephemeral,
            suppress_embeds=suppress_embeds,
            delete_after=delete_after,
        )


class WrappedInteractionResponse(disnake.InteractionResponse):
    """Interaction response implementation that wraps :class:`disnake.InteractionResponse`.

    This wrapped interaction response class natively supports
    disnake-ext-components' specialised components classes and -- unlike
    vanilla disnake interactions -- can send them without manually having to
    convert them to native disnake components first.

    Attribute access is simply proxied to the wrapped interaction response
    object by means of a custom :meth:`__getattr__` implementation.
    """  # noqa: E501

    __slots__ = ("_wrapped",)

    def __init__(self, wrapped: disnake.InteractionResponse):
        self._wrapped = wrapped

    def __getattribute__(self, name: str) -> typing.Any:  # noqa: ANN401
        """Get an attribute of this class or the wrapped interaction."""
        try:
            return super().__getattribute__(name)
        except AttributeError:
            return getattr(self._wrapped, name)

    async def send_message(  # pyright: ignore[reportIncompatibleMethodOverride]  # noqa: D102, E501
        self,
        content: typing.Optional[str] = None,
        *,
        embed: disnake.Embed = MISSING,
        embeds: typing.List[disnake.Embed] = MISSING,
        file: disnake.File = MISSING,
        files: typing.List[disnake.File] = MISSING,
        allowed_mentions: disnake.AllowedMentions = MISSING,
        view: disnake.ui.View = MISSING,
        components: Components[MessageComponents] = MISSING,
        tts: bool = False,
        ephemeral: bool = False,
        suppress_embeds: bool = False,
        delete_after: float = MISSING,
    ) -> None:
        # <<docstring inherited from disnake.Interaction>>

        return await self._wrapped.send_message(
            content=content,
            embed=embed,
            embeds=embeds,
            file=file,
            files=files,
            allowed_mentions=allowed_mentions,
            view=view,
            components=await _to_ui_components(components),
            tts=tts,
            ephemeral=ephemeral,
            suppress_embeds=suppress_embeds,
            delete_after=delete_after,
        )

    async def edit_message(  # pyright: ignore[reportIncompatibleMethodOverride]  # noqa: D102, E501
        self,
        content: typing.Optional[str] = None,
        *,
        embed: disnake.Embed = MISSING,
        embeds: typing.List[disnake.Embed] = MISSING,
        file: disnake.File = MISSING,
        files: typing.List[disnake.File] = MISSING,
        attachments: typing.Optional[typing.List[disnake.Attachment]] = MISSING,
        allowed_mentions: disnake.AllowedMentions = MISSING,
        view: disnake.ui.View = MISSING,
        components: typing.Optional[Components[MessageComponents]] = MISSING,
    ) -> None:
        # <<docstring inherited from disnake.Interaction>>

        return await self._wrapped.edit_message(
            content=content,
            embed=embed,
            embeds=embeds,
            file=file,
            files=files,
            attachments=attachments,
            allowed_mentions=allowed_mentions,
            view=view,
            components=await _to_ui_components(components, allow_none=True),
        )


class MessageInteraction(  # pyright: ignore
    WrappedInteraction, disnake.MessageInteraction
):
    """Message interaction implementation that wraps :class:`disnake.MessageInteraction`.

    This wrapped message interaction class natively supports
    disnake-ext-components' specialised components classes and -- unlike
    vanilla disnake interactions -- can send them without manually having to
    convert them to native disnake components first.

    Attribute access is simply proxied to the wrapped message interaction
    object by means of a custom :meth:`__getattr__` implementation.
    """  # noqa: E501

    # __slots__ = ()  # No slots on disnake.MessageInteraction...

    def __init__(self, wrapped: disnake.MessageInteraction):
        self._wrapped = wrapped

    # message = proxy.ProxiedProperty("_wrapped")


@typing.overload
def wrap_interaction(interaction: disnake.MessageInteraction) -> MessageInteraction:
    ...


@typing.overload
def wrap_interaction(interaction: disnake.Interaction) -> WrappedInteraction:
    ...


def wrap_interaction(interaction: disnake.Interaction) -> WrappedInteraction:
    """Wrap a disnake interaction type for disnake-ext-components compatibility.

    Interactions wrapped in this way can send disnake-ext-components'
    specialised components directly, without having to first convert them to
    native disnake components.

    Parameters
    ----------
    interaction:
        The interaction to wrap.

    Returns
    -------
    WrappedInteraction:
        The wrapped interaction. Note that this can be any subclass of
        :class:`WrappedInteraction`:

        - Wrapping a (subclass of) :class:`disnake.MessageInteraction` returns
        a :class:`MessageInteraction`,
        - Wrapping a (subclass of) :class:`disnake.ModalInteraction` returns a
        :class:`ModalInteraction`,
        - Wrapping any other interaction class returns a
        :class:`WrappedInteraction`.
    """
    if isinstance(interaction, disnake.MessageInteraction):
        return MessageInteraction(interaction)

    # TODO: ModalInteraction

    return WrappedInteraction(interaction)
