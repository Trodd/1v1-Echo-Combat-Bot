# 🏆 1v1-Echo-Combat-Bot

A powerful Discord bot for managing 1v1 **round-robin tournaments**, complete with draft signups, auto-threaded matchups, in-thread score reporting, result confirmation, and a live leaderboard. While originally built for *Echo Combat*, it supports **any 1v1 best-of-3 game format**.

---

## 🔧 Features

- ✅ Slash command to start 1v1 draft signups with a timestamp and interactive signup buttons  
- ✅ Players can sign up and remove themselves easily with buttons  
- 🎮 Automatically creates **round-robin** matchups between all signed-up players  
- 🧵 Generates **private match threads** only visible to the two players and the host  
- 🗳️ Score reporting buttons for **Map 1, 2, and 3**  
- ✅ Both players must confirm the results — confirmations reset if scores change  
- 🧠 Score confirmation UI shows who has confirmed so far  
- 🔁 Fully supports undo/reset:
  - Reopens match in the same thread if possible  
  - Deletes old score/results messages and result embeds  
  - Automatically **reverts player stats** if the match was finalized  
- 🏆 Leaderboard with **Wins / Losses / Games Played**, updated live after each match  
- 🔒 Button to **close and delete threads** once finished  
- 📤 Finalized match results are posted to a **public results channel** as embeds  
- ♻️ **Rehydrates all active matches and signups** after a bot restart — including their buttons and state  
- 📌 Handles **thread cap limits** by auto-creating overflow channels  
- 🛡️ Commands are **role-gated** to ensure only authorized users can run `/1v1` and `/undo`  

---

## 💬 Slash Commands

| Command   | Description                                |
|-----------|--------------------------------------------|
| `/1v1`    | Starts a draft using a UNIX timestamp      |
| `/undo`   | Reopens or resets a match between players  |

---

## 📦 Requirements

- Python 3.9 or higher  
- `discord.py` ≥ 2.3.2  
- A registered bot on [Discord Developer Portal](https://discord.com/developers/applications)

---

## 🛠️ Setup

### 1. Clone the repo:

```bash
git clone https://github.com/Trodd/1v1-draft-bot.git
cd 1v1-draft-bot
2. Install dependencies:
bash
Copy
Edit
pip install -r requirements.txt
3. Open draft.py and fill in the required configuration:
✅ Fill in these at the top:
python
Copy
Edit
# -----------FILL IN IDs HERE SO BOT CAN WORK------------------------

RESULTS_CHANNEL_ID = 1374266417364336641       # Channel to post match results
LEADERBOARD_CHANNEL_ID = 1374268467079024671   # Channel to post the leaderboard
REQUIRED_ROLE_ID = 1387186995146658013         # Role required to use /1v1 and /undo

#--------------------------------------------------------------------
🔐 Then scroll to the bottom and insert your bot token:
python
Copy
Edit
bot.run("YOUR_BOT_TOKEN")
Replace "YOUR_BOT_TOKEN" with your actual Discord bot token from the Developer Portal.

4. Run the bot:
bash
Copy
Edit
start.bat
🧠 Technical Notes
Uses discord.ui.View for persistent buttons

Match state, score confirmations, and signups are rehydrated from disk on bot restart

player_stats.json stores win/loss/game counts

rehydrate.json stores active match state

signups.json stores active signup sessions

📝 License
MIT License — free to use, modify, and distribute.
Works across bot restarts without losing match state

📝 License
MIT License — free to use, modify, and distribute.
