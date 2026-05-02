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

def update_stats(base_path, pool_size, status_text=None, emoji=None, error=None):
    """
    Maintains stats.json. Calculates error rates and manages a rolling 
    history of the last 15 updates. Tracks total status pool size.
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
            "status_pool_count": 0,
            "last_error": "None", "history": []
        }

    stats["total_attempts"] += 1
    stats["last_run"] = now
    stats["status_pool_count"] = pool_size

    if error:
        stats["failure_count"] += 1
        stats["last_error"] = str(error)[:200]
    else:
        stats["success_count"] += 1
        stats["last_error"] = "None"
        if status_text:
            # Stores text and emoji shortcode for dashboard mapping
            stats["history"].insert(0, {
                "time": now, 
                "status": status_text,
                "emoji": emoji
            })
            # Limit history to 15 entries to prevent file bloat
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
    
    # Status pool: Re-integrated requested items + variety expansion (Exactly 200)
    status_pool = [
        # --- REQUESTED ITEMS (35) ---
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
        ("Vanilla JS or bust", ":icecream:"), ("Markdown is life", ":memo:"),
        ("It's not a bug, it's a feature", ":beetle:"), ("Git commit -m 'Fixed everything'", ":package:"),
        ("Compiling...", ":hourglass_flowing_sand:"), ("Rubber ducking through a logic error", ":duck:"),
        ("One does not simply walk into production", ":mountain:"), ("RTFM (Read The Friendly Manual)", ":book:"),
        ("Pythonic by design", ":snake:"), ("The cloud is just someone else's computer", ":cloud:"),
        ("Hello World!", ":earth_americas:"), ("Don't repeat yourself (DRY)", ":droplet:"),
        ("Refactoring for the soul", ":hammer_and_wrench:"),

        # --- THE OFFICE US (35) ---
        ("I’m not superstitious, but I am a little stitious.", ":black_currant:"),
        ("Identity theft is not a joke, Jim!", ":eyeglasses:"),
        ("I declare bankruptcy!", ":money_with_wings:"), ("Threat Level Midnight", ":clapper:"),
        ("Assistant (to the) Regional Manager", ":briefcase:"), ("Bears, beets, Battlestar Galactica.", ":bear:"),
        ("How the turntables...", ":records:"), ("Dwight, you ignorant slut!", ":office:"),
        ("I'm an early bird and a night owl. I'm wise and I have worms.", ":owl:"),
        ("Sometimes I start a sentence and I don't even know where it's going.", ""),
        ("Parkour!", ":person_doing_cartwheel:"), ("Pretzel Day", ":pretzel:"),
        ("The Dundies", ":trophy:"), ("Did I stutter?", ""),
        ("I feel God in this Chili's tonight.", ":hot_pepper:"), ("The worst thing about prison was the Dementors.", ":ghost:"),
        ("Boy, have you lost your mind? Cause I’ll help you find it!", ""), ("Why are you the way that you are?", ""),
        ("Dunder Mifflin, this is Pam.", ":telephone_receiver:"), ("You miss 100% of the shots you don't take. - Michael Scott", ""),
        ("Jim Halpert is a smudge and arrogant.", ""), ("I'm fast. Somewhere between a snake and a mongoose.", ""),
        ("I don't want to work. I just want to bang on this mug all day.", ":coffee:"),
        ("I hate looking at your face. I wanna smash it.", ""), ("Rit-dit-dit-do-doo!", ""),
        ("That’s what she said.", ""), ("I wonder what people like about me. Probably my pigtails.", ""),
        ("If I can't scuba, then what's this all been about?", ":scuba:"), ("Creed Bratton has never stood out. He’s a survivor.", ""),
        ("Everything I have I owe to this job. This stupid, wonderful job.", ""),
        ("Save Bandit!", ":cat:"),
        ("I am running away from my responsibilities. And it feels good.", ":runner:"),
        ("Should have burned this place down when I had the chance.", ":fire:"),
        ("Safety but wait, a second, point of order. Shirley, occupant, which do we use?", ":ambulance:"),
        ("Business unless you’re Kevin.", ":cookie:"),

        # --- CINEMA & CLASSICS (35) ---
        ("Do or do not. There is no try.", ":crossed_swords:"), ("I hate snakes, Jock! I hate 'em!", ":snake:"),
        ("This belongs in a museum!", ":classical_building:"), ("Roads? Where we're going, we don't need roads.", ":red_car:"),
        ("1.21 Gigawatts!", ":high_voltage:"), ("Life finds a way.", ":seedling:"),
        ("Clever girl...", ":sauropod:"), ("Hold on to your butts.", ":smoking:"),
        ("Great Scott!", ":zap:"), ("No ticket!", ":ticket:"),
        ("X never, ever marks the spot.", ":multiplication:"), ("Fortune and glory, kid.", ":coin:"),
        ("I find your lack of faith disturbing.", ":ringed_planet:"), ("Resistance is futile.", ":stop_sign:"),
        ("I'm sorry, Dave. I'm afraid I can't do that.", ":red_circle:"), ("42: The answer to everything", ":key:"),
        ("I'll be back.", ":robot:"), ("Houston, we have a problem.", ":rocket:"),
        ("May the Force be with you.", ":milky_way:"), ("You're gonna need a bigger boat.", ":ship:"),
        ("To infinity and beyond!", ":rocket:"), ("I am your father.", ""),
        ("Elementary, my dear Watson.", ":mag:"), ("Bond. James Bond.", ":suit:"),
        ("Winter is coming.", ":snowflake:"), ("You shall not pass!", ":man_mage:"),
        ("Inconceivable!", ""), ("Follow the white rabbit.", ":rabbit:"),
        ("I'm gonna make him an offer he can't refuse.", ""), ("Keep your friends close, but your enemies closer.", ""),
        ("The first rule of Fight Club is: You do not talk about Fight Club.", ""),
        ("Say 'hello' to my little friend!", ":boom:"), ("Just keep swimming.", ":fish:"),
        ("My precious.", ":ring:"), ("I am Iron Man.", ":mechanical_arm:"),

        # --- VIDEO GAMES (35) ---
        ("The cake is a lie.", ":birthday:"), ("Praise the Sun!", ":sun_with_face:"),
        ("It's dangerous to go alone! Take this.", ":crossed_swords:"), ("Protocol 3: Protect the Pilot", ":robot:"),
        ("Snake? Snake?! SNAKE!!!", ":snake:"), ("Would you kindly?", ":anchor:"),
        ("War. War never changes.", ":radioactive:"), ("Hey! Listen!", ":fairy:"),
        ("Stay awhile and listen.", ":scroll:"), ("Reticulating splines...", ""),
        ("FINISH HIM", ":skull:"), ("Fus Ro Dah!", ":wind_face:"),
        ("Wasted", ""), ("You Died", ""), ("All your base are belong to us", ":video_game:"),
        ("Our princess is in another castle.", ""), ("It's-a me, Mario!", ":mushroom:"),
        ("Had to be me. Someone else might have gotten it wrong.", ""), ("A man chooses, a slave obeys.", ""),
        ("Nothing is true, everything is permitted.", ""), ("Do you get to the Cloud District very often?", ""),
        ("Prepare for unforeseen consequences.", ""), ("Endure and survive.", ""),
        ("Rip and tear, until it is done.", ""), ("May your road lead you to warm sands.", ""),
        ("Wind's howling.", ":wolf:"),
        ("The right man in the wrong place can make all the difference.", ":briefcase:"),
        ("Whether we wanted it or not, we've stepped into a war with the Cabal.", ":ringed_planet:"),
        ("A hunter must hunt.", ":crescent_moon:"),
        ("Kept you waiting, huh?", ":eyeglasses:"), ("Boy!", ":axe:"),
        ("The numbers, Mason! What do they mean?", ":input_numbers:"),
        ("I used to be an adventurer like you, then I took an arrow in the knee.", ":bow_and_arrow:"),
        ("Get over here!", ":chains:"),
        ("Don't make a girl a promise if you know you can't keep it.", ":sparkles:"),

        # --- BRUTALLY HONEST DEV REALITY (35) ---
        ("Writing code that I will hate in six months.", ""), ("It works. I don't know why. I'm not touching it.", ""),
        ("Fixing the fix that broke the fix.", ""), ("My code is a specialized form of art called 'Garbage'.", ""),
        ("Deleting 100 lines of code is more satisfying than writing them.", ":wastebasket:"), ("Segmentation fault (core dumped)", ""),
        ("git commit -m 'fixed bugs by creating new ones'", ""), ("A programmer is a machine that turns caffeine into code.", ":coffee:"),
        ("Documentation is a love letter to your future self.", ""), ("It's not a bug, it's a feature.", ":lady_beetle:"),
        ("Works on my machine.", ":shrug:"), ("Weeks of coding can save you hours of planning.", ""),
        ("Legacy code is code that works.", ""), ("Technical debt is high interest.", ":money_with_wings:"),
        ("If it's not in Git, it doesn't exist.", ""), ("90% of coding is staring at the screen.", ""),
        ("One man's constant is another man's variable.", ""), ("The best code is the code you can delete.", ""),
        ("Real programmers count from 0.", ""), ("Code never lies, comments sometimes do.", ""),
        ("Premature optimization is the root of all evil.", ""), ("First, solve the problem. Then, write the code.", ""),
        ("Code is like humor. If you have to explain it, it’s bad.", ""), ("I'm not procrastinating, I'm asynchronously processing.", ""),
        ("Java is to JavaScript what car is to carpet.", ""), ("A SQL query walks into a bar and asks... 'Can I join you?'", ""),
        ("Two hard things in CS: cache invalidation and naming things.", ""), ("Complexity is the enemy of reliability.", ""),
        ("Experience is the name everyone gives to their mistakes.", ""), ("To err is human, but to really foul things up you need a computer.", ""),
        ("Computers follow instructions, they don't read your mind.", ""), ("Testing leads to failure, and failure leads to understanding.", ""),
        ("Every bug was once a feature request.", ""), ("Refactoring: Because yesterday's me was an idiot.", ""),
        ("There is no such thing as a simple change.", ""),

        # --- LINUX & HARDWARE (35) ---
        ("I use Arch btw", ":penguin:"), ("RTFM", ""),
        ("Flatpak > Snap", ":package:"), ("Compiling the kernel...", ":coffee:"),
        ("Magic smoke containment specialist", ":dash:"), ("Distro hopping again...", ":cyclone:"),
        ("Kernel panic", ":exploding_head:"), ("chmod +x success.sh", ""),
        ("rm -rf /bin/worries", ""), ("grep -r 'meaning_of_life' /dev/null", ""),
        ("Everything is a file.", ""), ("Bash is a dish best served cold.", ""),
        ("Kill -9 everything.", ""), ("Pipe it to /dev/null.", ""),
        ("The BIOS is the boss.", ""), ("Systemd: Love it or leave it.", ""),
        ("Upgrading the firmware... wish me luck.", ""), ("Don't force it, get a bigger hammer.", ":hammer:"),
        ("Thermal paste is not a snack.", ""), ("The hardware works. The software is broken.", ""),
        ("It's a driver issue.", ""), ("Checking disk for errors...", ":mag:"),
        ("Fan speed: Maximum.", ""), ("Overclocked and thermal throttling", ":hot_face:"),
        ("I love the smell of ozone in the morning.", ""), ("Static electricity is my enemy.", ""),
        ("Re-seating the RAM usually works.", ""), ("Cable management is an art form.", ""),
        ("Waiting for the SSH connection...", ""), ("Is the server down or is it just me?", ""),
        ("Tailing the logs...", ":scroll:"), ("Sudo !!", ":zap:"),
        ("4GB of VRAM is enough for anyone... probably.", ":clapper:"),
        ("Minty fresh desktop environment", ":leafy_green:"),
        ("Dual-booting into chaos", ":wavy_dash:"),

        # --- LOGIC, CS THEORY & GENERAL (35) ---
        ("P vs NP: Still undecided", ":thinking:"), ("Recursion: See status for details", ":repeat:"),
        ("Entropy increases", ":cyclone:"), ("Schrödinger's Status", ":cat:"),
        ("Occam's Razor: Simplest is usually right.", ":hocho:"), ("Standard Deviation", ":chart_with_upwards_trend:"),
        ("The universe is a simulation.", ":milky_way:"), ("O(n log n) is efficient enough.", ""),
        ("Correlation is not causation.", ":chart_with_upwards_trend:"), ("Non-deterministic behavior detected.", ":dice:"),
        ("Absolute Zero.", ":snowflake:"), ("Everything is an object", ":package:"),
        ("Garbage collection in progress", ":put_litter_in_its_place:"), ("Hello World", ""),
        ("System.gc();", ""), ("Turing complete", ":checkered_flag:"),
        ("Off-by-one errors are the worst", ":straight_ruler:"), ("Floating point precision is a myth", ":money_with_wings:"),
        ("Race condition in progress...", ":racing_car:"),
        ("Heisenberg's Uncertainty Principle", ":atom_symbol:"), ("Stack Overflow", ":layers:"),
        ("Deadlock detected", ":lock:"), ("Big O: O(1) is the dream", ":rocket:"),
        ("Null pointer exception", ":point_up:"), ("Binary search for meaning", ":mag:"),
        ("Asymptotic complexity", ":chart_with_downwards_trend:"), ("The Halting Problem is unsolvable", ":stop_sign:"),
        ("Finite State Machine", ":gear:"), ("Inheritance: I am my father's son", ":family:"),
        ("Encapsulation is key", ":closed_lock_with_key:"), ("Boolean logic: True or False?", ":switch:"),
        ("Abstractions all the way down", ":arrow_down:"), ("Deterministic chaos", ":twisted_rightwards_arrows:"),
        ("Syntactic sugar", ":candy:"), ("Functional programming for purity", ":alembic:"),

        # --- EMOJI ONLY (35) ---
        (" ", ":computer:"), (" ", ":brain:"), (" ", ":tux:"), (" ", ":zap:"), (" ", ":floppy_disk:"),
        (" ", ":t_rex:"), (" ", ":joystick:"), (" ", ":alien:"), (" ", ":clapper:"), (" ", ":microchip:"),
        (" ", ":rocket:"), (" ", ":saturn:"), (" ", ":telescope:"), (" ", ":gear:"), (" ", ":hammer_and_wrench:"),
        (" ", ":keyboard:"), (" ", ":mouse_three_button:"), (" ", ":desktop_computer:"), (" ", ":battery:"), (" ", ":link:"),
        (" ", ":globe_with_meridians:"), (" ", ":satellite:"), (" ", ":pager:"), (" ", ":radio:"), (" ", ":level_slider:"),
        (" ", ":control_knobs:"), (" ", ":film_projector:"), (" ", ":video_game:"), (" ", ":crystal_ball:"), (" ", ":dna:"),
        (" ", ":atom_symbol:"), (" ", ":alembic:"), (" ", ":black_hole:"), (" ", ":compass:"), (" ", ":hourglass_flowing_sand:"),
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
            
            # Pass both text and emoji to the stats logger
            update_stats(base_path, len(status_pool), status_text=status_text, emoji=emoji)
            print(f"Set: {status_text}")
        else:
            raise Exception(f"HTTP {response.status_code}")

    except Exception as e:
        print(f"Error: {e}")
        # Log failure while preserving the pool size metric
        update_stats(base_path, len(status_pool), error=e)
        sys.exit(1)

if __name__ == "__main__":
    update_github_status()
