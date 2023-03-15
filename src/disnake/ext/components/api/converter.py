"""Protocols for overarching converter types."""

from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    import disnake
    import typing_extensions
    from disnake.ext.components.api import component as component_api

__all__: typing.Sequence[str] = ("Converter",)


class Converter(typing.Protocol):
    """The baseline protocol for any kind of converter.

    Any and all converters must implement this protocol in order to be properly
    handled by disnake-ext-components.

    A converter handles creating a component instance from a custom id by
    running all individual fields' parsers and aggregating the result into
    a component instance.
    """

    @classmethod
    def from_component(
        cls,
        component: type[component_api.RichComponent],
    ) -> typing_extensions.Self:
        """Create a converter from the provided component.

        This takes the component's fields into account and generates the
        corresponding parser types for each field if a parser was not provided
        manually for that particular field.

        Parameters
        ----------
        component:
            The component for which to create a converter.
        """
        ...

    async def loads(
        self,
        interaction: disnake.Interaction,
        params: typing.Mapping[str, str],
    ) -> component_api.RichComponent:
        """Create a new component instance from the provided custom id.

        This requires the custom id to already have been decomposed into
        individual fields. This is generally done using the
        :meth:`api.CustomID.match` method.

        Parameters
        ----------
        interaction:
            The interaction to use for creating the component instance.
        params:
            A mapping of field name to to-be-parsed field values.
        """
        # TODO: Return an ext-components specific conversion error.
        ...

    async def dumps(self, component: component_api.RichComponent) -> str:
        """Dump a component into a new custom id string.

        This converts the component's individual fields back into strings and
        and uses these strings to build a new custom id. This is generally done
        using the :meth:`api.CustomID.complete` method.

        Parameters
        ----------
        component:
            The component to dump into a custom id.
        """
        ...
