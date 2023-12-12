The Basics
==========

This section explains how to use `disnake-ext-components` to create and manage your components, and how to send them to Discord so that your users can interact with them.

Components
----------

Component classes are all :obj:`attrs` classes. If you're unfamiliar with attrs, know that they work very similarly to dataclasses.
A component class has two types of fields:

- **Internal fields**

  These are reserved for parameters that directly influence the component, such as the :obj:`~disnake.ui.Button.label` field for a button.
  For the most part, these match the attributes on the standard :ref:`disnake.ui <disnake_api_ui>` component classes.

- **Custom id fields**

  These are entirely user-defined, and their values are stored inside the components' custom ids.
  Custom ids are limited by the `discord api <https://discord.com/developers/docs/interactions/message-components#custom-id>`_ to have a maximum length of 100 characters, so the information you can store here is limited!

.. important::
    Both types of fields are created in the same way as normal attrs/dataclass fields. In particular, keep in mind that typehinting fields is **required**.

The examples in the tabs below show all available custom id parameters for each component type, and provide a very minimal example of how one such component could look.

.. tab:: Button

    The `disnake-ext-components`-equivalent of a :class:`disnake.ui.Button`.

    .. code-block:: py
        :linenos:

        class MyButton(components.RichButton):
            # All valid internal fields:
            label: str = "My button"
            style: disnake.ButtonStyle = disnake.ButtonStyle.primary
            emoji: str = "\N{WHITE HEAVY CHECK MARK}"
            disabled: bool = False

            # Custom id fields:
            foo: int      # field without default
            bar: int = 3  # field with default

            # A callback is required:
            async def callback(self, inter: disnake.MessageInteraction):
                await inter.response.send_message("Click!")

    .. important::
        Since callbacks are required and URL-buttons cannot have a callback, disnake-ext-components does *not* support the :obj:`url <disnake.ui.Button.url>` attribute.

.. tab:: String Select

    The `disnake-ext-components`-equivalent of a :class:`disnake.ui.StringSelect`.

    .. code-block:: py
        :linenos:

        class MyButton(components.RichStringSelect):
            # All valid internal fields:
            placeholder: str = "My string select"
            min_values: int = 1
            max_values: int = 2
            disabled: bool = False
            options: List[disnake.SelectOption] = [
                disnake.SelectOption(label="foo", value=1),
                disnake.SelectOption(label="bar", value=2),
            ]

            # Custom id fields:
            foo: int      # field without default
            bar: int = 3  # field with default

            # A callback is required:
            async def callback(self, inter: disnake.MessageInteraction):
                await inter.response.send_message("Click!")

.. tab:: User Select

    The `disnake-ext-components`-equivalent of a :class:`disnake.ui.UserSelect`.

    .. code-block:: py
        :linenos:

        class MyButton(components.RichUserSelect):
            # All valid internal fields:
            placeholder: str = "My user select"
            min_values: int = 1
            max_values: int = 2
            disabled: bool = False

            # Custom id fields:
            foo: int      # field without default
            bar: int = 3  # field with default

            # A callback is required:
            async def callback(self, inter: disnake.MessageInteraction):
                await inter.response.send_message("Click!")

.. tab:: Role Select

    The `disnake-ext-components`-equivalent of a :class:`disnake.ui.RoleSelect`.

    .. code-block:: py
        :linenos:

        class MyButton(components.RichRoleSelect):
            # All valid internal fields:
            placeholder: str = "My role select"
            min_values: int = 1
            max_values: int = 2
            disabled: bool = False

            # Custom id fields:
            foo: int      # field without default
            bar: int = 3  # field with default

            # A callback is required:
            async def callback(self, inter: disnake.MessageInteraction):
                await inter.response.send_message("Click!")

.. tab:: Channel Select

    The `disnake-ext-components`-equivalent of a :class:`disnake.ui.ChannelSelect`.

    .. code-block:: py
        :linenos:

        class MyButton(components.RichChannelSelect):
            # All valid internal fields:
            placeholder: str = "My channel select"
            min_values: int = 1
            max_values: int = 2
            disabled: bool = False

            # Custom id fields:
            foo: int      # field without default
            bar: int = 3  # field with default

            # A callback is required:
            async def callback(self, inter: disnake.MessageInteraction):
                await inter.response.send_message("Click!")

.. tab:: Mentionable Select

    The `disnake-ext-components`-equivalent of a :class:`disnake.ui.MentionableSelect`.

    .. code-block:: py
        :linenos:

        class MyButton(components.RichMentionableSelect):
            # All valid internal fields:
            placeholder: str = "My mentionable select"
            min_values: int = 1
            max_values: int = 2
            disabled: bool = False

            # Custom id fields:
            foo: int      # field without default
            bar: int = 3  # field with default

            # A callback is required:
            async def callback(self, inter: disnake.MessageInteraction):
                await inter.response.send_message("Click!")

