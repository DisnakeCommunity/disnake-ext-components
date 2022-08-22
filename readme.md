disnake-ext-components
======================

An extension for disnake aimed at making component interactions with listeners somewhat less cumbersome.  
Requires disnake version 2.5.0 or above.

Key Features
------------
- Smoothly integrates with [disnake](https://github.com/DisnakeDev/disnake),
- Uses an intuitive disnake slash-command-like syntax to create stateful persistent components,
- `custom_id` matching, conversion, and creation are automated for you,
- Allows you to implement custom RegEx for your listeners if you need more customized behavior.

Installing
----------

**Python 3.8 or higher is required**

To install the extension, run the following command in your command prompt/shell:

``` sh
# Linux/macOS
python3 -m pip install -U git+https://github.com/DisnakeCommunity/disnake-ext-components

# Windows
py -3 -m pip install -U git+https://github.com/DisnakeCommunity/disnake-ext-components
```
I will hopefully get it on PyPI soon-ish, but for now you'll have to install it from GitHub (which requires git to be installed on your PC).  
It will be installed to your existing [disnake](https://github.com/DisnakeDev/disnake) installation as an extension. From there, it can be imported as:

```py
from disnake.ext import components
```

Examples
-------

### Inside a cog
```py
import disnake
from disnake.ext import commands, components


class MyCog(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @components.button_listener()
    async def secret_listener(self, inter: disnake.MessageInteraction, *, secret: str, author: disnake.Member):
        await inter.response.send_message(f"You found {author.mention}'s secret message: '{secret}'!")

    @commands.slash_command()
    async def make_secret(self, inter: disnake.CommandInteraction, secret: str):
        """Store a secret message in a button!"""
        await inter.response.send_message(
            "Press this button to reveal the secret!",
            components=disnake.ui.Button(
                label="Reveal secret...",
                custom_id=self.secret_listener.build_custom_id(secret=secret, author=inter.author),
                # e.g. "secret_listener:extreme secrecy right here:872576125384147005"
            )
        )


def setup(bot: commands.Bot):
    bot.add_cog(MyCog(bot))
```
> This example is complete and should run as-is when loaded into a bot.

### Outside a cog
```py
import disnake
from disnake.ext import commands, components


bot = commands.Bot(commands.when_mentioned)

@components.button_listener(bot=bot)
async def secret_listener(inter: disnake.MessageInteraction, *, secret: str, author: disnake.Member):
    await inter.response.send_message(f"You found {author.mention}'s secret message: '{secret}'!")

@commands.slash_command()
async def make_secret(inter: disnake.CommandInteraction, secret: str):
    """Store a secret message in a button!"""
    await inter.response.send_message(
        "Press this button to reveal the secret!",
        components=disnake.ui.Button(
            label="Reveal secret...",
            custom_id=secret_listener.build_custom_id(secret=secret, author=inter.author),
        )
    )
```
> This example is complete and should run as-is.

For more examples, see [the examples folder](https://github.com/DisnakeCommunity/disnake-ext-components/tree/master/examples).

To-Do
-----
- PyPI release,
- Contribution guidelines,
- Support some sort of dependency injection.

Contributing
------------
Any contributions are welcome, feel free to open an issue or submit a pull request if you'd like to see something added. Contribution guidelines will come soon.
