# NOTE: This example does, by no means, provide the safest or most efficient means of creating a
#       simple game like this. For this specific case, for example, the converters aren't needed,
#       and just comparing strings would be easier. However, for sake of illustration, custom
#       converters are used here to show how they work.

import re
import typing as t

import disnake
from disnake.ext import commands, components

# Custom converter regex! The input must match this to run the converter function on it.
password_regex = re.compile(r"\d{1,4}")
"""Matches a string of one to four numbers."""


# Custom converter functions! One to go from str to whatever we want...
def to_password(arg: str) -> t.List[int]:
    """Converts a string "1234" to a list of ints [1, 2, 3, 4]."""
    return [int(char) for char in arg]


# ... and one to go back.
def from_password(arg: t.List[int]) -> str:
    """Converts a list of ints [1, 2, 3, 4] back to a str "1234" """
    return "".join(str(num) for num in arg)


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
        selected: t.List[int] = components.SelectValue("Choose carefully..."),
        # ^ We designate `selected` as the parameter where the Select's values go by annotating it
        #   as `components.SelectValue`. This must come before any other arguments.
        *,
        secret_password: components.Converted[
            password_regex,  # First the custom regex, if this is not matched, the converter is not run.
            to_password,  # The converter function to go from the input string to the password we want.
            from_password,  # The converter to go from password back to str. Used by `build_custom_id.`
        ] = ...,
    ):
        """The listener for the selects. Only responds to `custom_id`s that match the regex:
        ```py
        r"safe_listener:(\\d+{1,4})"
        ```
        Note how this contains the converter regex contained in `password_regex`.

        Furthermore, parameter `selected` is the parameter in which the user-selected values will be
        stored. Since it is annotated as a `typing.List[int]`, it will convert all the values to
        `int`s, and they will be stored in a list. Changing that to e.g. `typing.Set[str]` would
        instead convert the values to `str`s and store them in a set.
        """
        if selected == secret_password:
            await inter.response.send_message(f"{inter.author.mention} cracked the safe!")
        else:
            await inter.response.send_message(f"{inter.author.mention} failed to crack the safe!")

    @commands.slash_command()
    async def start_heist(
        self, inter: disnake.CommandInteraction, password: commands.Range[0, 9876]
    ):
        """Command to start the safe cracking minigame.

        Parameters
        ----------
        password: A number of up to 4 digits. Duplicate numbers will be dropped.
        """

        # First, we drop duplicate numbers as you cannot select the same value twice.
        password_digits = to_password(str(password))
        validated_password = sorted(set(password_digits), key=password_digits.index)

        await inter.response.send_message(
            f"After dropping duplicate numbers, the password was set to {validated_password}.",
            ephemeral=True,
        )

        select: disnake.ui.Select[t.Any] = disnake.ui.Select(
            placeholder="Choose carefully...",
            custom_id=await self.safe_listener.build_custom_id(secret_password=validated_password),
            # ^ use the list of ints to create the custom_id, e.g. "safe_listener:1234".
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
