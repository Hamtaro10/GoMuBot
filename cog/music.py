import discord
import pomice
from discord.ext import commands
from pomice import Track, NodePool, Playlist
from Player.player import GomuPlayer
from utils.utillity import format_duration, get_thumbnail, yt_search, logger
import os
from dotenv import load_dotenv
from pomice import Node

load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")
class MusicCog(commands.Cog):
    def __init__(self,bot: commands.Bot):
        self.bot: Node.bot = bot

    def get_node(self):
        node = NodePool.get_node(identifier='MAIN')
        if not node or not node.is_connected:
            logger.warning("❌ Node 'MAIN' tidak tersedia atau belum tersambung.")
            return None
        return node
    async def connect_voice(self, ctx, channel):
        node = self.get_node()
        if node is None:
            logger.info("Node gagal di load")
            return Exception
        
        await ctx.author.voice.channel.connect(cls=GomuPlayer, self_deaf=True, reconnect=True)
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

    @commands.Cog.listener()
    async def on_pomice_track_end(self, player: GomuPlayer, track: Track, reason: str):

        player.queue.history.append(track)
        if len(player.queue.history)>15:
            player.queue.history.pop(0)

        # Pengkondisian LooopMode pada event Handler
        if player.queue.loop_mode == pomice.LoopMode.TRACK:
            await player.play(track)
            return
        
        if player.queue.loop_mode == pomice.LoopMode.QUEUE:
            await player.do_next()
            return
        
        if getattr(player, 'autoplay', False):
            last_track = track.title
            track = await player.node.search_spotify_recommendations(query=last_track)
            await player.play(track)
            logger.info('Autoplay Dimainkan')
            return
    
        await player.do_next()
        
    

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
            return await ctx.send(embed=discord.Embed(description=f"Maaf ya aku lagi sibuk di {ctx.channel.mention}, kalo mau kamu bisa gabung bareng aku kok {ctx.author.mention}"))

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
            await voice.channel.connect(cls=GomuPlayer, self_deaf=True, reconnect=True)
            player: GomuPlayer = ctx.voice_client
            await player.set_context(ctx)

        # Logging waktu pencarian
        import time, re
        start = time.perf_counter()

        query = search.strip()
        is_spotify_playlist = "open.spotify.com/playlist/" in query
        is_youtube_url = re.match(r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/", query)

        results = None

        if not is_spotify_playlist and not is_youtube_url:
            yt_url = await yt_search(query, api_key=API_KEY, mode="official")
            if not yt_url:
                yt_url = await yt_search(query, api_key=API_KEY, mode="normal")
            if not yt_url:
                results = await player.get_tracks(query, search_type=pomice.SearchType.ytmsearch, ctx=ctx)
                if not results:
                    return logger.info('Video Tidak Ditemukan')
            else:
                results = await player.get_tracks(yt_url, ctx=ctx)
        else:
            results = await player.get_tracks(query, ctx=ctx) 
        end = time.perf_counter()
        logger.info(f"Query Lagu: '{search}' selesai dalam {round((end - start) * 1000)}ms")

        if not results:
            return await ctx.send(embed=discord.Embed(description="Lagu tidak ditemukan/query salah"), delete_after=8)

        if isinstance(results, Playlist):
            await self._play_playlist(ctx, player, results, search)
        else:
            await self._play_single_track(ctx, player, results[0])

    async def _play_playlist(self, ctx, player: GomuPlayer, playlist: pomice.Playlist, uri: str):
        title = getattr(playlist, 'title', None) or 'Spotify Playlist'
        playlist_uri = getattr(playlist, 'uri', None) or uri

        for track in playlist.tracks:
            player.queue.put(track)

        # Mulai track jika tidak sedang memutar apapun
        if not player.current and not player.is_playing:
            next_track = player.queue.get()
            await player.play(next_track)

        total_duration = sum(t.length for t in playlist.tracks)

        embed = discord.Embed(title="🎧 Memuat Playlist", color=discord.Color.blurple())
        embed.add_field(name="Playlist", value=f"[{title}]({playlist_uri})", inline=False)
        embed.add_field(name="Track Length", value=format_duration(total_duration), inline=True)
        embed.add_field(name="Tracks", value=str(len(playlist.tracks)), inline=True)

        thumbnail = get_thumbnail(playlist.tracks[0])
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)

        await ctx.send(embed=embed)



    async def _play_single_track(self, ctx, player: GomuPlayer, track: Track,):
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

    @commands.command(name="skip", aliases=["s", ])
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

    @commands.command(name="stop", help="Menghentikan lagu dan keluar dari voice channel.")
    async def stop(self, ctx: commands.Context):
        player: GomuPlayer = ctx.voice_client

        if not player or not player.is_connected:
            return await ctx.send(embed=discord.Embed(
                title="Tidak Terhubung",
                description="Bot tidak sedang berada di voice channel.",
                color=discord.Color.red()
            ))
        
        player.queue.clear()
        await player.disconnect()

        await ctx.send(embed=discord.Embed(
            title="Pemutaran Dihentikan",
            description="Bot keluar dari voice channel dan antrian dibersihkan.",
            color=discord.Color.blurple()
        ))

    @commands.command(name="autoplay", aliases=["ap","auto"], help="Auotplay lagu yang telah berakhir dengan lagu terkait (Related Song)")
    async def autoplay(self, ctx: commands.Context):
        player : GomuPlayer = ctx.voice_client

        if not player or not player.is_connected:
            return await ctx.send(embed=discord.Embed(
            title="Tidak Terhubung",
            description="Bot tidak sedang berada di voice channel.",
            color=discord.Color.red()
        ))

        self.get_node()

        player.autoplay = not getattr(player, 'autoplay', False)
        await ctx.send(embed=discord.Embed(
            description=f"Autoplay {'Diaktifkan' if player.autoplay else 'Dinonaktifkan'}"
         ))
        logger.info('Berhasil Set Autoplay')
        

    @commands.command(name="loop", aliases=["l"], help="Loop track yang sedang diputar.\n Mode = Track, Queue, Off")
    async def loop(self, ctx: commands.Context, mode: str):
        player: GomuPlayer = ctx.voice_client

        if not player or not player.is_connected:
            return await ctx.send(embed=discord.Embed(description="Bot sedang tidak berada di voice channel"))

        if not player.current:
            return await ctx.send(embed=discord.Embed(description="Tidak ada lagu yang sedang diputar untuk di-loop."))

        if not hasattr(player.queue, "set_loop_mode") or not hasattr(player.queue, "disable_loop"):
            return await ctx.send(embed=discord.Embed(description="Fitur loop tidak tersedia untuk antrian ini."))
        try:
            mode = mode.lower()  # Normalisasi input mode
            if mode in ["track", "lagu"]:
                player.queue.set_loop_mode(mode=pomice.LoopMode.TRACK)
                logger.info(f'Status Loop : {mode}')
                status = "Track Loop Diaktifkan 🔁"
            elif mode in ["queue", "playlist"]:
                tracks = player._current
                player.queue.set_loop_mode(mode=pomice.LoopMode.QUEUE)
                status = "Queue Loop Diaktifkan 🔁"
                logger.info(f'Status Loop : {mode}')
            elif mode in ["off", "none"]:
                player.queue.disable_loop()
                status = "Loop Dinonaktifkan ⏹️"
                logger.info(f'Status Loop : {mode}')
            else:
                return await ctx.send(embed=discord.Embed(description="Mode tidak valid. Gunakan 'Track', 'Queue', atau 'Off'."))

            await ctx.send(embed=discord.Embed(
                title="Loop Status",
                description=f"**{status}**",
                color=discord.Color.blurple()
            ))
        except Exception as e:
            logger.error(f"Error: {e}")
            await ctx.send(embed=discord.Embed(description="Terjadi kesalahan saat mengatur mode loop. Silakan coba lagi."))        

            
            
            if player.queue.loop_mode  == pomice.LoopMode.TRACK:
                logger.info("Lagu berhasil di Loop ke Track")
            elif player.queue.loop_mode == pomice.LoopMode.QUEUE :
                logger.info("Lagu berhasil di Loop ke Queue")
            else:
                logger.info("Lagu gagal di set loop")


async def setup(bot: commands.Bot):
    await bot.add_cog(MusicCog(bot))
