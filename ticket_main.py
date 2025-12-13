import os, discord
from discord.ext import commands
from discord import app_commands
from keep_alive import keep_alive

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    # Sync commands when the bot starts up
    await tree.sync()
    print(f'Logged in as {client.user}!')

# Define the slash command itself
@tree.command(name="release-game-password", description="[STAFF ONLY] Releases the game password to the user.")
async def release_password_command(interaction: discord.Interaction):
    
    # 1. SECURITY CHECK: Check if the user has the required role
    is_authorized = any(role.id == os.environ["SUPPORT"] for role in interaction.user.roles)

    if not is_authorized:
        await interaction.response.send_message(
            "You do not have permission to use this command.", 
            ephemeral=True # Makes the error message visible only to the staff member who used it
        )
        return

    # 2. WORKFLOW CHECK: Ensure this is used in a ticket channel (optional but recommended)
    # You might want to check if the channel name starts with "ticket-"

    # 3. SUCCESS: Acknowledge the command and send the password
    # Defer the response first to prevent timeouts while sending the actual message
    await interaction.response.defer(ephemeral=False) 

    # Find the original ticket creator if needed, but sending it in the channel works
    
    # Send the actual message to the channel
    await interaction.followup.send(
        f"**Approval Granted!**\n"
        f"Hey {interaction.channel.mention}, here is your requested information:\n"
        f"```\n{os.environ["PASSWORD"]}\n```\n"
        f"Please keep this confidential."
    )

# Run the bot with your Discord bot token
# You get this token from the Discord Developer Portal
keep_alive()
client.run(os.environ["TOKEN"])