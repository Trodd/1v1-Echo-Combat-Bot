import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone
import itertools
import json
import os
import asyncio
import re

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# -----------FILL IN IDs HERE SO BOT CAN WORK------------------------

RESULTS_CHANNEL_ID = 1374266417364336641                       # <---------------
LEADERBOARD_CHANNEL_ID = 1374268467079024671                   # <---------------       
REQUIRED_ROLE_ID = 1387186995146658013                          # <---------------

#--------------------------------------------------------------------

player_stats = {}
match_results = {}
STATS_FILE = "player_stats.json"
match_lookup = {}
REHYDRATE_FILE = "rehydrate.json"

def save_rehydrate():
    serializable = {}
    for thread_id, data in match_results.items():
        copy = data.copy()
        if isinstance(copy.get("confirmed"), set):
            copy["confirmed"] = list(copy["confirmed"])
        serializable[thread_id] = copy

    with open(REHYDRATE_FILE, "w") as f:
        json.dump(serializable, f)


def load_rehydrate():
    global match_results
    raw = safe_load_json(REHYDRATE_FILE)
    if raw:
        for tid, data in raw.items():
            if "confirmed" in data and isinstance(data["confirmed"], list):
                data["confirmed"] = set(data["confirmed"])
        match_results = raw
    else:
        match_results = {}


def load_stats():
    global player_stats
    raw = safe_load_json(STATS_FILE)
    if raw:
        player_stats = raw
    else:
        player_stats = {}


def save_stats():
    with open(STATS_FILE, "w") as f:
        json.dump(player_stats, f)

def ensure_stat(uid):
    uid = str(uid)
    if uid not in player_stats:
        player_stats[uid] = {"wins": 0, "losses": 0, "games": 0}
    return player_stats[uid]

def safe_load_json(filepath):
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, "r") as f:
            content = f.read().strip()
            if content:
                return json.loads(content)
    except json.JSONDecodeError:
        print(f"⚠️ {filepath} is invalid JSON.")
    return None


