"""Protocols for components and component managers."""

from __future__ import annotations

import typing

import disnake

if typing.TYPE_CHECKING:
    import typing_extensions

__all__: typing.Sequence[str] = ("RichComponent", "RichButton", "ComponentManager")


_T = typing.TypeVar("_T")

AnyEmoji = typing.Union[str, disnake.PartialEmoji, disnake.Emoji]
MaybeCoroutine = typing.Union[_T, typing.Coroutine[None, None, _T]]


@typing.runtime_checkable
class RichComponent(typing.Protocol):
    """The baseline protocol for any kind of component.

    Any and all components must implement this protocol in order to be properly
    handled by disnake-ext-components.
    """

    __slots__: typing.Sequence[str] = ()

    custom_id: typing.ClassVar[str]
    event: typing.ClassVar[str]

    @classmethod
    def should_invoke_for(cls, __interaction: disnake.Interaction) -> bool:
        """Determine whether to fire this component's callback.

        This is done by determining whether the passed interaction has a
        custom id that matches that of this component type.

        Parameters
        ----------
        interaction: disnake.Interaction
            The interaction to check.

        Returns
        -------
        bool:
            Whether or not a component of this kind caused the interaction.
        """
        ...

    @classmethod
    async def loads(
        cls,
        __interaction: typing.Any,  # noqa: ANN401
    ) -> typing_extensions.Self:
        """Load a fully-fledged component from an interaction.

        The interaction's custom id will be used to parse any special parameters.

        Parameters
        ----------
        interaction: disnake.Interaction
            The interaction from which to take the component data.

        Returns
        -------
        ComponentBase:
            An instance of this class with parameters extracted and parsed from
            the custom id.
        """
        # NOTE: The typing.Any annotation here is required so that we can
        #       narrow it down to specific interaction types later.
        ...

    async def dumps(self) -> str:
        """Dump an instance of this class into a custom id string.

        This ensures all special parameters are stored on the string in such a
        way that they can be losslessly loaded in the future by means of
        :meth:`loads`.

        Returns
        -------
        str:
            The parsed custom id.
        """
        ...

    async def callback(self, __interaction: disnake.Interaction) -> None:
        """Run the component callback.

        This should be implemented by the user in each concrete component type.

        To properly handle interactions, any interaction should first be
        checked using :meth:`should_invoke_for`, then turned into a component
        instance using :meth:`loads`. Finally, :meth:`callback` should be
        called on the component instance.

        Parameters
        ----------
        interaction: disnake.Interaction
            The interaction that caused this button to fire.
        """
        ...

    async def as_ui_component(self) -> disnake.ui.WrappedComponent:
        """Convert this component into a component that can be sent by disnake.

        Returns
        -------
        disnake.ui.WrappedComponent:
            A component that can be sent by disnake, maintaining the parameters
            and custom id set on this rich component.
        """
        ...

    @classmethod
    def set_manager(cls, __manager: typing.Optional[ComponentManager]) -> None:
        """Set the component manager for this component type.

        Parameters
        ----------
        manager: typing.Optional[:class:`ComponentManager`]
            The component manager to set on this component type.
        """
        ...


@typing.runtime_checkable
class RichButton(RichComponent, typing.Protocol):
    """Baseline protocol for Button-like components."""

    __slots__: typing.Sequence[str] = ()

    label: str | None
    """The label of the component.

    Either or both this field or the ``emoji`` field must be set.
    """
    style: disnake.ButtonStyle
    """The style of the component.

    This dictates how the button is displayed on discord.
    """
    emoji: AnyEmoji | None
    """The emoji that is to be displayed on this button.

    Either or both this field or the ``emoji`` field must be set.
    """
    disabled: bool
    """Whether or not this button is disabled.

    A disabled button is greyed out on discord, and cannot be pressed.
    Disabled buttons can therefore not cause any interactions, either.
    """

    async def as_ui_component(self) -> disnake.ui.Button[None]:  # noqa: D102
        # <<Docstring inherited from RichComponent>>
        ...


@typing.runtime_checkable
class RichSelect(RichComponent, typing.Protocol):
    """Baseline protocol for Select-like components."""

    __slots__: typing.Sequence[str] = ()

    placeholder: str | None
    """The placeholder of the component.

    This shows when nothing is selected, or shows nothing if set to ``None``.
    """
    min_values: int
    """The minimum number of values the user must select.

    This must lie between 1 and 25, inclusive.
    """
    max_values: int
    """The maximum number of values the user may select.

    This must lie between 1 and 25, inclusive.
    """
    disabled: bool
    """Whether or not this button is disabled.

    A disabled select is greyed out on discord, and cannot be used.
    Disabled selects can therefore not cause any interactions, either.
    """

    async def as_ui_component(self) -> disnake.ui.StringSelect[None]:  # noqa: D102
        # <<Docstring inherited from RichComponent>>
        ...


@typing.runtime_checkable
class ComponentManager(typing.Protocol):
    """The baseline protocol for any kind of component manager.

    Any and all component managers must implement this protocol in order to be
    properly handled by disnake-ext-components.

    Component managers keep track of registered components and manage
    registering (:meth:`subscribe`) and deregistering (:meth:`unsubscribe`) their
    callbacks to the bot.
    """

    __slots__: typing.Sequence[str] = ()

    def subscribe(
        self,
        component: type[RichComponent],
        /,
        *,
        recursive: bool = True,
    ) -> None:
        """Register a component to this component manager.

        This will automatically register the component callback as a listener
        to the bot.

        In case recursive is set to ``True``, all of the provided component's
        subclasses -- and recursively also the subclasses of those -- will also
        be registered.

        Parameters
        ----------
        component:
            The component to register.
        recursive:
            Whether or not to recursively register all subclasses of the component.
        """
        ...

    def unsubscribe(
        self,
        component: type[RichComponent],
        /,
        *,
        recursive: bool = True,
    ) -> None:
        """Deregister a component from this component manager.

        Note that this only works if the component has first been registered.

        This will automatically remove the listener for the provided component
        from the bot.

        In case recursive is set to ``True``, all of the provided component's
        subclasses -- and recursively also the subclasses of those -- will also
        be deregistered.

        Parameters
        ----------
        component:
            The component to register.
        recursive:
            Whether or not to recursively register all subclasses of the component.
        """
        ...
