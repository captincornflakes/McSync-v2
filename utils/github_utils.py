import os
import shutil
import zipfile
import io
import requests

def download_repo_as_zip(repo_url, temp_folder, config):
    token = config.get('repo_Token', '')
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

def extract_utils_folder(temp_folder, target_folder):
    repo_folder = os.path.join(temp_folder, "McSync-v2-main")
    utils_folder = os.path.join(repo_folder, "utils")
    if not os.path.exists(utils_folder):
        raise FileNotFoundError(f"'utils' folder not found in {repo_folder}.")
    if os.path.exists(target_folder):
        print(f"Removing existing target folder: {target_folder}")
        shutil.rmtree(target_folder)
    print(f"Copying 'utils' folder to {target_folder}...")
    os.makedirs(target_folder, exist_ok=True)
    for item in os.listdir(utils_folder):
        source = os.path.join(utils_folder, item)
        destination = os.path.join(target_folder, item)
        if os.path.isdir(source):
            shutil.copytree(source, destination, dirs_exist_ok=True)
        else:
            shutil.copy2(source, destination)

def load_github(config):
    if config and config.get('use_Git', False):
        print("Pulling repository from GitHub...")
        repo_url = config.get('repo_url', '')
        temp_folder = "repository_contents"
        if repo_url:
            try:
                download_repo_as_zip(repo_url, temp_folder, config)
                extract_functions_folder(temp_folder, "functions")
                extract_utils_folder(temp_folder, "utils")
            finally:
                if os.path.exists(temp_folder):
                    print(f"Cleaning up temporary folder: {temp_folder}")
                    shutil.rmtree(temp_folder)