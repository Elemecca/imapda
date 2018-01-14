
from aiosmtpd.smtp import SMTP

from imapda import __version__

class LMTP(SMTP):
    def __init__(self, **kwargs):
        # pass self as handler to superclass
        super().__init__(self, **kwargs)
        self.__ident__ = "IMAP Delivery Agent {}".format(__version__)

    # LMTP 4.1 - `LHLO` must behave identically to ESMTP `EHLO`
    async def smtp_LHLO(self, arg):
        await super().smtp_EHLO(arg)

    # LMTP 4.1 - SMTP `HELO` must not be supported
    async def smtp_HELO(self, arg):
        await self.push('500 this is LMTP, use LHLO instead of HELO')

    # LMTP 4.1 - ESMTP `EHLO` must not be supported
    async def smtp_EHLO(self, arg):
        await self.push('500 this is LMTP, use LHLO instead of EHLO')

    async def handle_DATA(self, server, session, envelope):
        return '250 OK good!'


class LMTPFactory(object):
    def __call__(self):
        return LMTP(
                enable_SMTPUTF8 = True,
            )
