import discord
from discord.ext import commands
import json
import secrets
import string

from utils.logger_utils import datalog
from utils.database_utils import reconnect_database, db_get, db_write, db_update, db_delete

class Listeners(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = bot.db_connection

    def generate_random_token(self, length=32):
        reconnect_database(self.conn)
        characters = string.ascii_letters + string.digits
        while True:
            token = ''.join(secrets.choice(characters) for _ in range(length))
            result = db_get(
                self.conn,
                "SELECT COUNT(*) FROM servers WHERE minecraft_token = %s",
                (token,),
                fetchone=True
            )
            if result and result[0] == 0:
                return token

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        reconnect_database(self.conn)
        guild_id = before.guild.id
        if before.roles != after.roles:
            roles = [{"name": role.name, "id": role.id} for role in after.roles if role.name != "@everyone"]
            roles_json = json.dumps(roles)
            try:
                db_update(self.conn, "UPDATE users SET roles = %s WHERE discord_id = %s", (roles_json, after.id))
            except Exception as e:
                datalog(self.conn, 'Listener', f"Failed to update roles in the database: {e}")
            try:
                db_update(self.conn, "UPDATE users SET discord_name = %s WHERE discord_id = %s", (after.name, after.id))
                datalog(self.conn, 'Listener', f"Member update - Server: {guild_id} User: {after.name} Roles: {roles_json}")
            except Exception as e:
                datalog(self.conn, 'Listener', f"Failed to update Discord name in the database: {e}")

    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        reconnect_database(self.conn)
        if before.name != after.name:
            guild_id = before.guild.id
            try:
                result = db_get(
                    self.conn,
                    "SELECT server_roles, subscriber_role, tier_1, tier_2, tier_3, override_role FROM channels_roles WHERE server_id = %s",
                    (guild_id,),
                    fetchone=True
                )
                if result:
                    server_roles, subscriber_role, tier_1, tier_2, tier_3, override_role = result
                    server_roles = json.loads(server_roles)
                    updated = False
                    for role in server_roles:
                        if role['id'] == before.id:
                            role['name'] = after.name
                            updated = True
                            break
                    if subscriber_role == before.name:
                        subscriber_role = after.name
                        datalog(self.conn, 'Listener', f"Server with ID {guild_id} updated subscriber role to {subscriber_role}.")
                        updated = True
                    if tier_1 == before.name:
                        tier_1 = after.name
                        datalog(self.conn, 'Listener', f"Server with ID {guild_id} updated tier_1 role to {tier_1}.")
                        updated = True
                    if tier_2 == before.name:
                        tier_2 = after.name
                        datalog(self.conn, 'Listener', f"Server with ID {guild_id} updated tier_2 role to {tier_2}.")
                        updated = True
                    if tier_3 == before.name:
                        tier_3 = after.name
                        datalog(self.conn, 'Listener', f"Server with ID {guild_id} updated tier_3 role to {tier_3}.")
                        updated = True
                    if override_role == before.name:
                        override_role = after.name
                        datalog(self.conn, 'Listener', f"Server with ID {guild_id} updated override_role role to {override_role}.")
                        updated = True
                    if updated:
                        updated_server_roles = json.dumps(server_roles)
                        db_update(
                            self.conn,
                            "UPDATE channels_roles SET server_roles = %s, subscriber_role = %s, tier_1 = %s, tier_2 = %s, tier_3 = %s, override_role = %s WHERE server_id = %s",
                            (updated_server_roles, subscriber_role, tier_1, tier_2, tier_3, override_role, guild_id)
                        )
            except Exception as e:
                datalog(self.conn, 'Listener', f"Failed to update server roles or tier roles in the database: {e}")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        reconnect_database(self.conn)
        server_id = member.guild.id
        user_id = member.id
        try:
            db_delete(self.conn, "DELETE FROM users WHERE server_id = %s AND user_id = %s", (server_id, user_id))
            datalog(self.conn, 'Listener', f"Member Deleted: {server_id} User: {user_id}")
            datalog(self.conn, 'Listener', f"User {member.name} (ID: {user_id}) removed from server {server_id}.")
        except Exception as e:
            datalog(self.conn, 'Listener', f"Failed to delete member from database: {e}")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        reconnect_database(self.conn)
        server_id = guild.id
        try:
            result = db_get(self.conn, "SELECT minecraft_token FROM servers WHERE server_id = %s", (server_id,), fetchone=True)
            if result:
                token = result[0]
                db_delete(self.conn, "DELETE FROM users WHERE token = %s", (token,))
                db_delete(self.conn, "DELETE FROM channels_roles WHERE server_id = %s", (server_id,))
                datalog(self.conn, 'Listener', f"Users with token {token} have been removed from the database.")
            db_delete(self.conn, "DELETE FROM servers WHERE server_id = %s", (server_id,))
            datalog(self.conn, 'Listener', f"Server with ID {server_id} has been removed from the database.")
        except Exception as e:
            datalog(self.conn, 'Listener', f"Error removing server with ID {server_id} from the database: {e}")

    @commands.Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild):
        reconnect_database(self.conn)
        try:
            server_id = after.id
            new_name = after.name
            new_owner_id = after.owner_id
            db_update(
                self.conn,
                "UPDATE servers SET server_name = %s, owner = %s WHERE server_id = %s",
                (new_name, new_owner_id, server_id)
            )
            datalog(self.conn, 'Listener', f"Updated server information for ID {server_id}.")
        except Exception as e:
            datalog(self.conn, 'Listener', f"Error updating server information for ID {server_id}: {e}")

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        reconnect_database(self.conn)
        try:
            server_id = guild.id
            server_name = guild.name
            minecraft_token = self.generate_random_token()
            owner = guild.owner_id
            db_write(
                self.conn,
                "INSERT INTO servers (server_id, server_name, minecraft_token, owner) VALUES (%s, %s, %s, %s)",
                (server_id, server_name, minecraft_token, owner)
            )
            datalog(self.conn, 'Listener', f"Server '{server_name}' (ID: {server_id}) has been added to the database.")
        except Exception as e:
            datalog(self.conn, 'Listener', f"Error adding server '{server_name}' (ID: {server_id}) to the database: {e}")

async def setup(bot):
    await bot.add_cog(Listeners(bot))
