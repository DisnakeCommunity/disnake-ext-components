"""Protocols for custom ids."""

from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    import typing_extensions
    from disnake.ext.components.api import component as component_api

__all__: typing.Sequence[str] = ("CustomID",)


class CustomID(typing.Protocol):
    """The baseline protocol for any kind of custom id.

    Any and all custom id implementations must implement this protocol in order
    to be handled by disnake-ext-components.
    """

    @classmethod
    def from_component(
        cls,
        component: typing.Type[component_api.RichComponent],
        /,
        *,
        name: typing.Optional[str] = None,
        sep: str = "|",
    ) -> typing_extensions.Self:
        """Build a custom id using the fields of the provided component.

        A name can optionally be provided. If not provided, the class name will
        be used instead. The generated custom id will be of the spec

        {name}{separator}{field_1}{separator}{field_2}{separator}{...}

        Parameters
        ----------
        component:
            The component from which to build the custom id.
        name:
            The name used for the custom id. If not provided, this will default
            to the name of the component class.
        sep:
            The separator character used to delimit the custom id's name and
            its individual fields.
        """
        ...

    def validate(self, __component: typing.Type[component_api.RichComponent]) -> None:
        """Validate the custom id with the component.

        This ensures that the custom id definition is valid for the component,
        ensuring that any mistakes in the definition of the custom id can be
        caught before the component is invoked.

        Parameters
        ----------
        component: typing.Type[components.api.RichComponent]
            The component used to validate this custom id.

        Raises
        ------
        ValueError:
            The custom id contains fields not present on the component class,
            and is therefore invalid.
        """
        ...

    def complete(self, component: component_api.RichComponent) -> str:
        """Complete the custom id with field values from the provided component.

        This automatically fills in all the custom id's fields based on the
        values assigned to the corresponding fields in the provided component.

        Parameters
        ----------
        component: typing.Type[components.api.RichComponent]
            The component used to complete this custom id.
        """
        ...

    def check_name(self, custom_id: str) -> bool:
        """Check if the custom id starts with the name part of this custom id.

        This is used as a preliminary check before a more expensive regex check
        is executed over the whole custom id.

        Parameters
        ----------
        custom_id: str
            The custom_id to compare to.

        Returns
        -------
        bool:
            Whether or not the input custom id has a name that matches this one.
        """
        # TODO: Consider removing this to only keep 'essential' methods.
        ...

    @typing.overload
    def match(
        self,
        custom_id: str,
        /,
        *,
        strict: typing.Literal[False] = False,
    ) -> typing.Optional[typing.Match[str]]:
        ...

    @typing.overload
    def match(
        self,
        custom_id: str,
        /,
        *,
        strict: typing.Literal[True],
    ) -> typing.Match[str]:
        ...

    def match(
        self,
        custom_id: str,
        /,
        *,
        strict: bool = False,
    ) -> typing.Optional[typing.Match[str]]:
        """Perform a full-fledged regex match with the custom id.

        This extracts all the parameters from the custom id in case of a match.
        If strict is set to ``True``, this method will error instead of
        returning None in case of a failed match.

        Parameters
        ----------
        custom_id: str
            The custom id to match.
        strict: bool
            Whether to return none (strict=False) or raise (strict=True) in
            case matching fails.

        Raises
        ------
        RuntimeError:
            Matching failed and strict was set to True.
        """
        ...
