import discord
from discord.ext import commands

class UpdateDatabase(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = bot.db_connection  # Access the connection from the bot instance
        self.cursor = self.conn.cursor()

    @commands.Cog.listener()
    async def on_ready(self):
        await self.update_users()

    def get_guild_id_by_token(self, token):
        query = "SELECT server_id FROM servers WHERE minecraft_token = %s"
        self.cursor.execute(query, (token,))
        result = self.cursor.fetchone()
        if result:
            return result['server_id']
        return None


    async def update_users(self):
        guild = self.bot.get_guild(YOUR_GUILD_ID)  # Replace with your server's ID
        if guild:
            for member in guild.members:
                roles = [role.id for role in member.roles]
                discord_name = member.name

                # Update the database with roles and Discord name
                query = """
                UPDATE users
                SET roles = %s, discord_name = %s
                WHERE discord_id = %s
                """
                params = (str(roles), discord_name, member.id)
                
                self.bot.cursor.execute(query, params)
                self.bot.conn.commit()

async def setup(bot):
    await bot.add_cog(UpdateDatabase(bot))
