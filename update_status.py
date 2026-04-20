import requests
import os
import sys
import random
import time
from datetime import datetime

def set_github_status(token, message, emoji):
    """Executes the GraphQL mutation with built-in retry logic."""
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
    variables = {"input": {"message": message, "emoji": emoji}}
    
    for attempt in range(3):
        try:
            response = requests.post(
                "https://api.github.com/graphql", 
                json={"query": query, "variables": variables}, 
                headers=headers,
                timeout=15
            )
            return response
        except Exception as e:
            if attempt == 2: raise e
            time.sleep(5)

def update_github_status():
    token = os.getenv('GH_TOKEN')
    base_path = os.path.dirname(os.path.abspath(__file__))
    state_file = os.path.join(base_path, "last_status.txt")
    
    failure_messages = [
        ("Damnit Connor, we’ve got to fix it", ":pensive:"),
        ("Damnit, gotta fix it again", ":weary:"),
        ("Script's broken, fix it Connor", ":wrench:")
    ]

    try:
        # --- 200 ANONYMIZED STATUS POOL ---
        status_pool = [
            # Retro & Math (25)
            ("↑ ↑ ↓ ↓ ← → ← → B A", ":video_game:"), ("Error 404: Status Not Found", ":ghost:"),
            ("Dial-up noises intensifying", ":telephone_receiver:"), ("3.1415926535...", ":pie:"), 
            ("Thinking in 01010110", ":computer:"), ("01001000 01101001", ":wave:"),
            ("The cake is a lie", ":cake:"), ("42", ":four_leaf_clover:"),
            ("Calculating Pi to the last digit", ":abacus:"), ("Waiting for the handshake... 56k", ":fax:"),
            ("127.0.0.1", ":house:"), ("Sudo make me a sandwich", ":bread:"),
            ("Centering a div...", ":distraught:"), ("Keyboard go clack", ":keyboard:"),
            ("Logic error in reality", ":warning:"), ("Buffer overflow in my brain", ":brain:"),
            ("Null pointer exception", ":point_up:"), ("Floating point math is hard", ":curly_loop:"),
            ("Recursion: see status", ":repeat:"), ("Entropy increases", ":cyclone:"),
            ("Hello World.", ":earth_americas:"), ("Parsing life.json", ":file_folder:"),
            ("Garbage collection in progress", ":wastebasket:"), ("Overflowing with data", ":droplet:"),
            ("Encrypted thoughts", ":lock:"),

            # Pop Culture: The Office & Social Network (25)
            ("just setting up my twttr - @jack", ":bird:"), ("Identity theft is not a joke, Jim!", ":clown_face:"),
            ("Threat Level Midnight", ":night_with_stars:"), ("I declare bankruptcy!", ":money_with_wings:"),
            ("World's Best Coder", ":coffee:"), ("Did I stutter?", ":face_with_raised_eyebrow:"),
            ("I’m not superstitious, but I am a little stitious", ":office:"), ("I’m wired.", ":zap:"),
            ("Drop the 'The'. Just 'Social'.", ":link:"), ("I’m CEO, B*tch", ":briefcase:"),
            ("The site is down!", ":warning:"), ("A billion is cooler", ":money_mouth_face:"),
            ("I think if your clients want to sit on my shoulders...", ":man_lifting_weights:"),
            ("You're not even the best Eduardo", ":disappointed:"), ("It's raining in Cambridge", ":cloud_with_rain:"),
            ("Park the car in Harvard Yard", ":blue_car:"), ("The Winklevii are coming", ":rowboat:"),
            ("I was the first to arrive", ":checkered_flag:"), ("Dwight, you ignorant slut", ":fire:"),
            ("That’s what she said", ":eyes:"), ("False. Black bear.", ":bear:"),
            ("Beets. Battlestar Galactica.", ":rocket:"), ("Stanley’s crossword puzzle", ":pencil:"),
            ("Kelly's business school", ":school:"), ("Michael Scott Paper Company", ":page_facing_up:"),

            # Pop Culture: Star Wars, Indy, Gaming (30)
            ("I have a bad feeling about this", ":milky_way:"), ("This is the way", ":garry:"),
            ("Execute Order 66", ":orbit:"), ("Hello there", ":crossed_swords:"),
            ("I am a Jedi, like my father before me", ":sun_with_face:"), ("It belongs in a museum!", ":classical_building:"),
            ("Fortune and glory, kid", ":gold:"), ("Why did it have to be snakes?", ":snake:"),
            ("Cranking 90s", ":bricks:"), ("Where we droppin'?", ":map:"),
            ("Chug Splash time", ":ocean:"), ("Storm's closing in", ":cloud_with_lightning:"),
            ("Mining straight down", ":pick:"), ("Sssshhh... *Boom*", ":creeper:"),
            ("Building a redstone computer", ":red_circle:"), ("Trading with villagers", ":moneybag:"),
            ("Inventory full", ":package:"), ("Achievement Get!", ":trophy:"),
            ("Stealth mode engaged", ":ninja:"), ("Respawning...", ":recycle:"),
            ("Stay on target", ":target:"), ("Use the source, Luke", ":sparkles:"),
            ("The thermal detonator is armed", ":bomb:"), ("Indy's hat", ":tophat:"),
            ("Choose wisely", ":cup_with_straw:"), ("Leeeroy Jenkins", ":crossed_swords:"),
            ("All your base are belong to us", ":alien:"), ("Finish him!", ":fist:"),
            ("It’s dangerous to go alone", ":shield:"), ("The princess is in another castle", ":european_castle:"),

            # Octocat & GitHub Lore (20)
            ("Hanging with Mona the Octocat", ":octocat:"), ("Pushing code to the mothership", ":shipit:"),
            ("Octocat-approved deployment", ":white_check_mark:"), ("Inhabiting the Octoverse", ":telescope:"),
            ("Mona said it looks good to me", ":thumbsup:"), ("GitHub Universe vibes", ":milky_way:"),
            ("Meow-ge conflict", ":crying_cat_face:"), ("Forking reality", ":fork_and_knife:"),
            ("Pull Request accepted", ":ok_hand:"), ("Starring the void", ":star:"),
            ("Main branch only", ":evergreen_tree:"), ("Blaming the git", ":point_right:"),
            ("Committed to the bit", ":memo:"), ("Open source or bust", ":unlock:"),
            ("Squashing bugs", ":bug:"), ("Refactoring the mothership", ":rocket:"),
            ("Staging changes", ":construction:"), ("Merging into the sun", ":sunny:"),
            ("Git-ting things done", ":muscle:"), ("Conflict resolved", ":handshake:"),

            # Generalized Tech & Dev (50)
            ("Linux enthusiast", ":penguin:"), ("Dual-booting into chaos", ":partition:"),
            ("Fans go brrrr", ":dash:"), ("VRAM management is a full-time job", ":memory:"),
            ("LocalStorage is all I need", ":file_cabinet:"), ("No centralized DBs here", ":no_entry:"),
            ("Active Noise Cancellation: ON", ":headphones:"), ("Mobile testing in progress", ":iphone:"),
            ("Building for the vintage web", ":floppy_disk:"), ("Nostr identity verified", ":key:"),
            ("Python script running...", ":snake:"), ("Small web, big dreams", ":house_with_garden:"),
            ("Cooling at max", ":cyclone:"), ("Refactoring for the sake of it", ":hammer:"),
            ("Reading documentation", ":books:"), ("Compiling...", ":hourglass_flowing_sand:"),
            ("Writing tests (allegedly)", ":test_tube:"), ("P2P research", ":link:"),
            ("Procedural world gen experiments", ":earth_americas:"), ("Improving WPM", ":keyboard:"),
            ("Minimalist CSS is the goal", ":art:"), ("Small Web protocol exploration", ":satellite:"),
            ("I’m in the zone", ":man_technologist:"), ("Solving merge conflicts", ":crossed_swords:"),
            ("Optimization in progress", ":rocket:"), ("Dark mode is the only mode", ":night_with_stars:"),
            ("Vim is a way of life", ":memo:"), ("Exit Vim? How?", ":question:"),
            ("Terminal velocity", ":zap:"), ("Bash script magic", ":sparkles:"),
            ("Scripting my own problems", ":robot:"), ("DevTools open 24/7", ":wrench:"),
            ("Console.log('help')", ":scream:"), ("Dockerizing the world", ":whale:"),
            ("Cloud native, local focused", ":cloud:"), ("JSON is my love language", ":heart:"),
            ("Vanilla JS or bust", ":icecream:"), ("Markdown is life", ":memo:"),
            ("Static site generation", ":building_construction:"), ("Peer-to-peer is the future", ":handshake:"),
            ("Reducing dependencies", ":scissors:"), ("Bloatware hater", ":no_entry_sign:"),
            ("Hardware hacking", ":nut_and_bolt:"), ("Kernel panic", ":face_pale_indisposed:"),
            ("Z-index: 9999", ":top:"), ("Flexing my flexbox", ":muscle:"),
            ("Gridlock", ":grid:"), ("Responsive design stress", ":mobile_phone_with_arrow:"),
            ("Backing up... nevermind", ":floppy_disk:"), ("The code works, I don't know why", ":shrug:"),

            # Sci-Fi & Aesthetics (25)
            ("Wake up, Samurai", ":city_sunset:"), ("There is no spoon", ":foggy:"),
            ("Neon nights", ":night_with_stars:"), ("Static in the signal", ":radio:"),
            ("Transmitting from the void", ":satellite_orbital:"), ("Cybernetic soul", ":chip:"),
            ("Androids and electric sheep", ":sheep:"), ("Rage against the machine", ":metal:"),
            ("System shock", ":high_voltage:"), ("Neural link connected", ":link:"),
            ("Chrome and circuit boards", ":mechanical_arm:"), ("Augmented reality", ":fire:"),
            ("The sky is the color of a dead channel", ":tv:"), ("High tech, low life", ":city_sunset:"),
            ("Data runner", ":running:"), ("Icebreaker", ":ice_cube:"),
            ("Netrunner", ":spider_web:"), ("Digital ghost", ":ghost:"),
            ("Sub-routine 42", ":gear:"), ("Glitch in the Matrix", ":zap:"),
            ("Overclocked existence", ":hourglass:"), ("Silicon dreams", ":thought_balloon:"),
            ("Analog heart", ":heart_decoration:"), ("Protocol 0", ":zero:"),
            ("End of line.", ":door:"),

            # Philosophy & Creative (25)
            ("Talk is cheap. Show me the code.", ":speech_balloon:"), ("Code is poetry", ":fountain_pen:"),
            ("Staring into the void", ":black_circle:"), ("Stay hungry, stay foolish", ":apple:"),
            ("Don't panic", ":towel:"), ("Everything is awesome", ":bricks:"),
            ("Converting coffee to code", ":coffee:"), ("Lost in the sauce", ":spaghetti:"),
            ("Digital archaeology", ":urn:"), ("Simulating a personality", ":robot:"),
            ("Less is more", ":heavy_minus_sign:"), ("Keep it simple", ":bulb:"),
            ("Form follows function", ":triangular_ruler:"), ("Think different", ":bulb:"),
            ("Innovate or die", ":rocket:"), ("Move fast, break things", ":boom:"),
            ("The medium is the message", ":tv:"), ("Simplicity is the ultimate sophistication", ":gem:"),
            ("Aesthetics of the early web", ":web:"), ("Digital minimalism", ":leafy_green:"),
            ("Building for humans", ":man:"), ("Designing for the future", ":crystal_ball:"),
            ("Crafting experiences", ":sparkles:"), ("Pixel perfect", ":straight_ruler:"),
            ("The grid is life", ":grid:")
        ]

        # Selection Logic
        last_status = ""
        if os.path.exists(state_file):
            with open(state_file, "r") as f:
                last_status = f.read().strip()

        available_statuses = [s for s in status_pool if s[0] != last_status]
        status_text, emoji = random.choice(available_statuses)

        if not token:
            raise ValueError("Token missing in environment.")

        response = set_github_status(token, status_text, emoji)

        if response.status_code == 200:
            res_data = response.json()
            if "errors" in res_data:
                raise Exception(f"GraphQL: {res_data['errors'][0]['message']}")
            
            with open(state_file, "w") as f:
                f.write(status_text)
            print(f"Status successfully set: {status_text}")
        else:
            raise Exception(f"HTTP {response.status_code}")

    except Exception as e:
        print(f"CRITICAL: {e}")
        fail_text, fail_emoji = random.choice(failure_messages)
        if token:
            try:
                set_github_status(token, fail_text, fail_emoji)
            except:
                pass 
        sys.exit(1)

if __name__ == "__main__":
    update_github_status()
