import discord
from discord.ext import commands
from discord import app_commands
import json

from utils.database_utils import db_get, db_write, db_update

class PartnersCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = bot.db_connection

    async def ensure_partner_record(self, guild_id):
        result = db_get(
            self.conn,
            "SELECT partners FROM partners WHERE server_id = %s",
            (guild_id,),
            fetchone=True
        )
        if not result:
            db_write(
                self.conn,
                "INSERT INTO partners (server_id, partners) VALUES (%s, %s)",
                (guild_id, "{}")
            )
            print(f"[Partners] Created new partners record for guild {guild_id}")
            return {}
        try:
            return json.loads(result[0]) if result[0] else {}
        except Exception as e:
            print(f"[Partners] Error loading partners JSON for guild {guild_id}: {e}")
            return {}

    @app_commands.command(name="partners_add", description="Add or update a Twitch partner and their tier roles.")
    @app_commands.describe(player="The Discord member to set as a Twitch partner")
    @app_commands.default_permissions(administrator=True)
    async def partners_add(self, interaction: discord.Interaction, player: discord.Member):
        guild = interaction.guild
        guild_id = guild.id
        partners_data = await self.ensure_partner_record(guild_id)

        # Only include managed roles that are NOT managed by bots (integration type is not 'bot')
        managed_roles = [
            r for r in guild.roles
            if r.managed and r != guild.default_role and (not hasattr(r, "tags") or not (r.tags and r.tags.bot_id))
        ]
        print(f"[Partners] Number of managed roles (not bot-managed) in guild {guild_id}: {len(managed_roles)}")  # Debug output
        if not managed_roles:
            await interaction.response.send_message(
                "❌ No managed (integration) roles found in this server (excluding bot-managed roles).", ephemeral=True
            )
            print(f"❌ [Partners] No managed roles (not bot-managed) found in guild {guild_id}")
            return

        class RoleSelect(discord.ui.Select):
            def __init__(self, roles, prompt):
                options = [
                    discord.SelectOption(label=role.name, value=str(role.id))
                    for role in roles
                ]
                super().__init__(
                    placeholder=prompt,
                    options=options,
                    min_values=1,
                    max_values=1
                )
                self.prompt = prompt

            async def callback(self, select_interaction: discord.Interaction):
                self.view.selected_role = self.values[0]
                await select_interaction.response.defer()
                self.view.stop()

        class RoleView(discord.ui.View):
            def __init__(self, roles, prompt):
                super().__init__(timeout=180)
                self.selected_role = None
                self.add_item(RoleSelect(roles, prompt))

        # Prompt for base subscriber role
        base_view = RoleView(managed_roles, "Select base subscriber role...")
        base_msg = await interaction.response.send_message(
            f"Select the **Base Subscriber Role** for {player.display_name}:", view=base_view, ephemeral=True
        )
        await base_view.wait()
        base_role = base_view.selected_role

        # Delete previous ephemeral before next prompt
        try:
            await interaction.delete_original_response()
        except Exception as e:
            print(f"❌ [Partners] Could not delete base role selection message: {e}")

        # Ask for Tier 1
        tier1_view = RoleView(managed_roles, "Select role for Tier 1...")
        tier1_msg = await interaction.followup.send(
            f"Select the **Tier 1 Role** for {player.display_name}:", view=tier1_view, ephemeral=True
        )
        await tier1_view.wait()
        tier_1_role = tier1_view.selected_role

        try:
            await tier1_msg.delete()
        except Exception as e:
            print(f"❌ [Partners] Could not delete Tier 1 selection message: {e}")

        # Ask for Tier 2
        tier2_view = RoleView(managed_roles, "Select role for Tier 2...")
        tier2_msg = await interaction.followup.send(
            f"Select the **Tier 2 Role** for {player.display_name}:", view=tier2_view, ephemeral=True
        )
        await tier2_view.wait()
        tier_2_role = tier2_view.selected_role

        try:
            await tier2_msg.delete()
        except Exception as e:
            print(f"❌ [Partners] Could not delete Tier 2 selection message: {e}")

        # Ask for Tier 3
        tier3_view = RoleView(managed_roles, "Select role for Tier 3...")
        tier3_msg = await interaction.followup.send(
            f"Select the **Tier 3 Role** for {player.display_name}:", view=tier3_view, ephemeral=True
        )
        await tier3_view.wait()
        tier_3_role = tier3_view.selected_role

        try:
            await tier3_msg.delete()
        except Exception as e:
            print(f"❌ [Partners] Could not delete Tier 3 selection message: {e}")

        # Save to DB
        def get_role_info(role_id):
            role = discord.utils.get(guild.roles, id=int(role_id)) if role_id else None
            if role:
                return {"id": str(role.id), "name": role.name}
            return {"id": "", "name": "None"}

        partners_data[player.display_name] = {
            "base": get_role_info(base_role),
            "tier_1": get_role_info(tier_1_role),
            "tier_2": get_role_info(tier_2_role),
            "tier_3": get_role_info(tier_3_role)
        }
        print(f"[Partners] Adding/updating partner '{player.display_name}' with data: {json.dumps(partners_data[player.display_name], indent=2)}")  # Debug output
        print(f"[Partners] Full partners_data for guild {guild_id}: {json.dumps(partners_data, indent=2)}")  # Debug output

        db_update(
            self.conn,
            "UPDATE partners SET partners = %s WHERE server_id = %s",
            (json.dumps(partners_data), guild_id)
        )
        print(f"[Partners] Updated partner {player.display_name} in guild {guild_id}: {partners_data[player.display_name]}")

        # Prepare summary of selected roles as an embed
        def get_role_name_from_info(role_info):
            return f"{role_info['name']} (ID: {role_info['id']})" if role_info["id"] else "None"

        summary_embed = discord.Embed(
            title=f"✅ Partner Roles Updated for {player.display_name}",
            color=discord.Color.green()
        )
        summary_embed.description = (
            f"❕ New users who link their Twitch & Discord accounts may have to wait ~15 minutes before Discord's API updates for the roles to be applied.\n As soon as the user gains their respective role on Discord, they can join the server!"
        )
        summary_embed.add_field(name="Base Subscriber Role:", value=get_role_name_from_info(partners_data[player.display_name]["base"]), inline=False)
        summary_embed.add_field(name="Tier 1 Role:", value=get_role_name_from_info(partners_data[player.display_name]["tier_1"]), inline=False)
        summary_embed.add_field(name="Tier 2 Role:", value=get_role_name_from_info(partners_data[player.display_name]["tier_2"]), inline=False)
        summary_embed.add_field(name="Tier 3 Role:", value=get_role_name_from_info(partners_data[player.display_name]["tier_3"]), inline=False)

        await interaction.followup.send(
            embed=summary_embed,
            ephemeral=True
        )

    @app_commands.command(name="partners_remove", description="Remove a Twitch partner from the partners list.")
    @app_commands.default_permissions(administrator=True)
    async def partners_remove(self, interaction: discord.Interaction):
        guild = interaction.guild
        guild_id = guild.id
        partners_data = await self.ensure_partner_record(guild_id)

        if not partners_data:
            await interaction.response.send_message(
                "❌ No partners found for this server.", ephemeral=True
            )
            print(f"❌ [Partners] No partners to remove in guild {guild_id}")
            return

        class RemovePartnerSelect(discord.ui.Select):
            def __init__(self, partner_names):
                options = [
                    discord.SelectOption(label=name, value=name)
                    for name in partner_names
                ]
                super().__init__(placeholder="Select a partner to remove...", options=options)

            async def callback(self, select_interaction: discord.Interaction):
                partner_name = self.values[0]
                if partner_name in partners_data:
                    del partners_data[partner_name]
                    db_update(
                        self.view.cog.conn,
                        "UPDATE partners SET partners = %s WHERE server_id = %s",
                        (json.dumps(partners_data), guild_id)
                    )
                    print(f"[Partners] Removed partner {partner_name} from guild {guild_id}")
                    await select_interaction.response.send_message(
                        f"✅ Removed partner: {partner_name}", ephemeral=True
                    )
                else:
                    print(f"[Partners] Tried to remove non-existent partner {partner_name} from guild {guild_id}")
                    await select_interaction.response.send_message(
                        f"❌ Partner {partner_name} not found.", ephemeral=True
                    )
                self.view.stop()

        view = discord.ui.View(timeout=180)
        view.cog = self
        view.add_item(RemovePartnerSelect(list(partners_data.keys())))
        print(f"[Partners] Prompting for partner removal in guild {guild_id}")
        await interaction.response.send_message(
            "Select a partner to remove:",
            view=view,
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(PartnersCog(bot))