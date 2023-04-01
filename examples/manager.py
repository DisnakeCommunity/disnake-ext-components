"""A simple example on the use of custom managers with disnake-ext-components.

Fair warning: component managers are fairly complex and leverage weak
references to their components in a lot of different places. For many things
to be able to unload and/or be garbage-collected appropriately, it is
imperative that there are no external references to components.
Making custom component managers is therefore very sensitive to introducing
a myriad of reference cycles and potentially even memory leaks, so discretion
is advised.

As far as safety goes, overwriting 'ComponentManager.callback_hook' as is done
in this example is fairly safe, provided you do not store the components
externally.
"""

import contextlib
import os
import time
import typing

import disnake
from disnake.ext import commands, components

# First and foremost, we create a bot as per usual. Since we don't need any
# prefix command capabilities, we opt for an InteractionBot.
bot = commands.InteractionBot()

# Next, we make a custom component manager.
class MyManager(components.ComponentManager):

    # For the sake of this example, we will make a custom manager that prints
    # the runtime of a component callback.

    @contextlib.contextmanager
    def callback_hook(
        self, component: components.api.RichComponent
    ) -> typing.Generator[None, None, None]:
        start_time = time.perf_counter()

        yield  # The component callback will be invoked here

        print(
            f"Component {type(component).__name__} finished running in"
            f" {(time.perf_counter() - start_time) * 1000:.3f} milliseconds."
        )

    # If you wish to stop a component from running, you can raise an exception
    # before the yield statement.


manager = MyManager(bot)

# Register *all* components (current and future) to this manager.
manager.basic_config()


# Then we make a simple component. For a more detailed explanation, see the
# 'button.py' example.
class MyButton(components.RichButton):
    label: str = "0"

    count: int

    async def callback(self, interaction: components.MessageInteraction) -> None:
        self.count += 1
        self.label = str(self.count)

        await interaction.response.edit_message(components=self)


# Finally, we make a command that sends the component.
@bot.slash_command()  # pyright: ignore  # still some unknowns in disnake
async def test_button(inter: disnake.CommandInteraction) -> None:
    wrapped = components.wrap_interaction(inter)
    component = MyButton(count=0)

    await wrapped.send(components=component)


# Lastly, we run the bot.
bot.run(os.getenv("EXAMPLE_TOKEN"))
