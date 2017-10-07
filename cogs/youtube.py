import io
import re

import discord
from discord.ext import commands

from utils import Paginator, group

API_BASE = 'https://www.googleapis.com/youtube/v3/'
YOUTUBE_BASE = 'https://www.youtube.com/'
VIDEO_BASE = YOUTUBE_BASE + 'watch?v='
CHANNEL_BASE = YOUTUBE_BASE + 'channel/'
PLAYLIST_BASE = YOUTUBE_BASE + 'playlist?list='

PLAYLIST_REGEX = re.compile(r'https?://www.youtube.com/.*?list=([a-zA-Z0-9-_]+).*')


class Query(commands.Converter):
    def __init__(self, *, multi=True, **kwargs):
        self.multi = multi
        self.params = {'part': 'id'}
        self.params.update(kwargs)

    def parse_argument(self, argument):
        if not self.multi:
            return argument, 1

        view = commands.view.StringView(argument)
        limit = commands.view.quoted_word(view)
        view.skip_ws()
        query = view.read_rest()
        try:
            limit = int(limit)
        except ValueError:
            query = f'{limit} {query}'
            limit = 1

        if not query:
            query = str(limit)
            limit = 1

        if limit <= 0:
            raise commands.BadArgument('Search limit must be greater than 0.')

        return query, limit

    async def convert(self, ctx, argument):
        query, limit = self.parse_argument(argument)

        params = {
            'q': query,
            'maxResults': limit,
        }
        params.update(self.params)
        return params


class YouTube:
    async def __error(self, ctx, exception):
        if isinstance(exception, commands.BadArgument):
            await ctx.send(exception)

    async def request(self, ctx, route, params):
        params['key'] = ctx.bot.youtube_key
        async with ctx.session.get(API_BASE + route, params=params) as r:
            if r.status == 200:
                return await r.json()

    @group(usage='[amount=1] <query>', invoke_without_command=True)
    async def search(self, ctx, *, params: Query(type='video')):
        """Searches YouTube for your query.

        If you don't pass in a subcommand, this will search for a video.
        If your query starts with a number you must put it in quotes.
        """

        await self.show_entries(ctx, params)

    @search.command(usage='[amount=1] <query>')
    async def channel(self, ctx, *, params: Query(type='channel')):
        """Searches YouTube for a channel."""

        await self.show_entries(ctx, params)

    @search.command(usage='[amount=1] <query>')
    async def playlist(self, ctx, *, params: Query(type='playlist')):
        """Searches YouTube for a playlist."""

        await self.show_entries(ctx, params)

    @search.command(usage='[amount=1] <query>')
    async def livestream(self, ctx, *, params: Query(type='video', eventType='live')):
        """Searches YouTube for a livestream."""

        await self.show_entries(ctx, params)

    @commands.command(aliases=['pldump'])
    async def dump(self, ctx, link: str):
        """Gets all the URLs from a YouTube playlist."""

        match = PLAYLIST_REGEX.match(link)
        if match is None:
            return await ctx.send('This is not a valid link.')

        playlist_id = match.group(1)
        videos = []

        params = {
            'part': 'contentDetails',
            'playlistId': playlist_id
        }
        entries = await self.get_entries(ctx, 'playlistItems', params, all_entries=True)
        if entries is None:
            return await ctx.send('This is not a valid playlist.')

        links = [VIDEO_BASE + entry['contentDetails']['videoId'] for entry in entries]

        file = io.BytesIO('\r\n'.join(links).encode('utf8'))
        await ctx.send(file=discord.File(file, 'playlist.txt'))

    async def get_entries(self, ctx, search_type, params, *, all_entries=False):
        entries = []
        limit = params.get('maxResults')

        while True:
            if all_entries:
                params['maxResults'] = 50
            else:
                params['maxResults'] = min(50, limit)
                limit = max(0, limit - 50)

            data = await self.request(ctx, search_type, params)
            if data is None:
                return entries

            items = data['items']
            entries.extend(items)

            page_token = data.get('nextPageToken')

            if page_token is None or limit == 0:
                return entries

            params['pageToken'] = page_token

    async def show_entries(self, ctx, params):
        entries = await self.get_entries(ctx, 'search', params)

        search_type = params['type']
        if not entries:
            return await ctx.send(f'No {search_type}s found.')

        base = globals().get(f'{search_type.upper()}_BASE')
        links = [base + entry['id'][f'{search_type}Id'] for entry in entries]

        try:
            paginator = Paginator(ctx, entries=links)
            await paginator.paginate()
        except Exception as e:
            await ctx.send(e)


def setup(bot):
    bot.add_cog(YouTube())
