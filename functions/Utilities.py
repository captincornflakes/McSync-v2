import discord
from discord.ext import commands
from discord import app_commands

class Utilities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = bot.db_connection  # Access the connection from the bot instance
        self.cursor = self.conn.cursor()

    @app_commands.command(name="clear", description="(for dev)")
    @app_commands.default_permissions(administrator=True)
    async def clear(self, interaction: discord.Interaction, amount: int = 100):
        """
        Clears a number of messages from the channel, including bot messages.
        Usage: /clear <number>
        """
        if amount <= 0:
            await interaction.response.send_message("Please specify a positive number of messages to delete.", ephemeral=True)
            return

        await interaction.response.send_message(f"Deleting {amount} messages...", ephemeral=True)
        await interaction.original_response().delete()  # Delete the command message

        messages = [message async for message in interaction.channel.history(limit=amount + 1)]

        for message in messages:
            try:
                await message.delete()
            except discord.Forbidden:
                await interaction.followup.send("I don't have permission to delete some messages.", ephemeral=True)
                return
            except discord.HTTPException as e:
                await interaction.followup.send(f"Failed to delete some messages: {e}", ephemeral=True)
                return

        await interaction.followup.send(f"Deleted {amount} messages.", ephemeral=True)




   
    @discord.app_commands.command(name="delete", description="(for dev)")
    @discord.app_commands.default_permissions(administrator=True)
    async def delete_server(self, interaction: discord.Interaction):
        server_id = interaction.guild.id

        # Get the server token
        self.cursor.execute("SELECT token FROM servers WHERE server_id = %s", (server_id,))
        result = self.cursor.fetchone()
        if result:
            token = result[0]

            # Delete all channels under the mcsync category and the category itself
            mcsync_category = discord.utils.get(interaction.guild.categories, name="mcsync")
            if mcsync_category:
                for channel in mcsync_category.channels:
                    await channel.delete(reason="Deleting mcsync channels during server deletion.")
                await mcsync_category.delete(reason="Deleting mcsync category during server deletion.")
            
            # Delete entries from users and channels_roles based on the token
            self.cursor.execute("DELETE FROM users WHERE token = %s", (token,))
            self.cursor.execute("DELETE FROM channels_roles WHERE token = %s", (token,))

            # Delete the server from the servers table
            self.cursor.execute("DELETE FROM servers WHERE server_id = %s", (server_id,))

            # Commit the changes to the database
            self.conn.commit()

            await interaction.response.send_message(f"Server, mcsync category, and all associated data have been deleted.", ephemeral=True)
        else:
            await interaction.response.send_message(f"No server found with ID {server_id}.", ephemeral=True)


# Setup function to add the cog to the bot
async def setup(bot):
    await bot.add_cog(Utilities(bot))

