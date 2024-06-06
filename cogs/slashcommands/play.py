import discord
from discord.app_commands import command
from discord.ext import commands
from utils.audio import ensure_voice, play_audio


class SlashPlay(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @command(name="play", description="Join your voice channel and plays the Hits.")
    async def play(self, interaction: discord.Interaction):
        voice_client = await ensure_voice(interaction)
        if voice_client is None:
            return

        embed = discord.Embed(color=discord.Color.green())

        if not voice_client.is_playing():
            play_audio(voice_client)
            embed.description = f"🎵 Playing Hits in {interaction.user.voice.channel.mention}"
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed.description = "🔊 Already playing audio in this channel."
            await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(SlashPlay(bot))
