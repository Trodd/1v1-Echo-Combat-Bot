# 🏆 1v1 Draft Match Bot

A Discord bot for managing 1v1 round-robin drafts, match threads, and win/loss leaderboards — perfect for leagues, tournaments, or competitive communities.

## 🔧 Features

- ✅ Slash command to start draft signups with embedded time and player list
- ✅ Players sign up with buttons (and can unsign)
- 🎮 Auto-generates round robin 1v1 matchups
- 🧵 Creates private threads for each match (visible only to players and admin)
- 🗳️ Map 1–3 score reporting buttons
- ✅ Both players must confirm match results
- 🏆 Leaderboard with W/L/GP (games played), sorted by wins
- 🔒 Close thread button (auto-deletes thread after a delay)
- 🔁 `!undo @user1 @user2` to reopen or recreate deleted threads
- 📤 Results posted as embeds to a public match results channel

## 💬 Commands

### Slash Commands
| Command           | Description                            |
|------------------|----------------------------------------|
| `/start_draft`    | Starts a draft with UNIX timestamp     |
| `/leaderboard`    | Displays player standings leaderboard  |
| `/undo`           | Reopens or remakes a match thread      |


## 🛠️ Setup

1. Clone the repo and install dependencies:
```bash
git clone https://github.com/yourusername/1v1-draft-bot.git
cd 1v1-draft-bot
pip install -r requirements.txt

Edit draft.py:

Set your bot token at the bottom:

python
Copy
Edit
bot.run("YOUR_BOT_TOKEN")
Set your results channel:

python
Copy
Edit
RESULTS_CHANNEL_ID = 123456789012345678
Run the bot:

bash
Copy
Edit
python draft.py
