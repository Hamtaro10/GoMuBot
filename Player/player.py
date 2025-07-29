import pomice
import discord
import asyncio
from discord.ext import commands
from Player.queue import GomuQueue
from pomice import Track
from utils.utillity import format_duration, get_thumbnail, build_progress_bar


class GomuPlayer(pomice.Player):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue = GomuQueue()
        self.ctx: commands.Context = None
        self.loop = False

    async def set_context(self, ctx: commands.Context):
        self.ctx = ctx
        self.dj = ctx.author


    async def do_next(self) -> None:
        try:
            next_track: pomice.Track = self.queue.get()
        except pomice.QueueEmpty:
            if self.ctx:
                embed = discord.Embed(
                    title="Antrian Lagu Kosong",
                    description="Tidak ada lagu tersisa. Gunakan `g!play` untuk menambahkan lagu.",
                    color=discord.Color.blurple()
                )
                await self.ctx.send(embed=embed)
            return

        await self.play(next_track)
        if self.ctx:
            embed = await self.create_now_playing_embed(next_track)
            await self.ctx.send(embed=embed)



    async def create_now_playing_embed(self, track: Track) -> discord.Embed:
        position_ms = self.position
        duration_ms = track.length

        progress_bar = build_progress_bar(position_ms, duration_ms)
        position_str = format_duration(position_ms)
        duration_str = format_duration(duration_ms)

        embed = discord.Embed(
            description=f"{track.title} - {track.author}",
            color=discord.Color.blurple()
        )
        embed.add_field(name="Track Length", value=f"{progress_bar}\n `{position_str} / {duration_str}`", inline=False)
        embed.set_author(name="GoMu Player", icon_url="https://media.giphy.com/media/gahyl3UyyjdLhg0KoR/giphy.gif")
        embed.add_field(name="Volume", value=f"{self.volume}%", inline=True)
        embed.add_field(name="🔁 Status Loop", value="Aktif" if self.loop else "Mati", inline=True)
        embed.set_footer(text=f"Requested by {self.ctx.author}", icon_url=self.ctx.author.display_avatar.url)

        thumbnail = get_thumbnail(track)
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)

        return embed
    
    def create_track_list_embed(tracks: list[pomice.Track], title="🎶 Antrian Lagu", max_items=15):
        description = ""
        for i, track in enumerate(tracks[:max_items], 1):
            description += f"{i}. {track.title} - {track.author}\n"

        if len(tracks) > max_items:
            description += f"\nDan {len(tracks) - max_items} lagu lainnya..."

        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.blurple()
        )
        return embed
