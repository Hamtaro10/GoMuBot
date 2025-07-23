# Discord Bot: Status Bot Musik
# Copyright: Hellenoir

import os
import datetime
import discord
import asyncio
from discord.ext import commands
from dotenv import load_dotenv
from datetime import timezone, timedelta
from db import load_bot_data, add_bot_data


# Load data awal
bot_data_list = load_bot_data()


# Fungsi bantu
def get_bot_list():
    return [bot["id"] for bot in bot_data_list]


def get_bot_names():
    return [bot["name"] for bot in bot_data_list]


# Load token dari .env
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
if TOKEN is None:
    raise RuntimeError("❌ DISCORD_TOKEN tidak ditemukan di file .env")

# Setup intents
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.voice_states = True
intents.message_content = True

# Inisialisasi bot
bot = commands.Bot(
    command_prefix=['g!','G!','GT'],
    intents=intents,
    case_insensitive = True                   
)

# Penyimpan pesan status per guild
status_message_ids = {}

# Zona waktu GMT+7
GMT_PLUS_7 = timezone(timedelta(hours=7))


# Fungsi update status bot musik
async def update_status_for_guild(guild):
    channel = next((c for c in guild.text_channels if c.name == 'status-bot'),
                   None)
    if not channel:
        channel = await guild.create_text_channel('status-bot')

    now = datetime.datetime.now(GMT_PLUS_7)
    embed = discord.Embed(
        title=
        "<a:growing:1387951619106279494> Growing Together Music Bot Status",
        description=
        "Bot ini ditujukan agar member voice lebih mudah memantau bot music yang sedang tersedia :D",
        color=discord.Color.dark_blue(),
        timestamp=now)
    embed.set_footer(text="✅ Tersedia  | ❌ Sedang Dipakai")

    for bot_info in bot_data_list:
        bot_id = bot_info["id"]
        bot_name = bot_info["name"]
        try:
            member = await guild.fetch_member(bot_id)
        except discord.NotFound:
            member = None

        mention_name = member.mention if member else f"<@{bot_id}>"

        if member and member.voice and member.voice.channel:
            status = f"❌ Sedang dipakai di `{member.voice.channel.name}`"
        else:
            status = "✅ Idle"

        embed.add_field(name=bot_name,
                        value=f"{mention_name} - {status}",
                        inline=False)

    existing_message = None
    async for message in channel.history(limit=50):
        if message.author == bot.user and message.embeds:
            existing_message = message
            break
    
    if existing_message:
        await existing_message.edit(embed=embed)
        status_message_ids[guild.id] = existing_message.id
    else:
        new_message = await channel.send(embed=embed)
        status_message_ids[guild.id] = new_message.id

# Event ketika bot online
@bot.event
async def on_ready():
    if bot.user:
        print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    for guild in bot.guilds:
        await update_status_for_guild(guild)


# Event ketika voice state bot berubah
@bot.event
async def on_voice_state_update(member, before, after):
    if member.id in get_bot_list():
        await update_status_for_guild(member.guild)

#Event Pemanggilan Bot
@bot.event
async def on_message(message):
    print(f"Pesan diterima: {message.content}")
    await bot.process_commands(message)


# Command untuk menambahkan bot musik
@bot.command("addbot")
async def addbot(ctx, bot_id: int, *, bot_name: str):
    bot_data_list = load_bot_data()

    for bot_entry in bot_data_list:
        if bot_entry["id"] == bot_id:
            await ctx.send("⚠️ Bot ini sudah ada di daftar.")
            return

    add_bot_data(bot_id, bot_name)
    bot_data_list = load_bot_data()
    await ctx.send(f"_Success_✅\n Bot **{bot_name}** berhasil ditambahkan !'")
    await update_status_for_guild(ctx.guild)

@bot.command("ping")
async def ping(ctx):
    await ctx.send("Pong!")

async def main():
    await bot.load_extension('cog.music')
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())

