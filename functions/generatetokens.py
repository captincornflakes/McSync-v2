import discord
from discord.ext import commands
import secrets
import string
from utils.database_utils import reconnect_database

class GenerateTokenCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = bot.db_connection

    def generate_random_token(self, length=32):
        characters = string.ascii_letters + string.digits
        return ''.join(secrets.choice(characters) for _ in range(length))

    async def update_json_and_database_with_token(self, guild):
        reconnect_database(self.conn)
        server_id = guild.id
        new_token = self.generate_random_token()

        try:
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT minecraft_token FROM servers WHERE server_id = %s", (server_id,))
                result = cursor.fetchone()
                existing_token = result[0] if result else None

                if existing_token:
                    cursor.execute(
                        "UPDATE servers SET minecraft_token = %s WHERE server_id = %s",
                        (new_token, server_id)
                    )
                    cursor.execute(
                        "UPDATE users SET token = %s WHERE token = %s",
                        (new_token, existing_token)
                    )
                else:
                    cursor.execute(
                        "INSERT INTO servers (server_id, minecraft_token) VALUES (%s, %s)",
                        (server_id, new_token)
                    )
                self.conn.commit()
            return new_token

        except Exception as e:
            self.conn.rollback()
            print(f"Database error occurred: {e}")
            return None

    @discord.app_commands.command(
        name="generatetoken",
        description="Generates a new Minecraft token. Place this token in the plugins config folder."
    )
    @discord.app_commands.default_permissions(administrator=True)
    async def token(self, interaction: discord.Interaction):
        new_token = await self.update_json_and_database_with_token(interaction.guild)
        if new_token:
            embed = discord.Embed(
                title="New Minecraft Token Generated",
                description="A new Minecraft token has been successfully generated and stored.",
                color=discord.Color.blue()
            )
            embed.add_field(name="Minecraft Token", value=f"`{new_token}`", inline=False)
            embed.set_footer(text="Place this token in the plugins config folder for activation.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            error_embed = discord.Embed(
                title="Token Generation Failed",
                description="An error occurred while generating the Minecraft token. Please try again later.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(GenerateTokenCog(bot))
