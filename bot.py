# -*- coding: utf-8 -*-
import asyncio
import os
import sys
import json
import random
import requests
from twitchio.ext import commands
from twitchio import Message

# 🔥 BOT CONFIGURATION 🔥
BOT_USERNAME = "glitchflame_"
TOKEN = "sn7jcseudhauuaoh5pqjdg7gmlujd6"
CHANNEL = "grx_omen"
CLIENT_ID = "gp762nuuoqcoxypju8c569th9wz7q5"
CLIENT_SECRET = "g566uupnly32fpa3bnlgqy91m4dvrc"

GIVEAWAY_ACTIVE = False
ENTRANTS = []
USER_POINTS = {}
CURRENT_BET = None
BETTING_OPEN = False
BET_ENTRIES = {}
BET_HISTORY_FILE = "bet_history.json"
BET_HISTORY = []

AUTO_RESPONSES = {
    "hello bot": "Hey there! 👋",
    "hello glitch": "Hey there! 👋",
    "how are you": "I'm just some code, but I'm doing great!",
    "gg": "GG! Well played. 🎮",
    "brb": "Take your time, we'll be here! 🕒",
    "good game": "Yep, that was a solid game! 🏆",
    "who is glitchflame?": "GlitchFlame is the legendary Twitch bot of Phoenix Union! 🔥"
}

RANKS = {
    0: "🌱 New Viewer",
    50: "🔥 Active Chatter",
    100: "⭐ Dedicated Fan",
    250: "🚀 Stream Regular",
    500: "🏆 VIP Status",
    1000: "👑 Twitch Legend"
}

class TwitchBot(commands.Bot):
    def __init__(self):
        super().__init__(token=TOKEN, prefix="!", initial_channels=[CHANNEL])
        self.load_bet_history()

    async def event_ready(self):
        print(f"✅ {self.nick} is online!")

    async def event_message(self, message: Message):
        if message.author.name.lower() == BOT_USERNAME.lower():
            return

        print(f"{message.author.name}: {message.content}")

        # 🔹 Auto-Responses
        for phrase, response in AUTO_RESPONSES.items():
            if phrase.lower() in message.content.lower():
                await message.channel.send(response)

        await self.handle_commands(message)

        # 🔹 Points System: Award 1 point per message
        username = message.author.name.lower()
        USER_POINTS[username] = USER_POINTS.get(username, 0) + 1

    def is_mod_or_streamer(self, ctx):
        return ctx.author.is_mod or ctx.author.name.lower() == CHANNEL.lower()

    # 🔥 RESTART COMMAND 🔥
    @commands.command(name="restart")
    async def restart(self, ctx):
        """Restarts the bot (Mods & Streamer Only)"""
        if self.is_mod_or_streamer(ctx):
            await ctx.send("🔄 Restarting bot...")
            os.execv(sys.executable, ["python"] + sys.argv)
        else:
            await ctx.send("⛔ Only the streamer or a mod can restart the bot.")

    # 🔹 Load bet history from file
    def load_bet_history(self):
        try:
            with open(BET_HISTORY_FILE, "r") as file:
                global BET_HISTORY
                BET_HISTORY = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            BET_HISTORY = []

    # 🔹 Save bet history to file
    def save_bet_history(self):
        with open(BET_HISTORY_FILE, "w") as file:
            json.dump(BET_HISTORY, file, indent=4)

    # 🔥 BETTING SYSTEM 🔥
    @commands.command(name="bet")
    async def bet(self, ctx, action: str = None, *args):
        global CURRENT_BET, BETTING_OPEN, BET_ENTRIES, BET_HISTORY

        if action == "start" and self.is_mod_or_streamer(ctx):
            if len(args) != 2:
                await ctx.send("⛔ Usage: !bet start <option1> <option2>")
                return
            CURRENT_BET = {args[0]: [], args[1]: []}
            BETTING_OPEN = True
            BET_ENTRIES = {}
            await ctx.send(f"🔥 Betting started! Choose: `{args[0]}` or `{args[1]}`. Use `!bet <option> <amount>` to enter!")

        elif action == "close" and self.is_mod_or_streamer(ctx):
            BETTING_OPEN = False
            await ctx.send("⛔ Betting is now closed! No more entries.")

        elif action == "result" and self.is_mod_or_streamer(ctx):
            if not CURRENT_BET or args[0] not in CURRENT_BET:
                await ctx.send("⛔ Invalid winner! Make sure you select an existing option.")
                return

            winner_option = args[0]
            winners = CURRENT_BET[winner_option]
            if not winners:
                await ctx.send(f"💀 No one bet on `{winner_option}`, no payouts.")
            else:
                for user, amount in winners:
                    USER_POINTS[user] = USER_POINTS.get(user, 0) + (amount * 2)
                await ctx.send(f"🎉 Winners of `{winner_option}` received double their bet!")

            # Store bet result in history
            total_bets = sum(len(bet_list) for bet_list in CURRENT_BET.values())
            BET_HISTORY.append({
                "options": list(CURRENT_BET.keys()),
                "winner": winner_option,
                "total_bets": total_bets
            })
            self.save_bet_history()

            CURRENT_BET = None
            BETTING_OPEN = False
            BET_ENTRIES = {}

        elif action == "history":
            if len(args) == 1 and args[0].isdigit():
                index = int(args[0]) - 1
                if 0 <= index < len(BET_HISTORY):
                    bet = BET_HISTORY[index]
                    await ctx.send(f"📜 Bet {index + 1}: {bet['options'][0]} vs {bet['options'][1]}, Winner: {bet['winner']}, Total Bets: {bet['total_bets']}")
                else:
                    await ctx.send("⛔ Invalid bet number.")
            else:
                await ctx.send("📜 Use `!bet history <n>` to see a past bet (1 for most recent).")

        elif BETTING_OPEN and action in CURRENT_BET:
            username = ctx.author.name.lower()
            if username in BET_ENTRIES:
                await ctx.send("⚠️ You already placed a bet!")
                return

            try:
                amount = int(args[0])
                if amount <= 0:
                    raise ValueError
            except ValueError:
                await ctx.send("⛔ Invalid amount! Usage: !bet <option> <amount>")
                return

            if USER_POINTS.get(username, 0) < amount:
                await ctx.send("⛔ You don't have enough points!")
                return

            USER_POINTS[username] -= amount
            CURRENT_BET[action].append((username, amount))
            BET_ENTRIES[username] = action
            await ctx.send(f"✅ {ctx.author.name} bet {amount} points on `{action}`!")

        else:
            await ctx.send("⛔ Invalid bet command. Try: `!bet start`, `!bet option amount`, `!bet close`, `!bet result option`, or `!bet history <n>`.")

if __name__ == "__main__":
    bot = TwitchBot()
    bot.run()
