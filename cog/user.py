import discord
from discord.ext import commands
import pomice.utils
from db import load_bot_data, get_connection
from discord.ext import tasks
from utils.utillity import format_afk_duration
import time
import pomice
from datetime import timezone, timedelta, datetime

# Zona waktu GMT+7
WIB = timezone(timedelta(hours=7))

class UserCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.status_message_ids = {}
        self.update_loop.start()
        self.afk_users = {}
        self.pinger: pomice.utils.Ping = get_connection()

    def cog_unload(self):
        self.update_loop.cancel()

    @tasks.loop(seconds=60)  # Ubah ke detik yang kamu mau
    async def update_loop(self):
        for guild in self.bot.guilds:
            try:
                await self.update_status_for_guild(guild)
            except Exception as e:
                print(f"[ERROR] Gagal update status untuk {guild.name}: {e}")

    @update_loop.before_loop
    async def before_update_loop(self):
        await self.bot.wait_until_ready()

    async def update_status_for_guild(self, guild: discord.Guild):
        bot_data_list = load_bot_data()
        channel = next((c for c in guild.text_channels if c.name == 'status-bot'), None)

        # Buat channel jika belum ada
        if not channel:
            channel = await guild.create_text_channel('status-bot')

        # Buat embed status
        now = datetime.now(WIB)
        embed = discord.Embed(
            title="<a:growing:1387951619106279494> Growing Together Music Bot Status",
            description="Bot ini ditujukan agar member voice lebih mudah memantau bot music yang sedang tersedia :D",
            color=discord.Color.blurple(),
            timestamp=now
        )
        embed.set_footer(text="✅ Tersedia  | ❌ Sedang Dipakai")

        for bot_info in bot_data_list:
            bot_id = bot_info["id"]
            bot_name = bot_info["name"]

            try:
                member = await guild.fetch_member(bot_id)
            except discord.NotFound:
                member = None

            mention = member.mention if member else f"<@{bot_id}>"

            if member and member.voice and member.voice.channel:
                status = f"❌ Sedang dipakai di `{member.voice.channel.name}`"
            else:
                status = "✅ Idle"

            embed.add_field(name=bot_name, value=f"{mention} - {status}", inline=False)

        # Cek apakah pesan sebelumnya sudah ada
        existing_message = None
        async for message in channel.history(limit=50):
            if message.author == self.bot.user and message.embeds:
                existing_message = message
                break

        # Edit atau kirim pesan baru
        if existing_message:
            await existing_message.edit(embed=embed)
            self.status_message_ids[guild.id] = existing_message.id
        else:
            new_message = await channel.send(embed=embed)
            self.status_message_ids[guild.id] = new_message.id

    @commands.command(name="update", hidden=True)
    async def updatestatus(self, ctx):
        guild = ctx.guild
        if not guild:
            await ctx.send("❌ Command ini hanya bisa dijalankan di dalam server.")
            return

        # Cari atau buat channel
        channel = discord.utils.get(guild.text_channels, name='status-bot')
        if not channel:
            channel = await guild.create_text_channel('status-bot')

        # Jalankan update status
        await self.update_status_for_guild(guild)

        # Kirim embed konfirmasi
        embed = discord.Embed(
            title="✅ Status Bot Musik Diperbarui",
            description=f"Status ketersediaan bot musik berhasil diperbarui di {channel.mention}.",
            color=discord.Color.blurple()
        )
        await ctx.send(embed=embed)

    @commands.command(name="ping", help="Command digunakan untuk mengirim input latensi perintah sekaligus berapa lama bot memproses perintah dengan server discord")
    async def ping(self, ctx):
        # Waktu saat command diterima
        timer = pomice.utils.Ping.Timer()
        start_time = time.perf_counter()
        timer.start()
        temp_message = await ctx.send("Mengukur ping...")
        timer.stop()
        end_time = time.perf_counter()
        latency = round((timer._stop - timer._start)* 1000)
        user_latency = round((end_time - start_time) * 1000) #ms

        embed = discord.Embed(
            title="🏓 Pong!",
            color=discord.Color.blurple()
        )
        embed.add_field(name="📶 Bot Latency", value=f"`{latency}ms`", inline=True)
        embed.add_field(name="🕐 User Latency", value=f"`{user_latency}ms`", inline=True)
        embed.set_footer(text=f"Requested By {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)

        await temp_message.edit(content=None, embed=embed)

    @commands.command(aliases=["a"], help="Berisikan informasi tentang bot")
    async def about(self, ctx):
            embed=discord.Embed(
                title="About Bot",
                description="""GoMu adalah bot serbaguna (All In One) yang dirancang untuk menyediakan berbagai fitur dalam satu platform. Selain berfungsi sebagai pemutar musik, GoMu juga dapat memantau ketersediaan bot musik lainnya di server Discord.

Saat ini, GoMu masih dalam tahap pengembangan dan akan terus diperbarui dengan fitur-fitur unggulan lainnya untuk meningkatkan pengalaman pengguna."""
            )
            embed.add_field(name="Social Media", value="[Instagram](https://instagram.com/what.iam__)", inline=False)
            embed.add_field(name="Donasi", value="[Donasi](https://trakteer.id/hellenoirism_/tip)", inline=False)
            embed.add_field(name="GoMu Official Server", value="[Official Server](https://discord.gg/USxjVVeBdN)", inline=False)
            embed.set_footer(text=f"Developed By : @Hellenoirism")
            await ctx.send(embed=embed)

    @commands.command(name="AFK", help="Set status AFK pada user" )
    async def afk(self, ctx, *, reason: str="AFK"):
        conn,cursor = get_connection()

        user_id = ctx.author.id
        original_nick = ctx.author.display_name
        now = datetime.now(WIB)

        try:
            # Cek apakah user sudah AFK
            cursor.execute("SELECT * FROM afk_users WHERE user_id = %s", (user_id,))
            existing_afk = cursor.fetchone()

            if existing_afk:
                await ctx.send(f"{ctx.author.mention} Kamu sudah dalam status AFK dengan alasan: **{existing_afk['reason']}**. Ketik sesuatu untuk keluar dari AFK dulu ya.", delete_after=10)
                return

            # Simpan AFK
            original_nick = ctx.author.display_name
            now = datetime.now(WIB)

            cursor.execute(
                "INSERT INTO afk_users (user_id, reason, original_nick, since) VALUES (%s, %s, %s, %s)",
                (user_id, reason, original_nick, now)
            )
            conn.commit()

            try:
                await ctx.author.edit(nick=f"!AFK {ctx.author.display_name}")
            except discord.Forbidden:
                await ctx.send("Gagal mengubah nickname")

            await ctx.send(f"{ctx.author.mention} Berhasil set AFK : **{reason}**", delete_after=10)

        finally:
            cursor.close()
            conn.close()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return
        
        conn, cursor = get_connection()

        try:
            cursor.execute(
                "SELECT * from afk_users WHERE user_id =%s", (message.author.id,)
            )
            afk_data = cursor.fetchone()

            if afk_data:
                cursor.execute("DELETE FROM afk_users WHERE user_id = %s", (message.author.id,))
                conn.commit()

                try:
                    await message.author.edit(nick=afk_data['original_nick'])
                except discord.Forbidden:
                    pass
                await message.channel.send(f"Welcome back {message.author.mention}, Status AFK-mu berhasil dihapus !", delete_after=10)
            
            for mention in message.mentions:
                cursor.execute("SELECT * FROM afk_users WHERE user_id = %s", (mention.id,))
                mention_data = cursor.fetchone()
                if mention_data:
                    afk_time = mention_data['since']
                    if afk_time.tzinfo is None:
                        afk_time = afk_time.replace(tzinfo=WIB)
                    delta = datetime.now(WIB) - afk_time
                    duration = format_afk_duration(delta)
                    await message.channel.send(
                        f"No no yaa! {mention.mention} Sedang AFK : **{mention_data['reason']}** - {duration}" , delete_after=25
                    )
        finally:
            cursor.close()
            conn.close()

    @commands.Cog.listener()
    async def on_ready(self):
        conn, cursor = get_connection()
        try:
            cursor.execute("SELECT * FROM afk_users")
            results = cursor.fetchall()

            for row in results:
                user_id = row['user_id']
                self.afk_users[user_id] = row  # simpan seluruh row (dict)

            print(f"[INFO] Loaded {len(self.afk_users)} AFK users on startup.")

        finally:
            cursor.close()
            conn.close()

            
            


async def setup(bot):
    cog = UserCog(bot)
    await bot.add_cog(cog)
    bot.status_cog = cog  # Agar dapat dipanggil di main.py
