import discord
from discord.ext import commands
from discord import app_commands

class Utilities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="clear", description="Clears a number of messages from the channel, including bot messages.")
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

# Setup function to add the cog to the bot
async def setup(bot):
    await bot.add_cog(Utilities(bot))

