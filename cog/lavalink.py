import discord
from discord.ext import commands
from pomice import NodePool, Player

class LavalinkCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="nodes", hidden=True)
    async def show_nodes(self, ctx):
        try:
            node = NodePool.get_node(identifier="MAIN")  # Ambil node spesifik dengan identifier
            if not node:
                await ctx.send("❌ No Lavalink nodes connected.")
            else:
                embed = discord.Embed(
                    description=f"""📡 **Lavalink Node Info**:
🟢 **Status:** {"Connected" if node.is_connected else "Disconnected"}
🌐 **REST URI:** {node._rest_uri}
🎶 **Active Players:** {node.player_count}
""")
            await ctx.send(embed=embed)
        except Exception as e:
            print(f"[ERROR] Gagal menjalankan perintah nodes: {e}")

            await ctx.send(f"❌ Terjadi kesalahan: {e}")

async def setup(bot):
    await bot.add_cog(LavalinkCog(bot))
