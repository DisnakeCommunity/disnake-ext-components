"""A simple example on the use of buttons with disnake-ext-components."""

import os

import disnake
from disnake.ext import commands, components

bot = commands.InteractionBot()

manager = components.get_manager()
manager.add_to_bot(bot)


@manager.register
class MyButton(components.RichButton):
    label: str = "0"

    count: int

    async def callback(self, interaction: components.MessageInteraction) -> None:
        self.count += 1
        self.label = str(self.count)

        await interaction.response.edit_message(components=self)


@bot.slash_command()  # pyright: ignore  # still some unknowns in disnake
async def test_button(inter: disnake.CommandInteraction) -> None:
    wrapped = components.wrap_interaction(inter)
    component = MyButton(count=0)

    await wrapped.response.send_message(components=component)


bot.run(os.getenv("EXAMPLE_TOKEN"))
