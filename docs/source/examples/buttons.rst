Buttons
=======
A simple example on the use of buttons with disnake-ext-components.


First and foremost, we create a bot as per usual. Since we don't need any
prefix command capabilities, we opt for an :class:`disnake.ext.commands.InteractionBot`.

.. literalinclude:: ../../../examples/button.py
    :caption: examples/button.py - create a Bot object
    :lines: 3-7, 10

Next, we make a component manager and register *all* components (current and future) to this manager.

.. literalinclude:: ../../../examples/button.py
    :caption: examples/button.py - create a component manager and register components
    :lines: 13, 16

Then we make a simple component.

.. literalinclude:: ../../../examples/button.py
    :caption: examples/button.py - create a component
    :lines: 20-29

Finally, we make a command that sends the component.

.. literalinclude:: ../../../examples/button.py
    :caption: examples/button.py - create a command and send the component
    :lines: 33-47
    :emphasize-lines: 4, 7-11

Source code
-----------

.. literalinclude:: ../../../examples/button.py
    :caption: examples/button.py
    :start-at: import os
    :lines: 1-5, 8, 11, 14-16, 18-29, 31-43, 45
    :emphasize-lines: 7-8, 26, 29-33
    :linenos: