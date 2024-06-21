import asyncio
import logging
import os
import discord
from dotenv import load_dotenv

load_dotenv()

STREAM_LINK = os.getenv('STREAM_LINK')

print(STREAM_LINK)


async def connect_to_channel(voice_channel):
    """
    Connects to the voice channel or moves to it if already connected to a different channel.
    """
    guild = voice_channel.guild
    voice_client = guild.voice_client

    if voice_client is None or not voice_client.is_connected():
        try:
            return await voice_channel.connect()
        except discord.ClientException as e:
            logging.error(f"Error connecting to channel: {e}")
            return None
    elif voice_client.channel != voice_channel:
        try:
            await voice_client.move_to(voice_channel)
        except discord.ClientException as e:
            logging.error(f"Error moving to a new channel: {e}")
            return None

    return voice_client


async def ensure_voice(interaction):
    """
    Ensures that the bot joins the correct voice channel of the user.
    """
    embed = discord.Embed(color=discord.Color.blue())

    if interaction.user.voice is None or interaction.user.voice.channel is None:
        embed.description = "🚫 You must be in a voice channel to run this command."
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return None

    voice_channel = interaction.user.voice.channel
    guild_voice_state = interaction.guild.voice_client

    if guild_voice_state and guild_voice_state.channel == voice_channel:
        embed.description = "🎶 I'm already in your voice channel."
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return guild_voice_state
    elif guild_voice_state:
        embed.description = f"🔊 I'm already connected to a different channel: {guild_voice_state.channel.mention}"
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return None

    permissions = voice_channel.permissions_for(interaction.guild.me)
    if not permissions.connect or not permissions.speak:
        embed.description = "⛔ I need the `CONNECT` and `SPEAK` permissions."
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return None

    return await connect_to_channel(voice_channel)


def play_audio(voice_client):
    """
    Plays the audio stream in the voice channel.
    """
    try:
        audio_source = discord.FFmpegPCMAudio(STREAM_LINK, options='-b:a 96k')
        if not voice_client.is_playing():
            voice_client.play(audio_source, after=lambda e: handle_playback_errors(e, voice_client))
    except Exception as e:
        logging.error(f"Error starting FFmpeg audio stream: {e}")
        asyncio.create_task(retry_play_audio(voice_client))


async def retry_play_audio(voice_client):
    """
    Retries to play audio after a delay in case of an error.
    """
    await asyncio.sleep(10)
    play_audio(voice_client)


def handle_playback_errors(error, voice_client):
    """
    Handles errors during playback and restarts the audio stream if needed.
    """
    if error:
        logging.error(f"FFmpeg playback error: {error}")
        asyncio.create_task(restart_audio_stream(voice_client.guild))


async def restart_audio_stream(guild):
    """
    Restarts the audio stream in the guild's voice channel.
    """
    voice_client = guild.voice_client
    if voice_client and voice_client.is_connected():
        voice_client.stop()
        play_audio(voice_client)
