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
    :lines: 9-13, 16


Create a manager object and register *all* components (current and future) to this manager.

.. literalinclude:: ../../../examples/select.py
    :caption: examples/select.py - creating a manager and registering components
    :lines: 19, 22


Define possible slots for our select.

.. literalinclude:: ../../../examples/select.py
    :caption: examples/select.py - defining slots
    :lines: 26-35


Define possible colours for our select.

.. literalinclude:: ../../../examples/select.py
    :caption: examples/select.py - defining colours
    :lines: 39-57


Then, we make the select.

.. literalinclude:: ../../../examples/select.py
    :caption: examples/select.py - creating a select subclass
    :lines: 61-115


Finally, we make a command that sends the component.
In this command, we initialise the timeout for the component.

.. literalinclude:: ../../../examples/select.py
    :caption: examples/select.py - creating a select subclass
    :lines: 120-132, 134

Source Code
-----------

.. literalinclude:: ../../../examples/select.py
    :caption: examples/select.py
    :start-at: import os
    :lines: 1-5, 8, 11, 14-16, 18-29, 31-51, 53-64, 66-68, 71-73, 75-77, 79-82, 84-88, 90-92, 94-97, 99-100, 102-105, 107-109, 112-113, 115-118, 123-124, 126
    :linenos: