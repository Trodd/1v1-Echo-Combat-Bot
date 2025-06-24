🏆 1v1-Echo-Combat-Bot
A powerful Discord bot for managing 1v1 round-robin tournaments, complete with draft signups, auto-threaded matchups, in-thread score reporting, result confirmation, and a live leaderboard. While originally built for Echo Combat, it supports any 1v1 best-of-3 game format.

🔧 Features
✅ Slash command to start 1v1 draft signups with a timestamp and interactive signup buttons

✅ Players can sign up and remove themselves easily with buttons

🎮 Automatically creates round-robin matchups between all signed-up players

🧵 Generates private match threads only visible to the two players and the host

🗳️ Score reporting buttons for Map 1, 2, and 3

✅ Both players must confirm the results — confirms reset if scores change

🧠 Score confirmation UI displays who has confirmed so far

🧼 Fully supports undo/reset:

Reopen match in same thread if possible

Deletes old score/results embeds

Automatically reverts player stats if the match was finalized

🏆 Leaderboard with Wins / Losses / Games Played, updated live after each match

🔒 Button to close and delete threads once finished

📤 Finalized match results are posted to a public results channel as embeds

♻️ Rehydrates all active matches and signups after a bot restart — including their buttons and state

📌 Handles thread cap limits by auto-creating overflow channels

🛡️ Commands are role-gated to ensure only authorized users can run /1v1 and /undo

💬 Slash Commands
Command	Description
/1v1	Starts a draft using a UNIX timestamp
/undo	Reopens or resets a match between two users

📦 Requirements
Python 3.9 or higher

discord.py ≥ 2.3.2

Create a Discord bot and add it to your server

🛠️ Setup
Clone the repo:

bash
Copy
Edit
git clone https://github.com/Trodd/1v1-draft-bot.git
cd 1v1-draft-bot
Install dependencies:

bash
Copy
Edit
pip install -r requirements.txt
Configure your draft.py:

Replace the token:

python
Copy
Edit
bot.run("YOUR_BOT_TOKEN")
Set your channel IDs:

python
Copy
Edit
RESULTS_CHANNEL_ID = 123456789012345678
LEADERBOARD_CHANNEL_ID = 123456789012345679
REQUIRED_ROLE_ID = 123456789012345680  # (Role required to use /1v1 or /undo)
Start the bot:

bash
Copy
Edit
start.bat
🧠 Technical Notes
Uses discord.ui.View for persistent buttons

Supports full rehydration via:

rehydrate.json (active matches & confirmations)

signups.json (active signup embeds)

All win/loss data is stored in player_stats.json

Slash commands registered automatically on startup

Works across bot restarts without losing match state

📝 License
MIT License — free to use, modify, and distribute.
