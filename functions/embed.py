import discord
from discord.ext import commands

from utils.logger_utils import datalog
from utils.database_utils import reconnect_database, db_get

class ReactionRole(commands.Cog):
     def __init__(self, bot):
          self.bot = bot
          self.conn = bot.db_connection

     @discord.app_commands.command(
          name="embed",
          description="Create an embed for users to gain the override role by reacting."
     )
     @discord.app_commands.default_permissions(administrator=True)
     async def embed(self, interaction: discord.Interaction):
          await interaction.response.defer(ephemeral=True)
          try:
               result = db_get(
                    self.conn,
                    "SELECT override_role FROM channels_roles WHERE server_id = %s",
                    (interaction.guild.id,),
                    fetchone=True
               )
               if not result:
                    await interaction.followup.send(
                         "❌ No override role is defined for this server.", ephemeral=True
                    )
                    return

               override_role_name = result[0]
               role = discord.utils.get(interaction.guild.roles, name=override_role_name)

               if not role:
                    await interaction.followup.send(
                         "❌ The role defined for this server does not exist on the server. 😲", ephemeral=True
                    )
                    return

               embed = discord.Embed(title="MCSync Follower React", color=discord.Color.blue())
               embed.add_field(
                    name="React to gain Follower Access",
                    value=f"React to this message with 👍 to gain the `{role.name}` role.",
               )
               embed.set_footer(text="⬇️ React below!")
               message = await interaction.channel.send(embed=embed)
               await message.add_reaction("👍")
               await interaction.followup.send(
                    f"✔️ Embed created for role `{role.name}` in this server.", ephemeral=True
               )

          except Exception as e:
               await interaction.followup.send(
                    f"❌ An error occurred: {e}", ephemeral=True
               )

     @commands.Cog.listener()
     async def on_raw_reaction_add(self, payload):
          if payload.emoji.name != "👍":
               return
          try:
               guild = self.bot.get_guild(payload.guild_id)
               if not guild:
                    return
               channel = guild.get_channel(payload.channel_id)
               if not channel:
                    return
               message = await channel.fetch_message(payload.message_id)
               if not message.embeds:
                    return
               embed = message.embeds[0]
               if embed.title != "MCSync Follower React":
                    return

               result = db_get(
                    self.conn,
                    "SELECT override_role FROM channels_roles WHERE server_id = %s",
                    (payload.guild_id,),
                    fetchone=True
               )
               if result:
                    override_role_name = result[0]
                    role = discord.utils.get(guild.roles, name=override_role_name)
                    member = guild.get_member(payload.user_id)
                    if not member:
                         try:
                              member = await guild.fetch_member(payload.user_id)
                         except Exception:
                              return
                    if role and member:
                         try:
                              await member.add_roles(role, reason="MCSync reaction role")
                         except discord.Forbidden:
                              datalog(self, 'roles', f"❌ Insufficient permissions to add role {role.name} to {member.name}. {guild}")
                         except Exception as e:
                              datalog(self, 'embed', f"❌ Error adding role: {e} - {guild}")
          except Exception as e:
               datalog(self, 'embed', f"❌ Error in on_raw_reaction_add: {e} - {guild}")

     @commands.Cog.listener()
     async def on_raw_reaction_remove(self, payload):
          if payload.emoji.name != "👍":
               return
          try:
               guild = self.bot.get_guild(payload.guild_id)
               if not guild:
                    return
               channel = guild.get_channel(payload.channel_id)
               if not channel:
                    return
               message = await channel.fetch_message(payload.message_id)
               if not message.embeds:
                    return
               embed = message.embeds[0]
               if embed.title != "MCSync Follower React":
                    return

               result = db_get(
                    self.conn,
                    "SELECT override_role FROM channels_roles WHERE server_id = %s",
                    (payload.guild_id,),
                    fetchone=True
               )
               if result:
                    override_role_name = result[0]
                    role = discord.utils.get(guild.roles, name=override_role_name)
                    member = guild.get_member(payload.user_id)
                    if not member:
                         member = await guild.fetch_member(payload.user_id)
                    if role and member:
                         try:
                              await member.remove_roles(role)
                         except discord.Forbidden:
                              datalog(self, 'embed', f"❌ Insufficient permissions to remove role {role.name} from {member.name}. {guild}")
          except Exception as e:
               datalog(self, 'embed', f"❌ Error in on_raw_reaction_remove: {e} - {guild}")

async def setup(bot):
     await bot.add_cog(ReactionRole(bot))