Since these classes are created using attrs, the ``__init__`` methods for your component classes are automatically generated. If you need further control, you can use attrs features like ``__attrs_post_init__`` to process each instance before they are handled by `disnake-ext-components`.


Component Managers
------------------

Now that we know how to create components, we need to learn how to hook these components into your bot. Luckily, this is pretty simple.
All we need is a :class:`~ComponentManager`, which we get using :func:`~get_manager`. For basic usage, we just call ``get_manager()`` without arguments and assign it to a variable. We then use :meth:`~ComponentManager.add_to_bot` and pass the bot to it to allow the manager to communicate with the bot.
Finally, we register components to the bot using :meth:`~ComponentManager.register`. This can be done in a few different ways, but for now the easiest way is to just use it as a basic decorator.

.. code-block:: py
    :linenos:

    import disnake
    from disnake.ext import commands, components

    bot = disnake.Bot(...)
    manager = components.get_manager()
    manager.add_to_bot(bot)

    @manager.register
    class MyButton(components.RichButton):
        label: str = "My Button"

        foo: int      # field without default
        bar: int = 3  # field with default

        async def callback(self, inter: disnake.MessageInteraction):
            await inter.response.send_message("Click!")

.. important::
    The use of :class:`disnake.Client` with `disnake-ext-components` requires disnake version 2.10.0 or above. On lower versions of disnake, you need to use any of disnake's :ref:`bot classes <ext_commands_api_bots>`.


Sending Components
------------------

Last but not least, we need to send our components to discord. To do so, we first need to create an instance of our button class. This is simply done by instantiating the class as with any other class. Any custom id fields without a default value must be provided. Since the class is made using `attrs`, it is fully typehinted, and your typechecker will let you know if you are missing anything.

.. tip::
    We definitely recommend using a type checker! `pyright <https://pypi.org/project/pyright>`_ is particularly compatible as `disnake-ext-components` was developed with it.

Actually sending the component works slightly differently from normal :ref:`disnake.ui <disnake_api_ui>` components. We have two options:

- **Explicit conversion**

  We can explicitly convert our `disnake-ext-components`-style component into a `disnake.ui`-style component using :meth:`~.RichComponent.as_ui_component`.

- **Interaction wrapping**

  Alternatively, we can wrap an interaction into a new `disnake-ext-components`-style interaction, which can automatically deal with `disnake-ext-components`-style components. This is done using :func:`~.wrap_interaction`.

  .. important::
    Interactions provided to component callbacks will automatically be wrapped. If you plan to use text commands, you must use explicit conversion, as :func:`~.wrap_interaction` does not support :class:`commands.Context <disnake.ext.commands.Context>`.

The examples in the tabs below show you how either of these options would look. You are free to pick whichever syntax you are more comfortable with.

.. tab:: Explicit conversion

    .. code-block:: py
        :linenos:

        class MyButton(components.RichButton):
            label = "My button"

            foo: int      # field without default
            bar: int = 3  # field with default

            async def callback(self, inter: disnake.MessageInteraction):
                new_button = await self.as_ui_component()
                await inter.response.send_message("Click!", components=new_button)


        @commands.slash_command()
        async def my_command(inter: disnake.MessageInteraction):
            button = MyButton(foo=1)
            ui_button = await button.as_ui_component()
            await inter.response.send_message(components=ui_button)

.. tab:: Interaction wrapping

    .. code-block:: py
        :linenos:

        class MyButton(components.RichButton):
            label = "My button"

            foo: int      # field without default
            bar: int = 3  # field with default

            async def callback(self, inter: components.MessageInteraction):
                await inter.response.send_message("Click!", components=self)


        @commands.slash_command()
        async def my_command(inter: disnake.MessageInteraction):
            wrapped = components.wrap_interaction(inter)
            button = MyButton(foo=1)
            await inter.response.send_message(components=button)

    .. note::
        The interaction in the button callback is now typehinted as a :class:`components.MessageInteraction <.MessageInteraction>` as opposed to a :class:`disnake.MessageInteraction`. This is only relevant for type-checking purposes.


.. _quickstart_basics_example:

Example
-------

You know know enough to make a fully functional component with `disnake-ext-components`! Combining the examples of the above sections nets you the following bot main file:

.. code-block:: py
    :linenos:

    import disnake
    from disnake.ext import commands, components

    bot = disnake.Bot(...)
    manager = components.get_manager()
    manager.add_to_bot(bot)

    @manager.register
    class MyButton(components.RichButton):
        label: str = "My button"

        foo: int      # field without default
        bar: int = 3  # field with default

        async def callback(self, inter: disnake.MessageInteraction):
            await inter.response.send_message("Click!", components=self)


    @commands.slash_command()
    async def my_command(inter: disnake.MessageInteraction):
        wrapped = components.wrap_interaction(inter)
        button = MyButton(foo=1)
        await inter.response.send_message(components=button)

    bot.run(...)
