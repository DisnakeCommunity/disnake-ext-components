import typing as t

import disnake
from disnake.ext import commands, components


class ListenerCog(commands.Cog):
    """Cog that implements a simple, extendable paginator with buttons that are fully persistent
    across bot reloads by storing state in their `custom_id`s.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    PAGES = (
        disnake.Embed(
            title="Page 1",
            description="Here's a page.\nYou can go both backwards and forwards!",
        ),
        disnake.Embed(
            title="Page 2",
            description="Here's another.\nTake it slow and have a cup of tea.",
        ),
        disnake.Embed(
            title="Page 3",
            description="Here's the last one,\nYou've reached the end... or have you?",
        ),
    )

    async def make_buttons(
        self, page: int, author: disnake.User
    ) -> t.List[disnake.ui.Button[t.Any]]:
        """Create paginator buttons for a given page and author."""
        return [
            disnake.ui.Button(
                label=label,
                custom_id=await self.hey_listen.build_custom_id(
                    page=page, where=where, author=author
                ),
                # ^ Builds a new custom_id based on the auto-generated spec of the listener.
                #   Uses the same parameters as the listeners to format the spec.
                #   If you are at any point curious as to what this spec looks like, you can
                #   view it through `self.hey_listen.id_spec`.
                #
                #   Example custom_id:
                #   "hey_listen:0:next:0110100001101001
                style=style,
            )
            for label, where, style in (
                ("<", "prev", disnake.ButtonStyle.gray),
                (">", "next", disnake.ButtonStyle.gray),
                ("x", "stop", disnake.ButtonStyle.red),
            )
        ]

    @components.button_listener()
    async def hey_listen(
        self,
        inter: disnake.MessageInteraction,
        *,
        page: int,
        where: t.Literal["prev", "next", "stop"],
        author: disnake.User,
    ):
        """The actual listener. Only responds to `custom_id`s that match the regex:
        ```py
        r"hey_listen:(\\d+):(prev|next|stop):(\\d+)"
        ```
        - Capture group 1, `(\\d+)`, corresponds to parameter `page: int`,
        - Capture group 2, `(prev|next|stop)`, corresponds to parameter `where: Literal["prev", "next", "stop"]`,
        - Capture group 3, `(\\d+)`, corresponds to parameter `author_id: int`.

        The regex is auto-generated, and requires zero user-input. However, it is possible to provide
        custom regex if need be.

        Types are automatically cast to the types used to annotate the parameters.
        """
        if inter.author != author:  # Ensure only the author can control the buttons.
            return

        if where == "stop":  # Delete the message if the author wants to stop using the paginator.
            await inter.response.defer()
            await inter.message.delete()
            return

        page = (page + 1 if where == "next" else page - 1) % len(self.PAGES)  # Change page.

        await inter.response.edit_message(  # Update page and buttons.
            embed=self.PAGES[page],
            components=await self.make_buttons(page, author),
        )

    @commands.command()
    async def start(self, ctx: commands.Context[commands.Bot]):
        """Start the paginator by sending the first page with corresponding buttons."""
        # We need the user object to keep this type-safe.
        user = author._user if isinstance(author := ctx.author, disnake.Member) else author

        await ctx.send(embed=self.PAGES[0], components=await self.make_buttons(0, user))


def setup(bot: commands.Bot):
    bot.add_cog(ListenerCog(bot))
