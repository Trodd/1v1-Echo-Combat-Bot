# 🏆 1v1-Echo-Combat-Bot

A Discord bot for managing 1v1 round-robin drafts, match threads, and win/loss leaderboards — perfect for leagues, tournaments, or competitive communities.
It technically can be used for any type of 1v1 best of 3 type of round-robin mode, but was mainly built for Echo Combat.

## 🔧 Features

- ✅ Slash command to start draft signups with embedded time and player list
- ✅ Players sign up with buttons (and can unsign)
- 🎮 Auto-generates round robin 1v1 matchups
- 🧵 Creates private threads for each match (visible only to players and admin)
- 🗳️ Map 1–3 score reporting buttons
- ✅ Both players must confirm match results
- 🏆 Leaderboard with W/L/GP (games played), sorted by wins
- 🔒 Close thread button (auto-deletes thread after a delay)
- 📤 Results posted as embeds to a public match results channel

## 💬 Commands

### Slash Commands
| Command           | Description                            |
|------------------|----------------------------------------|
| `/start_draft`    | Starts a draft with UNIX timestamp     |
| `/leaderboard`    | Displays player standings leaderboard  |
| `/undo`           | Reopens or remakes a match thread      |

## 📦 Requirements

- Python 3.9 or higher (https://www.python.org/downloads/)
- discord.py >= 2.3.2 (installed via pip)

## 🛠️ Setup

1. Clone the repo and install dependencies:
    ```bash
    git clone https://github.com/Trodd/1v1-draft-bot.git
    cd 1v1-draft-bot
    pip install -r requirements.txt
    ```

2. Edit `draft.py`:
    - Set your bot token at the bottom:
        ```python
        bot.run("YOUR_BOT_TOKEN")
        ```
    - Set your results channel:
        ```python
        RESULTS_CHANNEL_ID = 123456789012345678
        ```

3. Run the bot:
    ```bash
   start.bat
    ```

## 🧠 Notes

- Uses `discord.py 2.x` with `discord.ui` views and slash command support
- All match data and player stats are stored in `player_stats.json`
- Temporary match state (buttons, confirmations) is stored in memory

## 📝 License

MIT License. Free to use, modify, and share.
