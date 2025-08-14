import os
import asyncio
import pomice
import discord
from utils.utillity import logger
from help import CustomHelpCommand
from discord.ext import commands
from dotenv import load_dotenv
from datetime import timedelta, timezone, datetime

WIB = timezone(timedelta(hours=7))


# === Load Environment Variables ===
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
SERVER_PASSWORD = os.getenv("LAVALINK_PASSWORD")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
HOST = os.getenv("SERVER_HOST")
SPOTIFY_CLIENT_SECRET = os.getenv("SPCLIENT_SECRET")

# === Intents ===
intents = discord.Intents.all()

def pre_ready():
        print("""


   ▄██████▄   ▄██████▄     ▄▄▄▄███▄▄▄▄   ███    █▄  
  ███    ███ ███    ███  ▄██▀▀▀███▀▀▀██▄ ███    ███ 
  ███    █▀  ███    ███  ███   ███   ███ ███    ███ 
 ▄███        ███    ███  ███   ███   ███ ███    ███ 
▀▀███ ████▄  ███    ███  ███   ███   ███ ███    ███ 
  ███    ███ ███    ███  ███   ███   ███ ███    ███ 
  ███    ███ ███    ███  ███   ███   ███ ███    ███ 
  ████████▀   ▀██████▀    ▀█   ███   █▀  ████████▀  
                                                    



""")

# === Custom Bot Class ===
class GOMU(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned_or("g!", "G!"),
            intents=intents,
            help_command=CustomHelpCommand(),
            case_insensitive=True,
        )
        self.pool = pomice.NodePool()
        self.first_start = True


    def is_node_connected(self, identifier: str) -> bool:
        node = self.pool.nodes.get(identifier.upper())
        return node is not None and node.is_connected


    async def connect_node(self, identifier="MAIN"):
        try:
            await self.pool.create_node(
                bot=self,
                host=HOST,
                port=2333,
                password=SERVER_PASSWORD,
                identifier=identifier,
                spotify_client_id=SPOTIFY_CLIENT_ID,
                spotify_client_secret=SPOTIFY_CLIENT_SECRET
            )
            logger.info("✅ Node Lavalink berhasil dibuat dan tersambung")

        except pomice.NodeConnectionFailure:
            logger.warning(f"❌ Gagal membuat node Lavalink")

        except pomice.LavalinkVersionIncompatible:
            logger.warning(f"Versi lavalink tidak compatible")

    async def setup_hook(self):
        await self.load_extension("cog.lavalink")
        logger.info("Lavalink File Berhasil Di Load")
        await asyncio.sleep(0.25)
        await self.load_extension("cog.user")
        logger.info("User File Berhasil Di Load")
        await self.load_extension("cog.music")
        logger.info("Music File Berhasil Di Load")
        await self.load_extension("cog.search")
        logger.info("✅ Semua cog berhasil di-load")

    async def on_ready(self) -> None:
        if self.first_start:
            logger.info(f"✅ Bot login sebagai {self.user} ({self.user.id})")
            await self.connect_node("MAIN")
            if not self.is_node_connected("MAIN"):
                logger.warning("🔴 Node MAIN belum tersedia setelah login.")
            else:
                logger.info("🟢 Node MAIN aktif dan tersambung.")

            activity = discord.Activity(type=discord.ActivityType.watching, name="Goverment")
            await bot.change_presence(status=discord.Status.online, activity=activity)

            self.first_start= False

    async def on_message(self,message: discord.Message):
        if message.author.bot:
            return
        logger.debug(f"Pesan diterima: {message.content}")
        await self.process_commands(message)


# === Main Entry Point ===
bot = GOMU()

if __name__ == "__main__":
    try:
        pre_ready()
        logger.info(f'Welcome Mr Hellenoir')
        asyncio.run(bot.start(TOKEN))
    except KeyboardInterrupt:
        logger.info('Bot Memutuskan Konseksi')
