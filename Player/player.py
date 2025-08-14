import pomice
import discord
from discord.ext import commands 
from pomice import Track , TrackType
from Player.queue import GomuQueue
from utils.utillity import format_duration, get_thumbnail, build_progress_bar, logger


class GomuPlayer(pomice.Player):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue = GomuQueue()
        self.ctx: commands.Context = None
        self.controller: discord.Message = None

    async def set_context(self, ctx: commands.Context):
        self.ctx = ctx
        self.dj = ctx.author

    async def get_controler(self):
        return self.controller
    
    async def do_next(self) -> None:
        try:
            track : pomice.Track = self.queue.get()
        except pomice.QueueEmpty:
            if self.ctx:
                embed = discord.Embed(
                    description="Tidak ada lagu tersisa. Gunakan `g!play` untuk menambahkan lagu.",
                    color=discord.Color.blurple()
                )
                await self.ctx.send(embed=embed, delete_after=8)
                self.controller = None
            return

        await self.play(track)
        if self.ctx:
            embed = await self.create_now_playing_embed(track)

            if self.controller:
                try:
                    await self.controller.delete()
                except discord.NotFound:
                    pass

            self.controller = await self.ctx.send(embed=embed)
            logger.info('Embed diperbarui')






    async def create_now_playing_embed(self, track: Track) -> discord.Embed:
        position_ms = self.position
        duration_ms = track.length

        progress_bar = build_progress_bar(position_ms, duration_ms)
        position_str = format_duration(position_ms)
        duration_str = format_duration(duration_ms)

        loop_mode = self.queue.loop_mode
        if loop_mode is pomice.LoopMode.TRACK:
            loop_mode = "Track"
        elif loop_mode is pomice.LoopMode.QUEUE:
            loop_mode = "Queue"
        else:
            loop_mode = "Off"

        embed = discord.Embed(
            description=f"{track.title} - {track.author}",
            color=discord.Color.blurple()
        )
        embed.add_field(name="Track Length", value=f"{progress_bar}\n `{position_str} / {duration_str}`", inline=False)
        embed.set_author(name="GoMu Player", icon_url="https://media.giphy.com/media/gahyl3UyyjdLhg0KoR/giphy.gif")
        embed.add_field(name="Volume", value=f"{self.volume}%", inline=True)
        embed.add_field(name="🔁 Status Loop", value=f"{loop_mode}", inline=True)
        embed.set_footer(text=f"Requested by {self.ctx.author}", icon_url=self.ctx.author.display_avatar.url)

        thumbnail = get_thumbnail(track)
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)

        return embed