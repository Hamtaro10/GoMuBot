import discord
import asyncio
from typing import Optional
from discord.ext import commands
from yt_dlp import YoutubeDL
from discord import FFmpegPCMAudio
from datetime import timedelta

YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True'}
FFMPEG_OPTIONS = {'options': '-vn'}

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.current_title = None
        self.current_webpage_url = None
        self.current_thumbnail = None

    @commands.command(name="join")
    async def join(self, ctx):

        if ctx.author.voice is None:
            embed = discord.Embed(

            title="You Are Not In The Voice Channel",
            description=f'Oh jadi gitu sekarang?\nUdah gamau deket deket aku?',
            color=discord.Color.blue()
        )
            await ctx.send(embed=embed)
            return

        if ctx.voice_client is not None:
            current_channel = ctx.voice_client.channel
            embed = discord.Embed(
                title= "I'm busy, call another bot :P",
                description=f"botnya aku pake dulu yah, aku ada di {current_channel.mention}.\nKalo mau gabung kesini boleh kok :3",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
            return
        
        channel = ctx.author.voice.channel
        await channel.connect()
        await ctx.send("✅ Bot sudah berhasil join. Powered by: Hellenoir")
    
    #Command leave
    @commands.command(name="leave")
    async def leave(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("👋 Bot keluar dari voice channel.")
        else:
            await ctx.send("⚠️ Bot tidak sedang berada di voice channel.")
    
    #Command Play
    @commands.command(name="play")
    async def play(self, ctx, *, song: Optional[str]=None):
        if not ctx.author.voice:
            embed = discord.Embed(
                title="You must be in voice channel",
                description="Enak aja mau mainin tapi ga dimasukin >_<",
                color= discord.Color.blue()
            )
            await ctx.send(embed=embed)
            return
        
        if song is None:
            embed = discord.Embed(
            title="Please input the title",
            description="Masa kamu mau kosongin kaya hati aku sih :( ?\nContoh command : g!play [Judul lagu]",
            color=discord.Color.blue()
        )
            await ctx.send(embed=embed)
            return

        voice_channel = ctx.author.voice.channel

        if ctx.voice_client is None:
            await voice_channel.connect()

        vc = ctx.voice_client

        with YoutubeDL(YDL_OPTIONS) as ydl:
            if "youtube.com/watch" in song or "youtu.be" in song:
                info = ydl.extract_info(song, download=False)
            else:
                info = ydl.extract_info(f"ytsearch:{song}", download=False)["entries"][0]

            url = info['url']
            title = info['title']
            webpage_url = info.get('webpage_url', 'https://youtube.com')
            thumbnail = info.get('thumbnail', '')
            duration = info.get("duration")
            formatted_duration = str(timedelta(seconds=duration)) if duration else "Unknown"


            if vc.is_playing():
                vc.stop()

        def after_play():
            coro = ctx.send(embed=discord.Embed(
                title = "Lagunya Habis Deh",
                description=f"Lagu **[{title}]({webpage_url})** telah selesai diputar",
                color= discord.Color.blurple()
            ))
            sync = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
            try:
                sync.result()
            except Exception as e:
                print(f"Error Saat Mengirim embed {e}")

        vc.play(FFmpegPCMAudio(url, **FFMPEG_OPTIONS), after=after_play)

        # Simpan info saat ini
        self.current_title = title
        self.current_webpage_url = webpage_url
        self.current_thumbnail = thumbnail

        embed = discord.Embed(
            title="🎶 Now Playing",
            description=f"**[{title}]({webpage_url})**",
            color=discord.Color.blue()
        )

        embed.add_field(name="Durasi", value=formatted_duration, inline=True)
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)

        embed.set_footer(
            text=f"Diminta oleh {ctx.author.name}",
            icon_url=ctx.author.avatar.url
            if ctx.author.avatar 
            else None)
        await ctx.send(embed=embed)

    @commands.command(name="skip")
    async def skip(self, ctx):
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            await ctx.send("⚠️ Bot belum terhubung ke voice channel.")
            return

        if not vc.is_playing():
            await ctx.send("⚠️ Tidak ada musik yang sedang diputar.")
            return

        skipped_title = self.current_title
        skipped_url = self.current_webpage_url
        skipped_thumbnail = self.current_thumbnail

        vc.stop()
        self.current_title = None
        self.current_webpage_url = None
        self.current_thumbnail = None

        embed = discord.Embed(
            title="Skipped Song",
            description=f"**[{skipped_title}]({skipped_url})** telah di-skip.",
            color=discord.Color.orange(),
        )
        if skipped_thumbnail:
            embed.set_thumbnail(url=skipped_thumbnail)
            embed.set_footer(text=f"Di skip oleh {ctx.author.name}", icon=ctx.author.avatar.url if ctx.author.avatar else None)

        await ctx.send(embed=embed)

# Fungsi setup wajib untuk Cog async
async def setup(bot):
    await bot.add_cog(Music(bot))