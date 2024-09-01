import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Select
import os
import json
import secrets
import string

class Setup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = bot.db_connection  # Access the connection from the bot instance
        self.cursor = self.conn.cursor()
        self.roles = {
            "subscriber": "Twitch Subscriber",
            "tier_1": "Twitch Subscriber: Tier 1",
            "tier_2": "Twitch Subscriber: Tier 2",
            "tier_3": "Twitch Subscriber: Tier 3",
            "overide_role": "McSync Overide"
        }

    def generate_random_token(self, length=32):
        characters = string.ascii_letters + string.digits
        while True:
            token = ''.join(secrets.choice(characters) for _ in range(length))
            self.cursor.execute("SELECT COUNT(*) FROM servers WHERE minecraft_token = %s", (token,))
            if self.cursor.fetchone()[0] == 0:
                return token
            continue
   
    async def add_server(self, guild):  
        try:
            server_id = guild.id
            server_name = guild.name
            new_minecraft_token = self.generate_random_token()
            integrated = False
            owner = guild.owner_id
            users = len(guild.members)
            plus = False
            # Check if the server already exists
            self.cursor.execute("SELECT minecraft_token FROM servers WHERE server_id = %s", (server_id,))
            result = self.cursor.fetchone()
            existing_token = result[0] if result else None
            
            if existing_token:
                # Update existing server record
                update_sql = """
                    UPDATE servers 
                    SET server_name = %s, minecraft_token = %s, integrated = %s, owner = %s, users = %s, plus = %s 
                    WHERE server_id = %s
                """
                server_data = (server_name, new_minecraft_token, integrated, owner, users, plus, server_id)
                self.cursor.execute(update_sql, server_data)
            else:
                # Insert new server record
                insert_sql = """
                    INSERT INTO servers (server_id, server_name, minecraft_token, integrated, owner, users, plus) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                server_data = (server_id, server_name, new_minecraft_token, integrated, owner, users, plus)
                self.cursor.execute(insert_sql, server_data)
            
            # Update user tokens if the server already existed
            if existing_token:
                update_users_sql = "UPDATE users SET token = %s WHERE token = %s"
                self.cursor.execute(update_users_sql, (new_minecraft_token, existing_token))
        
            self.conn.commit()
            print("Server data successfully added to the database.")
            return new_minecraft_token
        except Exception as e:
            print(f"An error occurred: {e}")
            self.conn.rollback()

    async def add_channels_roles(self, guild: discord.Guild):
        try:
            server_id = guild.id

            # Retrieve roles from self.roles
            subscriber_role = self.roles.get('subscriber')
            tier_1 = self.roles.get('tier_1')
            tier_2 = self.roles.get('tier_2')
            tier_3 = self.roles.get('tier_3')
            override_role = self.roles.get('override_role')

            # Collect server roles
            server_roles = []
            for role in guild.roles:
                server_roles.append({
                    "name": role.name,
                    "id": role.id,
                    "permissions": role.permissions.value,
                    "color": role.color.value,
                    "managed": role.managed
                })
            server_roles_json = json.dumps(server_roles)

            # Collect server channels
            server_channels = []
            for channel in guild.channels:
                server_channels.append({
                    "channel_name": channel.name,
                    "channel_id": channel.id
                })
            server_channels_json = json.dumps(server_channels)

            # Get category and channels
            category = discord.utils.get(guild.categories, name='MCSync')
            if category:
                notifications_channel = discord.utils.get(category.channels, name='notifications')
                registrations_channel = discord.utils.get(category.channels, name='registrations')

                notifications_channel_id = notifications_channel.id if notifications_channel else None
                registrations_channel_id = registrations_channel.id if registrations_channel else None
            else:
                notifications_channel_id = None
                registrations_channel_id = None

            # Check if the server_id already exists in the database
            self.cursor.execute("SELECT server_id FROM channels_roles WHERE server_id = %s", (server_id,))
            result = self.cursor.fetchone()
            existing = result[0] if result else None

            if existing:
                # Update existing record
                update_sql = """
                    UPDATE channels_roles
                    SET subscriber_role = %s, tier_1 = %s, tier_2 = %s, tier_3 = %s, override_role = %s, 
                        notifications = %s, registrations = %s, server_roles = %s, server_channels = %s
                    WHERE server_id = %s
                """
                server_data = (
                    subscriber_role, tier_1, tier_2, tier_3, override_role, 
                    notifications_channel_id, registrations_channel_id, 
                    server_roles_json, server_channels_json, server_id
                )
                self.cursor.execute(update_sql, server_data)
            else:
                # Insert new record
                insert_sql = """
                    INSERT INTO channels_roles 
                    (server_id, subscriber_role, tier_1, tier_2, tier_3, override_role, 
                     notifications, registrations, server_roles, server_channels)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                server_data = (
                    server_id, subscriber_role, tier_1, tier_2, tier_3, override_role, 
                    notifications_channel_id, registrations_channel_id, 
                    server_roles_json, server_channels_json
                )
                self.cursor.execute(insert_sql, server_data)

            # Commit transaction
            self.conn.commit()
            print("Saved server roles.")
            return "Saved server roles."
        except Exception as e:
            print(f"An error occurred: {e}")
            self.conn.rollback()

 
    async def add_channels(self, guild):  
        category_name = 'McSync'
        category = discord.utils.get(guild.categories, name=category_name)
        if not category:
            category = await guild.create_category(category_name)
            overwrite = discord.PermissionOverwrite()
            overwrite.read_messages = False
            for role in guild.roles:
                if role.permissions.administrator:
                    await category.set_permissions(role, read_messages=True)
            await guild.create_text_channel('notifications', category=category)
            await guild.create_text_channel('registrations', category=category)

    @app_commands.command(name="setup", description="Setup your server with McSync.")
    @app_commands.default_permissions(administrator=True)
    async def setup(self, interaction: discord.Interaction):
        print(f"Setup Called - {interaction.guild.name}.")
        token = await self.add_server(interaction.guild)
        await self.add_channels(interaction.guild)
        await self.add_channels_roles(interaction.guild)
        await interaction.response.send_message(f"Server setup complete. Token is {token}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Setup(bot))
