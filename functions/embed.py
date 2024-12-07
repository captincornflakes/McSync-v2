import discord
from discord.ext import commands

class ReactionRole(commands.Cog):
     def __init__(self, bot):
          self.bot = bot
          self.conn = bot.db_connection

     @discord.app_commands.command(
          name="mcsync_embed",
          description="Create an embed for users to gain the override role by reacting."
     )
     @discord.app_commands.default_permissions(administrator=True)
     async def mcsync_embed(self, interaction: discord.Interaction):
          await interaction.response.defer(ephemeral=True)
          with self.conn.cursor() as cursor:
               cursor.execute("SELECT override_role FROM channels_roles WHERE server_id = ?",(interaction.guild.id,),)
               result = cursor.fetchone()

          if not result:
               await interaction.followup.send(
                    "No override role is defined for this server.", ephemeral=True
               )
               return
          override_role_id = result[0]
          role = interaction.guild.get_role(override_role_id)

          if not role:
               await interaction.followup.send(
                    "The role defined for this server does not exist on the server.", ephemeral=True
               )
               return
          embed = discord.Embed(title="MCSync React", color=discord.Color.blue())
          embed.add_field(
               name="React to gain role",
               value=f"React with 👍 to gain the `{role.name}` role.",
          )
          embed.set_footer(text="React to this message to gain roles!")
          message = await interaction.channel.send(embed=embed)
          await message.add_reaction("👍")
          await interaction.followup.send(
               f"Embed created for role `{role.name}` in this server.", ephemeral=True
          )

     @commands.Cog.listener()
     async def on_raw_reaction_add(self, payload):
          if payload.emoji.name != "👍":
               return

          with self.conn.cursor() as cursor:
               cursor.execute("SELECT override_role FROM channels_roles WHERE server_id = ?",(payload.guild_id,),)
               result = cursor.fetchone()

          if result:
               override_role_id = result[0]
               guild = self.bot.get_guild(payload.guild_id)
               if not guild:
                    return

               role = guild.get_role(override_role_id)
               member = guild.get_member(payload.user_id)
               if role and member:
                    try:
                         await member.add_roles(role)
                    except discord.Forbidden:
                         print(
                         f"Insufficient permissions to add role {role.name} to {member.name}."
                         )

     @commands.Cog.listener()
     async def on_raw_reaction_remove(self, payload):
          if payload.emoji.name != "👍":
               return
          with self.conn.cursor() as cursor:
               cursor.execute("SELECT override_role FROM channels_roles WHERE server_id = ?",(payload.guild_id,),)
               result = cursor.fetchone()
          if result:
               override_role_id = result[0]
               guild = self.bot.get_guild(payload.guild_id)
               if not guild:
                    return
               role = guild.get_role(override_role_id)
               member = guild.get_member(payload.user_id)
               if role and member:
                    try:
                         await member.remove_roles(role)
                    except discord.Forbidden:
                         print(
                         f"Insufficient permissions to remove role {role.name} from {member.name}."
                         )

async def setup(bot):
     await bot.add_cog(ReactionRole(bot))