# === Match View Logic ===
class MatchView(discord.ui.View):
    def __init__(self, player1, player2, admin_id, thread_id):
        super().__init__(timeout=None)
        self.p1 = player1
        self.p2 = player2
        self.admin_id = admin_id
        self.thread_id = thread_id
        self.score_msg = None
        match_results[thread_id] = {
            "scores": {},
            "confirmed": set(),
            "admin_id": admin_id,
            "players": [player1.id, player2.id],
            "score_msg": None
        }
        save_rehydrate()

    def record_score(self, map_number, winner_id):
        match_results[self.thread_id]["scores"][map_number] = f"<@{winner_id}>"

    def is_ready_to_finalize(self):
        scores = match_results[self.thread_id]["scores"]
        if len(scores) < 2:
            return False
        p1_wins = list(scores.values()).count(f"<@{self.p1.id}>")
        p2_wins = list(scores.values()).count(f"<@{self.p2.id}>")
        return p1_wins >= 2 or p2_wins >= 2

    def apply_result(self):
        scores = match_results[self.thread_id]["scores"]
        p1_count = list(scores.values()).count(f"<@{self.p1.id}>")
        p2_count = list(scores.values()).count(f"<@{self.p2.id}>")
        winner = self.p1 if p1_count > p2_count else self.p2
        loser = self.p2 if winner == self.p1 else self.p1

        if not match_results[self.thread_id].get("forfeit"):
            ensure_stat(winner.id)
            ensure_stat(loser.id)
            player_stats[str(winner.id)]["wins"] += 1
            player_stats[str(winner.id)]["games"] += 1
            player_stats[str(loser.id)]["losses"] += 1
            player_stats[str(loser.id)]["games"] += 1
            save_stats()

        return winner, loser, p1_count, p2_count

    async def update_score_message(self, thread):
        s = match_results[self.thread_id]["scores"]
        confirmed_ids = match_results[self.thread_id].get("confirmed", set())
        confirmed_users = [f"<@{uid}>" for uid in confirmed_ids]

        lines = [
            "**Scores**",
            f"Map 1: {s.get(1, '⏳')}",
            f"Map 2: {s.get(2, '⏳')}",
            f"Map 3: {s.get(3, '⏳')}",
            "",
            f"✅ Confirmed: {', '.join(confirmed_users) if confirmed_users else '*No one yet*'}"
        ]
        content = "\n".join(lines)

        if self.score_msg:
            await self.score_msg.edit(content=content)
        else:
            self.score_msg = await thread.send(content)
            match_results[self.thread_id]["score_msg"] = self.score_msg.id
            bot.add_view(self, message_id=self.score_msg.id)
        save_rehydrate()

    async def handle_click(self, interaction, map_number, winner):
        if interaction.user.id not in [self.p1.id, self.p2.id]:
            return await interaction.response.send_message("Not your match.", ephemeral=True)

        # Invalidate all confirmations on any score change
        match_results[self.thread_id]["confirmed"] = set()

        self.record_score(map_number, winner.id)
        await self.update_score_message(interaction.channel)
        save_rehydrate()

        if not interaction.response.is_done():
            await interaction.response.defer()

    @discord.ui.button(label="Map 1", style=discord.ButtonStyle.green, custom_id="match_map1")
    async def map1(self, interaction, button):
        button.label = f"Map 1 - {interaction.user.display_name} Wins"
        await self.handle_click(interaction, 1, interaction.user)

    @discord.ui.button(label="Map 2", style=discord.ButtonStyle.blurple, custom_id="match_map2")
    async def map2(self, interaction, button):
        button.label = f"Map 2 - {interaction.user.display_name} Wins"
        await self.handle_click(interaction, 2, interaction.user)

    @discord.ui.button(label="Map 3", style=discord.ButtonStyle.gray, custom_id="match_map3")
    async def map3(self, interaction, button):
        button.label = f"Map 3 - {interaction.user.display_name} Wins"
        await self.handle_click(interaction, 3, interaction.user)

    @discord.ui.button(label="✅ Confirm Result", style=discord.ButtonStyle.success, custom_id="match_confirm")
    async def confirm(self, interaction, button):
        data = match_results[self.thread_id]

        # Add the confirmer
        data["confirmed"].add(interaction.user.id)

        # Update visible message to show confirmed users
        await self.update_score_message(interaction.channel)

        # Check if enough maps are scored
        if not self.is_ready_to_finalize():
            return await interaction.response.send_message("Not enough maps scored.", ephemeral=True)

        # Finalize if both players confirmed
        if self.p1.id in data["confirmed"] and self.p2.id in data["confirmed"]:
            winner, loser, w_score, l_score = self.apply_result()
            result_msg = await interaction.channel.send(f"🏆 Match complete. Winner: <@{winner.id}>")
            match_results[self.thread_id]["result_msg"] = result_msg.id

            results_channel = bot.get_channel(RESULTS_CHANNEL_ID)
            if results_channel:
                embed = discord.Embed(
                    title="📊 Match Result",
                    color=discord.Color.blue()
                )
                embed.add_field(name="Players", value=f"<@{self.p1.id}> vs <@{self.p2.id}>", inline=False)
                embed.add_field(name="Winner", value=f"🏆 <@{winner.id}>", inline=True)
                embed.add_field(name="Final Score", value=f"{w_score} - {l_score}", inline=True)
                embed.set_footer(text="Best of 3 — Submitted via match thread")
                results_embed_msg = await results_channel.send(embed=embed)
                match_results[self.thread_id]["results_embed_msg"] = results_embed_msg.id

            # Replace match view with close thread button
            close_view = CloseThreadView(self.p1.id, self.p2.id, self.admin_id)
            msg = await interaction.message.edit(view=close_view)
            match_results[self.thread_id]["close_msg"] = msg.id
            bot.add_view(close_view, message_id=msg.id)

            match_results[self.thread_id]["finalized"] = True
            save_rehydrate()
            await update_leaderboard_message()

            # Acknowledge interaction quietly
            if not interaction.response.is_done():
                await interaction.response.defer()
        else:
            await interaction.response.send_message("Waiting for both confirmations.", ephemeral=True)
    
    @discord.ui.button(label="🏳️ Forfeit", style=discord.ButtonStyle.danger, custom_id="match_forfeit")
    async def forfeit(self, interaction: discord.Interaction, button):
        if interaction.user.id not in [self.p1.id, self.p2.id]:
            return await interaction.response.send_message("You're not part of this match.", ephemeral=True)

        forfeiter = interaction.user
        winner = self.p2 if forfeiter.id == self.p1.id else self.p1

        match_results[self.thread_id]["scores"] = {
            1: f"<@{winner.id}>",
            2: f"<@{winner.id}>"
        }
        match_results[self.thread_id]["confirmed"] = {self.p1.id, self.p2.id}

        await self.update_score_message(interaction.channel)

        result_msg = await interaction.channel.send(f"🏳️ <@{forfeiter.id}> forfeited. <@{winner.id}> wins by default.")
        match_results[self.thread_id]["result_msg"] = result_msg.id

        # Finalize flow
        match_results[self.thread_id]["forfeit"] = True
        winner, loser, w_score, l_score = self.apply_result()
        results_channel = bot.get_channel(RESULTS_CHANNEL_ID)
        if results_channel:
            embed = discord.Embed(
                title="📊 Match Result (Forfeit)",
                color=discord.Color.red()
            )
            embed.add_field(name="Players", value=f"<@{self.p1.id}> vs <@{self.p2.id}>", inline=False)
            embed.add_field(name="Winner", value=f"🏆 <@{winner.id}>", inline=True)
            embed.add_field(name="Result", value=f"Won by forfeit", inline=True)
            embed.set_footer(text="Best of 3 — Submitted via match thread")
            results_embed_msg = await results_channel.send(embed=embed)
            match_results[self.thread_id]["results_embed_msg"] = results_embed_msg.id

        close_view = CloseThreadView(self.p1.id, self.p2.id, self.admin_id)
        msg = await interaction.message.edit(view=close_view)
        match_results[self.thread_id]["close_msg"] = msg.id
        bot.add_view(close_view, message_id=msg.id)
        match_results[self.thread_id]["finalized"] = True
        save_rehydrate()

        await interaction.response.send_message("Match forfeited and recorded.", ephemeral=True)

