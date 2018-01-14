import asyncio
import signal
from contextlib import suppress
from functools import partial

from imapda.lmtp import LMTPFactory

class Server(object):
    def __init__(self):
        pass

    def run(self):
        loop = asyncio.get_event_loop()

        factory = LMTPFactory()
        server = loop.run_until_complete(
                loop.create_unix_server(factory, path="lmtp")
            )


        # signal handlers aren't supported on Windows
        with suppress(NotImplementedError):
            loop.add_signal_handler(signal.SIGINT, loop.stop)

        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass

        server.close()
        loop.run_until_complete(server.wait_closed())
        loop.close()
