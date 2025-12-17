import os, discord, psycopg2, atexit
from discord.ext import commands
from discord import app_commands
from keep_alive import keep_alive
from db import conn

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True 
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

AUTHORIZE = int(os.environ["SUPPORT"])


def init_db():
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS track_authority (
                id SERIAL PRIMARY KEY,
                track TEXT NOT NULL,
                claimed_by TEXT NOT NULL,
                reason TEXT NOT NULL,
                claimed_at TIMESTAMP DEFAULT NOW(),
                released_at TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            );
        """)

        cur.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS one_active_authority_per_track
            ON track_authority(track)
            WHERE is_active = TRUE;
        """)

@atexit.register
def close_db():
    conn.close()


#password release
@tree.command(name="release-password", description="[STAFF ONLY] Releases the game password to the user.")
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



#db commands
@tree.command(name="track-authority")
async def track_authority(interaction: discord.Interaction, track: str, reason: str):
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO track_authority
                (track, claimed_by, reason)
                VALUES (%s, %s, %s)
            """, (track, str(interaction.user.id), reason))

        await interaction.response.send_message(
            f"🚦 **Track {track}** claimed by {interaction.user.mention}"
        )

    except psycopg2.errors.UniqueViolation:
        await interaction.response.send_message(
            f"❌ **Track {track}** already has active authority.",
            ephemeral=True
        )



@tree.command(name="release-authority")
async def release_authority(
    interaction: discord.Interaction,
    track: str
):
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE track_authority
            SET is_active=FALSE, released_at=NOW()
            WHERE track=%s
              AND claimed_by=%s
              AND is_active=TRUE
        """, (track, str(interaction.user.id)))

        if cur.rowcount == 0:
            await interaction.response.send_message(
                "❌ You do not hold authority on this track.",
                ephemeral=True
            )
            return

    await interaction.response.send_message(
        f"✅ Authority on **{track}** released."
    )



PRIORITY_CHOICES = [
    app_commands.Choice(name="Critical", value="critical"),
    app_commands.Choice(name="High", value="high"),
    app_commands.Choice(name="Medium", value="medium"),
    app_commands.Choice(name="Low", value="low")
]

@tree.command(name="hot-car")
@app_commands.describe(
    car_id="Car ID that needs priority",
    location="Current location of car",
    reason="Why is this car urgent",
    priority="Priority level"
)
async def hot_car(
    interaction: discord.Interaction,
    car_id: str,
    location: str,
    reason: str,
    priority: app_commands.Choice[str]
):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO hot_car_requests
            (car_id, location, reason, priority, requested_by)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            car_id.strip().upper(),
            location.strip(),
            reason.strip(),
            priority.value,           # Use .value here
            str(interaction.user.id)
        ))
    await interaction.response.send_message(
        f"🔥 **Hot Car Request** submitted for car **{car_id}** at **{location}** "
        f"with priority **{priority.name}**.",
        ephemeral=False
    )



@tree.command(name="active-hotcars")
async def active_hotcars(interaction: discord.Interaction):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, car_id, location, priority, reason, requested_by
            FROM hot_car_requests
            WHERE status='open'
            ORDER BY requested_at ASC
        """)
        rows = cur.fetchall()

    if not rows:
        return await interaction.response.send_message(
            "🚫 No active hot car requests.", ephemeral=True
        )

    msg = "**🔥 Active Hot Car Requests:**\n"
    for id_, car, loc, pri, reason, uid in rows:
        msg += (
            f"\n**{car}** @ {loc} — Priority: {pri}\n"
            f"• Reason: {reason}\n"
            f"• Requested by: <@{uid}>\n"
        )
    await interaction.response.send_message(msg)


@client.event
async def on_ready():
    init_db()
    await tree.sync()
    print(f'Logged in as {client.user}!')

keep_alive()
client.run(os.environ["TOKEN"])