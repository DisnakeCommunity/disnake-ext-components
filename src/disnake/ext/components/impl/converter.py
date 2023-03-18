"""Standard implementation of the overarching converter type."""

from __future__ import annotations

import typing

import attr
from disnake.ext.components import fields
from disnake.ext.components.api import component as component_api
from disnake.ext.components.api import converter as converter_api
from disnake.ext.components.api import parser as parser_api
from disnake.ext.components.impl import custom_id as custom_id_impl
from disnake.ext.components.impl.parser import base as parser_base
from disnake.ext.components.internal import aio

if typing.TYPE_CHECKING:
    import disnake
    import typing_extensions

__all__: typing.Sequence[str] = ("Converter",)


@attr.define(slots=True)
class Converter(converter_api.Converter):
    """Implementation of the overarching converter type.

    A converter holds information about all the custom id fields of a component,
    and contains that component's parsers. In most situations, a converter can
    simply be created using :meth:`from_component`.
    """

    parsers: typing.Mapping[str, parser_api.Parser[typing.Any]]
    component: type[component_api.RichComponent]

    @classmethod
    def from_component(  # noqa: D102
        cls,
        component: type[component_api.RichComponent],
    ) -> typing_extensions.Self:
        # <<docstring inherited from converter_api.Converter>>

        parser: typing.Optional[parser_api.Parser[typing.Any]]

        parsers: dict[str, parser_api.Parser[typing.Any]] = {}
        for field in fields.get_fields(component, kind=fields.FieldType.CUSTOM_ID):
            parser = fields.get_parser(field)

            if not parser:
                parser = parser_base.get_parser(field.type or str).default()

            parsers[field.name] = parser

        return cls(parsers, component)

    async def loads_param(
        self,
        interaction: disnake.Interaction,
        param: str,
        value: str,
    ) -> object:
        """Parse a single custom id parameter to the desired type with its parser.

        Parameters
        ----------
        interaction:
            The interaction that caused the component to activate.
        param:
            The name of the custom id field that is to be parsed.
        value:
            The value of the custom id field that is to be parsed.

        Returns
        -------
        :class:`object`:
            The parsed custom id field value.
        """
        parser = self.parsers[param]
        result = parser.loads(interaction, value)
        return await aio.eval_maybe_coro(result)

    async def dumps_param(
        self,
        param: str,
        value: object,
    ) -> str:
        """Parse a single custom id parameter to its string form for custom id storage.

        Parameters
        ----------
        interaction:
            The interaction that caused the component to activate.
        param:
            The name of the custom id field that is to be parsed.
        value:
            The value of the custom id field that is to be parsed.

        Returns
        -------
        :class:`str`:
            The dumped custom id parameter, ready for storage inside a custom id.
        """
        parser = self.parsers[param]
        result = parser.dumps(value)
        return await aio.eval_maybe_coro(result)

    async def loads(  # noqa: D102
        self,
        interaction: disnake.Interaction,
        params: typing.Mapping[str, str],
    ) -> component_api.RichComponent:
        # <<docstring inherited from converter_api.Converter>>

        kwargs = {
            param: await self.loads_param(interaction, param, value)
            for param, value in params.items()
            if value
        }

        return self.component(**kwargs)

    async def dumps(self, component: component_api.RichComponent) -> str:  # noqa: D102
        # <<docstring inherited from converter_api.Converter>>

        component_type = type(component)

        kwargs = {
            field.name: await self.dumps_param(
                field.name, getattr(component, field.name)
            )
            for field in fields.get_fields(
                component_type, kind=fields.FieldType.CUSTOM_ID
            )
        }

        return typing.cast(
            custom_id_impl.CustomID, component_type.custom_id
        ).format_map(kwargs)
