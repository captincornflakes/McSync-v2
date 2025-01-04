import discord
from discord.ext import commands
import json
import secrets
import string

class Listeners(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = bot.db_connection
        self.cursor = self.conn.cursor()

    def reconnect_database(self):
        try:
            self.conn.ping(reconnect=True, attempts=3, delay=5)
        except Exception as e:
            print(f"Error reconnecting to the database: {e}")
            
    def generate_random_token(self, length=32):
        self.reconnect_database()
        characters = string.ascii_letters + string.digits
        while True:
            token = ''.join(secrets.choice(characters) for _ in range(length))
            self.cursor.execute("SELECT COUNT(*) FROM servers WHERE minecraft_token = %s", (token,))
            if self.cursor.fetchone()[0] == 0:
                return token
            continue

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        self.reconnect_database()
        guild_id = before.guild.id
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
                
                print(f"Member update - Server: {guild_id} User: {after.name} Roles: {roles_json}")
                self.conn.commit()
            except Exception as e:
                print(f"Failed to update Discord name in the database: {e}")
                self.conn.rollback()
    
    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        self.reconnect_database()
        if before.name != after.name:
            guild_id = before.guild.id
            query = "SELECT server_roles, subscriber_role, tier_1, tier_2, tier_3, override_role FROM channels_roles WHERE server_id = %s"
            self.cursor.execute(query, (guild_id,))
            result = self.cursor.fetchone()
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
                    print(f"Server with ID {guild_id} updated subscriber role to {subscriber_role}.")
                    updated = True
                if tier_1 == before.name:
                    tier_1 = after.name
                    print(f"Server with ID {guild_id} updated tier_1 role to {tier_1}.")
                    updated = True
                if tier_2 == before.name:
                    tier_2 = after.name
                    print(f"Server with ID {guild_id} updated tier_2 role to {tier_2}.")
                    updated = True
                if tier_3 == before.name:
                    tier_3 = after.name
                    print(f"Server with ID {guild_id} updated tier_3 role to {tier_3}.")
                    updated = True
                if override_role == before.name:
                    override_role = after.name
                    print(f"Server with ID {guild_id} updated override_role role to {override_role}.")
                    updated = True
                if updated:
                    updated_server_roles = json.dumps(server_roles)
                    update_query = "UPDATE channels_roles SET server_roles = %s, subscriber_role = %s, tier_1 = %s, tier_2 = %s, tier_3 = %s, override_role = %s WHERE server_id = %s"
                    try:
                        self.cursor.execute(update_query, (updated_server_roles, subscriber_role, tier_1, tier_2, tier_3, override_role, guild_id))
                        self.conn.commit()
                    except Exception as e:
                        print(f"Failed to update server roles or tier roles in the database: {e}")
                        self.conn.rollback()

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        self.reconnect_database()
        server_id = member.guild.id
        user_id = member.id
        self.cursor.execute("DELETE FROM users WHERE server_id = %s AND user_id = %s", (server_id, user_id))
        print(f"Member Deleted: {server_id} User: {user_id}")
        self.conn.commit()
        print(f"User {member.name} (ID: {user_id}) removed from server {server_id}.")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        self.reconnect_database()
        try:
            server_id = guild.id
            self.cursor.execute("SELECT minecraft_token FROM servers WHERE server_id = %s", (server_id,))
            result = self.cursor.fetchone()
            if result:
                token = result[0]
                self.cursor.execute("DELETE FROM users WHERE token = %s", (token,))
                self.cursor.execute("DELETE FROM channels_roles WHERE server_id = %s", (server_id,))
                print(f"Users with token {token} have been removed from the database.")
            self.cursor.execute("DELETE FROM servers WHERE server_id = %s", (server_id,))
            self.conn.commit()
            print(f"Server with ID {server_id} has been removed from the database.")
        except Exception as e:
            print(f"Error removing server with ID {server_id} from the database: {e}")

    @commands.Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild):
        self.reconnect_database()
        try:
            server_id = after.id
            new_name = after.name
            new_owner_id = after.owner_id
            update_sql = "UPDATE servers SET server_name = %s, owner = %s WHERE server_id = %s"
            update_data = (new_name, new_owner_id, server_id)
            self.cursor.execute(update_sql, update_data)
            self.conn.commit()
            print(f"Updated server information for ID {server_id}.")
        except Exception as e:
            print(f"Error updating server information for ID {server_id}: {e}")
            self.conn.rollback()

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        self.reconnect_database()
        try:
            server_id = guild.id
            server_name = guild.name
            minecraft_token = self.generate_random_token()
            owner = guild.owner_id
            insert_sql = "INSERT INTO servers (server_id, server_name, minecraft_token, owner) VALUES (%s, %s, %s, %s)"
            server_data = (server_id, server_name, minecraft_token, owner)
            self.cursor.execute(insert_sql, server_data)
            self.conn.commit()
            print(f"Server '{server_name}' (ID: {server_id}) has been added to the database.")
        except Exception as e:
            print(f"Error adding server '{server_name}' (ID: {server_id}) to the database: {e}")

async def setup(bot):
    await bot.add_cog(Listeners(bot))
