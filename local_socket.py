import socket
import asyncio
import uuid
from asyncio import AbstractEventLoop
from controller import controller, Request
import os
import time

SOCKET_PATH = "/tmp/permissions_bot_socket"


async def readRequest(connection: socket.socket, loop: AbstractEventLoop) -> Request:
    buffer = bytes()
    while len(buffer) < 4:
        readed = await loop.sock_recv(connection, 1024)
        if len(readed) == 0:
            return None
        buffer += readed
    size = int.from_bytes(buffer[:4], "little")
    if size <= 21:
        raise IOError("Incorrect request size: " + str(size))
    while len(buffer) < size:
        readed = await loop.sock_recv(connection, size)
        if len(readed) == 0:
            return None
        buffer += readed
        await asyncio.sleep(5)
    print("size:", size, " buffer:", buffer)
    return Request(
        uuid.UUID(bytes=buffer[4:20]),
        int.from_bytes(buffer[20:21], "little"),
        str(buffer[21:]),
    )


async def askRequest(connection: socket.socket, loop: AbstractEventLoop, req: Request):
    req.fut = loop.create_future()
    await controller.handleRequest(req)  # ask request
    await req.fut  # wait response
    if connection.fileno() != -1:
        response: bytes = req.id.bytes + bytes.fromhex(
            "01" if req.fut.result() else "00"
        )
        print("send response:", response.hex(sep=" ", bytes_per_sep=1))
        await loop.sock_sendall(connection, response)


async def handle(connection: socket.socket, loop: AbstractEventLoop) -> None:
    try:
        while req := await readRequest(connection, loop):
            print("handle request:", req.id, req.op, req.name)
            asyncio.create_task(askRequest(connection, loop, req))
    except IOError as error:
        print("readRequest error:", error)
    finally:
        print(f"Connection {connection.fileno()} close")
        connection.close()


async def listen_for_connection(server_socket: socket.socket, loop: AbstractEventLoop):
    while True:
        connection, address = await loop.sock_accept(server_socket)
        connection.setblocking(False)
        print(f"open connection {connection.fileno()}")
        asyncio.create_task(handle(connection, loop))


def delete_socket():
    try:
        os.unlink(SOCKET_PATH)
    except OSError:
        if os.path.exists(SOCKET_PATH):
            raise


async def run():
    delete_socket()
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server_socket:
            server_socket.setblocking(False)
            server_socket.bind(SOCKET_PATH)
            server_socket.listen()

            print(f"Open socket {SOCKET_PATH}")
            asyncio_loop = asyncio.get_event_loop()
            await listen_for_connection(server_socket, asyncio_loop)
    finally:
        delete_socket()
