
# JP Rust Bot

A Discord bot for tracking Rust players' sessions and activity using the BattleMetrics API and Steam API.

## Features
- Fetches player session data from BattleMetrics.
- Displays session data in a visual timeline for the last two weeks.
- Retrieves player profile details from Steam, including account creation date and online status.
- Supports dynamic server ID configuration for tracking player activity on specific servers.

## Setup Instructions

### 1. Clone the Repository
Clone the repository to your local machine:
```bash
git clone https://github.com/Simonjp1/jprustbot.git
cd jprustbot
```

### 2. Create a Virtual Environment (Optional but Recommended)
Set up a virtual environment to isolate dependencies:
```bash
python -m venv venv
source venv/bin/activate    # On macOS/Linux
venv\Scripts\activate       # On Windows
```

### 3. Install Dependencies
Install all required Python libraries using `pip`:
```bash
pip install -r requirements.txt
```

### 4. Add API Tokens
Create a file named `tokens.env` in the `jprustbot` directory and add your API tokens:
```plaintext
DISCORD_TOKEN=your_actual_discord_token
STEAM_API_KEY=your_actual_steam_api_key
API_TOKEN=your_actual_battlemetrics_api_token
```

### 5. Run the Bot
Start the bot:
```bash
python bot.py
```

## Bot Commands

### `/setserver <server_id>`
Sets the server ID for tracking Rust players. Example:
```
/setserver 1234567890
```
The bot will confirm the server ID and generate a BattleMetrics link.

### `/player <player_name>`
Fetches session data for a specific player on the currently set server. Displays:
- Player's BattleMetrics URL
- First time the player joined the server
- Total time spent on the server
- A visual timeline of sessions over the last two weeks

### `/id <steam_id>`
Fetches information about a player using their Steam ID. Displays:
- Steam profile name and creation date
- Online/offline status
- Player's BattleMetrics URL
- A visual timeline of sessions over the last two weeks



## Disclaimer

This project uses the Steam Web API and the BattleMetrics API to fetch player data and sessions. The use of these APIs complies with their respective terms of service. This project is not affiliated with or endorsed by Steam, Valve Corporation, or BattleMetrics.

Data provided by:
- [Steam Web API](https://partner.steamgames.com/doc/webapi_overview)
- [BattleMetrics API](https://www.battlemetrics.com/developers)
