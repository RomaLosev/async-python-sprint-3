import asyncio
import sys
from aioconsole import ainput


class Client:
    def __init__(self, loop: asyncio.AbstractEventLoop, server_ip: str = '127.0.0.1', server_port: int = 8000):
        self.__server_ip: str = server_ip
        self.__server_port: int = server_port
        self.__loop: asyncio.AbstractEventLoop = loop
        self.__reader: asyncio.StreamReader = None
        self.__writer: asyncio.StreamWriter = None

    @property
    def server_ip(self):
        return self.__server_ip

    @property
    def server_port(self):
        return self.__server_port

    @property
    def loop(self):
        return self.__loop

    @property
    def reader(self):
        return self.__reader

    @property
    def writer(self):
        return self.__writer

    async def connect_to_server(self):
        try:
            self.__reader, self.__writer = await asyncio.open_connection(
                self.server_ip, self.server_port)
            await asyncio.gather(
                self.receive_messages(),
                self.start_client_cli()
            )
        except Exception as ex:
            print("An error has occurred: " + ex)

        print("Shutting down")

    async def receive_messages(self):
        server_message: str = None
        while server_message != 'quit':
            server_message = await self.get_server_message()
            print(f"{server_message}")

        if self.loop.is_running():
            self.loop.stop()

    async def get_server_message(self):
        return str((await self.reader.read(255)).decode('utf8'))

    async def start_client_cli(self):
        client_message: str = None
        while client_message != 'quit':
            client_message = await ainput("")
            self.writer.write(client_message.encode('utf8'))
            await self.writer.drain()

        if self.loop.is_running():
            self.loop.stop()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    client = Client(loop)
    asyncio.run(client.connect_to_server())
