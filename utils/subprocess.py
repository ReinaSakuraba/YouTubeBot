import asyncio


async def subprocess(cmd):
    pipe = asyncio.subprocess.PIPE
    func = asyncio.create_subprocess_shell
    process = await func(cmd, stdout=pipe, stderr=pipe)

    result = await process.communicate()
    return ''.join(x.decode('utf-8') for x in result)
