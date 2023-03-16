"""Default implementation of the component manager api."""

from __future__ import annotations

import typing
import weakref

from disnake.ext import commands
from disnake.ext.components import interaction as interaction_impl
from disnake.ext.components.api import component as component_api
from disnake.ext.components.impl.component import base as component_base_impl

if typing.TYPE_CHECKING:
    import disnake

__all__: typing.Sequence[str] = ("ComponentManager",)


_TypeT = typing.TypeVar("_TypeT", bound="type[typing.Any]")
AnyBot = typing.Union[commands.Bot, commands.InteractionBot]


def _recurse_subclasses(cls: _TypeT) -> typing.Generator[_TypeT, None, None]:
    for subclass in cls.__subclasses__():
        yield subclass
        yield from _recurse_subclasses(subclass)


def _is_protocol(cls: type[typing.Any]) -> bool:
    return bool(getattr(cls, "_is_protocol", False))


def _assert_componentmeta(
    cls: type[typing.Any],
) -> component_base_impl.ComponentMeta:
    if isinstance(cls, component_base_impl.ComponentMeta):
        return cls

    msg = (
        "A valid component must have"
        f" {component_base_impl.ComponentMeta.__qualname__!r} as its metaclass."
    )
    raise TypeError(msg)


class ComponentManager(component_api.ComponentManager):
    """The default implementation of a component manager.

    This class keeps track of all components defined and their listener
    functions, and is in charge of registering them to and deregistering them
    from the bot. Note that by nature of this using :meth:`commands.Bot.listen`
    under the hood, this class does not support :class:`disnake.Client`-classes.

    Parameters
    ----------
    bot:
        The bot to register this manager's components on as listeners.
    """

    __slots__: typing.Sequence[str] = ("bot", "components")

    bot: AnyBot
    components: weakref.WeakSet[type[component_api.RichComponent]]

    def __init__(self, bot: AnyBot):
        self.bot = bot
        self.components = weakref.WeakSet()

    def _subscribe(self, component: type[component_api.RichComponent]) -> None:
        if not _assert_componentmeta(component).is_active:
            return

        component.set_manager(self)
        if not _is_protocol(component):
            self.bot.add_listener(self.wrap_component(component), component.event)

    # TODO: Consider using Any here so that you can actually pass protocol
    #       classes without pyright getting angry...
    def subscribe(  # noqa: D102
        self, component: type[component_api.RichComponent], /, *, recursive: bool = True
    ) -> None:
        # <<docstring inherited from component_api.ComponentManager>>

        self._subscribe(component)
        if not recursive:
            return

        for child_component in _recurse_subclasses(component):
            self._subscribe(child_component)

    def _unsubscribe(self, component: type[component_api.RichComponent]) -> None:
        _assert_componentmeta(component)

        component.set_manager(None)

        # TODO: Implement removing the listener from the bot.

    def unsubscribe(  # noqa: D102
        self, component: type[component_api.RichComponent], /, *, recursive: bool = True
    ) -> None:
        # <<docstring inherited from component_api.ComponentManager>>

        self._unsubscribe(component)
        if not recursive:
            return

        for child_component in _recurse_subclasses(component):
            self._unsubscribe(child_component)

    def wrap_component(
        self, component: type[component_api.RichComponent]
    ) -> typing.Callable[[disnake.Interaction], typing.Coroutine[None, None, None]]:
        """Wrap a component in a callable that handles instantiating and calling it.

        This is used to generate a callback to register to the bot as a listener.

        Parameters
        ----------
        component:
            The component to wrap.

        Returns
        -------
        typing.Callable[[:class:`disnake.Interaction`], typing.Coroutine[None, None, None]]:
            The generated callable.
        """  # noqa: E501

        async def component_listener(interaction: disnake.Interaction) -> None:
            if not _assert_componentmeta(component).is_active:
                # In case an extension was unloaded and the component in question
                # only lingers because it has not yet been garbage collected,
                # we manually unsubscribe it from the manager to prevent this
                # from happening again later.
                self.unsubscribe(component)

            if not component.should_invoke_for(interaction):
                return

            instance = await component.loads(interaction)
            await instance.callback(interaction_impl.wrap_interaction(interaction))
            return

        return component_listener

    def basic_config(self) -> None:
        """Do basic configuration for this manager.

        This automatically registers **all** current and future components to
        this manager.
        """
        # TODO: Do we keep this? Maybe rename it somehow?

        self.subscribe(component_base_impl.ComponentBase)  # pyright: ignore
