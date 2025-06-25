# 🏆 1v1-Echo-Combat-Bot

A powerful Discord bot for managing 1v1 **round-robin tournaments**, complete with draft signups, auto-threaded matchups, in-thread score reporting, result confirmation, and a live leaderboard. While originally built for *Echo Combat*, it supports **any 1v1 best-of-3 game format**.

---

## 🔧 Features

- ✅ Slash command to start 1v1 draft signups with a timestamp and optional notes  
- ✅ Players can sign up or unsign with interactive buttons  
- 🎮 Automatically creates **round-robin matchups** between all signed-up players  
- 🧵 Generates **private match threads** visible only to the two players and admin  
- 🗳️ Map score buttons for Map 1, Map 2, Map 3  
- ✅ Match confirmation — both players must confirm  
- 🔁 Confirmations reset if scores are changed to prevent tampering  
- 🧠 Confirmation view shows which players have confirmed so far  
- 🏳️ Forfeit button allows players to concede matches  
- 🛑 Admins can forfeit on behalf of players  
- 🔁 `/undo` reopens a match in the same thread (if it exists), reverts stats, and deletes old result messages  
- 🏆 Live leaderboard auto-updates with wins/losses/games played  
- 🔒 Close button to archive/delete match threads after finalization  
- 📤 Public embed of finalized results to a results channel  
- ♻️ Auto-rehydrates signups and matches after bot restart  
- 📌 Auto-manages thread caps by creating overflow channels  
- 🧑‍⚖️ All critical commands are **role-gated** using `REQUIRED_ROLE_ID`  

---

## 💬 Slash Commands

| Command                 | Description                                              |
|-------------------------|----------------------------------------------------------|
| `/1v1`                  | Starts a 1v1 draft with a time and optional note         |
| `/undo`                 | Resets or reopens a match between two players            |
| `/create_matchups`      | Admin-only: Generates threads for the latest signup      |
| `/clear_signup`         | Admin-only: Deletes latest signup embed and data         |
| `/kick_tourney_player`  | Admin-only: Kicks a user from signup and deletes matches |
| `/ban_tourney_player`   | Admin-only: Bans user from future signups                |
| `/unban_tourney_player` | Admin-only: Removes player from ban list                 |
| `/forfeit_match`        | Admin-only: Forces a forfeit win for a player            |
| `/edit_signup_time`     | Admin-only: Updates the start time of the latest signup  |
| `/edit_signup_note`     | Admin-only: Updates the note section of latest signup    |
| `/end_tournament`       | Admin-only: Archives and deletes all active match threads|

---

## 📦 Requirements

- Python 3.9 or higher  
- `discord.py` ≥ 2.3.2  
- A registered bot via the [Discord Developer Portal](https://discord.com/developers/applications)

---

## 🛠️ Setup

### 1. Clone the repo:

```bash
git clone https://github.com/Trodd/1v1-draft-bot.git
cd 1v1-draft-bot

### 2. Install dependencies:

```bash
pip install -r requirements.txt
```

### 3. Open `draft.py` and fill in the required configuration:

#### ✅ Fill in these at the top:

```python
# -----------FILL IN IDs HERE SO BOT CAN WORK------------------------

RESULTS_CHANNEL_ID = 1374266417364336641       # Channel to post match results
LEADERBOARD_CHANNEL_ID = 1374268467079024671   # Channel to post the leaderboard
REQUIRED_ROLE_ID = 1387186995146658013         # Role required to use /1v1 and /undo

#--------------------------------------------------------------------
```

#### 🔐 Then scroll to the bottom and insert your bot token:

```python
bot.run("YOUR_BOT_TOKEN")
```

Replace `"YOUR_BOT_TOKEN"` with your actual Discord bot token from the Developer Portal.

---

### 4. Run the bot:

```bash
start.bat
```

---

## 🧠 Technical Notes

- Uses `discord.ui.View` for persistent buttons  
- Match state, score confirmations, and signups are rehydrated from disk on bot restart  
- `player_stats.json` stores win/loss/game counts  
- `rehydrate.json` stores active match state  
- `signups.json` stores active signup sessions  

---

## 📝 License

MIT License — free to use, modify, and distribute.


