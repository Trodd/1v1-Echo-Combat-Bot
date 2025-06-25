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
2. Install dependencies:

pip install -r requirements.txt
3. Configure your bot
In draft.py, set the following constants:


RESULTS_CHANNEL_ID = 1374266417364336641       # Results embed channel
LEADERBOARD_CHANNEL_ID = 1374268467079024671   # Leaderboard channel
REQUIRED_ROLE_ID = 1387186995146658013         # Role required to manage matches
At the bottom of the file, add your bot token:


bot.run("YOUR_BOT_TOKEN")
Replace "YOUR_BOT_TOKEN" with your actual bot token from Discord’s Developer Portal.

4. Run the bot
Run the bot using the Windows batch file:


start.bat
Or directly via Python:


python draft.py
🧠 Technical Notes
player_stats.json — stores leaderboard stats

rehydrate.json — stores all active match thread data (including buttons/views)

signups.json — stores current and past signup sessions

banned_players.json — keeps track of players blocked from signing up

Persistent discord.ui.Views are automatically reattached on restart

Uses thread-safe design for ephemeral and permanent data

📝 License
MIT License — free to use, modify, and distribute.


