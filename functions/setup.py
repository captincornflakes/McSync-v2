import discord
from discord.ext import commands
from discord import app_commands
import string
import secrets

from utils.logger_utils import datalog
from utils.database_utils import reconnect_database

class Setup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = bot.db_connection
        self.override_role = "MCSync Override"
        self.category_name = "MCSync"
        self.subscriber = bot.subscriber
        self.tier_1 = bot.tier_1
        self.tier_2 = bot.tier_2
        self.tier_3 = bot.tier_3

    def generate_random_token(self, length=32):
        reconnect_database(self.conn)
        characters = string.ascii_letters + string.digits
        while True:
            token = ''.join(secrets.choice(characters) for _ in range(length))
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM servers WHERE minecraft_token = %s", (token,))
                if cursor.fetchone()[0] == 0:
                    return token

    async def add_override(self, guild):
        existing_role = discord.utils.get(guild.roles, name=self.override_role)
        if not existing_role:
            await guild.create_role(name=self.override_role, reason="✅ Role created by bot command")
        return f"✅ Override role created: {self.override_role}"

    async def add_channels(self, guild):
        category_name = self.category_name
        category = discord.utils.get(guild.categories, name=category_name)
        if not category:
            category = await guild.create_category(category_name)
            for role in guild.roles:
                if role.permissions.administrator:
                    await category.set_permissions(role, read_messages=True)
        notifications_channel = discord.utils.get(category.channels, name='notifications')
        if not notifications_channel:
            await guild.create_text_channel('notifications', category=category)
        registrations_channel = discord.utils.get(category.channels, name='registrations')
        if not registrations_channel:
            await guild.create_text_channel('registrations', category=category)
        return "✅ Channels created"

    def update_channels_roles(self, server_id, column, role):
        reconnect_database(self.conn)
        query = f"UPDATE channels_roles SET {column} = %s WHERE server_id = %s"
        with self.conn.cursor() as cursor:
            cursor.execute(query, (role, server_id))
            self.conn.commit()

    async def add_channels_roles(self, guild):
        # This is a placeholder for whatever logic you want for channels/roles setup
        # You can expand this as needed
        await self.add_channels(guild)
        return "✅ Channels and roles set up"

    async def add_server(self, guild):
        reconnect_database(self.conn)
        server_id = guild.id
        server_name = guild.name
        owner = guild.owner_id
        new_minecraft_token = self.generate_random_token()
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT minecraft_token FROM servers WHERE server_id = %s", (server_id,))
                result = cursor.fetchone()
                existing_token = result[0] if result else None
                if existing_token:
                    update_sql = "UPDATE servers SET server_name = %s, minecraft_token = %s, owner = %s WHERE server_id = %s"
                    server_data = (server_name, new_minecraft_token, owner, server_id)
                    cursor.execute(update_sql, server_data)
                    update_users_sql = "UPDATE users SET token = %s WHERE token = %s"
                    cursor.execute(update_users_sql, (new_minecraft_token, existing_token))
                else:
                    insert_sql = "INSERT INTO servers (server_id, server_name, minecraft_token, owner) VALUES (%s, %s, %s, %s)"
                    server_data = (server_id, server_name, new_minecraft_token, owner)
                    cursor.execute(insert_sql, server_data)
                self.conn.commit()
                cursor.execute("SELECT COUNT(*) FROM channels_roles WHERE server_id = %s", (server_id,))
                if cursor.fetchone()[0] == 0:
                    insert_query = "INSERT INTO channels_roles (server_id, server_roles, server_channels) VALUES (%s, %s, %s)"
                    cursor.execute(insert_query, (server_id, "[]", "[]"))
                    self.conn.commit()
            datalog(self, 'setup', f"✅ Server data successfully added to MCSync. {server_id}")
            return new_minecraft_token
        except Exception as e:
            datalog(self, 'setup', f"🚨 An error occurred: {e} - {server_id}")
            self.conn.rollback()
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
        #channels_roles_status = await self.add_channels_roles(interaction.guild)
        embed.add_field(name="Server Token", value=f"||`{server_token}`|| ⬅️ Click to Show", inline=False)
        embed.add_field(name="Override Settings", value=override_status, inline=False)
        #embed.add_field(name="Channels and Roles", value=channels_roles_status, inline=False)
        embed.set_footer(text="MCSync • Server Setup")
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Setup(bot))
