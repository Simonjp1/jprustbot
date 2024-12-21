import requests
import discord
from discord.ext import commands
import matplotlib.pyplot as plt
import datetime
import numpy as np
import io
from dotenv import load_dotenv
import os 

# Bot setup
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

load_dotenv("tokens.env")

# Replace these with your API tokens
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN") 
STEAM_API_KEY = os.getenv("STEAM_API_KEY")
API_TOKEN = os.getenv("API_TOKEN")

# Global server ID storage
current_server_id = None

def get_steam_profile(steam_id):
    base_url = "http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/"
    params = {"key": STEAM_API_KEY, "steamids": steam_id}
    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        data = response.json()
        players = data.get("response", {}).get("players", [])
        if players:
            player = players[0]
            profile_name = player.get("personaname", "Unknown")
            profile_state = "Online" if player.get("personastate", 0) > 0 else "Offline"
            profile_created = datetime.datetime.fromtimestamp(player.get("timecreated", 0)).strftime('%Y-%m-%d')

            return {
                "name": profile_name,
                "state": profile_state,
                "created": profile_created
            }
    return None

def fetch_session_data(player_id, server_id=None):
    base_url = f"https://api.battlemetrics.com/players/{player_id}/relationships/sessions"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    params = {"page[size]": 100}
    if server_id:
        params["filter[servers]"] = server_id

    all_sessions = []
    while True:
        response = requests.get(base_url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            sessions = data.get("data", [])
            all_sessions.extend(sessions)

            # Check for pagination
            next_page = data.get("links", {}).get("next")
            if next_page:
                base_url = next_page  # Update URL to the next page
            else:
                break
        else:
            break

    return all_sessions

def calculate_time_stats(sessions):
    first_time = None
    total_time = datetime.timedelta()

    for session in sessions:
        start_time = datetime.datetime.fromisoformat(session["attributes"]["start"].replace("Z", ""))
        stop_time = session["attributes"].get("stop")
        stop_time = datetime.datetime.fromisoformat(stop_time.replace("Z", "")) if stop_time else datetime.datetime.now()

        if not first_time or start_time < first_time:
            first_time = start_time

        total_time += stop_time - start_time

    return first_time, total_time

def format_time_ago(start_time):
    now = datetime.datetime.now()
    delta = now - start_time
    return f"{delta.days} days ago"

def format_time_hours(total_time):
    hours = total_time.total_seconds() // 3600
    return f"{int(hours)} hours"

def process_and_visualize_sessions(sessions):
    session_times = []
    for session in sessions:
        start_time = session["attributes"]["start"]
        stop_time = session["attributes"].get("stop", datetime.datetime.now().isoformat() + "Z")
        session_times.append((start_time, stop_time))

    today = datetime.datetime.now()
    days = [today - datetime.timedelta(days=i) for i in range(14, -1, -1)]
    time_intervals = [datetime.time(hour) for hour in range(0, 24, 3)]
    time_intervals.append(datetime.time(23, 59))

    fig, ax = plt.subplots(figsize=(12, 8))
    fig.patch.set_facecolor('black')
    ax.set_facecolor('black')

    for i, day in enumerate(days):
        for j in range(len(time_intervals) - 1):
            interval_start = datetime.datetime.combine(day, time_intervals[j])
            interval_end = datetime.datetime.combine(day, time_intervals[j + 1])
            ax.barh(i, 3, left=j * 3, color="red", edgecolor="black", align="center")

            for start, stop in session_times:
                start_dt = datetime.datetime.fromisoformat(start.replace("Z", ""))
                stop_dt = datetime.datetime.fromisoformat(stop.replace("Z", ""))
                if interval_start <= stop_dt and interval_end >= start_dt:
                    overlap_start = max(interval_start, start_dt)
                    overlap_end = min(interval_end, stop_dt)
                    interval_duration = (interval_end - interval_start).total_seconds()
                    overlap_duration = (overlap_end - overlap_start).total_seconds()
                    if overlap_duration > 0:
                        green_width = (overlap_duration / interval_duration) * 3
                        ax.barh(i, green_width, left=j * 3 + ((overlap_start - interval_start).total_seconds() / interval_duration) * 3, color="green", edgecolor="black", align="center")

    ax.set_xticks(range(0, 25, 3))
    ax.set_xticklabels([f"{hour:02}:00" for hour in range(0, 24, 3)] + ["24:00"], color="white")
    ax.set_yticks(range(len(days)))
    ax.set_yticklabels([day.strftime('%b %d') for day in days], color="white")
    ax.set_xlabel("Time (Hours)", color="white")
    ax.set_ylabel("Date", color="white")
    ax.set_title("Player Sessions (Last 2 Weeks)", color="white")

    buf = io.BytesIO()
    plt.savefig(buf, format="png", facecolor=fig.get_facecolor())
    buf.seek(0)
    plt.close()
    return buf

@bot.command()
async def setserver(ctx, server_id: str):
    global current_server_id
    current_server_id = server_id
    await ctx.send(f"Server ID has been set to https://www.battlemetrics.com/servers/rust/{server_id}")

@bot.command()
async def player(ctx, *, player_name: str):
    global current_server_id
    if not current_server_id:
        await ctx.send("Please set a server ID first using /setserver.")
        return

    base_url = "https://api.battlemetrics.com/players"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    params = {"filter[search]": player_name, "filter[servers]": current_server_id}

    response = requests.get(base_url, headers=headers, params=params)
    if response.status_code != 200:
        await ctx.send("Failed to fetch player data from BattleMetrics.")
        return

    data = response.json()
    if not data.get("data"):
        await ctx.send("No player found on the specified server.")
        return

    player = data["data"][0]
    player_id = player["id"]
    sessions = fetch_session_data(player_id, current_server_id)

    if not sessions:
        await ctx.send("No session data available for the specified player.")
        return

    first_time, total_time = calculate_time_stats(sessions)

    graph = process_and_visualize_sessions(sessions)
    await ctx.send(f"**Player Name:** {player_name}\n**BattleMetrics URL:** https://www.battlemetrics.com/players/{player_id}\n**First Time on Server:** {format_time_ago(first_time)}\n**Total Time on Server:** {format_time_hours(total_time)}")
    await ctx.send(file=discord.File(graph, "sessions.png"))

@bot.command()
async def id(ctx, steam_id: str):
    global current_server_id
    if not current_server_id:
        await ctx.send("Please set a server ID first using /setserver.")
        return

    steam_profile = get_steam_profile(steam_id)
    if not steam_profile:
        await ctx.send("Failed to fetch Steam profile. Ensure the SteamID is correct.")
        return

    base_url = "https://api.battlemetrics.com/players"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    params = {"filter[search]": steam_profile['name'], "filter[servers]": current_server_id}

    response = requests.get(base_url, headers=headers, params=params)
    if response.status_code != 200:
        await ctx.send("Failed to fetch player data from BattleMetrics.")
        return

    data = response.json()
    if not data.get("data"):
        await ctx.send("No player found on the specified server.")
        return

    player = data["data"][0]
    player_id = player["id"]
    sessions = fetch_session_data(player_id, current_server_id)

    if not sessions:
        await ctx.send("No session data available for the specified player.")
        return

    first_time, total_time = calculate_time_stats(sessions)

    graph = process_and_visualize_sessions(sessions)
    steam_profile_url = f"http://steamcommunity.com/profiles/{steam_id}"
    await ctx.send(f"**Steam Profile:** {steam_profile['name']}\n**Steam Profile Link:** {steam_profile_url}\n**State:** {steam_profile['state']}\n**Created On:** {steam_profile['created']}\n**BattleMetrics URL:** https://www.battlemetrics.com/players/{player_id}\n**First Time on Server:** {format_time_ago(first_time)}\n**Total Time on Server:** {format_time_hours(total_time)}")
    await ctx.send(file=discord.File(graph, "sessions.png"))

bot.run(DISCORD_TOKEN)
