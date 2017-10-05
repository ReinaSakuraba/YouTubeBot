import pkg_resources

import discord
from discord.ext import commands

from utils import subprocess, EmbedPaginator


class Info:
    @commands.command()
    async def uptime(self, ctx):
        """Shows the bot's current uptime."""

        await ctx.send(f'Uptime: **{ctx.bot.uptime}**')

    @commands.command()
    async def about(self, ctx):
        """Tells you information about the bot itself."""

        recent_changes = await self.get_recent_changes(limit=3)
        owner = ctx.bot.owner
        version = pkg_resources.get_distribution('discord.py')

        embed = discord.Embed(color=0xFF0000, timestamp=ctx.bot.start_time)
        embed.set_author(name=owner, icon_url=owner.avatar_url)
        embed.add_field(name='Uptime', value=ctx.bot.uptime)
        embed.add_field(name='Servers', value=len(ctx.bot.guilds), inline=False)
        embed.add_field(name='Memory Usage', value=ctx.bot.memory_usage)
        embed.add_field(name='CPU Usage', value=ctx.bot.cpu_usage)
        embed.add_field(name='Recent Changes', value=recent_changes, inline=False)
        embed.set_footer(text=f'Made with {version}', icon_url='http://i.imgur.com/5BFecvA.png')

        await ctx.send(embed=embed)

    @commands.command()
    async def changelog(self, ctx):
        """Shows recent changes made to the bot."""

        changes = await self.get_recent_changes()
        changes = changes.split('\n')

        try:
            paginator = EmbedPaginator(ctx, entries=changes)
            paginator.embed.title = 'Change Log'
            paginator.embed.color = 0xFF0000
            await paginator.paginate()
        except Exception as e:
            await ctx.send(e)

    @commands.command()
    async def invite(self, ctx):
        """Posts the bot's invite link."""

        app_info = await ctx.bot.application_info()

        permissions = discord.Permissions()
        permissions.read_messages = True
        permissions.send_messages = True
        permissions.manage_messages = True
        permissions.add_reactions = True
        permissions.embed_links = True
        permissions.read_message_history = True

        invite = discord.utils.oauth_url(app_info.id, permissions=permissions)
        await ctx.send(invite)

    @commands.command(aliases=['github'])
    async def source(self, ctx):
        """Posts the source code for the bot."""

        await ctx.send(await self.get_github_url())

    async def get_github_url(self):
        result = await subprocess('git remote get-url origin')
        return result[:-5]

    async def get_recent_changes(self, *, limit=None):
        url = await self.get_github_url()
        cmd = f'git log --pretty=format:"[%s]({url}/commit/%H) (%cr)"'
        if limit is not None:
            cmd += f' -{limit}'

        result = await subprocess(cmd)
        return result

    @commands.command()
    async def feedback(self, ctx, *, message: str):
        """Gives feedback about the bot.

        Used to request features or bug fixes.
        """

        channel = ctx.bot.get_channel(ctx.bot.feedback_channel)
        if channel is None:
            return

        embed = discord.Embed(title='Feedback', description=message)
        embed.timestamp = ctx.message.created_at
        embed.color = 0xFF0000
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
        embed.set_footer(text=f'Author ID: {ctx.author.id}')

        await channel.send(embed=embed)
        await ctx.send('Successfully sent feedback')


def setup(bot):
    bot.add_cog(Info())
