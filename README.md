# McSync v2.0.0 Beta

## Overview

The **McSync Plugin** is a versatile tool designed to synchronize subscriber counts between Discord and Minecraft. This plugin integrates both platforms, allowing seamless management and synchronization of subscriber data, enhancing interaction between community members and your Minecraft server.

## Features

- **Sync Subscriber Counts:** Automatically sync subscriber counts from Discord to Minecraft and vice versa.
- **Customizable Commands:** Configure commands to manage and display subscriber information.
- **Real-Time Updates:** Get real-time updates on subscriber changes across both platforms.
- **Role Management:** Assign roles based on subscriber count and manage permissions dynamically.

## Installation

### Requirements

- **Discord Bot Token:** A bot token from the [Discord Developer Portal](https://discord.com/developers/applications).
- **Minecraft Server:** A Minecraft server running a compatible plugin loader (e.g., Spigot, Bukkit).
- **Java:** Java Development Kit (JDK) for running Minecraft server plugins.
- **Python:** Python 3.8 or higher for running the Discord bot.

### Setup

1. **Clone the Repository:**

    ```sh
    git clone https://github.com/captincornflakes/McSync-v2.git
    cd McSync-v2
    ```
2. **Install Python Dependencies:**

    ```sh
    pip install -r requirements.txt
    ```

3. **Add the Plugin to Minecraft:**
```
Download the Jar file to your plugins folder

Ensure the Minecraft server is running with the plugin installed and properly configured.
Usage

```
4. **Sync Commands:**
```
Discord / commands:
/setup - (Admin Only) Setsup the server with datastores and channels. 
    Use is (/setup)
/delete - (Admin Only) Deletes the servers datastores. useful for testing. 
    Use is (/delete)
/update - (Admin Only) Updates stored roles in datastores. 
    Use is (/update)
/link - (all users) link the players minecraft username to the account. 
    Use is (/link <Minecraft Name>)
```

MineCraft Commands:
/settoken: Manually trigger a synchronization between Discord and Minecraft.

Syncing:
Subscribers are automatically synced when joining your MineCraft server.

5. **Configuration**

- Discord Bot:
Manage roles and permissions within your Discord server.

- Minecraft Plugin:
Adjust settings in the plugin configuration file to customize synchronization.

##  **Contributing**
Contributions are welcome! Please submit issues and pull requests via GitHub. For major changes, please open an issue to discuss what you would like to change.

##  **Fork the repository.**

Create a new branch (git checkout -b feature-branch).
Commit your changes (git commit -am 'Add new feature').
Push to the branch (git push origin feature-branch).
Create a new Pull Request.


##  **License**
This project is licensed under the MIT License. See the LICENSE file for details.

##  **Contact**
For any questions or support, please contact:

Email: your-email@example.com
GitHub Issues: GitHub Issues