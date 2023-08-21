.. currentmodule:: disnake-ext-components

Component Manager
=================

A simple example on the use of component managers with disnake-ext-components.


First and foremost, we create a bot as per usual. Since we don't need any
prefix command capabilities, we opt for an :class:`disnake.ext.commands.InteractionBot`.

.. literalinclude:: ../../../examples/manager.py
    :caption: examples/manager.py - creating a Bot object
    :lines: 3-8, 11


Next, we create a component manager.

A call to :func:`.get_manager` without arguments returns the root manager.
We register the root manager to the bot, which will ensure all components we register to any other manager will automatically be handled. This is because a manager handles its own components along with any of its children's.

.. literalinclude:: ../../../examples/manager.py
    :caption: examples/manager.py - create a root component manager
    :lines: 18-19
    :emphasize-lines: 1


We can create a child manager as follows

.. literalinclude:: ../../../examples/manager.py
    :caption: examples/manager.py - create a child manager
    :lines: 23


We can go deeper in the parent/child hierarchy by separating them with dots

.. literalinclude:: ../../../examples/manager.py
    :caption: examples/manager.py - create a deeply nested manager 
    :lines: 27

.. note::
    Any missing bits will automatically be filled in-- the above line has automatically created a manager named "foo.bar", too.


Now let us quickly register a button each to our ``foo_manager`` and our ``deeply_nested_manager``. To this end, we will use the button example

.. literalinclude:: ../../../examples/manager.py
    :caption: examples/manager.py - creating a button component
    :lines: 36-59


Customizing your component manager
----------------------------------

For most use cases, the default implementation of the component manager should suffice. Two methods of interest to customise your managers without having to subclass them are :class:`ComponentManager.as_callback_wrapper` and :class:`ComponentManager.as_error_handler`.

:class:`ComponentManager.as_callback_wrapper` wraps the callbacks of all components registered to that manager along with those of its children. Therefore, if we
# were to add a callback wrapper to the root manager, we would ensure it applies to *all* components. For example, say we want to log all component interactions

.. literalinclude:: ../../../examples/manager.py
    :caption: examples/manager.py - customizing your component manager
    :lines: 74-79, 83-89, 94-97
    :emphasize-lines: 1-6, 12

.. tip::
    For actual production code, please use logging instead of print.

Any code placed after the yield statement runs after the component callback is invoked. This can be used for cleanup of resources

.. note::
    Any changes made to the component instance by other wrappers and/or the callback itself are reflected here.


This feature can also be used as a check. By raising an exception before the component callback is invoked, you can prevent it from being invoked entirely. The exception is then also passed to exception handlers.

For example, let's allow *only* the original slash command author to interact with any components on this manager.

.. literalinclude:: ../../../examples/manager.py
    :caption: examples/manager.py - creating a check to prevent the component callback call
    :lines: 103-115, 118-130
    :emphasize-lines: 8-13, 26


Similarly, we can create an exception handler for our components. An exception handler function should return ``True`` if the error was handled, and ``False`` or ``None`` otherwise.
The default implementation hands the exception down to the next handler until it either is handled or reaches the root manager. If the root manager is reached (and does not have a custom exception handler), the exception is logged.

To demonstrate the difference, we will make a custom error handler only for the ``deeply_nested_manager``.

.. literalinclude:: ../../../examples/manager.py
    :caption: examples/manager.py - components custom error handler
    :lines: 143-155
    :emphasize-lines: 1-7, 11, 13

.. note::
    You do not need to explicitly return ``False``. Returning ``None`` is sufficient. Explicitly returning ``False`` is simply preferred for clarity.

Finally, we send the components to test the managers.

.. literalinclude:: ../../../examples/manager.py
    :caption: examples/manager.py - sending the components
    :lines: 163-176

Lastly, we run the bot.

.. literalinclude:: ../../../examples/manager.py
    :caption: examples/manager.py - running the bot
    :lines: 180

Source Code
-----------

.. literalinclude:: ../../../examples/manager.py
    :caption: examples/manager.py
    :lines: 3-8, 11, 18-21, 23, 27-29, 36-61, 74-79, 83-89, 94-99, 103-115, 118, 120, 122, 124-125, 127-132, 143-157, 163-178, 180
    :emphasize-lines: 8-9, 12-13, 42-47, 53, 68-73, 82, 85-91, 95, 97, 116
    :linenos: