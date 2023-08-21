Button
======
A simple example on the use of buttons with disnake-ext-components.


First and foremost, we create a bot as per usual. Since we don't need any
prefix command capabilities, we opt for an :class:`disnake.ext.commands.InteractionBot`.

.. literalinclude:: ../../../examples/button.py
    :caption: examples/button.py - create a Bot object
    :lines: 3-7, 10

Next, we make a component manager and register it to the bot.

.. literalinclude:: ../../../examples/button.py
    :caption: examples/button.py - create a component manager and registering it
    :lines: 13, 14

Then we make a simple component.

.. literalinclude:: ../../../examples/button.py
    :caption: examples/button.py - create a component
    :lines: 18-28
    :emphasize-lines: 1

Finally, we make a command that sends the component.

.. literalinclude:: ../../../examples/button.py
    :caption: examples/button.py - create a command and send the component
    :lines: 32-38
    :emphasize-lines: 4, 7

If we had not wrapped the interaction, we would have needed to do ``await inter.send(components=await component.as_ui_component())`` instead.

Source code
-----------

.. literalinclude:: ../../../examples/button.py
    :caption: examples/button.py
    :start-at: import os
    :lines: 1-5, 8, 11-14, 16-28, 30-31, 33-37, 41-42, 44
    :emphasize-lines: 7-8, 11, 26, 29
    :linenos: