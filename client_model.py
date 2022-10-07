from asyncio import StreamReader, StreamWriter
from datetime import datetime


class ClientModel:
    def __init__(self, reader: StreamReader, writer: StreamWriter):
        self._reader: StreamReader = reader
        self._writer: StreamWriter = writer
        self._ip: str = writer.get_extra_info('peername')[0]
        self._port: int = writer.get_extra_info('peername')[1]
        self.nickname: str = str(writer.get_extra_info('peername'))
        self.complaint_count: int = 0
        self.banned_time: datetime = None
        self.first_message: datetime = None
        self.message_count: int = 0

    def __str__(self):
        return f"{self.nickname} {self.ip}:{self.port}"

    @property
    def reader(self):
        return self._reader

    @property
    def writer(self):
        return self._writer

    @property
    def ip(self):
        return self._ip

    @property
    def port(self):
        return self._port

    async def get_message(self) -> str:
        return str((await self.reader.read(255)).decode('utf8'))

    def send_message(self, message: str) -> bytes:
        return self.writer.write(message)

    def ban_time(self):
        """
        Clear ban if more than 4 hours left
        """
        if self.banned_time:
            time_left = datetime.now() - self.banned_time
            if (time_left.seconds/60) >= 240:
                self.complaint_count = 0

    def messaging_time(self):
        """
        Clear message_count if more than 1 hour left
        """
        if self.first_message:
            time_left = datetime.now() - self.first_message
            if (time_left.seconds/60) >= 60:
                self.message_count = 0
