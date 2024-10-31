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
        return ''.join(secrets.choice(characters) for _ in range(length))

    async def update_json_and_database_with_token(self, guild):
        server_id = guild.id
        new_token = self.generate_random_token()

        try:
            self.cursor.execute("SELECT minecraft_token FROM servers WHERE server_id = %s", (server_id,))
            result = self.cursor.fetchone()
            existing_token = result[0] if result else None

            if existing_token:
                update_sql = "UPDATE servers SET minecraft_token = %s WHERE server_id = %s"
                self.cursor.execute(update_sql, (new_token, server_id))

                # Update users table where the token matches the existing server token
                update_users_sql = "UPDATE users SET token = %s WHERE token = %s"
                self.cursor.execute(update_users_sql, (new_token, existing_token))
            else:
                insert_sql = "INSERT INTO servers (server_id, minecraft_token) VALUES (%s, %s)"
                self.cursor.execute(insert_sql, (server_id, new_token))
            
            self.conn.commit()
            return new_token

        except Exception as e:
            self.conn.rollback()
            print(f"Database error occurred: {e}")
            return None

    @discord.app_commands.command(name="token", description="Generates a new Minecraft token. Place this token in the plugins config folder.")
    @discord.app_commands.default_permissions(administrator=True)
    async def token(self, interaction: discord.Interaction):
        new_token = await self.update_json_and_database_with_token(interaction.guild)
        
        if new_token:
            # Create an embed with the generated token
            embed = discord.Embed(
                title="New Minecraft Token Generated",
                description="A new Minecraft token has been successfully generated and stored.",
                color=discord.Color.blue()
            )
            embed.add_field(name="Minecraft Token", value=f"`{new_token}`", inline=False)
            embed.set_footer(text="Place this token in the plugins config folder for activation.")
            
            # Send the embed as the response
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            error_embed = discord.Embed(
                title="Token Generation Failed",
                description="An error occurred while generating the Minecraft token. Please try again later.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

# Setup function to add the cog to the bot
async def setup(bot):
    await bot.add_cog(TokenCog(bot))
