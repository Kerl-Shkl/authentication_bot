import local_socket
import signal
import asyncio
import frontend
import logging

shutdown_event = asyncio.Event()


async def main():
    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGINT, shutdown_event.set)

    local_socket_task = asyncio.create_task(local_socket.run())
    tg_bot_task = asyncio.create_task(frontend.run())
    tasks = [local_socket_task, tg_bot_task]

    await shutdown_event.wait()
    logging.info("Terminating. GoodBye!")
    frontend.dp.stop_polling()
    for task in tasks:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    asyncio.run(main())
