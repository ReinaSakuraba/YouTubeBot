import datetime
import traceback
from pathlib import Path

import psutil
import aiohttp
import discord
from discord.ext import commands

import config
from utils import human_time, CaseInsensitiveDict


class Context(commands.Context):
    @property
    def session(self):
        return self.bot.session


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='yt ', description=config.description,
                         pm_help=None, game=discord.Game(name='yt help'))

        self.all_commands = CaseInsensitiveDict(self.all_commands)

        self.youtube_key = config.youtube_key
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.process = psutil.Process()

        startup_extensions = [x.stem for x in Path('cogs').glob('*.py')]
        for extension in startup_extensions:
            try:
                self.load_extension(f'cogs.{extension}')
            except:
                print(f'Failed to load extension {extension}.')
                traceback.print_exc()

        self.loop.create_task(self.init())

    async def init(self):
        await self.wait_until_ready()
        self.start_time = datetime.datetime.utcnow()

        app_info = await self.application_info()
        self.owner_id = app_info.owner.id

        self.feedback_channel = self.get_channel(config.feedback_channel)

    @property
    def owner(self):
        return self.get_user(self.owner_id)

    @property
    def uptime(self):
        delta = datetime.datetime.utcnow() - self.start_time
        return human_time(delta.total_seconds())

    @property
    def memory_usage(self):
        memory_usage = self.process.memory_full_info().uss / 1024**2
        return f'{memory_usage:.2f} MiB'

    @property
    def cpu_usage(self):
        cpu_usage = self.process.cpu_percent() / psutil.cpu_count()
        return f'{cpu_usage}%'

    async def close(self):
        await self.session.close()
        await super().close()

    async def on_ready(self):
        print(f'Logged in as {self.user}')
        print('---------------')

    async def on_message(self, message):
        ctx = await self.get_context(message, cls=Context)
        await self.invoke(ctx)


if __name__ == '__main__':
    bot = Bot()
    bot.run(config.token)
