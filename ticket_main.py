import os, discord
from discord.ext import commands
from discord import app_commands
from keep_alive import keep_alive

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True 
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

AUTHORIZE = os.environ["SUPPORT"]


#password release
@tree.command(name="release-game-password", description="[STAFF ONLY] Releases the game password to the user.")
async def release_password_command(interaction: discord.Interaction):
    
    # SECURITY 
    is_authorized = any(role.id == AUTHORIZE for role in interaction.user.roles)

    if not is_authorized:
        await interaction.response.send_message(
            "You do not have permission to use this command.", 
            ephemeral=True # Makes the error message visible only to the staff member who used it
        )
        return

    await interaction.response.defer(ephemeral=False) 

    
    # Send the  message to the channel
    await interaction.followup.send(
        f"**Approval Granted!**\n"
        f"Hey {interaction.channel.mention}, here is your requested information:\n"
        f"```\n{os.environ["PASSWORD"]}\n```\n"
        f"Please keep this confidential."
    )


#ticket rename
@client.event
async def on_guild_channel_create(channel):
    # Only look at text channels
    if not isinstance(channel, discord.TextChannel):
        return
    
    # # Check if new channel is in the ticket category
    # if channel.category_id != TICKET_CATEGORY_ID:
    #     return

    try:
        # check channel topic for the creator’s ID or username
        creator_id = None
        if channel.topic:
            creator_id = channel.topic.strip()

        # check permission overwrites for member
        if not creator_id:
            for overwrite in channel.overwrites:
                if isinstance(overwrite, discord.Member):
                    creator_id = overwrite.id
                    break
        
        # Build the new name
        new_name = f"ticket-{creator_id}" if creator_id else f"ticket-{channel.id}"

        # Rename the channel
        await channel.edit(name=new_name)
        print(f"Renamed channel to: {new_name}")

    except Exception as e:
        print("Failed to rename ticket channel:", e)


@client.event
async def on_ready():
    await tree.sync()
    print(f'Logged in as {client.user}!')


keep_alive()
client.run(os.environ["TOKEN"])