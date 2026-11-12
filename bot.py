import os
import discord
import datetime

# ========= CONFIG VIA ENVIRONMENT VARIABLES =========
# These must be set in Railway's "Variables" settings
BOT_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
DEAFENED_CHANNEL_ID = int(os.getenv("DEAFENED_CHANNEL_ID"))
# ====================================================

intents = discord.Intents.default()
intents.guilds = True
intents.voice_states = True  # lets us see deafen/undeafen

client = discord.Client(intents=intents)

# user_id -> original_channel_id
previous_channels = {}


@client.event
async def on_ready():
    print(f"{datetime.datetime.now()} Logged in as {client.user} (ID: {client.user.id}) on server {GUILD_ID}")
    print(f"{datetime.datetime.now()} Deafen mover bot is running.")


@client.event
async def on_voice_state_update(member, before, after):
    # Ignore bots
    if member.bot:
        print(f"{datetime.datetime.now()} User {member.display_name} is a bot.")
        return

    # Only act on the one server we care about
    if member.guild.id != GUILD_ID:
        print(f"{datetime.datetime.now()} User {member.display_name} not on valid server.")
        return

    is_deafened = (before.self_deaf and after.self_deaf)
    just_deafened = (not before.self_deaf and after.self_deaf)
    just_undeafened = (before.self_deaf and not after.self_deaf)

    # CASE 1: user just self-deafened
    if just_deafened or is_deafened:
        print(f"{datetime.datetime.now()} User {member.display_name} is deafened.")
                
        # If they're already in that channel, don't move
        if after.channel.id == DEAFENED_CHANNEL_ID:
            return
        
        # If they're not in a voice channel, nothing to do
        if after.channel is None:
            print(f"{datetime.datetime.now()} User {member.display_name} not in voice.")
            return

        # Remember where they were
        previous_channels[member.id] = after.channel.id

        # Get the special "deafened" channel
        target = member.guild.get_channel(DEAFENED_CHANNEL_ID)
        if not isinstance(target, discord.VoiceChannel):
            print(f"{datetime.datetime.now()} ERROR: DEAFENED_CHANNEL_ID is not a valid voice channel.")
            return

        try:
            await member.move_to(target)
            print(f"{datetime.datetime.now()} Moved {member.display_name} to deafened channel.")
        except discord.Forbidden:
            print(f"{datetime.datetime.now()} Missing permission to move members.")
        except discord.HTTPException as e:
            print(f"Failed to move member: {e}")

    # CASE 2: user just self-undeafened
    elif just_undeafened:
        print(f"{datetime.datetime.now()} User {member.display_name} undeafened.")
        original_id = previous_channels.pop(member.id, None)
        if original_id is None:
            print(f"{datetime.datetime.now()} Missing original channel.")
            return

        # They must be currently in the deafened channel for us to move them back
        if after.channel is None or after.channel.id != DEAFENED_CHANNEL_ID:
            print(f"{datetime.datetime.now()} Not currently in Deafened channel.")
            return

        original = member.guild.get_channel(original_id)
        if not isinstance(original, discord.VoiceChannel):
            # original channel deleted or invalid
            print(f"{datetime.datetime.now()} Original channel missing.")
            return

        # If somehow already there, do nothing
        if after.channel.id == original.id:
            print(f"{datetime.datetime.now()} Already in original channel.")
            return

        try:
            await member.move_to(original)
            print(f"{datetime.datetime.now()} Moved {member.display_name} back to {original.name}.")
        except discord.Forbidden:
            print(f"{datetime.datetime.now()} Missing permission to move members back.")
        except discord.HTTPException as e:
            print(f"{datetime.datetime.now()} Failed to move member back: {e}")


if __name__ == "__main__":
    if not BOT_TOKEN:
        raise RuntimeError("You must set DISCORD_TOKEN, GUILD_ID, and DEAFENED_CHANNEL_ID env vars.")
    if not GUILD_ID or not DEAFENED_CHANNEL_ID:
        raise RuntimeError("GUILD_ID and DEAFENED_CHANNEL_ID must be non-zero integers.")
    client.run(BOT_TOKEN)
