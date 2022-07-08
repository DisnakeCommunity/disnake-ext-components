import datetime

import disnake_ext_components as components

# types_.ListenerType


def test_listenertype_const():

    LT = components.ListenerType

    assert LT.BUTTON == "on_button_click"
    assert LT.SELECT == LT.DROPDOWN == "on_dropdown"
    assert LT.MESSAGE_INTERACTION == LT.COMPONENT == "on_message_interaction"
    assert LT.MODAL == "on_modal_submit"


# types_.Converted


def test_converter():
    def to_datetime(arg: str) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(int(arg))

    def from_datetime(arg: datetime.datetime) -> str:
        return str(arg.timestamp())

    converter_annotation = components.Converted[
        components.patterns.STRICTINT,
        to_datetime,
        from_datetime,
    ]

    actual_converter = components.Converted(
        components.patterns.STRICTINT,
        to_datetime,
        from_datetime,
    )

    assert isinstance(converter_annotation, components.Converted)

    assert converter_annotation.regex == actual_converter.regex
    assert converter_annotation.converter_to == actual_converter.converter_to
    assert converter_annotation.converter_from == actual_converter.converter_from
