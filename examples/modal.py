import datetime
import os
import typing as t

import disnake
from disnake.ext import commands, components
from disnake.ext.components import patterns


def to_datetime(arg: str) -> datetime.datetime:
    return datetime.datetime.fromtimestamp(int(arg))


def from_datetime(arg: datetime.datetime) -> str:
    return str(int(arg.timestamp()))


class ModalCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.APP_CHANNEL_ID = int(os.environ["APP_CHANNEL_ID"])

    @components.modal_listener()
    async def application_form_listener(
        self,
        inter: disnake.ModalInteraction,
        name: str = components.ModalValue("Please enter your name..."),
        # ^ The value entered by the user in a 'short'-style TextInput.
        age: int = components.ModalValue("Please enter your age..."),
        # ^ The value entered by the user in a 'short'-style TextInput, converted to `int`.
        about_me: str = components.ParagraphModalValue("Please write something about yourself..."),
        # ^ The value entered by the user in a 'paragraph'-style TextInput.
        #   These fields are used by `build_modal` to automatically determine the type of TextInput.
        #   The strings inside these fields are used as placeholders.
        *,
        # ^ Parameters parsed from the custom_id are keyword-only, thus the modal parameters end here.
        destination: disnake.TextChannel = ...,
        # ^ 'Moderator' channel to which we send a confirmation.
        send_time: components.Converted[
            patterns.STRICTINT,  # A pre-defined pattern that matches an unsigned integer.
            to_datetime,  # A converter to go from a str UNIX timestamp to datetime.
            from_datetime,  # A converter to go from datetime back to str. Used by `build_modal`.
        ] = ...,
    ):
        """This listener listens for the regex pattern
        ```py
        r"application_form_listener:\\d{15,20}:\\d+"
        ```
        The two groups after the name correspond to the destination channel and send time, respectively.

        The topmost parameters are parsed from the :class:`disnake.ui.TextInput` fields of the
        :class:`disnake.ui.Modal`. :class:`components.ModalValue` and :class:`components.ParagraphModalValue`
        are used as helpers for :meth:`components.ModalListener.build_modal` to infer the desired TextInput
        parameters.

        The custom_id parameters and ModalValue parameters should be kept explicitly separate by denoting the
        custom_id parameters as keyword-only.
        """

        now = datetime.datetime.now()
        time_spent = (now - send_time).seconds
        mins, secs = divmod(time_spent, 60)

        application_embed = (  # Now we make an embed to send to the moderator channel...
            disnake.Embed()
            .set_author(name=str(inter.author), url=inter.author.display_avatar.url)
            .add_field(name="Who?", value=f"{name}, age {age}.")
            .add_field(name="About me...", value=about_me)
            .set_footer(text=f"This modal was filled out in {mins} minutes and {secs} seconds.")
        )

        await inter.response.send_message(  # Send confirmation to the applicant...
            "Thank you for your application! We hope to get back to you as soon as possible.",
            ephemeral=True,
        )

        # And finally send the embed to the moderator channel.
        await destination.send(embed=application_embed)

    @commands.slash_command()
    async def send_application(self, inter: disnake.CommandInteraction):
        """Fill in an application form for the Arl and Shift Appreciation Club."""

        modal = await self.application_form_listener.build_modal(
            "Application Form",
            # ^ The title for the modal
            destination=t.cast(disnake.TextChannel, disnake.Object(self.APP_CHANNEL_ID)),
            # ^ The destination channel. We cheat a bit and use a disnake.Object so we do not need to get/fetch.
            send_time=inter.created_at,
            # ^ The time at which the modal was sent (approximately).
        )

        await inter.response.send_modal(modal)


def setup(bot: commands.Bot):
    bot.add_cog(ModalCog(bot))
