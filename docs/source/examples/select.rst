Select
======
A simple example on the use of selects with disnake-ext-components.

For this example, we implement a select menu with double functionality.
Firstly, the select allows you to select one of three slots. After selecting a
slot, the select is modified to instead allow you to select a colour. The
selected slot and colour are then combined to colour the corresponding square.


First and foremost, we create a bot as per usual. Since we don't need any
prefix command capabilities, we opt for an :class:`~disnake.ext.commands.InteractionBot`.

.. literalinclude:: ../../../examples/select.py
    :caption: examples/select.py - creating a Bot object
    :lines: 9-17


Next, we make a component manager and register it to the bot.

.. literalinclude:: ../../../examples/select.py
    :caption: examples/select.py - creating a manager and registering it
    :lines: 19-20


Define possible slots for our select.

.. literalinclude:: ../../../examples/select.py
    :caption: examples/select.py - defining slots
    :lines: 23-32


Define possible colours for our select.

.. literalinclude:: ../../../examples/select.py
    :caption: examples/select.py - defining colours
    :lines: 35-53


Then, we make and register the select.

.. literalinclude:: ../../../examples/select.py
    :caption: examples/select.py - creating a select component
    :lines: 56-99
    :emphasize-lines: 1, 6-10

Set the placeholder text...

.. literalinclude:: ../../../examples/select.py
    :lines: 58

Set the options...

.. literalinclude:: ../../../examples/select.py
    :lines: 59

We store the slot the user is currently working with...

.. literalinclude:: ../../../examples/select.py
    :lines: 61

We store whether they're picking a slot or a colour...

.. literalinclude:: ../../../examples/select.py
    :lines: 62

And we store the colours for the three slots...

.. literalinclude:: ../../../examples/select.py
    :lines: 63-65

In the callback first we get the selected value.

This should never raise for a select.

.. literalinclude:: ../../../examples/select.py
    :lines: 68

If the selection was a slot, run slot selection logic.
To keep things tidy, we use a separate function for this.

.. literalinclude:: ../../../examples/select.py
    :lines: 71-72

Otherwise, run colour selection logic.

.. literalinclude:: ../../../examples/select.py
    :lines: 74-75

Render the new colours and update the select.

.. literalinclude:: ../../../examples/select.py
    :lines: 77-78

Then in ``handle_slots`` in case the user wishes to finalize, disable the select.

.. literalinclude:: ../../../examples/select.py
    :lines: 81-84

Update options and display.

.. literalinclude:: ../../../examples/select.py
    :lines: 86-87

Set the slot to the user's selection and set state to colour.

.. literalinclude:: ../../../examples/select.py
    :lines: 89-90

Then in ``handle_colours`` update the options.

.. literalinclude:: ../../../examples/select.py
    :lines: 93

Set the corresponding colour attribute and set state to slot.

.. literalinclude:: ../../../examples/select.py
    :lines: 95-96

Then in ``render_colours`` render our three squares.

.. literalinclude:: ../../../examples/select.py
    :lines: 99


Finally, we make a command that sends the component.
In this command, we initialise the timeout for the component.

.. literalinclude:: ../../../examples/select.py
    :caption: examples/select.py - sending the component
    :lines: 102-109
    :emphasize-lines: 3, 6-8

.. tip::
    Wrapping the interaction allows you to send the component as-is.

    If we had not wrapped the interaction, we would have needed to do ``await inter.send(components=await component.as_ui_component())`` instead.

Lastly, we run the bot.

.. literalinclude:: ../../../examples/select.py
    :caption: examples/select.py - running the bot
    :lines: 112

Source Code
-----------

.. literalinclude:: ../../../examples/select.py
    :caption: examples/select.py
    :lines: 9-112
    :emphasize-lines: 11-12, 48, 53-57, 96, 99-101, 104
    :linenos: