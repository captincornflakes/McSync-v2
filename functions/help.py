import discord
from discord.ext import commands

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="helpme")
    async def help_command(self, ctx):
        # Create an embed for the help message
        embed = discord.Embed(
            title="Bot Commands",
            description="Here is a list of available commands:",
            color=discord.Color.blue()
        )

        # Loop through all the commands and add them to the embed
        for command in self.bot.commands:
            embed.add_field(name=command.name, value=command.help or "No description", inline=False)

        # Add links to the embed
        embed.add_field(name="Discord Server", value="[Join our Discord](https://your-discord-link)", inline=False)
        embed.add_field(name="Website", value="[Visit our Website](https://your-website-link)", inline=False)

        # Send the embed
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(HelpCog(bot))
