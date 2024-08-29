import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Select
import os
import json
import secrets
import string

class ServerSetupCog(commands.Cog):
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
        """Generate a random string of letters and digits."""
        characters = string.ascii_letters + string.digits
        return ''.join(secrets.choice(characters) for i in range(length))
   
    @commands.command()
    async def add_server(self, guild):  
        try:
            server_id = guild.id
            server_name = guild.name
            icon = guild.icon_url if guild.icon else ""
            new_minecraft_token = self.generate_random_token()
            integrated = False
            owner = guild.owner_id
            users = len(guild.members)
            plus = False
            self.cursor.execute("SELECT minecraft_token FROM servers WHERE server_id = %s", (server_id,))
            result = self.cursor.fetchone()
            existing_token = result[0] if result else None
            if existing_token:
                update_sql = "UPDATE servers SET server_name = %s, minecraft_token = %s, integrated = %s, owner = %s, users = %s, icon = %s, plus = %s WHERE server_id = %s"
                server_data = (server_name, new_minecraft_token, integrated, owner, users, icon, plus, server_id)
                self.cursor.execute(update_sql, server_data)
            else:
                insert_sql = "INSERT INTO servers (server_id, server_name, minecraft_token, integrated, owner, users, icon, plus) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                server_data = (server_id, server_name, new_minecraft_token, integrated, owner, users, icon, plus)
                self.cursor.execute(insert_sql, server_data)
            if existing_token:
                update_users_sql = "UPDATE users SET token = %s WHERE token = %s"
                self.cursor.execute(update_users_sql, (new_minecraft_token, existing_token))
            self.conn.commit()
            print("Server data successfully added to the database.")
            return new_minecraft_token
        except Exception as e:
            print(f"An error occurred: {e}")
            self.conn.rollback()

    @commands.command()
    async def add_channels_roles(self, guild):  
        try:
            server_id = guild.id
            subscriber_role = self.roles['subscriber']
            tier_1 = self.roles['tier_1']
            tier_2 = self.roles['tier_2']
            tier_3 = self.roles['tier_3']
            overide_role = self.roles['overide_role']
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

            server_channels = []
            for channel in guild.channels:
                server_channels.append({
                    "channel_name": channel.name,
                    "channel_id": channel.id
                })
            server_channels_json = json.dumps(server_channels)
            category = discord.utils.get(guild.categories, name='McSync')
            notifications_channel = discord.utils.get(category.channels, name='notifications')
            notifications_channel_id = notifications_channel.id
            registrations_channel = discord.utils.get(category.channels, name='registrations')
            registrations_channel_id = registrations_channel.id
            self.cursor.execute("SELECT server_id FROM channels_roles WHERE server_id = %s", (server_id,))
            result = self.cursor.fetchone()
            existing = result[0] if result else None
            if existing:
                update_sql = "UPDATE channels_roles SET server_id = %s, subscriber_role = %s, tier_1 = %s, tier_2 = %s, tier_3 = %s, overide_role = %s, notifications = %s, registrations = %s, server_roles = %s, server_channels = %s WHERE server_id = %s"
                server_data = (server_id, subscriber_role, tier_1, tier_2, tier_3, overide_role, notifications_channel_id, registrations_channel_id, server_roles_json, server_channels_json, server_id)
                self.cursor.execute(update_sql, server_data)
            else:
                insert_sql = "INSERT INTO channels_roles (server_id, subscriber_role, tier_1, tier_2, tier_3, overide_role, notifications, registrations, server_roles, server_channels) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                server_data = (server_id, subscriber_role, tier_1, tier_2, tier_3, overide_role, notifications_channel_id, registrations_channel_id, server_roles_json, server_channels_json)
                self.cursor.execute(insert_sql, server_data)
            self.conn.commit()
            print("Saved server roles.")
            return "Saved server roles."
        except Exception as e:
            print(f"An error occurred: {e}")
            self.conn.rollback()
 
    @commands.command()
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

    @app_commands.command(name="setup", description="Sets up the server in the database and generate channels.")
    @app_commands.default_permissions(administrator=True)
    async def setup(self, interaction: discord.Interaction):
        print(f"Setup Called - {interaction.guild.name}.")
        token = await self.add_server(interaction.guild)
        await self.add_channels(interaction.guild)
        await self.add_channels_roles(interaction.guild)
        await interaction.response.send_message(f"Server setup complete. Token is {token}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ServerSetupCog(bot))
