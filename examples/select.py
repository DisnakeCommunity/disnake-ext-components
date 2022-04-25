import re
import typing as t

import disnake
from disnake.ext import commands, components

# First, we make a custom converter:
# For that, we need a regex pattern to match the input...
password_pattern = re.compile(r"\[\d+(, \d+)*\]")  # Match "[n1, n2, ...]"...


# And then we need an actual converter function...
def password_converter(arg: str) -> t.List[int]:  # Parse a match^ to a set of ints.
    """Converts a string "[1, 2, 3, ...]" to an actual list of ints [1, 2, 3, 4]."""
    return [int(char) for char in arg if char.isdigit()]


class SelectCog(commands.Cog):
    """Cog that implements a simple safe cracking game. A user can create a select with options
    0 through 9 and an up to four digit passcode. Other users can then try and crack the passcode
    by selecting the correct options in the correct order. This is fully persistent, as the passcode
    is stored in the select's custom_id.

    Note that this is not secure, as a savvy user could find this out using devtools!
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @components.select_listener()
    async def safe_listener(
        self,
        inter: disnake.MessageInteraction,
        selected: components.SelectValue[t.List[int]],
        # ^ We designate `selected` as the parameter where the Select's values go by annotating it
        #   as `components.SelectValue`. This must come before any other arguments.
        secret_password: components.Converted[password_pattern, password_converter],
        # ^ Here, we use `components.Converted` to assign our custom converter to param
        #   `secret_password`. The first argument should be the regex pattern (use r".*" if
        #   validation is not needed); the second argument should be the converter function.
    ):
        """The listener for the selects. Only responds to `custom_id`s that match the regex:
        ```py
        r"safe_listener:(\\[\\d+(, \\d+)*\\])"
        ```
        Note how this contains the custom converter regex we defined at the top of this file.

        Furthermore, parameter `selected` is the parameter in which the user-selected values will be
        stored. Since it is annotated as a `typing.List[int]`, it will convert all the values to
        `int`s, and they will be stored in a list. Changing that to e.g. `typing.Set[str]` would
        instead convert the values to `str`s and store them in a set.
        """
        # NOTE: it would be easier here to just compare the strings, as that does not require converters.
        # However, we use converters here to demonstrate their functionality.
        if selected == secret_password:
            await inter.response.send_message(f"{inter.author.mention} cracked the safe!")
        else:
            await inter.response.send_message(f"{inter.author.mention} failed to crack the safe!")

    @commands.slash_command()
    async def start_heist(
        self, inter: disnake.CommandInteraction, password: commands.Range[0, 9876]
    ):
        """Command to start the safe cracking minigame."""
        # First, we drop duplicate numbers as you cannot select the same value twice.
        password_digits = [int(char) for char in str(password)]
        validated_password = sorted(set(password_digits), key=password_digits.index)

        await inter.response.send_message(
            f"After dropping duplicate numbers, the password was set to {validated_password}.",
            ephemeral=True,
        )

        select: disnake.ui.Select[t.Any] = disnake.ui.Select(
            placeholder="Choose carefully...",
            custom_id=self.safe_listener.build_custom_id(validated_password),
            # ^ use the list of ints to create the custom_id, e.g. "safe_listener:[1, 2, 3, 4]".
            min_values=1,
            max_values=9,
            options=[str(i) for i in range(10)],
        )

        await inter.followup.send(
            "Enter the correct passcode to crack the safe!",
            components=select,
        )


def setup(bot: commands.Bot):
    bot.add_cog(SelectCog(bot))
