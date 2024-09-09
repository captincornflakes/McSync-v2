import discord
from discord.ext import commands
from discord import app_commands

class TwitchIntegrationChecker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def is_twitch_integration_setup(self, guild: discord.Guild) -> bool:
        try:
            integrations = await guild.integrations()
            for integration in integrations:
                if isinstance(integration, discord.integration.TwitchIntegration):
                    print(f"Twitch integration found for guild: {guild.name}")
                    return True
            print(f"No Twitch integration found for guild: {guild.name}")
            return False

        except discord.Forbidden:
            print(f"Bot lacks permissions to view integrations for guild: {guild.name}")
            return False
        except Exception as e:
            print(f"Error checking Twitch integration for guild: {guild.name}: {e}")
            return False

    @discord.app_commands.command(name='check_twitch', description='Checks if Twitch integration is set up for the current server.')
    async def check_twitch_command(self, interaction: discord.Interaction):
        guild = interaction.guild
        if guild:
            integration_status = await self.is_twitch_integration_setup(guild)
            if integration_status:
                await interaction.response.send_message("Twitch integration is set up for this server.")
            else:
                await interaction.response.send_message("Twitch integration is not set up for this server.")
        else:
            await interaction.response.send_message("This command can only be used in a server.")

# Set up the cog
async def setup(bot):
    await bot.add_cog(TwitchIntegrationChecker(bot))
