import disnake
from disnake.ext import commands, components


class Coggers(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @components.button_with_id(regex=r"succeeds:(?P<uid>\d+)")
    async def listener(self, inter: disnake.MessageInteraction, uid: str):
        s = inter.component.custom_id.replace(uid, f"**{uid}**")
        await inter.response.send_message(f"got: {s}")


def setup(bot: commands.Bot):
    bot.add_cog(Coggers(bot))
