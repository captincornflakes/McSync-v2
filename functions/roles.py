import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Select
import _asyncio

class ServerRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = bot.db_connection  # Access the connection from the bot instance
        self.cursor = self.conn.cursor()
        self.roles = {
            "subscriber": "Twitch Subscriber",
            "tier_1": "Twitch Subscriber: Tier 1",
            "tier_2": "Twitch Subscriber: Tier 2",
            "tier_3": "Twitch Subscriber: Tier 3",
            "overide_role": "McSync Overide"
        }
   
    @app_commands.command(name="roles", description="Setup roles for users.")
    @app_commands.default_permissions(administrator=True)
    async def role_setup(self, ctx):
        embed = discord.Embed(
            title="Role Setup",
            description="Would you like to customize the role setup or use the default Discord roles?",
            color=discord.Color.blue()
        )
        embed.add_field(name="Customize", value="React with 🛠️ to customize the role setup.", inline=False)
        embed.add_field(name="Default", value="React with ✅ to use default Discord roles.", inline=False)
        message = await ctx.send(embed=embed)
        await message.add_reaction("🛠️")
        await message.add_reaction("✅")
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["🛠️", "✅"]
        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
            if str(reaction.emoji) == "🛠️":
                await ctx.send("You chose to customize the role setup.")
                await self.custom_role_setup(ctx)
            elif str(reaction.emoji) == "✅":
                await ctx.send("You chose to use the default Discord roles.")
                await self.default_role_setup(ctx)

        except asyncio.TimeoutError:
            await ctx.send("Role setup timed out. Please try again.")

    async def custom_role_setup(self, ctx):
        await ctx.send("Starting custom role setup...")
        # Custom role setup logic here

    async def default_role_setup(self, ctx):
        role_names = self.roles
        server_id = ctx.guild.id
        guild = ctx.guild
        query = "UPDATE channels_roles SET subscriber_role = %s, tier_1 = %s, tier_2 = %s, tier_3 = %s, overide_role = %s WHERE server_id = %s"
        self.cursor.execute(query, (role_names.get("subscriber_role"), role_names.get("tier_1"), role_names.get("tier_2"), role_names.get("tier_3"), role_names.get("overide_role"), server_id))
        self.conn.commit()
        await guild.create_role(name=role_names.get("overide_role"), reason="Role created by bot command")
        await ctx.send("Default Discord roles have been set up and stored in the database.")


async def setup(bot):
    await bot.add_cog(ServerRoles(bot))
