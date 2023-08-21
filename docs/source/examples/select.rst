Select
======
A simple example on the use of selects with disnake-ext-components.

For this example, we implement a select menu with double functionality.
Firstly, the select allows you to select one of three slots. After selecting a
slot, the select is modified to instead allow you to select a colour. The
selected slot and colour are then combined to colour the corresponding square.


First and foremost, we create a bot as per usual. Since we don't need any
prefix command capabilities, we opt for an :class:`disnake.ext.commands.InteractionBot`.

.. literalinclude:: ../../../examples/select.py
    :caption: examples/select.py - creating a Bot object
    :lines: 9-16, 19


Next, we make a component manager and register it to the bot.

.. literalinclude:: ../../../examples/select.py
    :caption: examples/select.py - creating a manager and registering it
    :lines: 22-23


Define possible slots for our select.

.. literalinclude:: ../../../examples/select.py
    :caption: examples/select.py - defining slots
    :lines: 27-36


Define possible colours for our select.

.. literalinclude:: ../../../examples/select.py
    :caption: examples/select.py - defining colours
    :lines: 40-58


Then, we make and register the select.

.. literalinclude:: ../../../examples/select.py
    :caption: examples/select.py - creating a select component
    :lines: 62-116


Finally, we make a command that sends the component.
In this command, we initialise the timeout for the component.

.. literalinclude:: ../../../examples/select.py
    :caption: examples/select.py - sending the component
    :lines: 121-133

Source Code
-----------

.. literalinclude:: ../../../examples/select.py
    :caption: examples/select.py
    :lines: 9-16, 19-20, 22-25, 27-38, 40-60, 62-73, 75-77, 80-82, 84-86, 88-91, 93-97, 99-101, 103-106, 108-109, 111-114, 116-118, 121-122, 124-130, 134-135, 137 
    :linenos: