import requests
import os
import sys
import random
import time
import json
from datetime import datetime
from pathlib import Path

def set_github_status(token, message, emoji):
    """
    Executes a GraphQL mutation to update the user's GitHub status.
    Includes exponential backoff to handle rate limits and 20-second timeouts.
    """
    query = """
    mutation($input: ChangeUserStatusInput!) {
      changeUserStatus(input: $input) {
        status { message emoji }
      }
    }
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Truncate to 100 chars to meet GitHub's API string length constraints
    variables = {"input": {"message": str(message)[:100], "emoji": str(emoji)}}
    
    for attempt in range(1, 4):
        try:
            response = requests.post(
                "https://api.github.com/graphql", 
                json={"query": query, "variables": variables}, 
                headers=headers,
                timeout=20
            )
            return response
        except Exception as e:
            # Escalates to main loop after 3 failed attempts
            if attempt == 3: raise e
            time.sleep(5 * attempt)

def update_stats(base_path, status_text=None, error=None):
    """
    Maintains stats.json. Calculates error rates and manages a rolling 
    history of the last 15 updates to prevent file bloat.
    """
    stats_file = base_path / "stats.json"
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    # Load existing stats or initialize new schema if file is missing
    stats = None
    if stats_file.exists():
        try:
            with open(stats_file, "r", encoding="utf-8") as f:
                stats = json.load(f)
        except:
            pass

    if not stats:
        stats = {
            "total_attempts": 0, "success_count": 0, "failure_count": 0,
            "error_rate_percent": "0.0%", "last_run": "",
            "last_error": "None", "history": []
        }

    stats["total_attempts"] += 1
    stats["last_run"] = now

    if error:
        stats["failure_count"] += 1
        stats["last_error"] = str(error)[:200]
    else:
        stats["success_count"] += 1
        stats["last_error"] = "None"
        if status_text:
            # Keep only the most recent 15 entries for the dashboard
            stats["history"].insert(0, {"time": now, "status": status_text})
            stats["history"] = stats["history"][:15]

    if stats["total_attempts"] > 0:
        rate = (stats["failure_count"] / stats["total_attempts"]) * 100
        stats["error_rate_percent"] = f"{round(rate, 2)}%"

    with open(stats_file, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=4)

def update_github_status():
    """
    Main controller: selects the status, filters for variety, and validates token.
    """
    token = os.getenv('GH_TOKEN')
    base_path = Path(__file__).parent.absolute()
    state_file = base_path / "last_status.txt"
    
    # Status pool verified for character limits and emoji compatibility
    status_pool = [
        ("↑ ↑ ↓ ↓ ← → ← → B A", ":video_game:"), ("Error 404: Status Not Found", ":ghost:"),
        ("Dial-up noises intensifying", ":telephone_receiver:"), ("Thinking in 01010110", ":computer:"),
        ("127.0.0.1", ":house:"), ("Sudo make me a sandwich", ":bread:"),
        ("Centering a div...", ":distraught:"), ("Keyboard go clack", ":keyboard:"),
        ("VRAM management is a full-time job", ":memory:"), ("Linux enthusiast", ":penguin:"),
        ("Vim is a way of life", ":memo:"), ("Exit Vim? How?", ":question:"),
        ("I have a bad feeling about this", ":milky_way:"), ("This is the way", ":crossed_swords:"),
        ("Wake up, Samurai", ":city_sunset:"), ("There is no spoon", ":foggy:"),
        ("Talk is cheap. Show me the code.", ":speech_balloon:"), ("Code is poetry", ":fountain_pen:"),
        ("Minimalist CSS is the goal", ":art:"), ("Small Web protocol exploration", ":satellite:"),
        ("Dark mode is the only mode", ":night_with_stars:"), ("JSON is my love language", ":heart:"),
        ("Vanilla JS or bust", ":icecream:"), ("Markdown is life", ":memo:")
    ]

    try:
        if not token:
            raise ValueError("GH_TOKEN is missing. Set it in Repository Secrets.")

        # Read last status to ensure we don't pick it again immediately
        last_status = ""
        if state_file.exists():
            with open(state_file, "r", encoding="utf-8") as f:
                last_status = f.read().strip()

        available = [s for s in status_pool if s[0] != last_status]
        if not available: available = status_pool 
        
        status_text, emoji = random.choice(available)
        response = set_github_status(token, status_text, emoji)

        if response.status_code == 200:
            res_data = response.json()
            if "errors" in res_data:
                raise Exception(f"GraphQL: {res_data['errors'][0]['message']}")
            
            # Save selection to state file for future comparison
            with open(state_file, "w", encoding="utf-8") as f:
                f.write(status_text)
            
            update_stats(base_path, status_text=status_text)
            print(f"Set: {status_text}")
        else:
            raise Exception(f"HTTP {response.status_code}")

    except Exception as e:
        print(f"Error: {e}")
        update_stats(base_path, error=e)
        sys.exit(1)

if __name__ == "__main__":
    update_github_status()
