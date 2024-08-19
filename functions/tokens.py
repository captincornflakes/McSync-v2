import discord
from discord.ext import commands
import json
import secrets
import string
import os

class TokenCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def generate_random_token(self, length=32):
        """Generate a random string of letters and digits."""
        characters = string.ascii_letters + string.digits
        return ''.join(secrets.choice(characters) for i in range(length))

    async def update_json_with_token(self, guild):
        """Update the server JSON file with a new token and rename the old token file if necessary."""
        server_id = guild.id
        server_filename = f'datastores/{server_id}.json'
        new_token = self.generate_random_token()
        if os.path.exists(server_filename):
            with open(server_filename, 'r') as file:
                data = json.load(file)
        else:
            data = {}

        old_token = data.get('minecraft_token')
        data['minecraft_token'] = new_token
        with open(server_filename, 'w') as file:
            json.dump(data, file, indent=4)
        if old_token:
            old_token_filename = f'datastores/{old_token}.json'
            if os.path.exists(old_token_filename):
                new_token_filename = f'datastores/{new_token}.json'
                os.rename(old_token_filename, new_token_filename)
            else:
                with open(f'datastores/{new_token}.json', 'w') as new_file:
                    json.dump({}, new_file, indent=4)

        return new_token, server_filename

    @discord.app_commands.command(name="generate_token", description="Generates a new Minecraft token.")
    @discord.app_commands.default_permissions(administrator=True)
    async def generate_token(self, interaction: discord.Interaction):
        """Generates a new Minecraft token and updates it in the server's JSON file."""
        new_token, server_filename = await self.update_json_with_token(interaction.guild)
        await interaction.response.send_message(f"A new Minecraft token has been generated Token: `{new_token}`", ephemeral=True)

# Setup function to add the cog to the bot
async def setup(bot):
    await bot.add_cog(TokenCog(bot))
