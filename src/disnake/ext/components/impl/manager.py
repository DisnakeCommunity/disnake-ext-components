"""Default implementation of the component manager api."""

from __future__ import annotations

import contextlib
import typing
import weakref

from disnake.ext import commands
from disnake.ext.components import interaction as interaction_impl
from disnake.ext.components.api import component as component_api
from disnake.ext.components.impl.component import base as component_base_impl

if typing.TYPE_CHECKING:
    import disnake

__all__: typing.Sequence[str] = ("ComponentManager",)


_TypeT = typing.TypeVar("_TypeT", bound="typing.Type[typing.Any]")
AnyBot = typing.Union[commands.Bot, commands.InteractionBot]


def _recurse_subclasses(cls: _TypeT) -> typing.Generator[_TypeT, None, None]:
    for subclass in cls.__subclasses__():
        yield subclass
        yield from _recurse_subclasses(subclass)


def _is_protocol(cls: typing.Type[typing.Any]) -> bool:
    return bool(getattr(cls, "_is_protocol", False))


def _assert_componentmeta(
    cls: typing.Type[typing.Any],
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

    __slots__: typing.Sequence[str] = ("bot", "components", "_recursive_guard")

    bot: AnyBot
    components: weakref.WeakKeyDictionary[
        typing.Type[component_api.RichComponent],
        typing.Callable[[disnake.Interaction], typing.Coroutine[None, None, None]],
    ]
    _recursive_guard: typing.Optional[typing.Type[component_api.RichComponent]]

    def __init__(self, bot: AnyBot):
        self.bot = bot
        self.components = weakref.WeakKeyDictionary()
        self._recursive_guard = None

    @contextlib.contextmanager
    def _guard(
        self, component: typing.Type[component_api.RichComponent]
    ) -> typing.Generator[None, None, None]:
        self._recursive_guard = component
        yield
        self._recursive_guard = None

    def _subscribe(self, component: typing.Type[component_api.RichComponent]) -> None:
        if not _assert_componentmeta(component).is_active:
            return

        if self._recursive_guard is component:
            return

        with self._guard(component):
            component.set_manager(self)

            if not _is_protocol(component):
                callback = self.wrap_component(weakref.ref(component))

                self.components[component] = callback
                self.bot.add_listener(callback, component.event)

    # TODO: Consider using Any here so that you can actually pass protocol
    #       classes without pyright getting angry...
    def subscribe(  # noqa: D102
        self,
        component: typing.Type[component_api.RichComponent],
        /,
        *,
        recursive: bool = True,
    ) -> None:
        # <<docstring inherited from component_api.ComponentManager>>

        self._subscribe(component)
        if not recursive:
            return

        for child_component in _recurse_subclasses(component):
            self._subscribe(child_component)

    def _unsubscribe(self, component: typing.Type[component_api.RichComponent]) -> None:
        _assert_componentmeta(component)

        if self._recursive_guard is component:
            return

        with self._guard(component):
            component.set_manager(None)

            if not _is_protocol(component):
                callback = self.components.pop(component)
                self.bot.remove_listener(callback, component.event)

    def unsubscribe(  # noqa: D102
        self,
        component: typing.Type[component_api.RichComponent],
        /,
        *,
        recursive: bool = True,
    ) -> None:
        # <<docstring inherited from component_api.ComponentManager>>

        self._unsubscribe(component)
        if not recursive:
            return

        for child_component in _recurse_subclasses(component):
            self._unsubscribe(child_component)

    @contextlib.contextmanager
    def callback_hook(
        self, component: component_api.RichComponent  # noqa: ARG002
    ) -> typing.Generator[None, None, None]:
        """Wrap all component callbacks on this manager with this context manager.

        Any code before the ``yield``-statement will run after validating the
        component should run, but before its callback is invoked.
        Any code after the ``yield``-statement will run after the component
        callback is invoked.

        Parameters
        ----------
        component:
            The component instance that is about to be invoked.
        """
        yield

    def wrap_component(
        self,
        component_ref: weakref.ReferenceType[typing.Type[component_api.RichComponent]],
    ) -> typing.Callable[[disnake.Interaction], typing.Coroutine[None, None, None]]:
        """Wrap a component in a callable that handles instantiating and calling it.

        This is used to generate a callback to register to the bot as a listener.

        Parameters
        ----------
        component_ref:
            A :func:`weakref.ref` to the component to wrap.

        Returns
        -------
        typing.Callable[[:class:`disnake.Interaction`], typing.Coroutine[None, None, None]]:
            The generated callable.
        """  # noqa: E501

        async def component_listener(interaction: disnake.Interaction) -> None:
            component = component_ref()
            if not component:
                return

            if not _assert_componentmeta(component).is_active:
                # In case an extension was unloaded and the component in question
                # only lingers because it has not yet been garbage collected,
                # we manually unsubscribe it from the manager to prevent this
                # from happening again later.
                self.unsubscribe(component)

            if not component.should_invoke_for(interaction):
                return

            instance = await component.loads(interaction)

            with self.callback_hook(instance):
                await instance.callback(interaction_impl.wrap_interaction(interaction))

        return component_listener

    def basic_config(self) -> None:
        """Do basic configuration for this manager.

        This automatically registers **all** current and future components to
        this manager.
        """
        # TODO: Do we keep this? Maybe rename it somehow?

        self.subscribe(component_base_impl.ComponentBase)  # pyright: ignore
