Component Manager
=================

A simple example on the use of custom managers with disnake-ext-components.

.. warning::
    Component managers are fairly complex and leverage weak
    references to their components in a lot of different places. For many things
    to be able to unload and/or be garbage-collected appropriately, it is
    imperative that there are no external references to components.

    **Making custom component managers is therefore very sensitive to introducing
    a myriad of reference cycles and potentially even memory leaks, so discretion
    is advised.**

As far as safety goes, overwriting 'ComponentManager.callback_hook' as is done
in this example is fairly safe, provided you do not store the components
externally.


First and foremost, we create a bot as per usual. Since we don't need any
prefix command capabilities, we opt for an :class:`disnake.ext.commands.InteractionBot`.

.. literalinclude:: ../../../examples/manager.py
    :caption: examples/manager.py - creating a Bot object
    :lines: 16-23, 26


Next, we make a custom component manager.

For the sake of this example, we will make a custom manager that prints
the runtime of a component callback.

.. literalinclude:: ../../../examples/manager.py
    :caption: examples/manager.py - create a custom component manager
    :lines: 30, 35-46

.. note::
    If you wish to stop a component from running, you can raise an exception
    before the yield statement.


Create a manager object and register *all* components (current and future) to this manager.

.. literalinclude:: ../../../examples/manager.py
    :caption: examples/manager.py - create a manager object and register all components
    :lines: 52, 55


Then we make a simple component. For a more detailed explanation, see the
'button.py' example.

.. literalinclude:: ../../../examples/manager.py
    :caption: examples/manager.py - creating a component
    :lines: 60-69


Finally, we make a command that sends the component.

.. literalinclude:: ../../../examples/manager.py
    :caption: examples/manager.py - creating a command and send the component
    :lines: 73-80, 82


Source Code
-----------

.. literalinclude:: ../../../examples/manager.py
    :caption: examples/manager.py
    :start-at: import contextlib
    :lines: 1-8, 11-13, 15, 20-31, 35-37, 40-42, 45-56, 58-65, 67
    :linenos:
