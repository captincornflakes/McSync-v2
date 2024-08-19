import discord
from discord import app_commands
from discord.ext import commands
import os
import json

class ServerSetupCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def load_data(self, filename):
        try:
            with open(f'datastores/{filename}', 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            return None
        
    async def ensure_datastores_directory(self):
        if not os.path.exists('datastores'):
            os.makedirs('datastores')

    def generate_server_json(self, guild):
        """Generate a JSON file with the server ID as the name."""
        server_data = {
            "server_name": guild.name,
            "server_id": guild.id,
            "roles": [],
            "channels": []
        }
        
        for role in guild.roles:
            server_data["roles"].append({
                "name": role.name,
                "id": role.id,
                "permissions": role.permissions.value
            })
        
        json_path = os.path.join('datastores', f'{guild.id}.json')
        
        with open(json_path, 'w') as f:
            json.dump(server_data, f, indent=4)

    @app_commands.command(name="setup_server", description="Sets up the server by generating a JSON file with roles and channels.")
    @app_commands.default_permissions(administrator=True)
    async def setup_server(self, interaction: discord.Interaction):
        """Sets up the server by generating a JSON file with the server's roles and channels."""
        await self.ensure_datastores_directory()
        self.generate_server_json(interaction.guild)
        await interaction.response.send_message(f"Server setup complete! JSON file created for `{interaction.guild.name}`.", ephemeral=True)

   
    @app_commands.command(name="delete_server", description="Deletes the JSON file for the server.")
    @app_commands.default_permissions(administrator=True)
    async def delete_server(self, interaction: discord.Interaction):
        server_id = interaction.guild.id
        filename = f'datastores/{server_id}.json'
        if os.path.exists(filename):
            os.remove(filename)
            await interaction.send(f"The JSON file for server ID {server_id} has been deleted.", ephemeral=True)
        else:
            await interaction.send(f"No JSON file found for server ID {server_id}.", ephemeral=True)


    @commands.Cog.listener()
    async def on_ready(self):
        guilds = [guild.id for guild in self.bot.guilds]
        await self.bot.tree.sync(guild=guilds[0])

async def setup(bot):
    await bot.add_cog(ServerSetupCog(bot))
