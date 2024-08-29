import discord
from discord.ext import commands
import json

class RoleUpdate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = bot.db_connection
        self.cursor = self.conn.cursor()

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        # Check if roles have changed
        
        print(f"Updating Roles.")
        if before.roles != after.roles:
            # Get the list of role IDs after the update
            role_ids = [role.id for role in after.roles]

            # Convert the list of role IDs to a JSON string
            role_ids_json = json.dumps(role_ids)

            # Update the roles in the database
            query = "UPDATE users SET roles = %s WHERE discord_id = %s"
            try:
                self.cursor.execute(query, (role_ids_json, after.id))
                self.conn.commit()
            except Exception as e:
                print(f"Failed to update roles in the database: {e}")
                self.conn.rollback()

            query_name = "UPDATE users SET discord_name = %s WHERE discord_id = %s"
            try:
                self.cursor.execute(query_name, (after.name, after.id))
                self.conn.commit()
            except Exception as e:
                print(f"Failed to update Discord name in the database: {e}")
                self.conn.rollback()

async def setup(bot):
    await bot.add_cog(RoleUpdate(bot))
