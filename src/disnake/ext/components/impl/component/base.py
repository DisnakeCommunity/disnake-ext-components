"""Implementation of component base classes.

To easily integrate with disnake-ext-components, it is recommended to inherit
from any of these base classes. In any case, it is very much recommended to at
least use the `ComponentMeta` metaclass. Without this, a lot of internal
functionality will have to be manually re-implemented.
"""

from __future__ import annotations

import sys
import typing

import attr
import disnake
import typing_extensions
from disnake.ext.components import fields as fields
from disnake.ext.components.api import component as component_api
from disnake.ext.components.api import factory as factory_api
from disnake.ext.components.impl import custom_id as custom_id_impl
from disnake.ext.components.impl import factory as factory_impl

__all__: typing.Sequence[str] = ("ComponentBase",)


_T = typing.TypeVar("_T")

MaybeCoroutine = typing.Union[_T, typing.Coroutine[None, None, _T]]


_CountingAttr: type[typing.Any] = type(attr.field())
_AnyAttr: typing_extensions.TypeAlias = "attr.Attribute[typing.Any]"


def _extract_custom_id(interaction: disnake.Interaction) -> str:
    if isinstance(interaction, disnake.ModalInteraction):
        return interaction.custom_id

    elif isinstance(interaction, disnake.MessageInteraction):
        return typing.cast(str, interaction.component.custom_id)  # Guaranteed to exist.

    msg = "The provided interaction object does not have a custom id."
    raise TypeError(msg)


def _is_attrs_pass(namespace: dict[str, typing.Any]) -> bool:
    """Check if attrs has already influenced the class' namespace.

    Note that we check the namespace instead of using `attr.has`, because
    `attr.has` would always return `True` for a class inheriting an attrs class,
    and we specifically need to distinguish between the two passes inside
    `ComponentMeta.__new__`.
    """
    return namespace.get("__attrs_attrs__") is not None


def _is_protocol(cls: type[typing.Any]) -> bool:
    return getattr(cls, "_is_protocol", False)


def _finalise_custom_id(component: type[ComponentBase]) -> None:
    """Turn a string, auto id, or custom id into a fully-fledged custom id."""
    custom_id = component.custom_id

    if isinstance(custom_id, custom_id_impl.AutoID):
        # Make concrete custom id from provided auto-id...
        component.custom_id = custom_id_impl.CustomID.from_auto_id(component, custom_id)

    elif isinstance(custom_id, custom_id_impl.CustomID):
        # User-created custom id; ensure validity...
        custom_id.validate(component)

    elif isinstance(custom_id, str):  # pyright: ignore[reportUnnecessaryIsInstance]
        # Assume static custom id-- only a name without fields.
        # TODO: is this a good/"valuable" assumption?
        component.custom_id = custom_id_impl.CustomID(name=component.__name__)

    else:
        msg = (
            "A component's custom id must be of type 'str' or any derivative"
            f" thereof, got {type(custom_id).__name__!r}."
        )
        raise TypeError(msg)


def _apply_overrides(
    cls: type[ComponentBase],
    namespace: dict[str, typing.Any],
) -> None:
    """Turn malformed overrides into valid attrs fields."""
    if not attr.has(cls):  # Nothing to override.
        return

    # We only check pre-defined internal fields, such as label.
    for field in fields.get_fields(
        cls,
        kind=fields.FieldType.INTERNAL | fields.FieldType.MODAL,
    ):
        name = field.name
        if name not in namespace:
            continue

        new = namespace[name]

        # Ensure the new field isn't just magically an init-field now.
        if isinstance(new, _CountingAttr):
            # Emulate turning this into an Attribute so that the following checks work.
            # This may be slightly slow but it's only run once during class creation,
            # so it should be fine.
            new = typing.cast(
                "attr.Attribute[typing.Any]",
                attr.Attribute.from_counting_attr(name, new),  # pyright: ignore
            )
            new_field_type = fields.get_field_type(new)
            old_field_type = fields.get_field_type(field)

            # Ensure the field type remains unchanged.
            if new_field_type is not old_field_type:
                new_type_name = (new_field_type.name or "unknown").lower()
                old_type_name = (old_field_type.name or "unknown").lower()

                msg = (
                    f"Field '{cls.__name__}.{name}' is defined as a(n) {old_type_name} "
                    f"field, but was redefined as a(n) {new_type_name} field."
                )
                raise TypeError(msg)

            # Carry over the default value instead of the entire attribute.
            new = new.default

        new_field = attr.field(
            default=new,  # Update the default.
            init=field.init,
            metadata=field.metadata,
            on_setattr=field.on_setattr,
        )

        # Update the field information.
        setattr(cls, name, new_field)

        # Reapply the annotation, otherwise attrs breaks.
        cls.__annotations__.setdefault(name, field.type)


