import discord
import pomice

class QueuePagination(discord.ui.View):
    def __init__(self, queue: pomice.Queue, per_page: int = 10, timeout: int = 80):
        """View untuk menampilkan queue Pomice dengan pagination"""
        super().__init__(timeout=timeout)
        self.queue = queue          # instance pomice.Queue
        self.per_page = per_page
        self.current_page = 0

    def create_track_list_embed(self, tracks: list[pomice.Track], start_index: int, title="🎶 Antrian Lagu"):
        description = ""
        for i, track in enumerate(tracks, start=start_index + 1):
            description += f"**{i}.** {track.title} - {track.author}\n"

        remaining = len(self.queue._queue) - (start_index + len(tracks))
        if remaining > 0:
            description += f"\nDan {remaining} lagu lainnya..."

        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.blurple()
        )
        return embed

    def get_embed(self):
        tracks = self.queue._queue  # ambil list dari pomice.Queue
        start = self.current_page * self.per_page
        end = start + self.per_page
        page_tracks = tracks[start:end]

        max_page = max((len(tracks) - 1) // self.per_page, 0)
        return self.create_track_list_embed(
            page_tracks,
            start_index=start,
            title=f"🎶 Antrian Lagu - Halaman {self.current_page + 1}/{max_page + 1}"
        )

    @discord.ui.button(label="◀ Prev", style=discord.ButtonStyle.blurple, row=0)
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.blurple, row=0)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        tracks = self.queue._queue
        max_page = max((len(tracks) - 1) // self.per_page, 0)
        if self.current_page < max_page:
            self.current_page += 1
        await interaction.response.edit_message(embed=self.get_embed(), view=self)
