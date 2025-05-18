import discord
from discord.ext import commands

from utils.logger_utils import datalog

class TokenCog(commands.Cog):
     def __init__(self, bot):
          self.bot = bot
          self.conn = bot.db_connection  # Access the connection from the bot instance
          self.cursor = self.conn.cursor()

     def reconnect_database(self):
          try:
               self.conn.ping(reconnect=True, attempts=3, delay=5)
          except Exception as e:
               print(f"Error reconnecting to the database: {e}")
               
     async def get_token_from_database(self, guild):
          self.reconnect_database()
          server_id = guild.id

          try:
               # Query to fetch the existing token
               self.cursor.execute("SELECT minecraft_token FROM servers WHERE server_id = %s", (server_id,))
               result = self.cursor.fetchone()
               return result[0] if result else None  # Return the token if found, otherwise None
          except Exception as e:
               datalog(self, 'token', f"Database error occurred while retrieving the token: {e} - {server_id}")
               return None

     @discord.app_commands.command(name="token", description="Retrieves the Minecraft token for the server.")
     @discord.app_commands.default_permissions(administrator=True)
     async def token(self, interaction: discord.Interaction):
          token = await self.get_token_from_database(interaction.guild)
          if token:
               embed = discord.Embed(
               title="Minecraft Token",
               description="Here is the Minecraft token for this server.",
               color=discord.Color.blue()
               )
               embed.add_field(name="Minecraft Token", value=f"`{token}`", inline=False)
               embed.set_footer(text="Ensure this token is placed in the plugin's config folder.")
               await interaction.response.send_message(embed=embed, ephemeral=True)
          else:
               error_embed = discord.Embed(
               title="Token Not Found",
               description="No Minecraft token was found for this server in the database.",
               color=discord.Color.red()
               )
               await interaction.response.send_message(embed=error_embed, ephemeral=True)

# Setup function to add the cog to the bot
async def setup(bot):
     await bot.add_cog(TokenCog(bot))
