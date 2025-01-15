import discord
from discord.ext import commands
import os
import json
import tracemalloc
import logging
import asyncio
import mysql.connector
import requests
import zipfile
import io
import os
import shutil
from datetime import datetime, timezone

#pip install mysql-connector-python
#pip install discord.py
#pip install requests
#python -m pip install mojang

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
logging.basicConfig(level=logging.INFO, handlers=[handler])

def download_repo_as_zip(repo_url, token, temp_folder):
    zip_url = f"{repo_url}/archive/refs/heads/main.zip"
    headers = {'Authorization': f'token {token}'}
    print(f"Downloading repository from {zip_url}...")
    try:
        response = requests.get(zip_url, headers=headers)
        response.raise_for_status()  # Raise an error for HTTP errors
    except requests.exceptions.RequestException as e:
        print(f"Failed to download repository: {e}")
        raise
    print(f"Extracting ZIP file to {temp_folder}...")
    try:
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
            zip_file.extractall(temp_folder)
    except zipfile.BadZipFile as e:
        print(f"Failed to extract ZIP file: {e}")
        raise
    print(f"Repository extracted to {temp_folder}.")

def extract_functions_folder(temp_folder, target_folder):
    repo_folder = os.path.join(temp_folder, "McSync-v2-main")
    functions_folder = os.path.join(repo_folder, "functions")
    if not os.path.exists(functions_folder):
        raise FileNotFoundError(f"'functions' folder not found in {repo_folder}.")
    if os.path.exists(target_folder):
        print(f"Removing existing target folder: {target_folder}")
        shutil.rmtree(target_folder)
    print(f"Copying 'functions' folder to {target_folder}...")
    os.makedirs(target_folder, exist_ok=True)
    for item in os.listdir(functions_folder):
        source = os.path.join(functions_folder, item)
        destination = os.path.join(target_folder, item)
        if os.path.isdir(source):
            shutil.copytree(source, destination, dirs_exist_ok=True)
        else:
            shutil.copy2(source, destination)

def load_github():
    sync_github = True
    if sync_github:
        print("Pulling repository from GitHub...")
        repo_url = "https://github.com/captincornflakes/McSync-v2"
        token = "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"  # Hardcoded token (NOT recommended for production)
        temp_folder = "repository_contents"
        target_folder = "functions"
        try:
            download_repo_as_zip(repo_url, token, temp_folder)
            extract_functions_folder(temp_folder, target_folder)
        finally:
            if os.path.exists(temp_folder):
                print(f"Cleaning up temporary folder: {temp_folder}")
                shutil.rmtree(temp_folder)

def load_config():
    dev_config_file = "datastores/config-dev.json"
    prod_config_file = "datastores/config-prod.json"
    config = None
    try:
        with open(dev_config_file, 'r') as f:
            config = json.load(f)
            print(f"Loaded configuration from {dev_config_file}.")
    except FileNotFoundError:
        load_github()
        print(f"{dev_config_file} not found. Trying {prod_config_file}...")
        try:
            with open(prod_config_file, 'r') as f:
                config = json.load(f)
                print(f"Loaded configuration from {prod_config_file}.")
        except FileNotFoundError:
            print(f"Error: Neither {dev_config_file} nor {prod_config_file} could be found.")
            raise
    return config

config = load_config()

# Define the intents you want your bot to have
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent
intents.members = True  # Required to receive member update events
intents.guilds = True   # Required to receive guild events



# Prefix and bot initialization
PREFIX = "!"
# Load application_id as an integer
application_id = int(config['application_id'])
bot = commands.AutoShardedBot(command_prefix=PREFIX, intents=intents, application_id=application_id, help_command=None)

# Set up the database connection
db_config = config['database']
db_connection = mysql.connector.connect(
    host=db_config['host'],
    user=db_config['user'],
    password=db_config['password'],
    database=db_config['database'],
    autocommit=True,  # Enable autocommit to avoid stale connections
    connection_timeout=6000  # Set higher connection timeout
)
# Store the connection in the bot instance
bot.db_connection = db_connection

#bot defaults
bot.subscriber = "Twitch Subscriber"
bot.tier_1 = "Twitch Subscriber: Tier 1"
bot.tier_2 = "Twitch Subscriber: Tier 2"
bot.tier_3 = "Twitch Subscriber: Tier 3"


# Start memory tracking
tracemalloc.start()

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

@bot.event
async def on_ready():
    activity = discord.Activity(type=discord.ActivityType.playing, name=f"MCSync.live")
    await bot.change_presence(status=discord.Status.online, activity=activity)
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    print(f"Shard ID: {bot.shard_id}")
    print(f"Total Shards: {bot.shard_count}")
    
    for shard_id, latency in bot.latencies:
        print(f"Shard ID: {shard_id} | Latency: {latency*1000:.2f}ms")


def datalog(self, type, string):
    time = datetime.now().strftime("%m-%d-%Y %I:%M:%S %p")
    insert_sql = "INSERT INTO logs(time, type, content) VALUES (%s, %s, %s)"
    server_data = (time, type, string)
    self.cursor.execute(insert_sql, server_data)
    self.conn.commit()
    return True

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
    token = config['token']
    bot.run(token, log_handler=handler, log_level=logging.INFO)
