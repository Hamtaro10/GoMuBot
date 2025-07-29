import discord
import pomice
from discord.ext import commands
from pomice import Track, NodePool, Playlist
from Player.player import GomuPlayer
from utils.utillity import format_duration, get_thumbnail, yt_search
from main import GOMU
import os
from dotenv import load_dotenv
from utils.utillity import logger

load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")
class MusicCog(commands.Cog):
    def __init__(self,bot: commands.Bot):
        self.bot: GOMU = bot

    def get_node(self):
        node = NodePool.get_node(identifier="MAIN")
        if not node or not node.is_connected:
            logger.warning("❌ Node 'MAIN' tidak tersedia atau belum tersambung.")
            return None
        return node
    async def connect_voice(self, ctx, channel):
        node = self.get_node()
        if node is None:
            logger.info("Node gagal di load")
            return Exception
        
        await ctx.author.voice.channel.connect(cls=GomuPlayer, self_deaf=True)
        player: GomuPlayer = ctx.voice_client
        await player.set_context(ctx=ctx)
        logger.info("GoMu Player berhasil join")
        embed = discord.Embed(
            title=f"GoMu Berhasil Join ke {channel}",
            description="Halo, Terimakasih telah menggunakan bot ini\nKetik g!help atau G!help untuk list command yang tersedia :wink:",
            color=discord.Color.blurple()
        )
        embed.set_author(name="GoMu", icon_url="https://media.giphy.com/media/gahyl3UyyjdLhg0KoR/giphy.gif")
        embed.set_footer(text=f"Powered by : @Hellenoirism")
        await ctx.send(embed=embed)

    @commands.command("join", help="Memanggil bot ke voice channel")
    async def join(self, ctx: commands.Context, *, channel: discord.VoiceChannel = None):
        channel = channel or getattr(ctx.author.voice, "channel", None)
        if not channel:
            embed = discord.Embed(
                title="Kamu Lagi Ga Masuk Voice",
                description="Enak aja mau make tapi ga dimasukin dulu, no no yaaa :3",
                color=discord.Color.blurple()
            )
            embed.set_author(name="GoMu", icon_url="https://media.giphy.com/media/gahyl3UyyjdLhg0KoR/giphy.gif")
            return await ctx.send(embed=embed)
        try:
            await self.connect_voice(ctx, channel)
        except discord.ClientException as e:
            return await ctx.send(embed=discord.Embed(description=f"Aku udah disini loh 😡 {ctx.author.mention}"))

    @commands.command(aliases=["p", "ply", "putar", "pl"], help="Play lagu dengan keyword g!play [Judul Lagu + Nama Artist]")
    async def play(self, ctx: commands.Context, *, search: str) -> None:
        voice = ctx.author.voice
        if not voice or not voice.channel:
            embed = discord.Embed(
                title="Join Voicenya Dulu Yaaa",
                description=f"{ctx.author.mention} Enak aja, kalo mau denger musik bareng yuk join kesini {ctx.channel.mention}"
            )
            return await ctx.send(embed=embed)

        # Sambungkan bot jika belum terhubung
        player: GomuPlayer = ctx.voice_client
        if not player:
            await voice.channel.connect(cls=GomuPlayer, self_deaf=True)
            player: GomuPlayer = ctx.voice_client
            await player.set_context(ctx)

        # Cek node tersambung
        node = self.get_node()
        if not node:
            return await ctx.send("❌ Node tidak tersedia. Coba lagi nanti.")

        await player.set_context(ctx)

        # Logging waktu pencarian
        import time
        start = time.perf_counter()
        if "open.spotify.com" in search:
            query = f"spsearch: {search}"
        else:
            yt_url = await yt_search(search, api_key=API_KEY)
            if not yt_url:
                return await ctx.send("❌ Video tidak ditemukan.")
            query = yt_url
        results = await player.get_tracks(query)

        end = time.perf_counter()
        logger.info(f"Query Lagu: '{search}' selesai dalam {round((end - start) * 1000)}ms")

        if not results:
            return await ctx.send(embed=discord.Embed(description="Lagu tidak ditemukan/query salah"), delete_after=8)

        # Playlist vs single track
        if isinstance(results, Playlist):
            await self._play_playlist(ctx, player, results, search)
        else:
            await self._play_single_track(ctx, player, results[0])


    async def _play_playlist(self, ctx, player: GomuPlayer, playlist: pomice.Playlist, uri: str):
        title = getattr(playlist, 'title', None) or 'Spotify Playlist'
        playlist_uri = getattr(playlist, 'uri', None) or uri

        try:
            await player.play(track=playlist.tracks[0])
        except pomice.TrackLoadError:
            embed = discord.Embed(
                title=f"Playlist Error",
                description=f"Pastikan playlist ini bersifat publik dan bisa diakses.\n"
                            f"Kalau ada rahasia-rahasiaan gini aku gasuka >_<",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)

        for track in playlist.tracks[1:]:
            player.queue.put(track)

        total_duration = sum(t.length for t in playlist.tracks)

        embed = discord.Embed(title="🎧 Memuat Playlist", color=discord.Color.blurple())
        embed.add_field(name="Playlist", value=f"[{title}]({playlist_uri})", inline=False)
        embed.add_field(name="Track Length", value=format_duration(total_duration), inline=True)
        embed.add_field(name="Tracks", value=str(len(playlist.tracks)), inline=True)

        thumbnail = get_thumbnail(playlist.tracks[0])
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)

        await ctx.send(embed=embed)


    async def _play_single_track(self, ctx, player: GomuPlayer, track: Track):
        # Jika tidak ada lagu yang sedang diputar, mainkan langsung
        if not player.current:
            try:
                await player.play(track=track)
            except pomice.TrackLoadError:
                return await ctx.send("❌ Track tidak dapat diputar.")
            embed = await player.create_now_playing_embed(track)
            return await ctx.send(embed=embed)

        # Tambah ke antrian

        player.queue.put(track)
        logger.info("Berhasil menambahkan lagu ke Queue")
        embed = discord.Embed(
            title="Antrian Ditambahkan",
            description=f"{track.title} - {track.author}",
            color=discord.Color.blurple()
        )
        embed.add_field(name="Track Length", value=format_duration(track.length), inline=True)
        embed.add_field(name="Posisi Antrian", value=str(player.queue.qsize()), inline=True)
        thumbnail = get_thumbnail(track)
        embed.set_thumbnail(url=thumbnail)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed, delete_after=10)



    # @commands.Cog.listener()
    # async def on_voice_state_update(
    #     self,
    #     member: discord.Member,
    #     before: discord.VoiceState,
    #     after: discord.VoiceState,
    # ):
    #     if member != self.bot.user:
    #         return
    #     if member == self.bot.user:
    #         if after is None:
    #             vc: GomuPlayer = member.guild.voice_client
    #             await vc.disconnect()
    #             print("disconnected")
    #         else:
    #             guild = member.guild
    #             guild.voice_client.channel = after.channel


    @commands.Cog.listener()
    async def on_pomice_track_end(self, player: GomuPlayer, track: pomice.Track, reason: str):
        if reason != "FINISHED":
            return await player.do_next()
        
        if player.loop:
            await player.play(track)  # Mainkan ulang lagu yang sama
            return

        player.queue.history.append(track)
        if len(player.queue.history) > 10:
            player.queue.history.pop(0)

    @commands.command(name="queue", aliases=["q", "list"], help="Menampilkan antrian list lagu yang akan diputar")
    async def queue(self, ctx: commands.Context):
        player : GomuPlayer = ctx.voice_client
        if not player or not player.is_connected:
            embed= discord.Embed(
                title=f"Bot tidak ada di voice channel",
                description=f"Pastikan kamu ada di voice yang sama dengan bot ya",
                color=discord.Color.blurple()
            )
            return await ctx.send(embed=embed)
        player: GomuPlayer = ctx.voice_client
        queue = player.queue
        if queue.is_empty:
            embed = discord.Embed(
                title=f"Antrian Lagu Kosong",
                description=f"Maaf {ctx.author} saat ini antrianmu kosong, ketik g!play [judul lagu] untuk menambahkan lagu kedalam antrian"
            )
            return await ctx.send(embed=embed)
        
        queue_list = list(player.queue)
        show_queue = queue_list[:15]
        description=""

        for i, track in enumerate(show_queue, 1):
            description += f"{i}. {track.title} - {track.author}\n"

        if len(queue_list) > 15:
            description += f"\nDan {len(queue_list) - 15} lagu lainnya..."

        embed = discord.Embed(
            title="🎶 Antrian Lagu",
            description=description,
            color=discord.Color.blurple()
        )
        await ctx.send(embed=embed)

    @commands.command(name="skip")
    async def skip(self, ctx: commands.Context):
        node = NodePool.get_node()
        player: GomuPlayer = node.get_player(ctx.guild.id)

        if not player or not player.is_playing:
            embed = discord.Embed(
                title=f"Tidak ada lagu",
                description=f"Maaf {ctx.author} saat ini antrianmu kosong, ketik g!play [judul lagu] untuk menambahkan lagu kedalam antrian"
            )
            return await ctx.send(embed=embed)
        
        embed = discord.Embed(
            title="Skipped",
            description=f"{player.current.title} berhasil di skip",
            color=discord.Color.blurple()
        )
        embed.set_footer(text=f"Requested by : {ctx.author}")
        await ctx.send(embed=embed)
        await player.stop()
        await player.do_next()

    @commands.command(name="stop", help="Menghentikan lagu dan keluar dari voice channel.")
    async def stop(self, ctx: commands.Context):
        player: GomuPlayer = ctx.voice_client

        if not player or not player.is_connected:
            return await ctx.send(embed=discord.Embed(
                title="Tidak Terhubung",
                description="Bot tidak sedang berada di voice channel.",
                color=discord.Color.red()
            ))

        await player.disconnect()
        player.queue.clear()
        player.loop = False

        await ctx.send(embed=discord.Embed(
            title="Pemutaran Dihentikan",
            description="Bot keluar dari voice channel dan antrian dibersihkan.",
            color=discord.Color.blurple()
        ))


    @commands.command(name="loop",aliases=["l"], help="Loop track yang sedang diputar.")
    async def loop(self, ctx: commands.Context):
        player: GomuPlayer = ctx.voice_client

        if not player or not player.current:
            return await ctx.send(embed=discord.Embed(
                title="Tidak ada lagu",
                description="Tidak ada lagu yang sedang diputar untuk di-loop.",
                color=discord.Color.red()
            ))

        player.loop = not player.loop
        status = "diaktifkan 🔁" if player.loop else "dinonaktifkan ⏹️"

        await ctx.send(embed=discord.Embed(
            title="Loop Status",
            description=f"Loop telah {status} untuk lagu:\n**{player.current.title}**",
            color=discord.Color.blurple()
        ))


async def setup(bot: commands.Bot):
    await bot.add_cog(MusicCog(bot))
