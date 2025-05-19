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
            return {}
        try:
            return json.loads(result[0]) if result[0] else {}
        except Exception:
            return {}

    partners_group = app_commands.Group(name="partners", description="Manage Twitch partners and their tier roles.")

    @partners_group.command(name="add", description="Add or update a Twitch partner and their tier roles.")
    @app_commands.default_permissions(administrator=True)
    async def partners_add(self, interaction: discord.Interaction):
        guild = interaction.guild
        guild_id = guild.id
        partners_data = await self.ensure_partner_record(guild_id)

        twitch_managed_members = [
            m for m in guild.members if any(r.managed and "twitch" in r.name.lower() for r in m.roles)
        ]
        if not twitch_managed_members:
            await interaction.response.send_message(
                "No users with a Twitch integration role found.", ephemeral=True
            )
            return

        class PartnerSelect(discord.ui.Select):
            def __init__(self, members):
                options = [
                    discord.SelectOption(label=m.display_name, value=str(m.id))
                    for m in members
                ]
                super().__init__(placeholder="Select a Twitch partner...", options=options)

            async def callback(self, select_interaction: discord.Interaction):
                partner_id = int(self.values[0])
                partner_member = guild.get_member(partner_id)
                await select_interaction.response.send_message(
                    f"Selected partner: {partner_member.display_name}. Now select roles for each tier.",
                    ephemeral=True,
                    view=TierRoleView(self.view.cog, partner_member, partners_data)
                )

        class TierRoleSelect(discord.ui.Select):
            def __init__(self, roles, tier):
                options = [
                    discord.SelectOption(label=role.name, value=str(role.id))
                    for role in roles
                ]
                super().__init__(placeholder=f"Select role for {tier.replace('_', ' ').title()}...", options=options)
                self.tier = tier

            async def callback(self, select_interaction: discord.Interaction):
                self.view.selected_roles[self.tier] = self.values[0]
                await select_interaction.response.send_message(
                    f"Selected role for {self.tier.replace('_', ' ').title()}.",
                    ephemeral=True
                )

        class TierRoleView(discord.ui.View):
            def __init__(self, cog, partner_member, partners_data):
                super().__init__(timeout=120)
                self.cog = cog
                self.partner_member = partner_member
                self.partners_data = partners_data
                self.selected_roles = {}
                managed_roles = [r for r in partner_member.roles if r.managed and r != partner_member.guild.default_role]
                for tier in ["tier_1", "tier_2", "tier_3"]:
                    self.add_item(TierRoleSelect(managed_roles, tier))
                self.add_item(SaveButton(self))

        class SaveButton(discord.ui.Button):
            def __init__(self, view):
                super().__init__(label="Save", style=discord.ButtonStyle.green)
                self.view = view

            async def callback(self, interaction: discord.Interaction):
                partner_name = self.view.partner_member.display_name
                self.view.partners_data[partner_name] = {
                    "tier_1": self.view.selected_roles.get("tier_1", ""),
                    "tier_2": self.view.selected_roles.get("tier_2", ""),
                    "tier_3": self.view.selected_roles.get("tier_3", "")
                }
                db_update(
                    self.conn,
                    "UPDATE partners SET partners = %s WHERE server_id = %s",
                    (json.dumps(self.view.partners_data), interaction.guild.id)
                )
                await interaction.response.send_message(
                    f"✅ Partner roles updated for {partner_name}.", ephemeral=True
                )
                self.view.stop()

        view = discord.ui.View(timeout=60)
        view.cog = self
        view.add_item(PartnerSelect(twitch_managed_members))
        await interaction.response.send_message(
            "Select a Twitch partner to configure their tier roles:",
            view=view,
            ephemeral=True
        )

    @partners_group.command(name="remove", description="Remove a Twitch partner from the partners list.")
    @app_commands.default_permissions(administrator=True)
    async def partners_remove(self, interaction: discord.Interaction):
        guild = interaction.guild
        guild_id = guild.id
        partners_data = await self.ensure_partner_record(guild_id)

        if not partners_data:
            await interaction.response.send_message(
                "No partners found for this server.", ephemeral=True
            )
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
                        self.conn,
                        "UPDATE partners SET partners = %s WHERE server_id = %s",
                        (json.dumps(partners_data), guild_id)
                    )
                    await select_interaction.response.send_message(
                        f"✅ Removed partner: {partner_name}", ephemeral=True
                    )
                else:
                    await select_interaction.response.send_message(
                        f"Partner {partner_name} not found.", ephemeral=True
                    )
                self.view.stop()

        view = discord.ui.View(timeout=60)
        view.cog = self
        view.add_item(RemovePartnerSelect(list(partners_data.keys())))
        await interaction.response.send_message(
            "Select a partner to remove:",
            view=view,
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(PartnersCog(bot))