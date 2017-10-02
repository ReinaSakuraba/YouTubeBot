import asyncio

import discord


class CannotPaginate(Exception):
    pass


class Paginator:
    def __init__(self, ctx, *, entries):
        self.bot = ctx.bot
        self.entries = entries
        self.channel = ctx.channel
        self.author = ctx.author

        self.paginating = len(entries) > 1

        self.reaction_emojis = {
            '\N{BLACK LEFT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}': self.first_page,
            '\N{BLACK LEFT-POINTING TRIANGLE}': self.previous_page,
            '\N{BLACK RIGHT-POINTING TRIANGLE}': self.next_page,
            '\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}': self.last_page,
            '\N{BLACK SQUARE FOR STOP}': self.stop_pages,
        }

    async def show_entry(self, entry):
        self.current_entry = entry
        content = f'[{entry + 1}/{len(self.entries)}]\n{self.entries[entry]}'
        await self.message.edit(content=content)

    async def checked_show_entry(self, entry):
        if entry >= 0 and entry <= len(self.entries) - 1:
            await self.show_entry(entry)

    async def next_page(self):
        await self.checked_show_entry(self.current_entry + 1)

    async def previous_page(self):
        await self.checked_show_entry(self.current_entry - 1)

    async def first_page(self):
        await self.show_entry(0)

    async def last_page(self):
        await self.show_entry(len(self.entries) - 1)

    async def stop_pages(self):
        self.paginating = False
        await self.message.clear_reactions()

    def check(self, reaction, user):
        if user is None or user.id != self.author.id:
            return False

        if reaction.message.id != self.message.id:
            return False

        return reaction.emoji in self.reaction_emojis

    async def paginate(self):
        if len(self.entries) == 1:
            await self.channel.send(self.entries[0])
            return
        self.current_entry = 0
        self.message = await self.channel.send(f'[{self.current_entry + 1}/{len(self.entries)}]\n{self.entries[0]}')
        for emoji in self.reaction_emojis:
            await self.message.add_reaction(emoji)

        while self.paginating:
            try:
                reaction, user = await self.bot.wait_for('reaction_add', check=self.check, timeout=120.0)
            except asyncio.TimeoutError:
                self.paginating = False
                try:
                    await self.message.clear_reactions()
                finally:
                    break

            try:
                await self.message.remove_reaction(reaction, user)
            except:
                pass

            func = self.reaction_emojis.get(reaction.emoji)
            await func()
