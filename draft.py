import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone
import itertools
import json
import os
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

RESULTS_CHANNEL_ID = 1373873199393280102                # replace with your actual channel ID


# === Persistent Stat Storage ===
player_stats = {}
match_results = {}
STATS_FILE = "player_stats.json"
match_lookup = {}  # (player1_id, player2_id) → thread_id


def load_stats():
    global player_stats
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, "r") as f:
            player_stats = json.load(f)

def save_stats():
    with open(STATS_FILE, "w") as f:
        json.dump(player_stats, f)

def ensure_stat(uid):
    uid = str(uid)
    if uid not in player_stats:
        player_stats[uid] = {"wins": 0, "losses": 0, "games": 0}
    return player_stats[uid]

# === Score Submission & Match Logic ===
class MatchView(discord.ui.View):
    def __init__(self, player1, player2, admin_id, thread_id):
        super().__init__(timeout=None)
        self.p1 = player1
        self.p2 = player2
        self.admin_id = admin_id
        self.thread_id = thread_id
        self.score_msg = None
        match_results[thread_id] = {"scores": {}, "confirmed": set(), "admin_id": admin_id}

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
        lines = [
            f"**Scores**",
            f"Map 1: {s.get(1, '⏳')}",
            f"Map 2: {s.get(2, '⏳')}",
            f"Map 3: {s.get(3, '⏳')}"
        ]
        content = "\n".join(lines)
        if self.score_msg:
            await self.score_msg.edit(content=content)
        else:
            self.score_msg = await thread.send(content)

    async def handle_click(self, interaction, map_number, winner):
        if interaction.user.id not in [self.p1.id, self.p2.id]:
            return await interaction.response.send_message("Not your match.", ephemeral=True)
        self.record_score(map_number, winner.id)
        await self.update_score_message(interaction.channel)
        await interaction.response.send_message("Recorded.", ephemeral=True)

    @discord.ui.button(label="Map 1", style=discord.ButtonStyle.green)
    async def map1(self, i, b):
        b.label = f"Map 1 - {i.user.display_name} Wins"
        await self.handle_click(i, 1, i.user)

    @discord.ui.button(label="Map 2", style=discord.ButtonStyle.blurple)
    async def map2(self, i, b):
        b.label = f"Map 2 - {i.user.display_name} Wins"
        await self.handle_click(i, 2, i.user)

    @discord.ui.button(label="Map 3", style=discord.ButtonStyle.gray)
    async def map3(self, i, b):
        b.label = f"Map 3 - {i.user.display_name} Wins"
        await self.handle_click(i, 3, i.user)

    @discord.ui.button(label="✅ Confirm Result", style=discord.ButtonStyle.success)
    async def confirm(self, interaction, button):
        data = match_results[self.thread_id]
        data["confirmed"].add(interaction.user.id)

        if not self.is_ready_to_finalize():
            return await interaction.response.send_message("Not enough maps scored.", ephemeral=True)

        if self.p1.id in data["confirmed"] and self.p2.id in data["confirmed"]:
            winner, loser, w_score, l_score = self.apply_result()

            # 🧵 Announce in thread
            await interaction.channel.send(f"🏆 Match complete. Winner: <@{winner.id}>")

            # 📢 Announce in results channel
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
                await results_channel.send(embed=embed)

            # Show Close Thread button
            await interaction.message.edit(view=CloseThreadView(self.p1.id, self.p2.id, self.admin_id))
        else:
            await interaction.response.send_message("Waiting for both confirmations.", ephemeral=True)

