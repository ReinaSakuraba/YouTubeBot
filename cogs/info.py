import asyncio
import pkg_resources

import discord
from discord.ext import commands

from utils import subprocess


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

    @commands.command()
    async def source(self, ctx):
        """Posts the source code for the bot."""

        await ctx.send('https://github.com/ReinaSakuraba/YoutubeBot')

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


def setup(bot):
    bot.add_cog(Info())
