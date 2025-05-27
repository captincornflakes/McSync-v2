import discord
from discord.ext import commands

from utils.logger_utils import datalog
from utils.database_utils import reconnect_database, db_get

class TokenCog(commands.Cog):
     def __init__(self, bot):
          self.bot = bot
          self.conn = bot.db_connection  # Access the connection from the bot instance

     async def get_token_from_database(self, guild):
          reconnect_database(self.conn)
          server_id = guild.id
          try:
               result = db_get(
                    self.conn,
                    "SELECT minecraft_token FROM servers WHERE server_id = %s",
                    (server_id,),
                    fetchone=True
               )
               return result[0] if result else None
          except Exception as e:
               datalog(self.conn, 'token', f"Database error occurred while retrieving the token: {e} - {server_id}")
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
