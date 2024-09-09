import discord
from discord.ext import commands
import json
import secrets
import string
import os

class TokenCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = bot.db_connection  # Access the connection from the bot instance
        self.cursor = self.conn.cursor()

    def generate_random_token(self, length=32):
        characters = string.ascii_letters + string.digits
        return ''.join(secrets.choice(characters) for i in range(length))

    async def update_json_and_database_with_token(self, guild):
        server_id = guild.id
        new_token = self.generate_random_token()
        self.cursor.execute("SELECT token FROM servers WHERE server_id = %s", (server_id,))
        result = self.cursor.fetchone()
        existing_token = result[0] if result else None

        if existing_token:
            update_sql = "UPDATE servers SET token = %s WHERE server_id = %s"
            self.cursor.execute(update_sql, (new_token, server_id))
            # Update users table where the token matches the existing server token
            update_users_sql = "UPDATE users SET minecraft_token = %s WHERE minecraft_token = %s"
            self.cursor.execute(update_users_sql, (new_token, existing_token))
        else:
            insert_sql = """
                INSERT INTO servers 
                (server_id, token) 
                VALUES (%s, %s)
            """
            self.cursor.execute(insert_sql, (server_id, new_token))
        self.conn.commit()
        return new_token

    @discord.app_commands.command(name="token", description="Generates a new Minecraft token. Place this token in the plugins config folder.")
    @discord.app_commands.default_permissions(administrator=True)
    async def token(self, interaction: discord.Interaction):
        new_token = await self.update_json_and_database_with_token(interaction.guild)
        await interaction.response.send_message(f"A new Minecraft token has been generated and stored: `{new_token}`", ephemeral=True)

# Setup function to add the cog to the bot
async def setup(bot):
    await bot.add_cog(TokenCog(bot))
