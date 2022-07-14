import disnake
from disnake.ext import commands, components


class ComponentMatchingExample(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @components.match_component(component_type=disnake.ComponentType.button, label="simple_delete")
    async def simple_delete_listener(self, inter: disnake.MessageInteraction):
        """Check if the author has sufficient permissions. If so, delete the message."""
        await inter.response.defer()
        print(inter.component.custom_id)

        if (
            # DMs...
            isinstance(inter.channel, disnake.PartialMessageable)
            or isinstance(inter.author, disnake.User)
            # Author has manage_message permissions...
            or inter.channel.permissions_for(inter.author).manage_messages
        ):
            await inter.delete_original_message()
            return

        await inter.followup.send("You are not allowed to take this action!", ephemeral=True)

    @commands.slash_command()
    async def send_a_thing(self, inter: disnake.CommandInteraction):
        await inter.response.send_message(
            "Here's a thing.", components=await self.simple_delete_listener.build_component()
        )


def setup(bot: commands.Bot):
    bot.add_cog(ComponentMatchingExample(bot))