def _build_field_transformer_with_parsers(
    factory_builder: factory_impl.ComponentFactoryBuilder,
) -> typing.Callable[[type, list[_AnyAttr]], list[_AnyAttr]]:
    # Provide a ComponentFactoryBuilder to use as builder for the class, then
    # pass the resulting callback to the `field_transformer`. Finally, build
    # the full factory object after attrs is done creating the class.
    # We have a separate field transformer for protocols, as there's no reason
    # to build parsers for those classes, as they aren't instantiable anyways.

    def _field_transformer(cls: type, attributes: list[_AnyAttr]) -> list[_AnyAttr]:
        # Ensure all fields have valid metadata, fill missing parser types, and
        # build a ComponentFactory given all the attributes' parsers.

        # NOTE: Metadata is a mapping proxy, which means we can't directly
        #       mutate it. For this reason, we use evolve to copy and modify it.

        cls = typing.cast("type[ComponentBase]", cls)

        new_attributes: list[attr.Attribute[typing.Any]] = []

        for attribute in attributes:

            # Check if the field already has a field type defined.
            if fields.FieldMetadata.FIELDTYPE in attribute.metadata:
                if fields.FieldMetadata.PARSER in attribute.metadata:
                    parser = fields.get_parser(attribute)
                    if parser:
                        # Parser field defined and provided
                        factory_builder.add_field(attribute)
                        new_attributes.append(attribute)
                        continue

                    # Parser field defined but None provided (default).
                    parser = factory_builder.add_field(attribute)
                    evolved = attribute.evolve(
                        metadata={
                            **attribute.metadata,
                            fields.FieldMetadata.PARSER: parser,
                        }
                    )
                    new_attributes.append(evolved)
                    continue

                # Parser field not found, therefore no parser necessary.
                new_attributes.append(attribute)
                continue

            # No field definition found whatsoever; it's probably a custom id field.
            parser = factory_builder.add_field(attribute)
            evolved = attribute.evolve(
                metadata={
                    **attribute.metadata,  # Copy existing metadata
                    fields.FieldMetadata.FIELDTYPE: fields.FieldType.CUSTOM_ID,
                    fields.FieldMetadata.PARSER: parser,
                },
            )
            new_attributes.append(evolved)

        return new_attributes

    return _field_transformer


def _field_transformer(_: type, attributes: list[_AnyAttr]) -> list[_AnyAttr]:
    new_attributes: list[_AnyAttr] = []
    for attribute in attributes:

        # Check if the field already has a field type defined.
        if fields.FieldMetadata.FIELDTYPE in attribute.metadata:
            new_attributes.append(attribute)
            continue

        # If not, create a new attribute with field type set to custom id.
        # NOTE: Metadata is a mapping proxy, which means we can't directly
        #       mutate it. For this reason, we use evolve to copy and modify it.
        evolved = attribute.evolve(
            metadata={
                **attribute.metadata,  # Copy existing metadata
                fields.FieldMetadata.FIELDTYPE: fields.FieldType.CUSTOM_ID,
                fields.FieldMetadata.PARSER: None,
            },
        )
        new_attributes.append(evolved)

    return new_attributes


