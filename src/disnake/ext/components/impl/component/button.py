"""Default implementation of button-based components."""

import typing

import disnake
import typing_extensions
from disnake.ext.components import fields, interaction
from disnake.ext.components.api import component as component_api
from disnake.ext.components.impl import custom_id as custom_id_impl
from disnake.ext.components.impl.component import base as component_base

__all__: typing.Sequence[str] = ("RichButton",)


_AnyEmoji = typing.Union[str, disnake.PartialEmoji, disnake.Emoji]


@typing.runtime_checkable
class RichButton(
    component_api.RichButton, component_base.ComponentBase, typing.Protocol
):
    """The default implementation of a disnake-ext-components button.

    This works similar to a dataclass, but with some extra things to take into
    account.

    First and foremost, there are class variables for :attr:`label`,
    :attr:`style`, :attr:`emoji` and :attr:`disabled`. These set the
    corresponding attributes on the button class when they are sent to discord,
    and are meant to be overwritten by the user.

    Next, fields can be defined similarly to dataclasses, by means of a name,
    a type annotation, and an optional :func:`components.field` to set the
    default or a custom parser.

    Classes created in this way have auto-generated slots and an auto-generated
    ``__init__``. The init-signature contains all the custom id fields as
    keyword-only arguments.
    """

    event = "on_button_click"

    custom_id = custom_id_impl.AutoID()

    label: typing.Optional[str] = fields.internal(None)
    style: disnake.ButtonStyle = fields.internal(disnake.ButtonStyle.secondary)
    emoji: typing.Optional[_AnyEmoji] = fields.internal(None)
    disabled: bool = fields.internal(False)  # noqa: FBT003

    async def as_ui_component(self) -> disnake.ui.Button[None]:  # noqa: D102
        # <<docstring inherited from component_api.RichButton>>

        return disnake.ui.Button(
            style=self.style,
            label=self.label,
            disabled=self.disabled,
            emoji=self.emoji,
            custom_id=await self.dumps(),
        )

    @classmethod
    async def loads(  # noqa: D102
        cls, interaction: disnake.MessageInteraction, /
    ) -> typing_extensions.Self:
        # <<Docstring inherited from component_api.RichComponent>>

        # TODO: Maybe copy over internal attributes from the inter.component.
        # TODO: Error handling around match for more sensible errors.

        custom_id = typing.cast(str, interaction.component.custom_id)
        component_custom_id = typing.cast(custom_id_impl.CustomID, cls.custom_id)

        match = component_custom_id.match(custom_id, strict=True)

        return typing.cast(
            typing_extensions.Self,
            await cls.factory.loads(interaction, match.groupdict()),
        )

    async def callback(  # pyright: ignore[reportIncompatibleMethodOverride]  # noqa: D102, E501
        self,
        __inter: interaction.MessageInteraction,
    ) -> None:
        # <<docstring inherited from component_api.RichButton>>

        # NOTE: We narrow the interaction type down to a disnake.MessageInteraction
        #       here. This isn't typesafe, but it's just cleaner for the user.
        ...
