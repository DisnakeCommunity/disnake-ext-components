from __future__ import annotations

import inspect
import sys
import typing as t

import disnake
from disnake.ext import commands

from . import abc, deprecation, params, types_, utils

__all__ = [
    "button_listener",
    "ButtonListener",
    "select_listener",
    "SelectListener",
    "modal_listener",
    "ModalListener",
    "match_component",
]


if sys.version_info >= (3, 10):
    from typing import Concatenate, ParamSpec

else:
    from typing_extensions import Concatenate, ParamSpec

T = t.TypeVar("T")
P = ParamSpec("P")

MaybeCollection = t.Union[t.Collection[T], T]
ParentT = t.TypeVar("ParentT")

ListenerT = t.TypeVar("ListenerT", bound="abc.BaseListener[t.Any, t.Any, t.Any]")

ComponentListener = t.Union[
    "ButtonListener[t.Any, t.Any]",
    "SelectListener[t.Any, t.Any]",
]

ButtonReference = t.Union[
    disnake.Button,
    disnake.ui.Button[t.Any],
    types_.AbstractComponent,
]
SelectReference = t.Union[
    disnake.SelectMenu,
    disnake.ui.Select[t.Any],
    types_.AbstractComponent,
]


# fmt: off
ButtonListenerCallback = t.Union[
    t.Callable[Concatenate[ParentT, disnake.MessageInteraction, P], types_.Coro[T]],
    t.Callable[Concatenate[disnake.MessageInteraction, P], types_.Coro[T]],
]

SelectListenerCallback = t.Union[
    t.Callable[Concatenate[ParentT, disnake.MessageInteraction, P], types_.Coro[T]],
    t.Callable[Concatenate[ParentT, disnake.MessageInteraction, t.Any, P], types_.Coro[T]],

    t.Callable[Concatenate[disnake.MessageInteraction, P], types_.Coro[T]],
    t.Callable[Concatenate[disnake.MessageInteraction, t.Any, P], types_.Coro[T]],
]

# flake8: noqa: E501
ModalListenerCallback = t.Union[
    t.Callable[Concatenate[ParentT, disnake.ModalInteraction, P], types_.Coro[T]],
    t.Callable[Concatenate[ParentT, disnake.ModalInteraction, t.Any, P], types_.Coro[T]],
    t.Callable[Concatenate[ParentT, disnake.ModalInteraction, t.Any, t.Any, P], types_.Coro[T]],
    t.Callable[Concatenate[ParentT, disnake.ModalInteraction, t.Any, t.Any, t.Any, P], types_.Coro[T]],
    t.Callable[Concatenate[ParentT, disnake.ModalInteraction, t.Any, t.Any, t.Any, t.Any, P], types_.Coro[T]],
    t.Callable[Concatenate[ParentT, disnake.ModalInteraction, t.Any, t.Any, t.Any, t.Any, t.Any, P], types_.Coro[T]],

    t.Callable[Concatenate[disnake.ModalInteraction, P], types_.Coro[T]],
    t.Callable[Concatenate[disnake.ModalInteraction, t.Any, P], types_.Coro[T]],
    t.Callable[Concatenate[disnake.ModalInteraction, t.Any, t.Any, P], types_.Coro[T]],
    t.Callable[Concatenate[disnake.ModalInteraction, t.Any, t.Any, t.Any, P], types_.Coro[T]],
    t.Callable[Concatenate[disnake.ModalInteraction, t.Any, t.Any, t.Any, t.Any, P], types_.Coro[T]],
    t.Callable[Concatenate[disnake.ModalInteraction, t.Any, t.Any, t.Any, t.Any, t.Any, P], types_.Coro[T]],
]
# fmt: on


