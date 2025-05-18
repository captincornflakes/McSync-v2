import json

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
            raise
    return config