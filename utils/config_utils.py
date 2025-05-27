import json
import os

def load_config():
    dev_config_file = "datastores/config-dev.json"
    prod_config_file = "datastores/config-prod.json"
    config = None
    try:
        with open(dev_config_file, 'r') as f:
            config = json.load(f)
            print(f"Loading configuration from {dev_config_file}.")
    except FileNotFoundError:
        print(f"{dev_config_file} not found. Trying {prod_config_file}...")
        try:
            with open(prod_config_file, 'r') as f:
                config = json.load(f)
                print(f"Loading configuration from {prod_config_file}.")
        except FileNotFoundError:
            print(f"Error: Neither {dev_config_file} nor {prod_config_file} could be found.")
            print("Generating default config at datastores/config-prod.json ...")
            generate_default_config("datastores/config-prod.json")
            with open(dev_config_file, 'r') as f:
                config = json.load(f)
    return config

def generate_default_config(path="datastores/config-prod.json"):
    """Generate a default config file at the given path."""
    default_config = {
        "token": "",
        "application_id": 0,
        "status": "loading",
        "use_Git": False,
        "repo_url": "https://github.com/captincornflakes/McSync-v2",
        "repo_temp": "Disocrd-Bot-Template-main",
        "repo_Token": "",
        "use_DB": True,
        "database": {
            "host": "",
            "user": "",
            "password": "",
            "database": ""
        }
    }
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(default_config, f, indent=4)
    print(f"Default config generated at {path}")