class ButtonListener(abc.BaseListener[P, T, disnake.MessageInteraction]):
    """An advanced component listener that supports syntax similar to disnake slash commands.
    This listener is specific for :class:`disnake.ui.Button`s, and supports storing data inside
    the Button's custom_id.

    Mainly created using :func:`components.button_listener`.

    Parameters
    ----------
    func: Callable[[...], Any]
        The function that is to be used as callback for the listener. A :class:`ButtonListener`
        requires the first (non-self) parameter to be annotated as `disnake.MessageInteraction`.
        If the listener is invoked because a matching component is interacted with, the input is
        converted to match the function's annotations.
    regex: Union[:class:`str`, :class:`re.Pattern`, None]
        If provided, this will override the default behavior of automatically generating matching
        regex for the listener, and will use custom regex instead. For the listener to fire, the
        incoming `custom_id` must pass being `re.fullmatch`ed with this regex. Use named capture
        groups to match group names with function parameter names.
    sep: :class:`str`
        The symbol(s) used to separate individual components of the `custom_id`. Defaults to ':'.
        Under normal circumstances, this should not lead to conflicts. In case ':' is intentionally
        part of the `custom_id`s matched by the listener, this should be set to a different value
        to prevent conflicts.
    reference: Optional[Union[:class:`disnake.Button`, :class:`disnake.ui.Button`, :class:`AbstractComponent`]
        A reference component used to set default values in `~.build_component`.
    """

    __cog_listener_names__: t.List[types_.ListenerType] = [types_.ListenerType.BUTTON]

    reference: types_.AbstractComponent
    """A reference component used to set default values in `~.build_component`."""

    def __init__(
        self,
        callback: ButtonListenerCallback[ParentT, P, T],
        *,
        name: t.Optional[str] = None,
        regex: t.Union[str, t.Pattern[str], None] = None,
        sep: str = ":",
        reference: t.Optional[ButtonReference] = None,
    ) -> None:
        super().__init__(callback, name=name, regex=regex, sep=sep)

        special_params, listener_params = utils.extract_listener_params(self._signature)

        if special_params:
            raise TypeError(
                f"A {type(self).__name__} does not take any special arguments, got "
                f"{len(special_params)}. Please confirm you didn't forget the `*,` in the callback."
            )

        self.params = [params.ParamInfo.from_param(param) for param in listener_params]
        self.reference = self._choose_optimal_reference(reference)

    def _choose_optimal_reference(
        self,
        component: t.Optional[ButtonReference],
    ) -> types_.AbstractComponent:
        if component is not None:  # Manually provided takes highest priority
            if isinstance(component, types_.AbstractComponent):
                return component
            return types_.AbstractComponent.from_component(component)

        # Nothing of use was found, return an AbstractComponent that can match any button.
        return types_.AbstractComponent(type=disnake.ComponentType.button)

    async def __call__(  # pyright: ignore
        self,
        inter: disnake.MessageInteraction,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> t.Optional[T]:
        """Run all parameter converters, and if everything correctly converted, run the listener
        callback with the converted arguments.

        Parameters
        ----------
        inter: :class:`disnake.MessageInteraction`
            The interaction that intiated the listener.
        *args: Any
            Any arguments passed to the listener. Only really relevant when the listener is
            called manually. In all other cases, args will be empty, and parsing will instead
            be done based on the custom_id of the interaction.
            Note that arguments passed manually will be assumed correct, and will not be converted.

        Returns
        -------
        Any:
            If the decorated listener function is made to return anything, it will similarly
            be returned here. In all other cases, this will return `None`.
        """
        if args or kwargs:
            # The user manually called the listener so we skip any checks and just run.
            # Inter may thus not actually be an inter, but I feel like that's on the user.
            x = super().__call__(inter, *args, **kwargs)
            return await x

        if (custom_id := inter.component.custom_id) is None:
            return

        try:
            custom_id_params = self.parse_custom_id(custom_id)
        except ValueError:
            return

        if not await utils.assert_all_checks(self.checks, inter):
            return

        converted: t.Dict[str, t.Any] = {}
        for param, arg in zip(self.params, custom_id_params):
            converted[param.name] = await param.convert(
                arg,
                inter=inter,
                converted=list(converted.values()),
                skip_validation=bool(self.regex),
            )

        return await super().__call__(inter, **converted)

    async def build_component(
        self,
        style: t.Optional[disnake.ButtonStyle] = None,
        label: t.Optional[str] = None,
        disabled: t.Optional[bool] = None,
        url: t.Optional[str] = None,
        emoji: t.Union[str, disnake.Emoji, disnake.PartialEmoji, None] = None,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> disnake.ui.Button[t.Any]:
        return self.reference.with_overrides(
            style=style,
            label=label,
            disabled=disabled,
            url=url,
            emoji=emoji,
            custom_id=await self.build_custom_id(*args, **kwargs),
        ).as_component(disnake.ui.Button[t.Any])

    @deprecation.deprecated("build_component")
    async def build_button(
        self,
        style: disnake.ButtonStyle = disnake.ButtonStyle.secondary,
        label: t.Optional[str] = None,
        disabled: bool = False,
        url: t.Optional[str] = None,
        emoji: t.Union[str, disnake.Emoji, disnake.PartialEmoji, None] = None,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> disnake.ui.Button[t.Any]:
        return await self.build_component(
            style=style,
            label=label,
            disabled=disabled,
            url=url,
            emoji=emoji,
            *args,
            **kwargs,
        )

    build_button.__doc__ = build_component.__doc__


def button_listener(
    *,
    name: t.Optional[str] = None,
    regex: t.Union[str, t.Pattern[str], None] = None,
    sep: str = ":",
    bot: t.Optional[commands.Bot] = None,
    reference: t.Optional[ButtonReference] = None,
) -> t.Callable[[ButtonListenerCallback[ParentT, P, T]], ButtonListener[P, T]]:
    """Create a new :class:`ButtonListener` from a decorated function. The :class:`ButtonListener`
    will take care of regex-matching and persistent data stored in the `custom_id` of the
    :class:`disnake.ui.Button`.

    - The first parameter of the function (disregarding `self` inside a cog) is the
    :class:`disnake.MessageInteraction`.
    - After the Interaction, a ``*,`` should be added to separate it from the custom_id values.
    Custom-id values will always need to be keyword-only.
    - Any remaining parameters are stored in and resolved from the `custom_id`.

    Parameters
    ----------
    name: Optional[:class:`str`]
        A custom name to use as the base for custom ids. If no name is provided, the name of the
        wrapped callback function will be used instead.
    regex: Union[:class:`str`, :class:`re.Pattern`, None]
        Used to set custom regex for the listener to use, instead of the default automatic parsing.
        Defaults to None, which makes the :class:`ButtonListener` use the default automatic parsing.
    sep: :class:`str`
        The separator to use between `custom_id` parts. Defaults to ":". This is generally fine,
        however, if this character is meant to appear elsewhere in the `custom_id`, this should
        be changed to avoid conflicts.
    bot: :class:`commands.Bot`
        The bot to attach the listener to. This is only used as a shorthand to register the
        listener if it is defined outside of a cog. Alternatively, the usual `bot.listen` decorator
        or `bot.add_listener` method will work fine, too; provided the correct name is set.

    Returns
    -------
    :class:`ButtonListener`
        The newly created :class:`ButtonListener`.
    """

    def wrapper(
        func: ButtonListenerCallback[ParentT, P, T],
    ) -> ButtonListener[P, T]:
        listener = ButtonListener[P, T](
            func,
            name=func.__name__ if name is None else name,
            regex=regex,
            sep=sep,
            reference=reference,
        )

        if bot is not None:
            bot.add_listener(listener, types_.ListenerType.BUTTON)

        return listener

    return wrapper


class SelectListener(abc.BaseListener[P, T, disnake.MessageInteraction]):
    """An advanced component listener that supports syntax similar to disnake slash commands.
    This listener is specific for :class:`disnake.ui.Select`s, and supports both receiving the
    user-selected items on the select, and storing data inside the Select's custom_id.

    Mainly created using :func:`components.select_listener`.

    Parameters
    ----------
    func: Callable[[...], Any]
        The function that is to be used as callback for the listener. A :class:`SelectListener`
        requires the first (non-self) parameter to be annotated as `disnake.MessageInteraction`,
        and the second as `components.SelectValue`. If the listener is invoked because a matching
        component is interacted with, the input is converted to match the function's annotations.
    regex: Union[:class:`str`, :class:`re.Pattern`, None]
        If provided, this will override the default behavior of automatically generating matching
        regex for the listener, and will use custom regex instead. For the listener to fire, the
        incoming `custom_id` must pass being `re.fullmatch`ed with this regex. Use named capture
        groups to match group names with function parameter names.
    sep: :class:`str`
        The symbol(s) used to separate individual components of the `custom_id`. Defaults to ':'.
        Under normal circumstances, this should not lead to conflicts. In case ':' is intentionally
        part of the `custom_id`s matched by the listener, this should be set to a different value
        to prevent conflicts.
    reference: Optional[Union[:class:`disnake.SelectMenu`, :class:`disnake.ui.Select`, :class:`AbstractComponent`]
        A reference component used to set default values in `~.build_component`.
    """

    __cog_listener_names__: t.List[types_.ListenerType] = [types_.ListenerType.SELECT]

    select_param: t.Optional[params.ParamInfo]
    """The parameter with which the user-selected value(s) will be parsed. The values will be
    converted to match the type annotation of this parameter.
    """

    reference: types_.AbstractComponent
    """A reference component used to set default values in `~.build_component`."""

    def __init__(
        self,
        callback: SelectListenerCallback[ParentT, P, T],
        *,
        name: t.Optional[str] = None,
        regex: t.Union[str, t.Pattern[str], None] = None,
        sep: str = ":",
        reference: t.Optional[SelectReference] = None,
    ) -> None:
        super().__init__(callback, name=name, regex=regex, sep=sep)

        special_params, listener_params = utils.extract_listener_params(self._signature)
        self.params = [params.ParamInfo.from_param(param) for param in listener_params]

        if len(special_params) > 1:
            raise TypeError(
                f"A `{type(self).__name__}` must have exactly zero or one parameter before "
                f"the keyword-only argument separator (`*,`), got {len(special_params)}."
            )

        if special_params:
            self.select_param = params.ParamInfo.from_param(param := special_params[0])
            self.reference = self._choose_optimal_reference(reference, param)

        else:
            self.select_param = None
            self.reference = self._choose_optimal_reference(reference, None)

    def _choose_optimal_reference(
        self,
        component: t.Optional[SelectReference],
        param: t.Optional[inspect.Parameter],
    ) -> types_.AbstractComponent:
        if component is not None:  # Manually provided takes highest priority
            if isinstance(component, types_.AbstractComponent):
                return component
            return types_.AbstractComponent.from_component(component)

        if param is not None and isinstance(default := param.default, types_.AbstractComponent):
            if not default.get("options") and types_.get_origin(param.annotation) is t.Literal:
                # No options were defined in the AbstractComponent but the parameter was
                # annotated as literal, thus we should infer the options from the parameter.
                return default.with_overrides(
                    options=[str(arg) for arg in types_.get_args(param.annotation)]
                )

            return default

        # Nothing of use was found, return an AbstractComponent that can match any select.
        return types_.AbstractComponent(type=disnake.ComponentType.select)

    async def __call__(  # pyright: ignore
        self,
        inter: disnake.MessageInteraction,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> t.Optional[T]:
        """Run all parameter converters, and if everything correctly converted, run the listener
        callback with the converted arguments.

        Parameters
        ----------
        inter: :class:`disnake.MessageInteraction`
            The interaction that intiated the listener.
        *args: Any
            Any arguments passed to the listener. Only really relevant when the listener is
            called manually. In all other cases, args will be empty, and parsing will instead
            be done based on the custom_id of the interaction.
            Note that arguments passed manually will be assumed correct, and will not be converted.

        Returns
        -------
        Any:
            If the decorated listener function is made to return anything, it will similarly
            be returned here. In all other cases, this will return `None`.
        """
        if args or kwargs:
            # The user manually called the listener so we skip any checks and just run.
            # Inter may thus not actually be an inter, but I feel like that's on the user.
            x = super().__call__(inter, *args, **kwargs)
            return await x

        if not inter.values or (custom_id := inter.component.custom_id) is None:
            return

        try:
            custom_id_params = self.parse_custom_id(custom_id)
        except ValueError:
            return

        if not await utils.assert_all_checks(self.checks, inter):
            return

        # First convert custom_id params...
        converted: t.Dict[str, t.Any] = {}
        for param, arg in zip(self.params, custom_id_params):
            converted[param.name] = await param.convert(
                arg,
                inter=inter,
                converted=list(converted.values()),
                skip_validation=bool(self.regex),
            )

        # User didn't supply select params, can still be accessed through inter.values; return.
        if self.select_param is None:
            return await super().__call__(inter, **converted)

        # User did supply select params, convert inter.values and provide it to the param.
        converted_values = await self.select_param.convert(
            inter.values, inter=inter, converted=converted
        )

        return await super().__call__(inter, converted_values, **converted)

    async def build_component(
        self,
        placeholder: t.Optional[str] = None,
        min_values: t.Optional[int] = None,
        max_values: t.Optional[int] = None,
        options: t.Union[t.List[disnake.SelectOption], t.List[str], t.Dict[str, str], None] = None,
        disabled: t.Optional[bool] = None,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> disnake.ui.Select[t.Any]:
        """Build a :class:`disnake.ui.Select` that matches this listener.

        By default, this will create a select with custom_id based on the custom_id parameters.
        All other parameters use the normal select defaults, except this defaults max_options to
        ``len(options)``. These values can be overwritten by setting the parameter default to a
        :func:`.SelectValue`, and call it with the parameters you wish to set on the select.

        Parameters
        ----------
        **kwargs: Any
            The keyword-only parameters of the listener to store on the select's custom_id.

        Returns:
        :class:`disnake.ui.Select`
            The newly created select.
        """
        if self.select_param:
            # We need the underlying `inspect.Parameter` here...
            param = self.select_param.param

            # Parse options from `typing.Literal` if none were provided.
            if options is None and types_.get_origin(param.annotation) is t.Literal:
                options = [str(arg) for arg in types_.get_args(param.annotation)]

        return self.reference.with_overrides(
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            options=options,
            disabled=disabled,
            custom_id=await self.build_custom_id(*args, **kwargs),
        ).as_component(disnake.ui.Select[t.Any])

    @deprecation.deprecated("build_component")
    async def build_select(
        self,
        placeholder: t.Optional[str] = None,
        min_values: t.Optional[int] = None,
        max_values: t.Optional[int] = None,
        options: t.Union[t.List[disnake.SelectOption], t.List[str], t.Dict[str, str], None] = None,
        disabled: t.Optional[bool] = None,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> disnake.ui.Select[t.Any]:
        return await self.build_component(
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            options=options,
            disabled=disabled,
            *args,
            **kwargs,
        )

    build_select.__doc__ = build_component.__doc__


def select_listener(
    *,
    name: t.Optional[str] = None,
    regex: t.Union[str, t.Pattern[str], None] = None,
    sep: str = ":",
    bot: t.Optional[commands.Bot] = None,
    reference: t.Optional[SelectReference] = None,
) -> t.Callable[[SelectListenerCallback[ParentT, P, T]], SelectListener[P, T]]:
    """Create a new :class:`SelectListener` from a decorated function. The :class:`SelectListener`
    will take care of regex-matching and persistent data stored in the `custom_id` of the
    :class:`disnake.ui.Select`.

    - The first parameter of the function (disregarding `self` inside a cog) is the
    :class:`disnake.MessageInteraction`.
    - The next parameter will receive the selected values, and should be annotated as
    :class:`.SelectValue`. This should be narrowed down with an inner type. In case e.g. a list of
    strings is desired for all the values, the annotation would be
    `param: components.SelectValue[typing.List[str]]`.
    - After the select value, a ``*,`` should be added to separate it from the custom_id values.
    Custom-id values will always need to be keyword-only.
    - Any remaining parameters are stored in and resolved from the `custom_id`.

    Parameters
    ----------
    name: Optional[:class:`str`]
        A custom name to use as the base for custom ids. If no name is provided, the name of the
        wrapped callback function will be used instead.
    regex: Union[:class:`str`, :class:`re.Pattern`, None]
        Used to set custom regex for the listener to use, instead of the default automatic parsing.
        Defaults to None, which makes the :class:`SelectListener` use the default automatic parsing.
    sep: :class:`str`
        The separator to use between `custom_id` parts. Defaults to ":". This is generally fine,
        however, if this character is meant to appear elsewhere in the `custom_id`, this should
        be changed to avoid conflicts.
    bot: :class:`commands.Bot`
        The bot to attach the listener to. This is only used as a shorthand to register the
        listener if it is defined outside of a cog. Alternatively, the usual `bot.listen` decorator
        or `bot.add_listener` method will work fine, too; provided the correct name is set.

    Returns
    -------
    :class:`SelectListener`
        The newly created :class:`SelectListener`.
    """

    def wrapper(
        func: SelectListenerCallback[ParentT, P, T],
    ) -> SelectListener[P, T]:
        listener = SelectListener[P, T](
            func,
            name=func.__name__ if name is None else name,
            regex=regex,
            sep=sep,
            reference=reference,
        )

        if bot is not None:
            bot.add_listener(listener, types_.ListenerType.SELECT)

        return listener

    return wrapper


class ModalListener(abc.BaseListener[P, T, disnake.ModalInteraction]):

    __cog_listener_names__: t.List[types_.ListenerType] = [types_.ListenerType.MODAL]

    modal_params: t.List[params.ParamInfo]
    """The parameters with which the user-entered value(s) will be parsed. The values will be
    converted to match the type annotations of these parameters.
    """

    def __init__(
        self,
        callback: ModalListenerCallback[ParentT, P, T],
        *,
        name: t.Optional[str] = None,
        regex: t.Union[str, t.Pattern[str], None] = None,
        sep: str = ":",
    ) -> None:
        super().__init__(callback, name=name, regex=regex, sep=sep)

        special_params, listener_params = utils.extract_listener_params(self._signature)

        if not 1 <= len(special_params) <= 5:
            raise TypeError(
                f"A `{type(self).__name__}` must have between one and five parameters before the "
                f"keyword-only argument separator (`*,`), got {len(special_params)}."
            )

        self.params = [params.ParamInfo.from_param(param) for param in listener_params]
        self.modal_params = [params.ParamInfo.from_param(param) for param in special_params]
        self.field_ids = [f"{self.__name__}{self.sep}{param.name}" for param in special_params]

    async def __call__(  # pyright: ignore
        self,
        inter: disnake.ModalInteraction,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> t.Optional[T]:
        """Run all parameter converters, and if everything correctly converted, run the listener
        callback with the converted arguments.

        Parameters
        ----------
        inter: :class:`disnake.ModalInteraction`
            The interaction that intiated the listener.
        *args: Any
            Any arguments passed to the listener. Only really relevant when the listener is
            called manually. In all other cases, args will be empty, and parsing will instead
            be done based on the custom_id of the interaction.
            Note that arguments passed manually will be assumed correct, and will not be converted.

        Returns
        -------
        Any:
            If the decorated listener function is made to return anything, it will similarly
            be returned here. In all other cases, this will return `None`.
        """
        if args or kwargs:
            return await super().__call__(inter, *args, **kwargs)

        if list(inter.text_values) != self.field_ids:
            return

        try:
            custom_id_params = self.parse_custom_id(inter.custom_id)
        except ValueError:
            return

        if not await utils.assert_all_checks(self.checks, inter):
            return

        converted: t.Dict[str, t.Any] = {}
        for param, arg in zip(self.params, custom_id_params):
            converted[param.name] = await param.convert(
                arg,
                inter=inter,
                converted=list(converted.values()),
                skip_validation=bool(self.regex),
            )

        for param, field_id in zip(self.modal_params, self.field_ids):
            converted[param.name] = await param.convert(
                inter.text_values[field_id],
                inter=inter,
                converted=list(converted.values()),
            )

        return await super().__call__(inter, **converted)

    async def build_component(  # TODO: Update with new ModalValue functionality.
        self,
        title: str,
        components: t.Optional[t.List[disnake.ui.TextInput]] = None,  # TODO: Disnake 2.6 typing.
        timeout: float = 600,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> disnake.ui.Modal:
        """Build a :class:`disnake.ui.Modal` that matches this listener. Uses the positional
        parameters of the callback to construct the :class:`disnake.ui.TextInput`s of the Modal.

        By default, this will create a TextInput with name equal to the parameter name
        (underscores are replaced with spaces) and custom_id based on the custom_id parameters.
        All other parameters use the normal TextInput defaults. These values can be overwritten
        by setting the parameter default to a :func:`.ModalValue` or :func:`.ParagraphModalValue`,
        and call it with the parameters you wish to set on the TextInput.

        Parameters
        ----------
        title: :class:`str`
            The title of the Modal.
        timeout: :class:`float`
            The timeout of the Modal, in seconds.
        **kwargs: Any
            The keyword-only parameters of the listener to store on the Modal's custom_id.

        Returns:
        :class:`disnake.ui.Modal`
            The newly created Modal.
        """
        if components is None:

            components = []
            for param, custom_id in zip(self.modal_params, self.field_ids):

                if not isinstance(modal_value := param.param.default, params._ModalValue):
                    modal_value = params._ModalValue()

                if isinstance(modal_value := param.param.default, params._ModalValue):
                    placeholder = modal_value.placeholder
                    style = modal_value.style
                    label = modal_value.label or param.name.replace("_", " ")
                    value = modal_value.value
                    required = modal_value.required
                    min_length = modal_value.min_length
                    max_length = modal_value.max_length
                else:
                    placeholder = None
                    style = disnake.TextInputStyle.short
                    label = param.name.replace("_", " ")
                    value = param.default if param.optional else None
                    required = True
                    min_length = None
                    max_length = None

                components.append(
                    disnake.ui.TextInput(
                        label=label,
                        custom_id=custom_id,
                        style=style,
                        placeholder=placeholder,
                        value=value,
                        required=required,
                        min_length=min_length,
                        max_length=max_length,
                    )
                )

        return disnake.ui.Modal(
            title=title,
            components=components,
            custom_id=await self.build_custom_id(*args, **kwargs),
            timeout=timeout,
        )


def modal_listener(
    *,
    name: t.Optional[str] = None,
    regex: t.Union[str, t.Pattern[str], None] = None,
    sep: str = ":",
    bot: t.Optional[commands.Bot] = None,
) -> t.Callable[[ModalListenerCallback[ParentT, P, T]], ModalListener[P, T]]:
    """Create a new :class:`ModalListener` from a decorated function. The ModalListener will take
    care of regex-matching and persistent data stored in the custom_id of the :class:`disnake.ui.Modal`.

    - The first parameter of the function (disregarding `self` inside a cog) is the
    :class:`disnake.ModalInteraction`.
    - Next, up to five parameters can be used for the Modal's :class:`disnake.ui.TextInput` fields.
    By default, these will be treated as TextInputs with style :class:`disnake.TextInputStyle.small`,
    To set placeholder text, set the parameter default to one of :func:`.ModalValue` or
    :func:`.ParagraphModalValue`, and call it with the placeholder you wish to set. Finally, the user
    input is converted to the type annotation of the parameter.
    - After the modal values themselves, a ``*,`` should be added to separate the modal values and
    custom_id values. Custom-id values will always need to be keyword-only.
    - Any keyword-only parameters are stored in and resolved from the custom_id. Note that only the
    Modal's custom_id is used for parsing. The 5 TextInput custom_ids are not used for this purpose.
    Use an Ellipsis (``...``) or `components.FAKE_DEFAULT` as a default for these parameters if you
    want them to be required.

    One can easily create a matching modal by calling :meth:`ModalListener.build_modal`, which will
    take the data set on the :class:`.ModalValue`s into account to create fitting names, placeholders,
    and styles for each TextInput.

    Example
    -------

    ```py
    @components.modal_listener()
    async def my_listener(
        inter: disnake.ModalInteraction,
        short_int: int = components.ModalValue("Please enter an integer."),
        long_str: str = components.ModalValue("Please enter some text."),
        *,
        custom_id_param: int = ...
    ):
        ...
    ```

    Parameters
    ----------
    name: Optional[:class:`str`]
        A custom name to use as the base for custom ids. If no name is provided, the name of the
        wrapped callback function will be used instead.
    regex: Union[:class:`str`, :class:`re.Pattern`, None]
        Used to set custom regex for the listener to use, instead of the default automatic parsing.
        Defaults to None, which makes the :class:`ModalListener` use the default automatic parsing.
    sep: :class:`str`
        The separator to use between `custom_id` parts. Defaults to ":". This is generally fine,
        however, if this character is meant to appear elsewhere in the `custom_id`, this should
        be changed to avoid conflicts.
    bot: :class:`commands.Bot`
        The bot to attach the listener to. This is only used as a shorthand to register the
        listener if it is defined outside of a cog. Alternatively, the usual `bot.listen` decorator
        or `bot.add_listener` method will work fine, too; provided the correct name is set.

    Returns
    -------
    :class:`ModalListener`
        The newly created :class:`ModalListener`.
    """

    def wrapper(
        func: ModalListenerCallback[ParentT, P, T],
    ) -> ModalListener[P, T]:
        listener = ModalListener[P, T](
            func,
            name=func.__name__ if name is None else name,
            regex=regex,
            sep=sep,
        )

        if bot is not None:
            bot.add_listener(listener, types_.ListenerType.MODAL)

        return listener

    return wrapper


@t.overload
def match_component(
    component: t.Union[disnake.Button, disnake.ui.Button[t.Any]],
    /,
    *,
    bot: t.Optional[commands.Bot] = None,
) -> t.Callable[[ButtonListenerCallback[ParentT, P, T]], ButtonListener[P, T]]:
    ...


@t.overload
def match_component(
    *,
    component_type: t.Literal[disnake.ComponentType.button],
    style: disnake.ButtonStyle = ...,
    custom_id: str = ...,
    disabled: bool = ...,
    label: str = ...,
    emoji: t.Union[disnake.PartialEmoji, disnake.Emoji, str] = ...,
    bot: t.Optional[commands.Bot] = None,
) -> t.Callable[[ButtonListenerCallback[ParentT, P, T]], ButtonListener[P, T]]:
    ...


@t.overload
def match_component(
    component: t.Union[disnake.SelectMenu, disnake.ui.Select[t.Any]],
    /,
    *,
    bot: t.Optional[commands.Bot] = None,
) -> t.Callable[[SelectListenerCallback[ParentT, P, T]], SelectListener[P, T]]:
    ...


@t.overload
def match_component(
    *,
    component_type: t.Literal[disnake.ComponentType.select],
    custom_id: str = ...,
    placeholder: str = ...,
    min_values: int = ...,
    max_values: int = ...,
    disabled: bool = ...,
    options: t.List[disnake.SelectOption] = ...,
    label: str = ...,
    bot: t.Optional[commands.Bot] = None,
) -> t.Callable[[SelectListenerCallback[ParentT, P, T]], SelectListener[P, T]]:
    ...


def match_component(
    component: t.Optional[
        t.Union[
            disnake.Button,
            disnake.ui.Button[t.Any],
            disnake.SelectMenu,
            disnake.ui.Select[t.Any],
        ]
    ] = None,
    /,
    *,
    component_type: t.Optional[disnake.ComponentType] = None,
    bot: t.Optional[commands.Bot] = None,
    **kwargs: t.Any,
) -> t.Callable[[t.Callable[..., t.Any]], ComponentListener]:
    """Create a listener that listens for components that match the provided one.
    A component can be provided either as an actual component, or as keyword-arguments with the
    necessary information to build a component. Note that these are mutually exclusive.

    This will generate a fully qualified listener based on the parameters entered. From there, one
    can easily create matching components using the `~.build_component` methods.

    Parameters
    ----------
    component: Union[:class:`disnake.Button`, :class:`disnake.ui.Button`, :class:`disnake.SelectMenu`, :class:`disnake.ui.Select`]
        The component to match. As this passes a fully qualified component with all its
        parameters set, this will make the listener look for an *exact* match of the passed
        component.

        Note that passing components is mutually exclusive with passing any keyword arguments
        outside of `bot`.
    component_type: :class:`disnake.ComponentType`
        The type of component the listener is for. If using keyword args to provide a component to
        match, this parameter is required.

        Note that passing keyword arguments is mutually exclusive with passing a concrete component.
    **kwargs: Any
        Any other parameters that can be passed to the desired component type.
    bot: Optional[:class:`commands.Bot`]
        Useful when defining this listener in the main file. This can be used to automatically
        register the listener to the bot. This is automatically taken care of inside of cogs.

    Raises
    ------
    ValueError
        Either both or neither of `component` and `component_type` were passed. Please make sure
        to pass strictly one of these parameters. Furthermore, make sure to not combine a
        concrete component with further kwargs.
    TypeError
        The passed component is not of compatible type, or the passed component_type is not
        among `disnake.ComponentType.button` or `disnake.ComponentType.select`

    Returns
    -------
    Union[:class:`ButtonListener`, :class:`SelectListener`]
        A component listener with a component matching check registered. The listener will match
        the type of the provided component.
    """
    if component is not None and (component_type is not None or kwargs):
        raise ValueError(
            "Please provide exactly one of `component` or `component_type` and its kwargs."
        )

    if component is not None:
        if isinstance(component, (disnake.Button, disnake.ui.Button)):
            listener_class = ButtonListener
        elif isinstance(
            component, (disnake.SelectMenu, disnake.ui.Select)
        ):  # pyright: ignore  # Valid redundancy imo.
            listener_class = SelectListener
        else:
            raise TypeError(
                "Expected `component` to be an instance of disnake.Button, disnake.ui.Button, "
                f"disnake.SelectMenu or disnake.ui.Select; got {type(component).__name__}."
            )

    elif component_type is not None:
        if component_type is disnake.ComponentType.button:
            listener_class = ButtonListener
        elif component_type is disnake.ComponentType.select:
            listener_class = SelectListener
        else:
            raise TypeError(
                "Expected `component_type` to be either disnake.ComponentType.button or "
                f"disnake.ComponentType.select; got {component_type.name}."
            )

    else:
        raise ValueError(
            "Please provide exactly one of `component` or `component_type` and its kwargs."
        )

    if component_type:
        kwargs["type"] = component_type

    def wrapper(callback: t.Callable[..., t.Any]) -> ComponentListener:
        if component is not None:
            reference = types_.AbstractComponent.from_component(component)
            name = component.custom_id
        else:
            reference = types_.AbstractComponent(**kwargs)
            name = kwargs.get("custom_id")

        listener = listener_class(callback, name=name, reference=reference)
        listener.add_check(utils.build_component_matching_check(reference))

        if bot:
            for listener_type in listener.__cog_listener_names__:
                bot.add_listener(listener, listener_type)

        return listener

    return wrapper
