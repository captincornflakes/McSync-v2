import discord
from discord.ext import commands
from discord import app_commands

class Utilities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = bot.db_connection  # Access the connection from the bot instance
        self.cursor = self.conn.cursor()

    @discord.app_commands.command(name="delete", description="(for dev)")
    @discord.app_commands.default_permissions(administrator=True)
    async def delete_server(self, interaction: discord.Interaction):
        server_id = interaction.guild.id
        self.cursor.execute("SELECT token FROM servers WHERE server_id = %s", (server_id,))
        result = self.cursor.fetchone()
        if result:
            token = result[0]
            mcsync_category = discord.utils.get(interaction.guild.categories, name="mcsync")
            if mcsync_category:
                for channel in mcsync_category.channels:
                    await channel.delete(reason="Deleting mcsync channels during server deletion.")
                await mcsync_category.delete(reason="Deleting mcsync category during server deletion.")
            self.cursor.execute("DELETE FROM users WHERE token = %s", (token,))
            self.cursor.execute("DELETE FROM channels_roles WHERE token = %s", (token,))
            self.cursor.execute("DELETE FROM servers WHERE server_id = %s", (server_id,))
            self.conn.commit()
            await interaction.response.send_message(f"Server, mcsync category, and all associated data have been deleted.", ephemeral=True)
        else:
            await interaction.response.send_message(f"No server found with ID {server_id}.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Utilities(bot))