class CloseThreadView(discord.ui.View):
    def __init__(self, p1_id, p2_id, admin_id):
        super().__init__(timeout=120)
        self.allowed_ids = {p1_id, p2_id, admin_id}

    @discord.ui.button(label="🔒 Close Thread", style=discord.ButtonStyle.danger)
    async def close_thread(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in self.allowed_ids:
            return await interaction.response.send_message("You're not allowed to close this thread.", ephemeral=True)

        await interaction.response.send_message("Thread will be closed and deleted shortly...", ephemeral=True)

        await interaction.channel.edit(archived=True, locked=True)

        await asyncio.sleep(5)  # wait before deleting
        try:
            await interaction.channel.delete()
        except discord.Forbidden:
            print(f"❌ Failed to delete thread {interaction.channel.name} (no permissions).")
        except Exception as e:
            print(f"❌ Error deleting thread: {e}")

# === Signup View ===
class SignupView(discord.ui.View):
    def __init__(self, admin_id, event_time):
        super().__init__(timeout=300)
        self.players = []
        self.admin_id = admin_id
        self.event_time = event_time
        self.embed_msg = None

    async def update_embed(self):
        embed = discord.Embed(
            title="🎯 1v1 Draft Signups",
            description=f"🕒 Starts: <t:{int(self.event_time.timestamp())}:F>\n\n" +
                        "**Players Signed Up:**\n" +
                        ("\n".join(f"• <@{p.id}>" for p in self.players) or "*No players yet*"),
            color=discord.Color.green()
        )
        await self.embed_msg.edit(embed=embed, view=self)

    @discord.ui.button(label="✅ Sign Up", style=discord.ButtonStyle.green)
    async def signup(self, interaction: discord.Interaction, button):
        if interaction.user in self.players:
            return await interaction.response.send_message("You're already signed up.", ephemeral=True)
        self.players.append(interaction.user)
        await self.update_embed()
        await interaction.response.send_message("Signed up!", ephemeral=True)

    @discord.ui.button(label="❌ Unsign", style=discord.ButtonStyle.red)
    async def unsign(self, interaction: discord.Interaction, button):
        if interaction.user not in self.players:
            return await interaction.response.send_message("You weren't signed up.", ephemeral=True)
        self.players.remove(interaction.user)
        await self.update_embed()
        await interaction.response.send_message("You have been removed from signups.", ephemeral=True)

    @discord.ui.button(label="🎮 Create Matchups", style=discord.ButtonStyle.blurple)
    async def create_matchups(self, interaction: discord.Interaction, button):
        if interaction.user.id != self.admin_id:
            return await interaction.response.send_message("Only the host can create matches.", ephemeral=True)

        if len(self.players) < 2:
            return await interaction.response.send_message("Not enough players.", ephemeral=True)

        combos = list(itertools.combinations(self.players, 2))
        for p1, p2 in combos:
            thread = await interaction.channel.create_thread(
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
            key = tuple(sorted([p1.id, p2.id]))
            match_lookup[key] = thread.id


            view = MatchView(p1, p2, interaction.user.id, thread.id)
            await thread.send(
                f"**Match:** <@{p1.id}> vs <@{p2.id}>\nUse the buttons below to report map results. Only the Winner for each map will press the the button. Both need to confirm before submitting.",
                view=view
            )

        await interaction.response.send_message("✅ Round robin matches created.", ephemeral=True)

# === Commands ===
@bot.tree.command(name="start_draft", description="Start a 1v1 draft")
@app_commands.describe(start_time="Match start time as UNIX timestamp")
async def start_draft(interaction: discord.Interaction, start_time: str):
    try:
        event_time = datetime.fromtimestamp(int(start_time), timezone.utc)
    except:
        return await interaction.response.send_message("Invalid timestamp format.", ephemeral=True)

    view = SignupView(admin_id=interaction.user.id, event_time=event_time)
    embed = discord.Embed(
        title="🎯 1v1 Draft Signups",
        description=f"🕒 Starts: <t:{int(event_time.timestamp())}:F>\n\n**Players Signed Up:**\n*No players yet*",
        color=discord.Color.green()
    )
    msg = await interaction.channel.send(embed=embed, view=view)
    view.embed_msg = msg
    await interaction.response.send_message("Draft started!", ephemeral=True)

@bot.tree.command(name="leaderboard", description="View top players")
async def leaderboard(interaction: discord.Interaction):
    if not player_stats:
        return await interaction.response.send_message("No matches recorded yet.", ephemeral=True)

    sorted_stats = sorted(player_stats.items(), key=lambda x: x[1]["wins"], reverse=True)

    header = "#  | Player               |  W |  L | GP"
    divider = "-" * len(header)
    rows = []

    for idx, (uid, stats) in enumerate(sorted_stats[:15], start=1):
        try:
            user = await bot.fetch_user(int(uid))  # Fetch actual username
            name = user.display_name[:20]  # Truncate if too long
        except:
            name = f"User-{uid[:5]}"

        wins = stats["wins"]
        losses = stats["losses"]
        games = stats["games"]

        row = f"{str(idx).ljust(2)} | {name.ljust(20)} | {str(wins).rjust(2)} | {str(losses).rjust(2)} | {str(games).rjust(2)}"
        rows.append(row)

    full_text = f"{header}\n{divider}\n" + "\n".join(rows)
    embed = discord.Embed(title="🏆 1v1 Leaderboard", color=discord.Color.gold())
    embed.description = f"```{full_text}```"

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="undo", description="Undo a match by player pair")
@app_commands.describe(user1="First player", user2="Second player")
async def undo(interaction: discord.Interaction, user1: discord.User, user2: discord.User):
    if interaction.user.bot:
        return

    key = tuple(sorted([user1.id, user2.id]))
    thread_id = match_lookup.get(key)

    if thread_id:
        try:
            thread = await interaction.guild.fetch_channel(thread_id)
            await thread.edit(archived=False, locked=False)
            await thread.send(f"<@{user1.id}> <@{user2.id}> match reopened by admin.")

            match_results[thread.id] = {
                "scores": {},
                "confirmed": set(),
                "admin_id": interaction.user.id,
                "players": [user1.id, user2.id]
            }

            view = MatchView(user1, user2, interaction.user.id, thread.id)
            await thread.send("Match reset. Submit scores below:", view=view)
            return await interaction.response.send_message("✅ Match reopened.", ephemeral=True)
        except discord.NotFound:
            pass  # thread deleted, continue to recreate

    # Make new thread if deleted or missing
    new_thread = await interaction.channel.create_thread(
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
    await new_thread.send(f"<@{user1.id}> <@{user2.id}> your match has been reopened. Use the buttons below.", view=view)
    await interaction.response.send_message("✅ Match recreated and players notified.", ephemeral=True)

@bot.event
async def on_ready():
    load_stats()
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user}")

bot.run("BOT_TOKEN_HERE")                  # put bot token here



