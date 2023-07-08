"""An example showcasing how attrs utilities can be used with ext-components."""

import os

import disnake
from disnake.ext import commands, components

# Say we wish to create a component, but we do not know the number of options
# beforehand, and we would like the user to be able to select all of them. It
# can be cumbersome to manually keep updating the `max_values` parameter of the
# select. Luckily, with the knowledge that ext-components is built upon the
# `attrs` lib, a few options become available to us.
# For this example, we will be making use of attrs classes' __attrs_post_init__
# method, which is called immediately after attrs finishes its normal
# initialisation logic. If you're familiar with dataclasses, this is essentially
# the same as a dataclass' __post_init__ method.

# First and foremost, we create a bot as per usual. Since we don't need any
# prefix command capabilities, we opt for an InteractionBot.
bot = commands.InteractionBot()

# Next, we make a component manager and register it to the bot.
manager = components.get_manager()
manager.add_to_bot(bot)


@manager.register
class CustomisableSelect(components.RichStringSelect):
    # Now, we ensure that max_values adapts to the passed number of options.
    # Since rich components use attrs under the hood, this can easily be
    # achieved through the __attrs_post_init__ method.
    def __attrs_post_init__(self) -> None:
        self.max_values = len(self.options)

    async def callback(self, interaction: components.MessageInteraction) -> None:
        selection = (
            "\n".join(f"- {value}" for value in interaction.values)
            if interaction.values
            else "nothing :("
        )

        await interaction.response.send_message(
            f"You selected:\n{selection}", ephemeral=True
        )


@bot.slash_command()  # pyright: ignore
async def make_select(interaction: disnake.CommandInteraction, options: str) -> None:
    """Make your own select menu.

    Parameters
    ----------
    options:
        A comma-separated string with all options. Max 25.
    """
    # If the string is empty or whitespace, the user did not provide options.
    if not options.strip():
        await interaction.response.send_message("You must specify at least one option!")
        return

    # Next, we make the options by splitting over commas.
    actual_options = [
        disnake.SelectOption(label=option.strip())
        for option in options.split(",")
    ]  # fmt: skip

    # Before creating the component, validate that there's max 25 options.
    if len(actual_options) > 25:
        await interaction.response.send_message("You must specify at most 25 options!")
        return

    # If everything went correctly, we send the component.
    wrapped = components.wrap_interaction(interaction)
    await wrapped.response.send_message(
        components=CustomisableSelect(options=actual_options),
    )


# Lastly, we run the bot.
bot.run(os.getenv("EXAMPLE_TOKEN"))
