disnake-ext-components
======================

An extension for disnake aimed at making component interactions with listeners somewhat less cumbersome.

Key Features
------------
- Smoothly integrates with [disnake](https://github.com/DisnakeDev/disnake),
- Integrate regex checks into your listeners to comprehensively filter components by `custom_id`,

Installing
----------

**Python 3.8 or higher is required**

To install the extension, run the following command in your command prompt:

``` sh
# Linux/macOS
python3 -m pip install -U disnake

# Windows
py -3 -m pip install -U disnake
```

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

    @components.button_with_id(regex=r"register:(?P<uid>\d+)")
    async def register_user(self, inter: disnake.MessageInteraction, uid: str):
        # first ensure the user who clicked the button is the user who created it
        if inter.author.uid != int(uid):
            return
        await inter.response.send_message(f"{inter.author.mention} successfully registered!")


def setup(bot: commands.Bot):
    bot.add_cog(MyCog(bot))
```
A listener defined like this will only fire if the `custom_id` of the button pressed matches the regex defined in the decorator. Anything matched by the [named capture group](https://docs.python.org/3/howto/regex.html#non-capturing-and-named-groups) "uid" is passed into the "uid" parameter of the method `register_user`. In this way, any number of named capture groups and function parameters can be added, as long as the `custom_id` character length is not exceeded. At the time of writing, this amounts to 100 characters.

In case a full regex check is not needed, a simple check by id can also be done:
```py
    @components.button_with_id(id="example_button")
    async def register_user(self, inter: disnake.MessageInteraction):
        ...
```

To-Do
-----

### `commands.Bot.listen()`-equivalent

Currently, only listeners inside `commands.Cog`s are supported. I plan to make the existing decorators work like `commands.Bot.listen()` soon, too, so that they can be used as follows:
```py
import disnake
from disnake.ext import commands, components


bot = commands.Bot()


@components.button_with_id(id="example")
async def my_listener(inter: disnake.MessageInteraction):
    """This will fire only for buttons with custom_id "example" """
    ...


bot.run("token")
```

### Component constructor
I aim to make a component constructor that makes it easier to create these buttons with state inside the `custom_id`. Ideally, I'd like to then also make a `listener_from_component` or similar decorator that will automatically make the necessary regex checks for the user. I'm still thinking how to best implement this, so an actual implementation can be quite a ways off.

### Inferring types from typehints and casting
Coming back to a previous example, we could match a user ID from a `custom_id` and cast that to a `disnake.Member` object:
```py
@components.button_with_id(regex=r"register:(?P<member>\d+)")
async def register_user(self, inter: disnake.MessageInteraction, member: disnake.Member):
    # the uid matched by the regex gets casted to a disnake.Member because it is typehinted as such.
    ...
```
Since I can use existing disnake implementation for this, this will probably actually be implemented soon.

Contributing
------------
Any contributions are welcome, feel free to open an issue or pull request if you'd like to see something added. Contribution guidelines will come soon, and hopefully I'll figure out how to do some simple CI to automatic black/pyright/mypy up and running.