import discord
from discord.ext import commands
import json
import os

class MinecraftName(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_user_info(self, user):
        """Return a dictionary with user info and their roles."""
        user_info = {
            'username': user.name,
            'discriminator': user.discriminator,
            'id': user.id,
            'roles': [role.name for role in user.roles if role.name != "@everyone"]
        }
        return user_info

    async def register_minecraftname(self, guild, minecraftname, user):
        """Register the Minecraft name in the server's JSON file and include user info and roles."""
        server_id = guild.id
        server_filename = f'datastores/{server_id}.json'
        new_token = self.generate_random_token()

        # Ensure the datastores directory exists
        os.makedirs('datastores', exist_ok=True)

        if os.path.exists(server_filename):
            with open(server_filename, 'r') as file:
                data = json.load(file)
        else:
            data = {}

        # Get the current minecraft_token
        minecraft_token = data.get('minecraft_token', new_token)
        data['minecraft_token'] = minecraft_token

        # Write the updated data to the server JSON file
        with open(server_filename, 'w') as file:
            json.dump(data, file, indent=4)

        # Ensure minecraft_token data exists
        token_filename = f'datastores/{minecraft_token}.json'
        if not os.path.exists(token_filename):
            with open(token_filename, 'w') as new_file:
                json.dump({}, new_file, indent=4)

        # Update the JSON file with the new Minecraft name and user info
        with open(token_filename, 'r') as file:
            token_data = json.load(file)

        # Register the minecraftname under the current token and add user info
        token_data['minecraftname'] = minecraftname
        token_data['user_info'] = self.get_user_info(user)

        with open(token_filename, 'w') as file:
            json.dump(token_data, file, indent=4)

        return minecraft_token, token_filename

    @discord.app_commands.command(name="minecraft", description="Register a Minecraft name to the current token.")
    @discord.app_commands.default_permissions(administrator=True)
    async def minecraft(self, interaction: discord.Interaction, minecraftname: str):
        """Command to register a Minecraft name to the current token and include user info and roles."""
        user = interaction.user
        result = await self.register_minecraftname(interaction.guild, minecraftname, user)
        if result:
            await interaction.response.send_message(
                f"Successfully registered. Please log in to the Minecraft server.",ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "Failed to register the Minecraft name.",ephemeral=True
            )

    def generate_random_token(self, length=32):
        """Generate a random string of letters and digits."""
        import secrets
        import string
        characters = string.ascii_letters + string.digits
        return ''.join(secrets.choice(characters) for i in range(length))

# Setup function to add the cog to the bot
async def setup(bot):
    await bot.add_cog(MinecraftName(bot))