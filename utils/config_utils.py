import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def load_config():
    """Load configuration entirely from environment variables."""
    config = {
        'token': os.getenv('DISCORD_TOKEN', ''),
        'application_id': int(os.getenv('APPLICATION_ID', '0') or '0'),
        'status': os.getenv('BOT_STATUS', 'loading'),
        'use_Git': os.getenv('USE_GIT', 'false').lower() in ('true', '1', 'yes'),
        'repo_url': os.getenv('REPO_URL', 'https://github.com/captincornflakes/McSync-v2'),
        'repo_temp': os.getenv('REPO_TEMP', 'Discord-Bot-Template-main'),
        'repo_Token': os.getenv('REPO_TOKEN', ''),
        'use_DB': os.getenv('USE_DB', 'true').lower() in ('true', '1', 'yes'),
        'database': {
            'host': os.getenv('DB_HOST', ''),
            'user': os.getenv('DB_USER', ''),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', ''),
            'port': int(os.getenv('DB_PORT', '3306') or '3306')
        }
    }
    
    # Validate required settings
    if not config['token']:
        print("Warning: DISCORD_TOKEN not set in environment variables.")
    if not config['application_id']:
        print("Warning: APPLICATION_ID not set in environment variables.")
    if config['use_DB'] and not all(config['database'].values()):
        print("Warning: Database is enabled but missing configuration (DB_HOST, DB_USER, DB_PASSWORD, DB_NAME).")
    
    print("Configuration loaded from environment variables.")
    return config
