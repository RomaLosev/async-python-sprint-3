import asyncio
from asyncio import StreamReader, StreamWriter
from loguru import logger

from client_model import Client

logger.add(
    'chat.log',
    format='{time} {level} {message}',
    level='DEBUG',
)

WELCOME = "Welcome to chat \n"\
          "Please choose you nickname \n" \
          "Write /nick <your nickname> \n" \
          "You can send private msg \n" \
          "Write /private <nickname> <message>\n" \
          "Write quit to leave chat"


class Server:
    def __init__(self, loop: asyncio.AbstractEventLoop, ip: str = '127.0.0.1', port: int = 8000):
        self.__ip: str = ip
        self.__port: int = port
        self.__loop: asyncio.AbstractEventLoop = loop
        self.__clients: dict[asyncio.Task, Client] = {}
        self.__logger = logger

        logger.info(f"Server Initialized with {self.ip}:{self.port}")

    @property
    def ip(self):
        return self.__ip

    @property
    def port(self):
        return self.__port

    @property
    def logger(self):
        return self.__logger

    @property
    def loop(self):
        return self.__loop

    @property
    def clients(self):
        return self.__clients

    def start_server(self):
        try:
            srv = asyncio.start_server(
                self.accept_client, self.ip, self.port
            )
            self.loop.run_until_complete(srv)
            self.loop.run_forever()
        except Exception as e:
            self.logger.error(e)
        except KeyboardInterrupt:
            self.logger.warning("Keyboard Interrupt Detected. Shutting down!")

        self.shutdown_server()

    def accept_client(self, reader: StreamReader, writer: StreamWriter):
        client = Client(reader, writer)
        task = asyncio.Task(self.incoming_client_message_cb(client))
        self.clients[task] = client
        writer.write(WELCOME.encode())
        client_ip = writer.get_extra_info('peername')[0]
        client_port = writer.get_extra_info('peername')[1]
        self.logger.info(f"New Connection: {client_ip}:{client_port}")

        task.add_done_callback(self.disconnect_client)

    async def incoming_client_message_cb(self, client: Client):
        while True:
            client_message = await client.get_message()

            if client_message.startswith("quit"):
                break
            elif client_message.startswith("/"):
                self.handle_client_command(client, client_message)
            else:
                self.broadcast_message(
                    f"{client.nickname}: {client_message}".encode('utf8'))

            self.logger.info(f"{client_message}")

            await client.writer.drain()

        self.logger.info("Client Disconnected!")

    def handle_client_command(self, client: Client, client_message: str):
        client_message = client_message.replace("\n", "").replace("\r", "")
        if client_message.startswith("/nick"):
            split_client_message = client_message.split(" ")
            if len(split_client_message) >= 2:
                client.nickname = split_client_message[1]
                client.writer.write(
                    f"Nickname changed to {client.nickname}\n".encode('utf8'))
                return

        elif client_message.startswith("/private"):
            split_client_message = client_message.split(" ")
            if len(split_client_message) >= 2:
                msg_for = split_client_message[1]
                for target in self.clients.values():
                    if msg_for == target.nickname:
                        self.private_message(
                            (
                                client_message.replace(
                                    "/private", f"private message from {client.nickname}: "
                                ).replace(f"{msg_for}", "")
                             ).encode(), target
                        )
        else:
            client.writer.write("Invalid Command\n".encode('utf8'))

    def broadcast_message(self, message: bytes, exclusion_list: list = []):
        logger.info(self.clients)
        for client in self.clients.values():
            if client not in exclusion_list:
                client.writer.write(message)

    @staticmethod
    def private_message(message: bytes, target: Client):
        target.writer.write(message)

    def disconnect_client(self, task: asyncio.Task):
        client = self.clients[task]

        self.broadcast_message(
            f"{client.nickname} has left!".encode('utf8'), [client])

        del self.clients[task]
        client.writer.write('quit'.encode('utf8'))
        client.writer.close()
        self.logger.info("End Connection")

    def shutdown_server(self):
        self.logger.info("Shutting down server!")
        for client in self.clients.values():
            client.writer.write('quit'.encode('utf8'))
        self.loop.stop()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    server = Server(loop)
    server.start_server()