class CloseThreadView(discord.ui.View):
    def __init__(self, p1_id, p2_id, admin_id):
        super().__init__(timeout=None)
        self.allowed_ids = {p1_id, p2_id, admin_id}

    @discord.ui.button(label="🔒 Close Thread", style=discord.ButtonStyle.danger, custom_id="close_thread")
    async def close_thread(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in self.allowed_ids:
            return await interaction.response.send_message("You're not allowed to close this thread.", ephemeral=True)

        # ✅ Acknowledge interaction early
        await interaction.response.send_message("Thread will be closed and deleted shortly...", ephemeral=True)

        try:
            await interaction.channel.edit(archived=True, locked=True)
        except Exception as e:
            print(f"⚠️ Failed to lock thread: {e}")

        await asyncio.sleep(5)

        try:
            await interaction.channel.delete()
        except discord.Forbidden:
            print(f"❌ Failed to delete thread {interaction.channel.name} (no permissions).")
        except Exception as e:
            print(f"❌ Error deleting thread: {e}")

# === Signup View ===
class SignupView(discord.ui.View):
    def __init__(self, admin_id, event_time):
        super().__init__(timeout=None)
        self.players = []
        self.admin_id = admin_id
        self.event_time = event_time
        self.notes = ""
        self.embed_msg = None

    def save_signup(self):
        if not self.embed_msg:
            return

        signup_data = {
            "message_id": self.embed_msg.id,
            "channel_id": self.embed_msg.channel.id,
            "admin_id": self.admin_id,
            "event_time": self.event_time.isoformat(),
            "players": [p.id for p in self.players],
            "notes": self.notes,
            "notes": getattr(self, "notes", "")
        }

        all_signups = []
        if os.path.exists("signups.json"):
            try:
                with open("signups.json", "r") as f:
                    content = f.read().strip()
                    if content:
                        all_signups = json.loads(content)
            except json.JSONDecodeError:
                print("⚠️ signups.json invalid — resetting.")

        for i, data in enumerate(all_signups):
            if data["message_id"] == signup_data["message_id"]:
                all_signups[i] = signup_data
                break
        else:
            all_signups.append(signup_data)

        with open("signups.json", "w") as f:
            json.dump(all_signups, f)

    async def update_embed(self):
        embed = discord.Embed(
            title="🎯 1v1 Echo Combat Signups",
            description=f"🕒 Starts: <t:{int(self.event_time.timestamp())}:F>\n\n"
                        "**Players Signed Up:**\n" +
                        ("\n".join(f"• <@{p.id}>" for p in self.players) or "*No players yet*"),
            color=discord.Color.green()
        )

        # ✅ Add notes if available
        if getattr(self, "notes", "").strip():
            embed.add_field(name="📝 Notes", value=self.notes.strip(), inline=False)

        await self.embed_msg.edit(embed=embed, view=self)

    @discord.ui.button(label="✅ Sign Up", style=discord.ButtonStyle.green, custom_id="signup")
    async def signup(self, interaction: discord.Interaction, button):
        try:
            with open("banned_players.json", "r") as f:
                banned = json.load(f)
        except:
            banned = []

        if interaction.user.id in banned:
            return await interaction.response.send_message("🚫 You are banned from this tournament.", ephemeral=True)

        if interaction.user in self.players:
            return await interaction.response.send_message("You're already signed up.", ephemeral=True)
        self.players.append(interaction.user)
        await self.update_embed()
        self.save_signup()
        await interaction.response.send_message("Signed up!", ephemeral=True)

    @discord.ui.button(label="❌ Unsign", style=discord.ButtonStyle.red, custom_id="unsign")
    async def unsign(self, interaction: discord.Interaction, button):
        if interaction.user not in self.players:
            return await interaction.response.send_message("You weren't signed up.", ephemeral=True)
        self.players.remove(interaction.user)
        await self.update_embed()
        self.save_signup()
        await interaction.response.send_message("You have been removed from signups.", ephemeral=True)

# === Commands ===
@bot.tree.command(name="1v1", description="Start a 1v1 draft")
@app_commands.describe(
    start_time="Match start time as UNIX timestamp (e.g., <t:TIMESTAMP:F>)",
    note="Optional notes to include in the signup embed"
)
async def start_draft(interaction: discord.Interaction, start_time: str, note: str = ""):

    role = discord.utils.get(interaction.guild.roles, id=REQUIRED_ROLE_ID)

    if role is None:
        return await interaction.response.send_message("⚠️ Required role not found in this server.", ephemeral=True)

    if role not in interaction.user.roles:
        return await interaction.response.send_message(
            f"⛔ You must have the `{role.name}` role to use this command.",
            ephemeral=True
        )

    try:
        match = re.search(r"<t:(\d+):[a-zA-Z]?>", start_time)
        if match:
            timestamp = int(match.group(1))
        else:
            timestamp = int(start_time)  # fallback if raw timestamp

        event_time = datetime.fromtimestamp(timestamp, timezone.utc)
    except:
        return await interaction.response.send_message("Invalid timestamp format.", ephemeral=True)

    view = SignupView(admin_id=interaction.user.id, event_time=event_time)
    view.notes = note.strip()
    embed = discord.Embed(
        title="🎯 1v1 Draft Signups",
        description=f"🕒 Starts: <t:{int(event_time.timestamp())}:F>\n\n**Players Signed Up:**\n*No players yet*",
        color=discord.Color.green()
    )
    msg = await interaction.channel.send(embed=embed, view=view)
    view.embed_msg = msg
    await view.update_embed()
    view.save_signup()
    bot.add_view(view, message_id=msg.id)

    await interaction.response.send_message("Draft started!", ephemeral=True)


async def update_leaderboard_message():
    if not player_stats:
        return

    channel = bot.get_channel(LEADERBOARD_CHANNEL_ID)
    if not channel:
        print("⚠️ Leaderboard channel not found.")
        return

    msg_id_file = "leaderboard_message_id.txt"
    message = None
    if os.path.exists(msg_id_file):
        try:
            with open(msg_id_file, "r") as f:
                message_id = int(f.read().strip())
                message = await channel.fetch_message(message_id)
        except:
            pass

    sorted_stats = sorted(player_stats.items(), key=lambda x: x[1]["wins"], reverse=True)
    embed = discord.Embed(title="🏆 1v1 Leaderboard", color=discord.Color.gold())
    for idx, (uid, stats) in enumerate(sorted_stats[:15], start=1):
        try:
            user = await bot.fetch_user(int(uid))
            name = user.display_name
        except:
            name = f"User-{uid[:5]}"
        wins = stats["wins"]
        losses = stats["losses"]
        games = stats["games"]
        embed.add_field(
            name=f"**{idx}. {name}**",
            value=f"🏅 **Wins:** {wins}  ❌ **Losses:** {losses}  🎮 **Games:** {games}",
            inline=False
        )

    if message:
        await message.edit(embed=embed)
    else:
        message = await channel.send(embed=embed)
        with open(msg_id_file, "w") as f:
            f.write(str(message.id))

@bot.tree.command(name="create_matchups", description="Create 1v1 match threads from the latest signup")
async def create_matchups(interaction: discord.Interaction):
    role = discord.utils.get(interaction.guild.roles, id=REQUIRED_ROLE_ID)
    if role not in interaction.user.roles:
        return await interaction.response.send_message(
            f"⛔ You must have the `{role.name}` role to use this command.",
            ephemeral=True
        )

    # Load signups.json
    try:
        with open("signups.json", "r") as f:
            all_signups = json.load(f)
    except Exception as e:
        return await interaction.response.send_message(f"❌ Failed to load signups.json: {e}", ephemeral=True)

    if not all_signups:
        return await interaction.response.send_message("⚠️ No signups found.", ephemeral=True)

    # Get the most recent one (last in the list)
    signup_data = all_signups[-1]
    players = [await bot.fetch_user(uid) for uid in signup_data["players"]]
    if len(players) < 2:
        return await interaction.response.send_message("❌ Not enough players to create matchups.", ephemeral=True)

    await interaction.response.defer(ephemeral=True, thinking=True)

    combos = list(itertools.combinations(players, 2))
    parent_channel = interaction.channel
    guild = interaction.guild

    for p1, p2 in combos:
        all_threads = await guild.active_threads()
        active_threads = [t for t in all_threads if t.parent_id == parent_channel.id]

        if len(active_threads) >= 50:
            i = 1
            while True:
                temp_name = f"combat-1v1-overflow-{i}"
                existing = discord.utils.get(guild.text_channels, name=temp_name)
                if not existing:
                    break
                i += 1

            parent_channel = await guild.create_text_channel(
                name=temp_name,
                overwrites={
                    guild.default_role: discord.PermissionOverwrite(send_messages=False, view_channel=True),
                    guild.me: discord.PermissionOverwrite(send_messages=True, manage_channels=True)
                },
                reason="Auto-created fallback channel due to thread cap"
            )

        thread = await parent_channel.create_thread(
            name=f"{p1.name}_vs_{p2.name}",
            type=discord.ChannelType.private_thread,
            invitable=False
        )

        await thread.add_user(p1)
        await thread.add_user(p2)
        await thread.add_user(interaction.user)

        match_results[thread.id] = {
            "scores": {},
            "confirmed": set(),
            "admin_id": interaction.user.id,
            "players": [p1.id, p2.id]
        }
        match_lookup[tuple(sorted([p1.id, p2.id]))] = thread.id

        view = MatchView(p1, p2, interaction.user.id, thread.id)
        msg = await thread.send(
            f"**Match:** <@{p1.id}> vs <@{p2.id}>\nUse the buttons below to report map results.",
            view=view
        )
        view.score_msg = msg
        match_results[thread.id]["score_msg"] = msg.id
        bot.add_view(view, message_id=msg.id)
        save_rehydrate()

    await interaction.followup.send("✅ Round robin matches created from latest signup.", ephemeral=True)

@bot.tree.command(name="undo", description="Undo a match by player pair")
@app_commands.describe(user1="First player", user2="Second player")
async def undo(interaction: discord.Interaction, user1: discord.User, user2: discord.User):
    role = discord.utils.get(interaction.guild.roles, id=REQUIRED_ROLE_ID)

    if role is None:
        return await interaction.response.send_message("⚠️ Required role not found in this server.", ephemeral=True)

    if role not in interaction.user.roles:
        return await interaction.response.send_message(
            f"⛔ You must have the `{role.name}` role to use this command.",
            ephemeral=True
        )

    if interaction.user.bot:
        return

    def revert_stats_if_finalized(tid):
        if tid not in match_results:
            return
        data = match_results[tid]
        if not data.get("finalized"):
            return

        scores = data.get("scores", {})
        p1_id, p2_id = data["players"]
        p1 = str(p1_id)
        p2 = str(p2_id)

        p1_wins = list(scores.values()).count(f"<@{p1_id}>")
        p2_wins = list(scores.values()).count(f"<@{p2_id}>")

        if p1_wins == p2_wins:
            return  # no clear winner

        winner, loser = (p1, p2) if p1_wins > p2_wins else (p2, p1)

        for pid in [winner, loser]:
            ensure_stat(pid)

        player_stats[winner]["wins"] = max(0, player_stats[winner]["wins"] - 1)
        player_stats[loser]["losses"] = max(0, player_stats[loser]["losses"] - 1)
        player_stats[winner]["games"] = max(0, player_stats[winner]["games"] - 1)
        player_stats[loser]["games"] = max(0, player_stats[loser]["games"] - 1)

        save_stats()

    current_channel = interaction.channel

    # ✅ Case 1: undo inside thread
    if isinstance(current_channel, discord.Thread):
        thread_id = current_channel.id
        data = match_results.get(thread_id)
        
        # Check if players match the undo request
        if data and set(data["players"]) == {user1.id, user2.id}:
            revert_stats_if_finalized(thread_id)

            # 🧹 Delete old score/result messages if they exist
            old_data = match_results.get(thread_id)
            if old_data:
                for key in ("score_msg", "result_msg", "results_embed_msg"):
                    msg_id = old_data.get(key)
                    if msg_id:
                        try:
                            if key == "results_embed_msg":
                                results_channel = bot.get_channel(RESULTS_CHANNEL_ID)
                                if results_channel:
                                    msg = await results_channel.fetch_message(msg_id)
                                    await msg.delete()
                                    print(f"✅ Deleted results embed message ID {msg_id}")
                            else:
                                msg = await current_channel.fetch_message(msg_id)
                                await msg.delete()
                                print(f"✅ Deleted {key} message ID {msg_id}")
                        except Exception as e:
                            print(f"⚠️ Could not delete {key} ({msg_id}): {e}")

            # ✅ Reset match data
            match_results[thread_id] = {
                "scores": {},
                "confirmed": set(),
                "admin_id": interaction.user.id,
                "players": [user1.id, user2.id],
            }

            view = MatchView(user1, user2, interaction.user.id, thread_id)
            msg = await current_channel.send("Match has been reset. Submit scores again below:", view=view)
            view.score_msg = msg
            match_results[thread_id]["score_msg"] = msg.id
            bot.add_view(view, message_id=msg.id)
            save_rehydrate()

            return await interaction.response.send_message("✅ Match reset in current thread.", ephemeral=True)

    # ✅ Case 2: undo from another channel, reuse thread
    key = tuple(sorted([user1.id, user2.id]))
    thread_id = match_lookup.get(key)

    if thread_id:
        try:
            thread = await interaction.guild.fetch_channel(thread_id)
            await thread.edit(archived=False, locked=False)
            await thread.send(f"<@{user1.id}> <@{user2.id}> match reopened by admin.")

            revert_stats_if_finalized(thread.id)

            # 🧹 Delete old score/result messages if they exist
            old_data = match_results.get(thread.id)
            if old_data:
                for key in ("score_msg", "result_msg", "results_embed_msg"):
                    msg_id = old_data.get(key)
                    if msg_id:
                        try:
                            if key == "results_embed_msg":
                                results_channel = bot.get_channel(RESULTS_CHANNEL_ID)
                                if results_channel:
                                    msg = await results_channel.fetch_message(msg_id)
                                    await msg.delete()
                                    print(f"✅ Deleted results embed message ID {msg_id}")
                            else:
                                msg = await thread.fetch_message(msg_id)
                                await msg.delete()
                                print(f"✅ Deleted {key} message ID {msg_id}")
                        except Exception as e:
                            print(f"⚠️ Could not delete {key} ({msg_id}): {e}")

            # ✅ Reset match data
            match_results[thread.id] = {
                "scores": {},
                "confirmed": set(),
                "admin_id": interaction.user.id,
                "players": [user1.id, user2.id]
            }

            view = MatchView(user1, user2, interaction.user.id, thread.id)
            msg = await thread.send("Match reset. Submit scores again below:", view=view)
            view.score_msg = msg
            match_results[thread.id]["score_msg"] = msg.id
            bot.add_view(view, message_id=msg.id)
            save_rehydrate()

            return await interaction.response.send_message("✅ Match reopened in original thread.", ephemeral=True)

        except discord.NotFound:
            # 🧹 Even if the thread is gone, delete the results embed if it exists
            old_data = match_results.get(thread_id)
            if old_data:
                msg_id = old_data.get("results_embed_msg")
                if msg_id:
                    try:
                        results_channel = bot.get_channel(RESULTS_CHANNEL_ID)
                        if results_channel:
                            msg = await results_channel.fetch_message(msg_id)
                            await msg.delete()
                            print(f"✅ Deleted results embed for closed/deleted thread {thread_id}")
                    except Exception as e:
                        print(f"⚠️ Could not delete orphaned results embed: {e}")

    # ✅ Case 3: fallback — create new thread
    parent_channel = interaction.channel
    if isinstance(parent_channel, discord.Thread):
        parent_channel = parent_channel.parent

    new_thread = await parent_channel.create_thread(
        name=f"{user1.name}_vs_{user2.name}_redo",
        type=discord.ChannelType.private_thread,
        invitable=False
    )
    await new_thread.add_user(user1)
    await new_thread.add_user(user2)
    await new_thread.add_user(interaction.user)

    match_results[new_thread.id] = {
        "scores": {},
        "confirmed": set(),
        "admin_id": interaction.user.id,
        "players": [user1.id, user2.id]
    }
    match_lookup[key] = new_thread.id

    view = MatchView(user1, user2, interaction.user.id, new_thread.id)
    msg = await new_thread.send(f"<@{user1.id}> <@{user2.id}> your match has been reopened. Use the buttons below.", view=view)
    view.score_msg = msg
    match_results[new_thread.id]["score_msg"] = msg.id
    bot.add_view(view, message_id=msg.id)
    save_rehydrate()

    await interaction.response.send_message("✅ Match recreated and players notified.", ephemeral=True)

@bot.tree.command(name="next_draft_time", description="Edit the start time of the latest draft signup")
@app_commands.describe(new_time="New start time (UNIX timestamp or <t:...> format)")
async def next_draft_time(interaction: discord.Interaction, new_time: str):
    role = discord.utils.get(interaction.guild.roles, id=REQUIRED_ROLE_ID)
    if role not in interaction.user.roles:
        return await interaction.response.send_message(
            f"⛔ You must have the `{role.name}` role to use this command.",
            ephemeral=True
        )

    signups = safe_load_json("signups.json") or []
    if not signups:
        return await interaction.response.send_message("📭 No signup drafts to update.", ephemeral=True)

    # Parse new time
    try:
        match = re.search(r"<t:(\d+):[a-zA-Z]?>", new_time)
        timestamp = int(match.group(1)) if match else int(new_time)
        event_time = datetime.fromtimestamp(timestamp, timezone.utc)
    except:
        return await interaction.response.send_message("❌ Invalid time format.", ephemeral=True)

    # Find the most recent signup (last in file)
    data = signups[-1]
    data["event_time"] = event_time.isoformat()

    # Update the message
    channel = bot.get_channel(data["channel_id"])
    if not channel:
        return await interaction.response.send_message("⚠️ Could not find signup channel.", ephemeral=True)

    try:
        msg = await channel.fetch_message(data["message_id"])
    except discord.NotFound:
        return await interaction.response.send_message("⚠️ Signup message not found.", ephemeral=True)

    # Update JSON
    with open("signups.json", "w") as f:
        json.dump(signups, f)

    # Refresh the embed
    view = SignupView(data["admin_id"], event_time)
    view.notes = data.get("notes", "")
    view.players = [await bot.fetch_user(uid) for uid in data["players"]]
    view.embed_msg = msg
    await view.update_embed()
    bot.add_view(view, message_id=msg.id)

    return await interaction.response.send_message(
        f"✅ Draft time updated to <t:{int(event_time.timestamp())}:F>", ephemeral=True
    )

@bot.tree.command(name="edit_notes", description="Edit the notes on the latest 1v1 signup draft")
@app_commands.describe(notes="The new notes to display under the signup")
async def edit_notes(interaction: discord.Interaction, notes: str):
    role = discord.utils.get(interaction.guild.roles, id=REQUIRED_ROLE_ID)
    if role not in interaction.user.roles:
        return await interaction.response.send_message(
            f"⛔ You must have the `{role.name}` role to use this command.",
            ephemeral=True
        )

    signups = safe_load_json("signups.json") or []
    if not signups:
        return await interaction.response.send_message("📭 No signup drafts to update.", ephemeral=True)

    # Find the most recent signup
    data = signups[-1]
    data["notes"] = notes

    # Locate the message
    channel = bot.get_channel(data["channel_id"])
    if not channel:
        return await interaction.response.send_message("⚠️ Could not find signup channel.", ephemeral=True)

    try:
        msg = await channel.fetch_message(data["message_id"])
    except discord.NotFound:
        return await interaction.response.send_message("⚠️ Signup message not found.", ephemeral=True)

    # Update JSON
    with open("signups.json", "w") as f:
        json.dump(signups, f)

    # Rebuild view and embed
    view = SignupView(data["admin_id"], datetime.fromisoformat(data["event_time"]))
    view.notes = notes
    view.players = [await bot.fetch_user(uid) for uid in data["players"]]
    view.embed_msg = msg
    await view.update_embed()
    bot.add_view(view, message_id=msg.id)

    return await interaction.response.send_message("✅ Notes updated successfully.", ephemeral=True)

@bot.tree.command(name="forfeit_match", description="Force a forfeit result for a 1v1 match")
@app_commands.describe(
    forfeiter="The player who is forfeiting",
    opponent="The player who is receiving the win"
)
async def forfeit_match(interaction: discord.Interaction, forfeiter: discord.User, opponent: discord.User):
    role = discord.utils.get(interaction.guild.roles, id=REQUIRED_ROLE_ID)
    if role not in interaction.user.roles:
        return await interaction.response.send_message(
            f"⛔ You must have the `{role.name}` role to use this command.",
            ephemeral=True
        )

    key = tuple(sorted([forfeiter.id, opponent.id]))
    thread_id = match_lookup.get(key)

    if not thread_id:
        return await interaction.response.send_message("❌ No existing match found between these players.", ephemeral=True)

    try:
        thread = await interaction.guild.fetch_channel(thread_id)
    except discord.NotFound:
        return await interaction.response.send_message("❌ Could not fetch the match thread.", ephemeral=True)

    # Record match as forfeit win for opponent
    match_results[thread_id] = {
        "scores": {
            1: f"<@{opponent.id}>",
            2: f"<@{opponent.id}>"
        },
        "confirmed": {forfeiter.id, opponent.id},
        "admin_id": interaction.user.id,
        "players": [forfeiter.id, opponent.id],
        "finalized": True
    }

    result_msg = await thread.send(f"🏳️ <@{forfeiter.id}> has forfeited. <@{opponent.id}> wins by default.")
    match_results[thread_id]["result_msg"] = result_msg.id

    # Update stats
    winner, loser, w_score, l_score = (opponent, forfeiter, 2, 0)
    ensure_stat(winner.id)
    ensure_stat(loser.id)
    player_stats[str(winner.id)]["wins"] += 1
    player_stats[str(winner.id)]["games"] += 1
    player_stats[str(loser.id)]["losses"] += 1
    player_stats[str(loser.id)]["games"] += 1
    save_stats()

    # Post to results channel
    results_channel = bot.get_channel(RESULTS_CHANNEL_ID)
    if results_channel:
        embed = discord.Embed(
            title="📊 Match Result (Admin Forfeit)",
            color=discord.Color.orange()
        )
        embed.add_field(name="Players", value=f"<@{forfeiter.id}> vs <@{opponent.id}>", inline=False)
        embed.add_field(name="Winner", value=f"🏆 <@{opponent.id}>", inline=True)
        embed.add_field(name="Result", value="Forfeit by admin", inline=True)
        embed.set_footer(text="Best of 3 — Submitted by admin override")
        results_embed_msg = await results_channel.send(embed=embed)
        match_results[thread_id]["results_embed_msg"] = results_embed_msg.id

    save_rehydrate()

    # Archive and delete thread
    try:
        await thread.edit(archived=True, locked=True)
        await asyncio.sleep(5)
        await thread.delete()
    except Exception as e:
        print(f"⚠️ Error closing thread after forfeit: {e}")

    await interaction.response.send_message("✅ Forfeit recorded and thread closed.", ephemeral=True)

@bot.tree.command(name="end_tournament", description="End the tournament early and clean up all threads")
async def end_tournament(interaction: discord.Interaction):
    role = discord.utils.get(interaction.guild.roles, id=REQUIRED_ROLE_ID)
    if role not in interaction.user.roles:
        return await interaction.response.send_message(
            f"⛔ You must have the `{role.name}` role to use this command.",
            ephemeral=True
        )

    await interaction.response.send_message("⚠️ Ending tournament — cleaning up threads...", ephemeral=True)

    cleaned_threads = 0
    cleaned_channels = 0

    # Step 1: Archive and delete all match threads
    for thread_id in list(match_results.keys()):
        try:
            thread = await interaction.guild.fetch_channel(thread_id)
            if isinstance(thread, discord.Thread):
                await thread.edit(archived=True, locked=True)
                await asyncio.sleep(2)
                await thread.delete()
                cleaned_threads += 1
        except Exception as e:
            print(f"⚠️ Failed to delete thread {thread_id}: {e}")

    # Step 2: Optionally delete temp overflow text channels
    for channel in interaction.guild.text_channels:
        if channel.name.startswith("combat-1v1-overflow"):
            try:
                await channel.delete(reason="Tournament ended")
                cleaned_channels += 1
            except Exception as e:
                print(f"⚠️ Could not delete overflow channel {channel.name}: {e}")

    await interaction.followup.send(
        f"✅ Tournament ended early.\n🧵 Threads deleted: `{cleaned_threads}`\n🗑️ Temp channels deleted: `{cleaned_channels}`",
        ephemeral=True
    )

@bot.tree.command(name="clear_signup", description="Remove the latest active signup embed and data")
async def clear_signup(interaction: discord.Interaction):
    role = discord.utils.get(interaction.guild.roles, id=REQUIRED_ROLE_ID)
    if role not in interaction.user.roles:
        return await interaction.response.send_message(
            f"⛔ You must have the `{role.name}` role to use this command.",
            ephemeral=True
        )

    if not os.path.exists("signups.json"):
        return await interaction.response.send_message("❌ No signups.json file found.", ephemeral=True)

    try:
        with open("signups.json", "r") as f:
            all_signups = json.load(f)
    except Exception as e:
        return await interaction.response.send_message(f"❌ Could not read signups.json: {e}", ephemeral=True)

    if not all_signups:
        return await interaction.response.send_message("⚠️ No active signups to clear.", ephemeral=True)

    latest = all_signups[-1]

    # Attempt to delete the signup embed message
    try:
        channel = bot.get_channel(latest["channel_id"])
        if channel:
            msg = await channel.fetch_message(latest["message_id"])
            await msg.delete()
    except Exception as e:
        print(f"⚠️ Failed to delete signup message: {e}")
    
    import shutil

    # Backup before removal
    shutil.copy("signups.json", "signups_backup.json")

    # Remove from list and save
    all_signups.pop()
    with open("signups.json", "w") as f:
        json.dump(all_signups, f)

    await interaction.response.send_message("✅ Latest signup has been cleared.", ephemeral=True)

@bot.tree.command(name="kick_tourney_player", description="Kick a player from the tournament")
@app_commands.describe(user="Player to remove from signup and match threads")
async def kick_tourney_player(interaction: discord.Interaction, user: discord.User):
    role = discord.utils.get(interaction.guild.roles, id=REQUIRED_ROLE_ID)
    if role not in interaction.user.roles:
        return await interaction.response.send_message("⛔ You don't have permission to use this command.", ephemeral=True)

    # 1. Remove from latest signup
    try:
        with open("signups.json", "r") as f:
            signups = json.load(f)
    except Exception:
        signups = []

    if not signups:
        return await interaction.response.send_message("⚠️ No active signups found.", ephemeral=True)

    latest = signups[-1]
    if user.id in latest["players"]:
        latest["players"].remove(user.id)
        # ✅ Preserve existing notes when re-saving
        for s in signups:
            if s["message_id"] == latest["message_id"]:
                s["players"] = latest["players"]
                break

        with open("signups.json", "w") as f:
            json.dump(signups, f)

        # Update signup message if possible
        try:
            ch = bot.get_channel(latest["channel_id"])
            msg = await ch.fetch_message(latest["message_id"])
            view = SignupView(latest["admin_id"], datetime.fromisoformat(latest["event_time"]))
            view.players = [await bot.fetch_user(uid) for uid in latest["players"]]
            view.embed_msg = msg
            view.notes = latest.get("notes", "")
            await view.update_embed()
        except Exception as e:
            print(f"⚠️ Could not update signup embed after kick: {e}")

    # 2. Clean up all match threads involving user
    to_remove = []
    for thread_id, data in list(match_results.items()):
        if user.id in data.get("players", []):
            try:
                thread = await bot.fetch_channel(int(thread_id))
                await thread.send(f"🚫 Match cancelled due to player kick: <@{user.id}>")
                await thread.edit(archived=True, locked=True)
                await asyncio.sleep(2)
                await thread.delete()
            except Exception as e:
                print(f"⚠️ Could not clean up thread {thread_id}: {e}")
            to_remove.append(thread_id)

    for tid in to_remove:
        match_results.pop(tid, None)

    # 3. Clean up from match_lookup
    for k in list(match_lookup.keys()):
        if user.id in k:
            match_lookup.pop(k, None)

    save_rehydrate()
    await interaction.response.send_message(f"✅ {user.mention} has been kicked from the tournament.", ephemeral=True)

@bot.tree.command(name="ban_tourney_player", description="Ban a player from participating in this tournament")
@app_commands.describe(user="Player to block from signing up")
async def ban_tourney_player(interaction: discord.Interaction, user: discord.User):
    role = discord.utils.get(interaction.guild.roles, id=REQUIRED_ROLE_ID)
    if role not in interaction.user.roles:
        return await interaction.response.send_message("⛔ You don't have permission to use this command.", ephemeral=True)

    # ✅ Auto-create file if missing
    if not os.path.exists("banned_players.json"):
        with open("banned_players.json", "w") as f:
            json.dump([], f)

    # Load ban list
    with open("banned_players.json", "r") as f:
        banned = json.load(f)

    if user.id in banned:
        return await interaction.response.send_message(f"{user.mention} is already banned.", ephemeral=True)

    banned.append(user.id)
    with open("banned_players.json", "w") as f:
        json.dump(banned, f)

    await interaction.response.send_message(f"✅ {user.mention} is now banned from the tournament.", ephemeral=True)

@bot.tree.command(name="unban_tourney_player", description="Remove a player from the tournament ban list")
@app_commands.describe(user="Player to unban")
async def unban_tourney_player(interaction: discord.Interaction, user: discord.User):
    role = discord.utils.get(interaction.guild.roles, id=REQUIRED_ROLE_ID)
    if role not in interaction.user.roles:
        return await interaction.response.send_message(
            f"⛔ You don't have permission to use this command.", ephemeral=True
        )

    # Load or create ban list
    if not os.path.exists("banned_players.json"):
        return await interaction.response.send_message("⚠️ No ban list found.", ephemeral=True)

    try:
        with open("banned_players.json", "r") as f:
            banned = json.load(f)
    except json.JSONDecodeError:
        return await interaction.response.send_message("❌ Failed to read ban list (corrupted JSON).", ephemeral=True)

    if user.id not in banned:
        return await interaction.response.send_message(f"{user.mention} is not banned.", ephemeral=True)

    banned.remove(user.id)
    with open("banned_players.json", "w") as f:
        json.dump(banned, f)

    await interaction.response.send_message(f"✅ {user.mention} has been unbanned from the tournament.", ephemeral=True)

@bot.event
async def on_ready():
    load_stats()
    load_rehydrate()
    await bot.tree.sync()
    await update_leaderboard_message()

    # Rehydrate SignupViews
    try:
        if os.path.exists("signups.json"):
            with open("signups.json", "r") as f:
                content = f.read().strip()
                if not content:
                    print("ℹ️ signups.json is empty.")
                    signups = []
                else:
                    signups = json.loads(content)
        else:
            signups = []

        for data in signups:
            channel = bot.get_channel(data["channel_id"])
            if not channel:
                continue
            try:
                message = await channel.fetch_message(data["message_id"])
            except discord.NotFound:
                continue
            view = SignupView(data["admin_id"], datetime.fromisoformat(data["event_time"]))
            view.notes = data.get("notes", "")
            view.players = [await bot.fetch_user(uid) for uid in data["players"]]
            view.embed_msg = message
            await view.update_embed()
            bot.add_view(view, message_id=message.id)

    except (json.JSONDecodeError, Exception) as e:
        print(f"⚠️ Could not load signups.json: {e}")

    # Rehydrate MatchViews + CloseThreadViews
    for thread_id_str, data in list(match_results.items()):
        if data.get("finalized"):
            continue
        try:
            thread_id = int(thread_id_str)
            thread = await bot.fetch_channel(thread_id)
            if not thread:
                continue
            p1 = await bot.fetch_user(data["players"][0])
            p2 = await bot.fetch_user(data["players"][1])
            admin = data["admin_id"]
            view = MatchView(p1, p2, admin, thread_id)
            msg_id = data.get("score_msg")
            if msg_id:
                try:
                    msg = await thread.fetch_message(msg_id)
                    view.score_msg = msg
                    bot.add_view(view, message_id=msg_id)
                except:
                    msg = await thread.send(f"**Match:** <@{p1.id}> vs <@{p2.id}> (reloaded)", view=view)
                    view.score_msg = msg
                    match_results[thread_id]["score_msg"] = msg.id
                    bot.add_view(view, message_id=msg.id)
                    save_rehydrate()
            else:
                msg = await thread.send(f"**Match:** <@{p1.id}> vs <@{p2.id}> (reloaded)", view=view)
                view.score_msg = msg
                match_results[thread_id]["score_msg"] = msg.id
                bot.add_view(view, message_id=msg.id)
                save_rehydrate()

            close_msg_id = data.get("close_msg")
            if close_msg_id:
                try:
                    msg = await thread.fetch_message(close_msg_id)
                    close_view = CloseThreadView(p1.id, p2.id, admin)
                    bot.add_view(close_view, message_id=msg.id)
                except Exception as e:
                    print(f"⚠️ Failed to rehydrate CloseThreadView for thread {thread_id}: {e}")
        except Exception as e:
            print(f"❌ Failed to rehydrate thread {thread_id_str}: {e}")

    print(f"✅ Logged in as {bot.user}")


bot.run("BOT_TOKEN_HERE")




