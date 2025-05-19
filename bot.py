import discord
from discord.ext import commands
import os
import tracemalloc
import logging
import asyncio
from utils.github_utils import load_github
from utils.database_utils import setup_database_connection, get_active_connection_count
from utils.config_utils import load_config

# Logging setup
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
logging.basicConfig(level=logging.INFO, handlers=[handler])

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

# Config and bot setup (only load ONCE)
config = load_config()
load_github(config)
bot = commands.AutoShardedBot(
    command_prefix="!",
    intents=intents,
    application_id=int(config['application_id']),
    help_command=None,
    # shard_count=2,  # Uncomment and set if you want to specify the number of shards
    # shard_ids=[0, 1],  # Uncomment and set if you want to specify which shards this instance runs
)
bot.config = config
bot.db_connection = setup_database_connection(config)
bot.subscriber = "Twitch Subscriber"
bot.tier_1 = "Twitch Subscriber: Tier 1"
bot.tier_2 = "Twitch Subscriber: Tier 2"
bot.tier_3 = "Twitch Subscriber: Tier 3"
bot.override_role = "MCSync Override"
bot.category_name = "MCSync"

# Start memory tracking
tracemalloc.start()

# Extension loader
async def load_extensions_from_folder(folder):
    for filename in os.listdir(folder):
        if filename.endswith('.py') and filename != '__init__.py':
            module_name = filename[:-3]
            module_path = f'{folder}.{module_name}'
            try:
                await bot.load_extension(module_path)
                print(f'Loaded extension: {module_path}')
            except Exception as e:
                print(f'Failed to load extension {module_path}. Reason: {e}')

async def check_active_connections():
    await bot.wait_until_ready()
    while not bot.is_closed():
        if bot.db_connection:
            count = get_active_connection_count(bot.db_connection)
            print(f"[DB] Active connections: {count}")
        await asyncio.sleep(300)  # 5 minutes

@bot.event
async def on_ready():
    activity = discord.Activity(type=discord.ActivityType.playing, name="MCSync.live")
    await bot.change_presence(status=discord.Status.online, activity=activity)
    print(f'Logged in as {bot.user} ({bot.user.id})')
    print(f"Shard Count: {bot.shard_count}")
    for shard_id, latency in bot.latencies:
        print(f"Shard ID: {shard_id} | Latency: {latency*1000:.2f}ms")
    # Start the background task only once
    if not hasattr(bot, "active_conn_task"):
        bot.active_conn_task = asyncio.create_task(check_active_connections())

@bot.event
async def on_shard_ready(shard_id):
    print(f"Shard {shard_id} is ready.")

@bot.event
async def on_guild_join(guild):
    await bot.tree.sync(guild=guild)

# Setup hook to load extensions
async def setup_hook():
    await load_extensions_from_folder('functions')
    await bot.tree.sync()

bot.setup_hook = setup_hook

@bot.event
async def on_close():
    if bot.db_connection:
        bot.db_connection.close()
        print("Database connection closed.")

if __name__ == '__main__':
    token = config['token']
    bot.run(token, log_handler=handler, log_level=logging.INFO)
