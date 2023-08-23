"""A simple example on the use of selects with disnake-ext-components.

For this example, we implement a select menu with double functionality.
Firstly, the select allows you to select one of three slots. After selecting a
slot, the select is modified to instead allow you to select a colour. The
selected slot and colour are then combined to colour the corresponding square.
"""

from __future__ import annotations

import os
import typing

import disnake
from disnake.ext import commands, components

bot = commands.InteractionBot()

manager = components.get_manager()
manager.add_to_bot(bot)


LEFT = "\N{BLACK LEFT-POINTING TRIANGLE}\N{VARIATION SELECTOR-16}"
MIDDLE = "\N{BLACK CIRCLE FOR RECORD}\N{VARIATION SELECTOR-16}"
RIGHT = "\N{BLACK RIGHT-POINTING TRIANGLE}\N{VARIATION SELECTOR-16}"

SLOT_OPTIONS = [
    disnake.SelectOption(label="Left", value="left", emoji=LEFT),
    disnake.SelectOption(label="Middle", value="middle", emoji=MIDDLE),
    disnake.SelectOption(label="Right", value="right", emoji=RIGHT),
    disnake.SelectOption(label="Finalise", emoji="\N{WHITE HEAVY CHECK MARK}"),
]


BLACK_SQUARE = "\N{BLACK LARGE SQUARE}"
BLUE_SQUARE = "\N{LARGE BLUE SQUARE}"
BROWN_SQUARE = "\N{LARGE BROWN SQUARE}"
GREEN_SQUARE = "\N{LARGE GREEN SQUARE}"
PURPLE_SQUARE = "\N{LARGE PURPLE SQUARE}"
RED_SQUARE = "\N{LARGE RED SQUARE}"
WHITE_SQUARE = "\N{WHITE LARGE SQUARE}"
YELLOW_SQUARE = "\N{LARGE YELLOW SQUARE}"

COLOUR_OPTIONS = [
    disnake.SelectOption(label="Black", value=BLACK_SQUARE, emoji=BLACK_SQUARE),
    disnake.SelectOption(label="Blue", value=BLUE_SQUARE, emoji=BLUE_SQUARE),
    disnake.SelectOption(label="Brown", value=BROWN_SQUARE, emoji=BROWN_SQUARE),
    disnake.SelectOption(label="Green", value=GREEN_SQUARE, emoji=GREEN_SQUARE),
    disnake.SelectOption(label="Purple", value=PURPLE_SQUARE, emoji=PURPLE_SQUARE),
    disnake.SelectOption(label="Red", value=RED_SQUARE, emoji=RED_SQUARE),
    disnake.SelectOption(label="White", value=WHITE_SQUARE, emoji=WHITE_SQUARE),
    disnake.SelectOption(label="Yellow", value=YELLOW_SQUARE, emoji=YELLOW_SQUARE),
]


@manager.register
class MySelect(components.RichStringSelect):
    placeholder: str = "Please select a square."
    options: typing.List[disnake.SelectOption] = SLOT_OPTIONS

    slot: str = "0"
    state: str = "slot"
    colour_left: str = BLACK_SQUARE
    colour_middle: str = BLACK_SQUARE
    colour_right: str = BLACK_SQUARE

    async def callback(self, inter: components.MessageInteraction) -> None:
        assert inter.values is not None
        selected = inter.values[0]

        if self.state == "slot":
            self.handle_slots(selected)

        else:
            self.handle_colours(selected)

        msg = self.render_colours()
        await inter.response.edit_message(msg, components=self)

    def handle_slots(self, selected: str) -> None:
        if selected == "Finalise":
            self.disabled = True
            self.placeholder = "Woo!"
            return

        self.options = COLOUR_OPTIONS
        self.placeholder = f"Please select a colour for the {selected} square."

        self.slot = selected
        self.state = "colour"

    def handle_colours(self, selected: str) -> None:
        self.options = SLOT_OPTIONS

        setattr(self, f"colour_{self.slot}", selected)
        self.state = "slot"

    def render_colours(self) -> str:
        return f"{self.colour_left}{self.colour_middle}{self.colour_right}\n"


@bot.slash_command()  # pyright: ignore  # still some unknowns in disnake
async def test_select(inter: disnake.CommandInteraction) -> None:
    wrapped = components.wrap_interaction(inter)

    component = MySelect()
    await wrapped.response.send_message(
        component.render_colours(), components=component
    )


bot.run(os.getenv("EXAMPLE_TOKEN"))
