"""Default implementation of select-based components."""

from __future__ import annotations

import typing

import attr
import disnake
from disnake.ext.components import fields, interaction
from disnake.ext.components.api import component as component_api
from disnake.ext.components.impl import custom_id as custom_id_impl
from disnake.ext.components.impl.component import base as component_base

if typing.TYPE_CHECKING:
    import typing_extensions


class BaseSelect(
    component_api.RichSelect, component_base.ComponentBase, typing.Protocol
):
    """The default implementation of a disnake-ext-components select.

    This works similar to a dataclass, but with some extra things to take into
    account.

    First and foremost, there are class variables for :attr:`placeholder`,
    :attr:`min_values`, :attr:`max_values`, :attr:`disabled`, and:attr:`options`
    (available only when using :class:`RichStringSelect`).
    These set the corresponding attributes on the select class when they are
    sent to discord, and are meant to be overwritten by the user.

    Fields can be defined similarly to dataclasses, by means of a name, a type
    annotation, and an optional :func:`components.field` to set the default or
    a custom parser. The options field specifically is designated with
    :func:`components.options` instead.

    Classes created in this way have auto-generated slots and an auto-generated
    ``__init__``. The init-signature contains all the custom id fields as
    keyword-only arguments.
    """

    event = "on_dropdown"

    custom_id = custom_id_impl.AutoID()

    placeholder: typing.Optional[str] = fields.internal(None)
    min_values: int = fields.internal(1)
    max_values: int = fields.internal(1)
    disabled: bool = fields.internal(False)  # noqa: FBT003

    async def as_ui_component(self) -> disnake.ui.BaseSelect:  # noqa: D102
        # <<docstring inherited from component_api.RichButton>>
        ...

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

        return await cls.factory.loads(interaction, match.groupdict())

    async def callback(  # pyright: ignore[reportIncompatibleMethodOverride]  # noqa: D102, E501
        self, __inter: interaction.MessageInteraction
    ) -> None:
        # <<docstring inherited from component_api.RichButton>>

        # NOTE: We narrow the interaction type down to a disnake.MessageInteraction
        #       here. This isn't typesafe, but it's just cleaner for the user.
        ...


class RichStringSelect(BaseSelect, typing.Protocol):
    """The default implementation of a disnake-ext-components string select."""
    options: list[disnake.SelectOption] = fields.internal(
        attr.Factory(list)  # pyright: ignore
    )

    async def as_ui_component(self) -> disnake.ui.StringSelect[None]:
        return disnake.ui.StringSelect(
            placeholder=self.placeholder,
            min_values=self.min_values,
            max_values=self.max_values,
            disabled=self.disabled,
            options=self.options,
            custom_id=await self.dumps(),
        )


class RichUserSelect(BaseSelect, typing.Protocol):
    """The default implementation of a disnake-ext-components user select."""
    async def as_ui_component(self) -> disnake.ui.UserSelect[None]:
        return disnake.ui.UserSelect(
            placeholder=self.placeholder,
            min_values=self.min_values,
            max_values=self.max_values,
            disabled=self.disabled,
            custom_id=await self.dumps(),
        )


class RichRoleSelect(BaseSelect, typing.Protocol):
    """The default implementation of a disnake-ext-components role select."""
    async def as_ui_component(self) -> disnake.ui.RoleSelect[None]:
        return disnake.ui.RoleSelect(
            placeholder=self.placeholder,
            min_values=self.min_values,
            max_values=self.max_values,
            disabled=self.disabled,
            custom_id=await self.dumps(),
        )


class RichMentionableSelect(BaseSelect, typing.Protocol):
    """The default implementation of a disnake-ext-components mentionable select."""
    async def as_ui_component(self) -> disnake.ui.MentionableSelect[None]:
        return disnake.ui.MentionableSelect(
            placeholder=self.placeholder,
            min_values=self.min_values,
            max_values=self.max_values,
            disabled=self.disabled,
            custom_id=await self.dumps(),
        )


class RichChannelSelect(BaseSelect, typing.Protocol):
    """The default implementation of a disnake-ext-components channel select."""
    async def as_ui_component(self) -> disnake.ui.ChannelSelect[None]:
        return disnake.ui.ChannelSelect(
            placeholder=self.placeholder,
            min_values=self.min_values,
            max_values=self.max_values,
            disabled=self.disabled,
            custom_id=await self.dumps(),
        )
