import discord
from discord.ext import commands
from discord import app_commands

from bot import datalog

class Roles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = bot.db_connection  # Assuming the connection is passed from the bot
        self.cursor = self.conn.cursor()
        self.subscriber = bot.subscriber
        self.tier_1 = bot.tier_1
        self.tier_2 = bot.tier_2
        self.tier_3 = bot.tier_3

    def reconnect_database(self):
        try:
            self.conn.ping(reconnect=True, attempts=3, delay=5)
        except Exception as e:
            print(f"Error reconnecting to the database: {e}")
            
    def update_channels_roles(self, server_id, column, role):
        self.reconnect_database()
        datalog(self, 'roles', f"Final Update Role - server: {server_id} Role: {role}")
        query = f"UPDATE channels_roles SET {column} = %s WHERE server_id = %s"
        self.cursor.execute(query, (role, server_id))
        self.conn.commit()

    async def update_subscriber_role(self, interaction: discord.Interaction):
        server_id = interaction.guild.id
        role_name = self.subscriber
        datalog(self, 'roles', f"Subscriber update - server: {server_id} Role: {role_name}")
        role = discord.utils.get(interaction.guild.roles, name=role_name)
        if role:
            await interaction.followup.send(f"'Twitch Subscriber' role already exists: {role.mention}", ephemeral=True)
            self.update_channels_roles(server_id, 'subscriber_role', role.name)
            await self.update_tier_1_role(interaction)
        else:
            class RoleSelect(discord.ui.Select):
                def __init__(self, roles):
                    options = [
                        discord.SelectOption(label=role.name, value=str(role.name))
                        for role in roles
                    ]
                    super().__init__(placeholder="Select a subscriber role...", options=options)

                async def callback(self, select_interaction: discord.Interaction):
                    selected_role_name = self.values[0]
                    selected_role = discord.utils.get(select_interaction.guild.roles, name=selected_role_name)
                    if selected_role:
                        await select_interaction.response.send_message(f"You selected {selected_role.mention} as the subscriber role.", ephemeral=True)
                        self.view.cog.update_channels_roles(server_id, 'subscriber_role', selected_role_name)
                        await self.view.cog.update_tier_1_role(select_interaction)

            roles = [role for role in interaction.guild.roles if role.managed and role != interaction.guild.default_role]
            select = RoleSelect(roles)
            view = discord.ui.View(timeout=60)
            view.add_item(select)
            view.cog = self
            await interaction.followup.send("Please select a role from the dropdown:", view=view, ephemeral=True)

    async def update_tier_1_role(self, interaction: discord.Interaction):
        server_id = interaction.guild.id
        role_name = self.tier_1
        datalog(self, 'roles', f"tier 1 role update - server: {server_id} Role: {role_name}")
        role = discord.utils.get(interaction.guild.roles, name=role_name)
        if role:
            await interaction.followup.send(f"'Twitch Subscriber: Tier 1' role already exists: {role.mention}", ephemeral=True)
            self.update_channels_roles(server_id, 'tier_1', role.name)
            await self.update_tier_2_role(interaction)
        else:
            class RoleSelect(discord.ui.Select):
                def __init__(self, roles):
                    options = [
                        discord.SelectOption(label=role.name, value=str(role.name))
                        for role in roles
                    ]
                    super().__init__(placeholder="Select a Tier 1 role...", options=options)

                async def callback(self, select_interaction: discord.Interaction):
                    selected_role_name = self.values[0]
                    selected_role = discord.utils.get(select_interaction.guild.roles, name=selected_role_name)
                    if selected_role:
                        await select_interaction.response.send_message(f"You selected {selected_role.mention} as the Tier 1 role.", ephemeral=True)
                        self.view.cog.update_channels_roles(server_id, 'tier_1', selected_role_name)
                        await self.view.cog.update_tier_2_role(select_interaction)

            roles = [role for role in interaction.guild.roles if role.managed and role != interaction.guild.default_role]
            select = RoleSelect(roles)
            view = discord.ui.View(timeout=60)
            view.add_item(select)
            view.cog = self
            await interaction.followup.send("Please select a role from the dropdown:", view=view, ephemeral=True)

    async def update_tier_2_role(self, interaction: discord.Interaction):
        server_id = interaction.guild.id
        role_name = self.tier_2
        datalog(self, 'roles', f"Tier 2 role update - server: {server_id} Role: {role_name}")
        role = discord.utils.get(interaction.guild.roles, name=role_name)
        if role:
            await interaction.followup.send(f"'Twitch Subscriber: Tier 2' role already exists: {role.mention}", ephemeral=True)
            self.update_channels_roles(server_id, 'tier_2', role.name)
            await self.update_tier_3_role(interaction)
        else:
            class RoleSelect(discord.ui.Select):
                def __init__(self, roles):
                    options = [
                        discord.SelectOption(label=role.name, value=str(role.name))
                        for role in roles
                    ]
                    super().__init__(placeholder="Select a Tier 2 role...", options=options)

                async def callback(self, select_interaction: discord.Interaction):
                    selected_role_name = self.values[0]
                    selected_role = discord.utils.get(select_interaction.guild.roles, name=selected_role_name)
                    if selected_role:
                        await select_interaction.response.send_message(f"You selected {selected_role.mention} as the Tier 2 role.", ephemeral=True)
                        self.view.cog.update_channels_roles(server_id, 'tier_2', selected_role_name)
                        await self.view.cog.update_tier_3_role(select_interaction)

            roles = [role for role in interaction.guild.roles if role.managed and role != interaction.guild.default_role]
            select = RoleSelect(roles)
            view = discord.ui.View(timeout=60)
            view.add_item(select)
            view.cog = self
            await interaction.followup.send("Please select a role from the dropdown:", view=view, ephemeral=True)

    async def update_tier_3_role(self, interaction: discord.Interaction):
        server_id = interaction.guild.id
        role_name = self.tier_3
        datalog(self, 'roles', f"Tier 3 role update - server: {server_id} Role: {role_name}")
        role = discord.utils.get(interaction.guild.roles, name=role_name)
        if role:
            await interaction.followup.send(f"'Twitch Subscriber: Tier 3' role already exists: {role.mention}", ephemeral=True)
            self.update_channels_roles(server_id, 'tier_3', role.name)
        else:
            class RoleSelect(discord.ui.Select):
                def __init__(self, roles):
                    options = [
                        discord.SelectOption(label=role.name, value=str(role.name))
                        for role in roles
                    ]
                    super().__init__(placeholder="Select a Tier 3 role...", options=options)

                async def callback(self, select_interaction: discord.Interaction):
                    selected_role_name = self.values[0]
                    selected_role = discord.utils.get(select_interaction.guild.roles, name=selected_role_name)
                    if selected_role:
                        await select_interaction.response.send_message(f"You selected {selected_role.mention} as the Tier 3 role.", ephemeral=True)
                        self.view.cog.update_channels_roles(server_id, 'tier_3', selected_role_name)

            roles = [role for role in interaction.guild.roles if role.managed and role != interaction.guild.default_role]
            select = RoleSelect(roles)
            view = discord.ui.View(timeout=60)
            view.add_item(select)
            view.cog = self
            await interaction.followup.send("Please select a role from the dropdown:", view=view, ephemeral=True)

    @app_commands.command(name="roles", description="Setup your server with MCSync roles.")
    @app_commands.default_permissions(administrator=True)
    async def roles(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)  # Defer the initial response to keep the interaction alive
        await self.update_subscriber_role(interaction)

async def setup(bot):
    await bot.add_cog(Roles(bot))
