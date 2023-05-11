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
import typing_extensions
from disnake.ext.components import fields as fields
from disnake.ext.components.api import component as component_api
from disnake.ext.components.api import parser as parser_api
from disnake.ext.components.impl import custom_id as custom_id_impl
from disnake.ext.components.impl import factory as factory_impl
from disnake.ext.components.impl import parser as parser_impl

if typing.TYPE_CHECKING:
    import disnake

__all__: typing.Sequence[str] = ("ComponentBase",)


_T = typing.TypeVar("_T")

MaybeCoroutine = typing.Union[_T, typing.Coroutine[None, None, _T]]
_AnyAttr: typing_extensions.TypeAlias = "attr.Attribute[typing.Any]"


def _is_attrs_pass(namespace: typing.Dict[str, typing.Any]) -> bool:
    """Check if attrs has already influenced the class' namespace.

    Note that we check the namespace instead of using `attr.has`, because
    `attr.has` would always return `True` for a class inheriting an attrs class,
    and we specifically need to distinguish between the two passes inside
    `ComponentMeta.__new__`.
    """
    return namespace.get("__attrs_attrs__") is not None


def _is_protocol(cls: typing.Type[typing.Any]) -> bool:
    return getattr(cls, "_is_protocol", False)


def _finalise_custom_id(component: typing.Type[ComponentBase]) -> None:
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


def _determine_parser(
    attribute: _AnyAttr,
    overwrite: typing.Optional[_AnyAttr],
    *,
    required: bool = True,
) -> typing.Optional[parser_api.Parser[typing.Any]]:
    parser = fields.get_parser(attribute)
    if parser:
        return parser

    if overwrite:
        parser = fields.get_parser(overwrite)
        if parser:
            return parser

    if required:
        parser_type = parser_impl.get_parser(attribute.type or str)
        return parser_type.default()

    return None


def _eval_type(cls: type, annotation: typing.Any) -> typing.Any:  # noqa: ANN401
    # Get the module globals in which the class was defined. This is the most
    # probable candidate in which to find the type annotations' definitions.
    #
    # For the most part, this should be safe. Conflicts where e.g. a component
    # inheriting from RichButton but not defining _AnyEmoji in their own module
    # are safe, because the type has already been passed through this function
    # when the RichButton class was initially created.
    cls_globals = sys.modules[cls.__module__].__dict__

    if isinstance(annotation, str):
        annotation = typing.ForwardRef(annotation, is_argument=False)

    # Evaluate the typehint with the provided globals.
    return typing._eval_type(annotation, cls_globals, None)  # pyright: ignore


def _assert_valid_overwrite(attribute: _AnyAttr, overwrite: _AnyAttr) -> None:
    if fields.FieldMetadata.FIELDTYPE not in overwrite.metadata:
        return

    # The field was defined using fields.field / fields.internal / etc.
    # Ensure the overwrite matches the original field type.

    attribute_type = fields.get_field_type(overwrite)
    overwrite_type = fields.get_field_type(attribute)

    if overwrite_type is not attribute_type:
        new = (attribute_type.name or "<unknown>").lower()
        old = (overwrite_type.name or "<unknown>").lower()
        msg = (
            f"Invalid field override. Field {overwrite.name} is defined as"
            f" a(n) {new} field, but was overwritten as a(n) {old} field."
        )
        raise TypeError(msg)


def _is_custom_id_field(field: _AnyAttr) -> bool:
    return (
        fields.get_field_type(field, fields.FieldType.CUSTOM_ID)
        is fields.FieldType.CUSTOM_ID
    )


def _field_transformer(
    cls: type, attributes: typing.List[_AnyAttr]
) -> typing.List[_AnyAttr]:
    is_concrete = not _is_protocol(cls)
    super_attributes: typing.Dict[str, _AnyAttr] = (
        {field.name: field for field in fields.get_fields(cls)} if attr.has(cls) else {}
    )

    finalised_attributes: typing.List[_AnyAttr] = []
    for attribute in attributes:
        # Fields only need a parser if
        # - The component is concrete,
        # - The field is a custom-id field.
        # In case of an overwrite, we check the field type of the super-field.
        super_attribute = super_attributes.get(attribute.name)
        needs_parser = is_concrete and _is_custom_id_field(super_attribute or attribute)

        # Ensure all forward-references are evaluated.
        evolved = attribute.evolve(type=_eval_type(cls, attribute.type))

        if super_attribute:
            # This field overwrites a pre-existing field. Merge metadata and
            # ensure the parser isn't overwritten if the new value is None.
            _assert_valid_overwrite(super_attribute, attribute)
            metadata = {**super_attribute.metadata, **evolved.metadata}

        else:
            # Not an overwrite, ensure the fieldtype is set to CUSTOM_ID if not
            # already provided.
            metadata = {
                fields.FieldMetadata.FIELDTYPE: fields.FieldType.CUSTOM_ID,
                **evolved.metadata,
            }

        # TODO: Make copy of parser instead of using the same instance
        metadata[fields.FieldMetadata.PARSER] = _determine_parser(
            evolved,
            super_attribute,
            required=needs_parser,
        )

        # Apply finalised metadata.
        finalised_attributes.append(evolved.evolve(metadata=metadata))

    return finalised_attributes


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
    factory: component_api.ComponentFactory[typing_extensions.Self]  # pyright: ignore
    _parent: typing.Optional[typing.Type[typing.Any]]
    __module_id__: int

    def __new__(  # noqa: D102
        mcls,  # pyright: ignore[reportSelfClsParameterName]
        name: str,
        bases: tuple[type, ...],
        namespace: typing.Dict[str, typing.Any],
    ) -> ComponentMeta:
        # NOTE: This is run twice for each new class; once for the actual class
        #       definition, and once more by attr.define(). We ensure we only
        #       run the full class creation logic once.

        # Set slots if attrs hasn't already done so.
        namespace.setdefault("__slots__", ())

        cls = typing.cast(
            "typing.Type[ComponentBase]",
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
        # _apply_overrides(cls, namespace)

        cls = attr.define(
            cls,
            slots=True,
            kw_only=True,
            field_transformer=_field_transformer,
        )

        if _is_protocol(cls):
            cls.factory = factory_impl.NoopFactory.from_component(cls)
            return cls

        cls.factory = factory_impl.ComponentFactory.from_component(cls)

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

    _parent: typing.ClassVar[typing.Optional[typing.Type[typing.Any]]] = None
    manager: typing.ClassVar[typing.Optional[component_api.ComponentManager]] = None
    factory = factory_impl.NoopFactory()

    async def as_ui_component(self) -> disnake.ui.WrappedComponent:  # noqa: D102
        # <<Docstring inherited from component_api.RichComponent>>
        ...
