import discord
from discord.ext import commands
import aiohttp
import json

class MinecraftNameCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = bot.db_connection  # Access the connection from the bot instance
        self.cursor = self.conn.cursor()

    async def get_uuid(self, minecraftname):
        """Fetch the UUID of a Minecraft username using Mojang's API."""
        url = f"https://api.mojang.com/users/profiles/minecraft/{minecraftname}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['id']  # Return the UUID from the response data
                else:
                    return None

    async def get_server(self, server_id):
        """Fetch the Minecraft token for a specific server."""
        self.cursor.execute('SELECT minecraft_token FROM servers WHERE server_id = %s', (server_id,))
        result = self.cursor.fetchone()
        return result[0] if result else None
    
    async def add_minecraft(self, guild, minecraftname, user):
        """Add or update a Minecraft account in the server's registration in the database."""
        try:
            token = await self.get_server(guild.id)
            minecraft_name = minecraftname
            minecraft_uuid = await self.get_uuid(minecraftname)
            discord_name = user.name
            discord_id = user.id

            # Gather the user's roles
            roles = [{"name": role.name, "id": role.id} for role in user.roles if role.name != "@everyone"]
            roles_json = json.dumps(roles)  # Convert roles list to JSON string


            if not token or not minecraft_uuid:
                return "Failed to register. Missing token or Minecraft UUID."

            # Check if the record already exists
            self.cursor.execute('SELECT COUNT(*) FROM users WHERE discord_id = %s AND token = %s', (discord_id, token))
            exists = self.cursor.fetchone()[0]

            if exists:
                # Update the existing record
                sql = "UPDATE users SET minecraft_name = %s, minecraft_uuid = %s, roles = %s WHERE discord_id = %s AND token = %s"
                self.cursor.execute(sql, (minecraft_name, minecraft_uuid, roles_json, discord_id, token))
                message = "Record updated successfully."
            else:
                # Insert a new record
                sql = "INSERT INTO users (token, minecraft_name, minecraft_uuid, discord_name, discord_id, roles) VALUES (%s, %s, %s, %s, %s, %s)"
                self.cursor.execute(sql, (token, minecraft_name, minecraft_uuid, discord_name, discord_id, roles_json))
                message = "User successfully added to the database."

            self.conn.commit()
            print(message)
            return message

        except Exception as e:
            print(f"An error occurred: {e}")
            self.conn.rollback()  # Rollback in case of error
            return "Registration failed due to a database error."

    @discord.app_commands.command(name="mcsync", description="Register a Minecraft name to the current token.")
    async def mcsync(self, interaction: discord.Interaction, minecraftname: str):
        result = await self.add_minecraft(interaction.guild, minecraftname, interaction.user)
        await interaction.response.send_message(
            f"{result}" if result else "Error.",
            ephemeral=True
        )

# Setup function to add the cog to the bot
async def setup(bot):
    await bot.add_cog(MinecraftNameCog(bot))
