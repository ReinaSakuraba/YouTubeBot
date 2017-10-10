import io
import re

import discord
from discord.ext import commands
import dateutil.parser

from utils import Paginator, group

API_BASE = 'https://www.googleapis.com/youtube/v3/'
YOUTUBE_BASE = 'https://www.youtube.com/'
VIDEO_BASE = YOUTUBE_BASE + 'watch?v='
CHANNEL_BASE = YOUTUBE_BASE + 'channel/'
PLAYLIST_BASE = YOUTUBE_BASE + 'playlist?list='

VIDEO_REGEX = re.compile(r'https?://(?:www\.youtube\.com/watch\?.*v=|youtu\.be/)(?P<video_id>[\w-]+)')
CHANNEL_REGEX = re.compile(r'https?://www\.youtube\.com/(?:channel/(?P<channel_id>[\w-]+)|user/(?P<username>[\w-]+))')
PLAYLIST_REGEX = re.compile(r'https?://(?:www\.youtube\.com/(?:watch|playlist)\?|youtu\.be/).*list=(?P<playlist_id>[\w-]+)')


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

    @group(invoke_without_command=True)
    async def info(self, ctx, link: str):
        """Gets info from your YouTube link.
        
        If you don't pass in a subcommand, this will
        get info for a video.
        """

        match = VIDEO_REGEX.match(link)
        if match is None:
            return await ctx.send('This is not a valid link.')

        video_id = match.group('video_id')

        params = {
        	    'id': video_id,
        	    'part': 'snippet,statistics',
        	}

        data = await self.request(ctx, 'videos', params)

        items = data['items']
        if not items:
            return await ctx.send('This is not a valid channel.')

        info = items[0]
        snippet = info['snippet']
        statistics = info['statistics']

        created_at = dateutil.parser.parse(snippet['publishedAt'])
        icon = snippet['thumbnails']['default']['url']
        url = VIDEO_BASE + info['id']
        description = snippet['description']
        stats = '\n'.join(f'{k[:-5].title()}s: {v}' for k, v in statistics.items())

        embed = discord.Embed(title=snippet['title'], timestamp=created_at, color=0xFF0000, url=url)
        if description:
            embed.description = description

        embed.add_field(name='Stats', value=stats)
        embed.add_field(name='Uploader', value=snippet['channelTitle'])
        embed.set_thumbnail(url=icon)
        embed.set_footer(text='Created')

        await ctx.send(embed=embed)

    @info.command(name='channel')
    async def info_channel(self, ctx, link: str):
        """Gets info about a channel."""

        match = CHANNEL_REGEX.match(link)
        if match is None:
            return await ctx.send('This is not a valid link.')

        channel_id = match.group('channel_id')
        username = match.group('username')

        params = {'id': channel_id} if channel_id else {'forUsername': username}
        params['part'] = 'snippet,statistics'


        data = await self.request(ctx, 'channels', params)

        items = data['items']
        if not items:
            return await ctx.send('This is not a valid channel.')

        info = items[0]
        snippet = info['snippet']
        statistics = info['statistics']

        created_at = dateutil.parser.parse(snippet['publishedAt'])
        icon = snippet['thumbnails']['high']['url']
        url = CHANNEL_BASE + info['id']
        description = snippet['description']

        embed = discord.Embed(timestamp=created_at, color=0xFF0000)
        if description:
            embed.description = description

        embed.set_author(name=snippet['title'], icon_url=icon, url=url)
        embed.add_field(name='Subscribers', value=statistics['subscriberCount'])
        embed.add_field(name='Videos', value=statistics['videoCount'])
        embed.add_field(name='Total Views', value=statistics['viewCount'])
        embed.set_footer(text='Created')

        await ctx.send(embed=embed)

    @info.command(name='playlist')
    async def info_playlist(self, ctx, link: str):
        """Gets info about a playlist."""

        match = PLAYLIST_REGEX.match(link)
        if match is None:
            return await ctx.send('This is not a valid link.')

        playlist_id = match.group('playlist_id')

        params = {
            'part': 'snippet,contentDetails',
            'id': playlist_id,
        }
        data = await self.request(ctx, 'playlists', params)

        items = data['items']
        if not items:
            return await ctx.send('This is not a valid playlist.')

        info = items[0]
        snippet = info['snippet']
        details = info['contentDetails']

        url = PLAYLIST_BASE + info['id']
        created_at = dateutil.parser.parse(snippet['publishedAt'])
        description = snippet['description']

        embed = discord.Embed(title=snippet['title'], timestamp=created_at, color=0xFF0000, url=url)
        if description:
            embed.description = description
        embed.set_thumbnail(url=snippet['thumbnails']['default']['url'])
        embed.add_field(name='Videos', value=details['itemCount'])
        embed.add_field(name='Created By', value=snippet['channelTitle'])
        embed.set_footer(text='Created')

        await ctx.send(embed=embed)

    @commands.command(aliases=['pldump'])
    async def dump(self, ctx, link: str):
        """Gets all the URLs from a YouTube playlist."""

        match = PLAYLIST_REGEX.match(link)
        if match is None:
            return await ctx.send('This is not a valid link.')

        playlist_id = match.group(1)

        params = {
            'part': 'contentDetails',
            'playlistId': playlist_id
        }
        entries = await self.get_entries(ctx, 'playlistItems', params, all_entries=True)
        if not entries:
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
