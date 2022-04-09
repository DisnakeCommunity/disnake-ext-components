disnake-ext-components
======================


**NOTE!**
Proper functionality is currently reliant on a [bugfix](https://github.com/DisnakeDev/disnake/pull/444) that will be implemented in the upcoming version of disnake. If you wish to use this module, you'll have to install disnake from master (`pip install git+https://github.com/DisnakeDev/disnake.git`), or manually make the changes in your local installation. This will last until disnake is updated to version 2.5.0.
---

---
An extension for disnake aimed at making component interactions with listeners somewhat less cumbersome.

Key Features
------------
- Smoothly integrates with [disnake](https://github.com/DisnakeDev/disnake),
- Use an intuitive disnake slash-command-like syntax to create stateful persistent components,
- `custom_id` matching, conversion, and creation are automated for you,
- Allows you to implement custom regex for your listeners if you need more customized behavior.

Installing
----------

**Python 3.8 or higher is required**

To install the extension, run the following command in your command prompt:

``` sh
# Linux/macOS
python3 -m pip install -U git+https://github.com/Chromosomologist/disnake-ext-components

# Windows
py -3 -m pip install -U git+https://github.com/Chromosomologist/disnake-ext-components
```
I will hopefully get it on PyPI soon-ish, but for now you'll have to install from github (which requires git to be installed on your pc).  
It will be installed to your existing [disnake](https://github.com/DisnakeDev/disnake) installation as an extension. From there, it can be imported as:

```py
from disnake.ext import components
```

Example
-------

### Inside a cog
```py
import disnake
from disnake.ext import commands, components


class MyCog(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @components.component_listener()
    async def secret_listener(self, inter: disnake.MessageInteraction, secret: str, author: disnake.Member):
        await inter.response.send_message(f"You found {author.mention}'s secret message: '{secret}'!")

    @commands.slash_command()
    async def make_secret(self, inter: disnake.CommandInteraction, secret: str):
        """Store a secret message in a button!"""
        await ctx.send(
            "Press this button to reveal the secret!",
            components=disnake.ui.Button(
                label="Reveal secret...",
                custom_id=self.secret_listener.create_custom_id(secret=secret, author=inter.author.id),
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


bot = disnake.Bot("..")

@components.component_listener(bot=bot)
async def secret_listener(inter: disnake.MessageInteraction, secret: str, author: disnake.Member):
    await inter.response.send_message(f"You found {author.mention}'s secret message: '{secret}'!")

@commands.slash_command()
async def make_secret(inter: disnake.CommandInteraction, secret: str):
    """Store a secret message in a button!"""
    await ctx.send(
        "Press this button to reveal the secret!",
        components=disnake.ui.Button(
            label="Reveal secret...",
            custom_id=register_user.create_custom_id(secret=secret, author=inter.author.id),
        )
    )
```
> This example is complete and should run as-is.

For more examples, see [the examples folder](https://github.com/Chromosomologist/disnake-ext-components/tree/master/examples).

To-Do
-----
- CI,
- Contribution guidelines.
- Support passing objects to `ComponentListener.build_custom_id` instead of str/int/float/bool only,
- Wait for disnake 2.5.0 release and publish to PyPI,
- Support `commands.inject`/`commands.Injection`,

Contributing
------------
Any contributions are welcome, feel free to open an issue or pull request if you'd like to see something added. Contribution guidelines will come soon, and hopefully I'll figure out how to do some simple CI to automatic black/pyright/mypy up and running.
