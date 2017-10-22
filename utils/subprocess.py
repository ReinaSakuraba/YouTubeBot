import asyncio


async def run_subprocess(cmd):
    pipe = asyncio.subprocess.PIPE
    func = asyncio.create_subprocess_shell
    process = await func(cmd, stdout=pipe, stderr=pipe)

    result = await process.communicate()
    return [x.decode('utf-8') for x in result]