@typing_extensions.dataclass_transform(
    kw_only_default=True, field_specifiers=(fields.field, fields.internal)
)
class ComponentMeta(typing._ProtocolMeta):  # pyright: ignore[reportPrivateUsage]
    """Metaclass for all disnake-ext-components component types.

    It is **highly** recommended to use this metaclass for any class that
    should interface with the componenents api exposed by
    disnake-ext-components.

    This metaclass handles :mod:`attr` class generation, custom id completion,
    interfacing with component managers, parser and factory generation, and
    automatic slotting.
    """

    custom_id: custom_id_impl.CustomID

    # HACK: Pyright doesn't like this but it does seem to work with typechecking
    #       down the line. I might change this later (e.g. define it on
    #       BaseComponent instead, but that comes with its own challenges).
    factory: factory_api.ComponentFactory[typing_extensions.Self]  # pyright: ignore
    _parent: typing.Optional[type[typing.Any]]
    __module_id__: int

    def __new__(  # noqa: D102
        mcls,  # pyright: ignore[reportSelfClsParameterName]
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, typing.Any],
    ) -> ComponentMeta:
        # NOTE: This is run twice for each new class; once for the actual class
        #       definition, and once more by attr.define(). We ensure we only
        #       run the full class creation logic once.

        # Set slots if attrs hasn't already done so.
        namespace.setdefault("__slots__", ())

        cls = typing.cast(
            "type[ComponentBase]",
            super().__new__(mcls, name, bases, namespace),
        )

        # If this is attrs' pass, return immediately after it has worked its magic.
        if _is_attrs_pass(namespace):
            return cls

        # A reference to the actual module object is needed to ensure the
        # component is still in scope. In case the referenced module is no
        # longer in sys.modules, the component should be considered inactive,
        # and it will (hopefully) soon be GC'ed.
        cls.__module_id__ = id(sys.modules[cls.__module__])

        # Before we pass the class off to attrs, check if any fields were
        # overwritten. If so, check them for validity and update them to proper
        # attrs fields. This adds support for redefining internal fields as
        # `label = "foo"` instead of `label = fields.internal("foo")`
        _apply_overrides(cls, namespace)

        if _is_protocol(cls):
            cls = attr.define(
                cls,
                slots=True,
                kw_only=True,
                field_transformer=_field_transformer,
            )

            cls.factory = factory_impl.NoopFactory.from_component(cls)
            return cls

        builder = factory_impl.ComponentFactoryBuilder()
        cls = attr.define(
            cls,
            slots=True,
            kw_only=True,
            field_transformer=_build_field_transformer_with_parsers(builder),
        )

        cls.factory = builder.build(cls)  # pyright: ignore

        # Subscribe the new component to its manager if it inherited one.
        if cls.manager:
            cls.manager.subscribe(cls)

        _finalise_custom_id(cls)
        return cls

    # NOTE: This is relevant because classes are removed by gc instead of
    #       reference-counting. This means that, even though a module has been
    #       unloaded or a class has been `del`'d, it will still stick around
    #       until gc picks it up. Since we do not want to activate components
    #       that have gone out-of-scope in this sense, we need to explicitly
    #       account for this.
    @property
    def is_active(self) -> bool:
        """Determine whether this component is currently in an active module."""
        return (
            self.__module__ in sys.modules
            and self.__module_id__ == id(sys.modules[self.__module__])
        )  # fmt: skip


@typing.runtime_checkable
class ComponentBase(
    component_api.RichComponent, typing.Protocol, metaclass=ComponentMeta
):
    """Overarching base class for any kind of component."""

    _parent: typing.ClassVar[typing.Optional[type[typing.Any]]] = None
    manager: typing.ClassVar[typing.Optional[component_api.ComponentManager]] = None

    @classmethod
    def set_manager(  # noqa: D102
        cls, manager: typing.Optional[component_api.ComponentManager], /
    ) -> None:
        # <<docstring inherited from component_api.RichComponent>>

        if cls.manager is manager:
            return

        if cls.manager:
            cls.manager.unsubscribe(cls, recursive=False)

        cls.manager = manager

    @classmethod
    def should_invoke_for(  # noqa: D102
        cls, interaction: disnake.Interaction, /
    ) -> bool:
        # <<Docstring inherited from component_api.RichComponent>>

        custom_id = typing.cast(custom_id_impl.CustomID, cls.custom_id)
        return custom_id.check_name(_extract_custom_id(interaction))

    async def dumps(self) -> str:  # noqa: D102
        # <<Docstring inherited from component_api.RichComponent>>

        factory = type(self).factory
        return await factory.dumps(self)

    async def as_ui_component(self) -> disnake.ui.WrappedComponent:  # noqa: D102
        # <<Docstring inherited from component_api.RichComponent>>
        ...
