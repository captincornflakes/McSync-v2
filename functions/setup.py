import json
import discord
from discord.ext import commands
from discord import app_commands
import string
import secrets

class Setup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = bot.db_connection  # Assuming the connection is passed from the bot
        self.cursor = self.conn.cursor()
        self.override_role = "MCSync Override"
        self.category_name = "MCSync"
        self.subscriber = bot.subscriber
        self.tier_1 = bot.tier_1
        self.tier_2 = bot.tier_2
        self.tier_3 = bot.tier_3

    def generate_random_token(self, length=32):
        """Generate a unique 32-character Minecraft token."""
        characters = string.ascii_letters + string.digits
        while True:
            token = ''.join(secrets.choice(characters) for _ in range(length))
            # Ensure token is unique by checking the database
            self.cursor.execute("SELECT COUNT(*) FROM servers WHERE minecraft_token = %s", (token,))
            if self.cursor.fetchone()[0] == 0:
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
        query = f"UPDATE channels_roles SET {column} = %s WHERE server_id = %s"
        self.cursor.execute(query, (role, server_id))
        self.conn.commit()

    async def add_channels_roles(self, guild):
        try:
            server_id = guild.id
            server_roles = []
            notifications = ""
            registrations = ""
            subscriber = ""
            tier_1 = ""
            tier_2 = ""
            tier_3 = ""
            for role in guild.roles:
                server_roles.append({"name": role.name, "id": role.id, "managed": role.managed})
                if role.name == self.subscriber:
                    subscriber = role.name
                if role.name == self.tier_1:
                    tier_1 = role.name
                if role.name == self.tier_2:
                    tier_2 = role.name
                if role.name == self.tier_3:
                    tier_3 = role.name
                    
            server_roles_json = json.dumps(server_roles)
            server_channels = []
            for channel in guild.channels:
                if channel.type not in {discord.ChannelType.voice, discord.ChannelType.category}:
                    server_channels.append({"channel_name": channel.name, "channel_id": channel.id})
                    if channel.name == "notifications":
                        notifications = channel.id
                    if channel.name == "registrations":
                        registrations = channel.id
            server_channels_json = json.dumps(server_channels)
            update_sql = "UPDATE channels_roles SET subscriber_role = %s, tier_1 = %s, tier_2 = %s, tier_3 = %s, notifications = %s, registrations = %s, override_role = %s, server_roles = %s, server_channels = %s WHERE server_id = %s"
            server_data = ( subscriber, tier_1, tier_2, tier_3, notifications, registrations, self.override_role, server_roles_json, server_channels_json, server_id)
            self.cursor.execute(update_sql, server_data)
            self.conn.commit()
            if subscriber == "" or tier_1 == "" or tier_2 == "" or tier_3 == "":
                return "🚨 Twitch Integration roles are not the default, Please run /roles to select roles."
            else:
                return "✅ We've detected the roles as the default roles that Twitch creates"
        except Exception as e:
            self.conn.rollback()
            return "An error occurred saving roles."

    async def add_server(self, guild):  
        try:
            server_id = guild.id
            server_name = guild.name
            owner = guild.owner_id
            new_minecraft_token = self.generate_random_token()
            self.cursor.execute("SELECT minecraft_token FROM servers WHERE server_id = %s", (server_id,))
            result = self.cursor.fetchone()
            existing_token = result[0] if result else None
            if existing_token:
                update_sql = "UPDATE servers SET server_name = %s, minecraft_token = %s, owner = %s WHERE server_id = %s"
                server_data = (server_name, new_minecraft_token, owner, server_id)
                self.cursor.execute(update_sql, server_data)
                update_users_sql = "UPDATE users SET token = %s WHERE token = %s"
                self.cursor.execute(update_users_sql, (new_minecraft_token, existing_token))
            else:
                insert_sql = "INSERT INTO servers (server_id, server_name, minecraft_token, owner) VALUES (%s, %s, %s, %s)"
                server_data = (server_id, server_name, new_minecraft_token, owner)
                self.cursor.execute(insert_sql, server_data)
            self.conn.commit()
            query = "SELECT COUNT(*) FROM channels_roles WHERE server_id = %s"
            self.cursor.execute(query, (server_id,))
            if self.cursor.fetchone()[0] == 0:
                insert_query = "INSERT INTO channels_roles (server_id, server_roles, server_channels) VALUES (%s, %s, %s)"
                self.cursor.execute(insert_query, (server_id, "[]", "[]"))
                self.conn.commit()
            print("✅ Server data successfully added to MCSync.")
            return new_minecraft_token
        except Exception as e:
            print(f"🚨 An error occurred: {e}")
            self.conn.rollback()

        #await interaction.followup.send(f"{await self.add_channels(interaction.guild)}", ephemeral=True)
    @discord.app_commands.command(name="setup", description="Setup your server with MCSync.")
    @discord.app_commands.default_permissions(administrator=True)
    async def setup(self, interaction: discord.Interaction):
        # Initial response embed
        embed = discord.Embed(
            title="Server Setup Completed",
            description="Your server has been set up with the following settings:",
            color=discord.Color.green()
        )
        # Gather setup information
        server_token = await self.add_server(interaction.guild)
        override_status = await self.add_override(interaction.guild)
        channels_roles_status = await self.add_channels_roles(interaction.guild)
        # Append each step's result as a field
        embed.add_field(name="Server Token", value=f"||`{server_token}`|| ⬅️ Click to Show", inline=False)
        embed.add_field(name="Override Settings", value=override_status, inline=False)
        embed.add_field(name="Channels and Roles", value=channels_roles_status, inline=False)
        embed.set_footer(text="MCSync • Server Setup")
        # Send the embed as a single response
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Setup(bot))
