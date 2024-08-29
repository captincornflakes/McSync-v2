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
        if before.roles != after.roles:
            roles = [{"name": role.name, "id": role.id} for role in after.roles if role.name != "@everyone"]
            roles_json = json.dumps(roles)  # Convert roles list to JSON string
            query = "UPDATE users SET roles = %s WHERE discord_id = %s"
            try:
                self.cursor.execute(query, (roles_json, after.id))
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

    
    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        if before.name != after.name:
            guild_id = before.guild.id
            query = "SELECT server_roles, subscriber_role, tier_1, tier_2, tier_3 FROM channels_roles WHERE server_id = %s"
            self.cursor.execute(query, (guild_id,))
            result = self.cursor.fetchone()
            if result:
                server_roles, subscriber_role, tier_1, tier_2, tier_3 = result
                server_roles = json.loads(server_roles)
                updated = False
                for role in server_roles:
                    if role['id'] == before.id:
                        role['name'] = after.name
                        updated = True
                        break
                if subscriber_role == before.name:
                    subscriber_role = after.name
                    updated = True
                if tier_1 == before.name:
                    tier_1 = after.name
                    updated = True
                if tier_2 == before.name:
                    tier_2 = after.name
                    updated = True
                if tier_3 == before.name:
                    tier_3 = after.name
                    updated = True
                if updated:
                    updated_server_roles = json.dumps(server_roles)
                    update_query = "UPDATE channels_roles SET server_roles = %s, subscriber_role = %s, tier_1 = %s, tier_2 = %s, tier_3 = %s WHERE server_id = %s"
                    try:
                        self.cursor.execute(update_query, (updated_server_roles, subscriber_role, tier_1, tier_2, tier_3, guild_id))
                        self.conn.commit()
                    except Exception as e:
                        print(f"Failed to update server roles or tier roles in the database: {e}")
                        self.conn.rollback()


async def setup(bot):
    await bot.add_cog(RoleUpdate(bot))
