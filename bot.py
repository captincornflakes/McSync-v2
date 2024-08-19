import discord
from discord.ext import commands
import os
import json
import tracemalloc
import logging
import asyncio

# Enable logging
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
logging.basicConfig(level=logging.INFO, handlers=[handler])

# Start memory tracking
tracemalloc.start()

# Load the bot token from a JSON file in the 'datastores' folder
def load_token():
    with open('datastores/config.json') as f:
        data = json.load(f)
        return data.get('token')

# Load the bot token from a JSON file in the 'datastores' folder
def load_application_id():
    with open('datastores/config.json') as f:
        data = json.load(f)
        return data.get('application_id')
    
# Define the intents you want your bot to have
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent

# Prefix and bot initialization
PREFIX = "!"
bot = commands.Bot(command_prefix=PREFIX, intents=intents, application_id=load_application_id())

# Function to load all Python files from a directory as extensions
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

# Event: When the bot is ready and connected
@bot.event
async def on_ready():
    print('Bot is ready')
    activity = discord.Activity(type=discord.ActivityType.listening, name=f"{PREFIX}help")
    await bot.change_presence(status=discord.Status.idle, activity=activity)
    print(f'Logged in as {bot.user.name} ({bot.user.id})')

# Event: Sync commands when bot joins a new guild
@bot.event
async def on_guild_join(guild):
    await bot.tree.sync(guild=guild)

# Setup hook to load extensions
async def setup_hook():
    await load_extensions_from_folder('functions')
    await bot.tree.sync()

# Assign setup_hook to the bot
bot.setup_hook = setup_hook

# Run the bot with your token
if __name__ == '__main__':
    token = load_token()
    bot.run(token, log_handler=handler, log_level=logging.INFO)
