import local_socket
import asyncio
import frontend


async def main():
    local_socket_task = asyncio.create_task(local_socket.run())
    tg_bot_task = asyncio.create_task(frontend.run())

    await local_socket_task
    await tg_bot_task


if __name__ == "__main__":
    asyncio.run(main())
