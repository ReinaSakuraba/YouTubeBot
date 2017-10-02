import io
import inspect
import textwrap
import traceback
from contextlib import redirect_stdout

from discord.ext import commands


class Owner:
    """Owner-only commands used to maintain the bot."""

    def __init__(self):
        self._last_result = None

    async def __local_check(self, ctx):
        return ctx.author == ctx.bot.owner

    async def __error(self, ctx, exception):
        if isinstance(exception, commands.CheckFailure):
            await ctx.send('Only the bot owner may use this command.')

    def cleanup_code(self, content):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])

        # remove `foo`
        return content.strip('` \n')

    def get_syntax_error(self, e):
        if e.text is None:
            return f'```py\n{e.__class__.__name__}: {e}\n```'
        return f'```py\n{e.text}{"^":>{e.offset}}\n{e.__class__.__name__}: {e}```'

    @commands.command(name='eval')
    async def _eval(self, ctx, *, body: str):
        """Evaluates a code"""

        env = {
            'bot': ctx.bot,
            'ctx': ctx,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'message': ctx.message,
            '_': self._last_result
        }

        env.update(globals())

        body = self.cleanup_code(body)
        stdout = io.StringIO()

        to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

        try:
            exec(to_compile, env)
        except Exception as e:
            return await ctx.send(f'```py\n{e.__class__.__name__}: {e}\n```')

        func = env['func']
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception as e:
            value = stdout.getvalue()
            await ctx.send(f'```py\n{value}{traceback.format_exc()}\n```')
        else:
            value = stdout.getvalue()
            try:
                await ctx.message.add_reaction('\u2705')
            except:
                pass

            if ret is None:
                if value:
                    await ctx.send(f'```py\n{value}\n```')
            else:
                self._last_result = ret
                await ctx.send(f'```py\n{value}{ret}\n```')

    @commands.command()
    async def setavatar(self, ctx, link: str):
        """Sets the bot's avatar."""

        async with ctx.session.get(link) as r:
            if r.status == 200:
                try:
                    await ctx.bot.user.edit(avatar=await r.read())
                except Exception as e:
                    await ctx.send(e)
                else:
                    await ctx.send('Avatar set.')
            else:
                await ctx.send('Unable to download image.')

    @commands.command()
    async def setname(self, ctx, *, name: str):
        """Sets the bot's name."""

        try:
            await ctx.bot.user.edit(username=name)
        except Exception as e:
            await ctx.send(e)
        else:
            await ctx.send('Name set.')

    @commands.command()
    async def logout(self, ctx):
        """Logs out of the bot."""

        await ctx.bot.logout()

    @commands.command()
    async def load(self, ctx, *, module: str):
        """Loads a module."""

        module = f'cogs.{module}'
        try:
            ctx.bot.load_extension(module)
        except Exception as e:
            await ctx.send(f'```py\n{traceback.format_exc()}\n```')
        else:
            await ctx.send('\N{OK HAND SIGN}')

    @commands.command()
    async def unload(self, ctx, *, module: str):
        """Unloads a module."""

        module = f'cogs.{module}'
        try:
            ctx.bot.unload_extension(module)
        except Exception as e:
            await ctx.send(f'```py\n{traceback.format_exc()}\n```')
        else:
            await ctx.send('\N{OK HAND SIGN}')

    @commands.command()
    async def reload(self, ctx, *, module: str):
        """Reloads a module."""

        module = f'cogs.{module}'
        try:
            ctx.bot.unload_extension(module)
            ctx.bot.load_extension(module)
        except Exception as e:
            await ctx.send(f'```py\n{traceback.format_exc()}\n```')
        else:
            await ctx.send('\N{OK HAND SIGN}')


def setup(bot):
    bot.add_cog(Owner())
