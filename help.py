import discord
import logging
from discord.ext import commands

# === Logging Setup ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CustomHelpCommand(commands.HelpCommand):
    async def send_bot_help(self, mapping):
        embed = discord.Embed(
            title="📖 GOMU DICTIONARY",
            description="Halo,selamat datang di kamus GoMu☺️\n\nBerikut adalah daftar command berdasarkan kategorinya :",
            color=discord.Color.blurple()
        )
        embed.set_author(
            name="GoMu",
            icon_url="https://media.giphy.com/media/gahyl3UyyjdLhg0KoR/giphy.gif"
        )

        for cog, commands_list in mapping.items():
            filtered = await self.filter_commands(commands_list, sort=True)
            filtered = [cmd for cmd in filtered if cmd.name != "help"]

            if not filtered:
                continue

            if cog:
                raw_name = cog.qualified_name
                cog_name = raw_name.replace("Cog", "").replace("Commands", "").strip()
            else:
                cog_name = "Tidak Berkategori"

            command_names = [f"`{self.context.clean_prefix}{cmd.name}`" for cmd in filtered]
            embed.add_field(
                name=f"📁 {cog_name}",
                value=", ".join(command_names),
                inline=False
            )

        embed.set_footer(text=f"Gunakan {self.context.clean_prefix}help <command> untuk detail.")
        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command):
        embed = discord.Embed(
            title=f"GoMu Help Untuk`{command.name}`",
            description=command.help or "Tidak ada deskripsi.",
            color=discord.Color.blurple()
        )
        embed.add_field
        embed.add_field(name="Usage", value=f"`{self.context.clean_prefix}{command.name} {command.signature}`", inline=False)
        await self.get_destination().send(embed=embed)
