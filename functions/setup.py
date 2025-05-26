import discord
from discord.ext import commands
from discord import app_commands
import string
import secrets
import json

from utils.logger_utils import datalog
from utils.database_utils import reconnect_database, db_get, db_write, db_update

class Setup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = bot.db_connection
        self.override_role = bot.override_role
        self.category_name = bot.category_name
        self.subscriber = bot.subscriber
        self.tier_1 = bot.tier_1
        self.tier_2 = bot.tier_2
        self.tier_3 = bot.tier_3

    def generate_random_token(self, length=32):
        reconnect_database(self.conn)
        characters = string.ascii_letters + string.digits
        while True:
            token = ''.join(secrets.choice(characters) for _ in range(length))
            result = db_get(
                self.conn,
                "SELECT COUNT(*) FROM servers WHERE minecraft_token = %s",
                (token,),
                fetchone=True
            )
            if result and result[0] == 0:
                return token

    async def add_override(self, guild):
        existing_role = discord.utils.get(guild.roles, name=self.override_role)
        if not existing_role:
            await guild.create_role(name=self.override_role, reason="✅ Role created by bot command")
        return f"✅ Override role created: {self.override_role}"

    async def add_channels(self, guild):
        return "✅ No channels created"

    def update_channels_roles(self, server_id, column, role):
        reconnect_database(self.conn)
        query = f"UPDATE channels_roles SET {column} = %s WHERE server_id = %s"
        db_update(self.conn, query, (role, server_id))

    async def add_channels_roles(self, guild):
        # Save all roles, indicating if each is managed
        roles_info = [
            {"id": role.id, "name": role.name, "managed": role.managed}
            for role in guild.roles if role != guild.default_role
        ]
        channels_info = [
            {"id": channel.id, "name": channel.name}
            for channel in guild.channels
        ]
        db_update(
            self.conn,
            "UPDATE channels_roles SET server_roles = %s, server_channels = %s WHERE server_id = %s",
            (json.dumps(roles_info), json.dumps(channels_info), guild.id)
        )
        return "✅ Roles and channels info set up"

    async def add_server(self, guild):
        reconnect_database(self.conn)
        server_id = guild.id
        server_name = guild.name
        owner = guild.owner_id
        new_minecraft_token = self.generate_random_token()
        try:
            result = db_get(
                self.conn,
                "SELECT minecraft_token FROM servers WHERE server_id = %s",
                (server_id,),
                fetchone=True
            )
            existing_token = result[0] if result else None
            if existing_token:
                db_update(
                    self.conn,
                    "UPDATE servers SET server_name = %s, minecraft_token = %s, owner = %s WHERE server_id = %s",
                    (server_name, new_minecraft_token, owner, server_id)
                )
                db_update(
                    self.conn,
                    "UPDATE users SET token = %s WHERE token = %s",
                    (new_minecraft_token, existing_token)
                )
            else:
                db_write(
                    self.conn,
                    "INSERT INTO servers (server_id, server_name, minecraft_token, owner) VALUES (%s, %s, %s, %s)",
                    (server_id, server_name, new_minecraft_token, owner)
                )
            result = db_get(
                self.conn,
                "SELECT COUNT(*) FROM channels_roles WHERE server_id = %s",
                (server_id,),
                fetchone=True
            )
            if result and result[0] == 0:
                db_write(
                    self.conn,
                    "INSERT INTO channels_roles (server_id, server_roles, server_channels) VALUES (%s, %s, %s)",
                    (server_id, "[]", "[]")
                )
            datalog(self.conn, 'setup', f"✅ Server data successfully added to MCSync. {server_id}")
            return new_minecraft_token
        except Exception as e:
            datalog(self.conn, 'setup', f"🚨 An error occurred: {e} - {server_id}")
            return None

    @discord.app_commands.command(name="setup", description="Setup your server with MCSync.")
    @discord.app_commands.default_permissions(administrator=True)
    async def setup(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Server Setup Completed",
            description="Your server has been set up with the following settings:",
            color=discord.Color.green()
        )
        server_token = await self.add_server(interaction.guild)
        override_status = await self.add_override(interaction.guild)
        channels_roles_status = await self.add_channels_roles(interaction.guild)  # <-- Call here
        embed.add_field(name="Server Token", value=f"||`{server_token}`|| ⬅️ Click to Show", inline=False)
        embed.add_field(name="Override Settings", value=override_status, inline=False)
        embed.add_field(name="Roles/Channels", value=channels_roles_status, inline=False)  # Optional: show status
        embed.set_footer(text="MCSync • Server Setup")
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Setup(bot))
