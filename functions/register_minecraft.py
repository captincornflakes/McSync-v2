import discord
from discord.ext import commands
import aiohttp
import json

import requests
from utils.logger_utils import datalog
from utils.database_utils import reconnect_database  # <-- Add this import
    
class MinecraftNameCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = bot.db_connection
        self.cursor = self.conn.cursor()

    
    async def get_uuid(self, minecraftname):
        url_main = f"https://api.mojang.com/users/profiles/minecraft/{minecraftname}"
        url_fallback = f"https://api.ashcon.app/mojang/v2/user/{minecraftname}"
        async with aiohttp.ClientSession() as session:
            # Try the main URL
            async with session.get(url_main) as response:
                if response.status == 200:
                    data = await response.json()
                    print(data)
                    return data['id']
            # If the main URL fails, try the fallback URL
            async with session.get(url_fallback) as response:
                if response.status == 200:
                    data = await response.json()
                    print(data['uuid'].replace('-', ''))
                    return data['uuid'].replace('-', '')
        # If both fail, return None
        return None

    async def get_server(self, server_id):
        reconnect_database(self.conn)
        with self.conn.cursor() as cursor:
            cursor.execute('SELECT minecraft_token FROM servers WHERE server_id = %s', (server_id,))
            result = cursor.fetchone()
        return result[0] if result else None
    
    
    async def add_minecraft(self, guild, minecraftname, user):
        reconnect_database(self.conn)
        try:
            token = await self.get_server(guild.id)
            minecraft_name = minecraftname
            minecraft_uuid = await self.get_uuid(minecraftname)
            discord_name = user.name
            discord_id = user.id
            created = ""
            lastcon = ""
            roles = [{"name": role.name, "id": role.id} for role in user.roles if role.name != "@everyone"]
            roles_json = json.dumps(roles) 
            if not minecraft_uuid:
                return "Failed to register. The username is invalid."
            if not token:
                return "Failed to register. MCSync has not been configured for this server yet!"
            with self.conn.cursor() as cursor:
                cursor.execute('SELECT COUNT(*) FROM users WHERE discord_id = %s AND token = %s', (discord_id, token))
                exists = cursor.fetchone()[0]
                if exists:
                    message = f"{minecraft_name} updated successfully."
                    sql = "UPDATE users SET minecraft_name = %s, minecraft_uuid = %s, roles = %s WHERE discord_id = %s AND token = %s"
                    cursor.execute(sql, (minecraft_name, minecraft_uuid, roles_json, discord_id, token))
                else:
                    message = f"{minecraft_name} successfully added to MCSync."
                    sql = "INSERT INTO users (token, minecraft_name, minecraft_uuid, discord_name, discord_id, roles, created, lastcon) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                    cursor.execute(sql, (token, minecraft_name, minecraft_uuid, discord_name, discord_id, roles_json, created, lastcon))
                self.conn.commit()
            datalog(self, 'register', message)
            return message
        except Exception as e:
            datalog(self, 'register', f"An error occurred: {e}")
            print(f"An error occurred: {e}")
            self.conn.rollback()  
            return "Registration failed, a database error occured."

    @discord.app_commands.command(name="mcsync", description="Register your Minecraft Username with MCSync to this server.")
    async def mcsync(self, interaction: discord.Interaction, minecraftname: str):
        result = await self.add_minecraft(interaction.guild, minecraftname, interaction.user)
        embed = discord.Embed(
            title="MCSync Registration",
            description=f"{result}" if result else "An error occurred.",
            color=discord.Color.green() if "successfully" in result.lower() else discord.Color.red()
            )
        embed.set_footer(text="MCSync Bot • Minecraft Registration")
        embed.set_thumbnail(url=f"https://api.mcheads.org/ioshead/{minecraftname}") 
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(MinecraftNameCog(bot))
