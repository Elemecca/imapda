
from email_validator import validate_email, EmailNotValidError
from aiosmtpd.smtp import SMTP

from imapda import __version__

class LMTP(SMTP):
    def __init__(self, factory, **kwargs):
        # pass self as handler to superclass
        super().__init__(self, **kwargs)
        self.factory = factory
        self.__ident__ = "IMAP Delivery Agent {}".format(__version__)

    # LMTP 4.1 - `LHLO` must behave identically to ESMTP `EHLO`
    async def smtp_LHLO(self, arg):
        await super().smtp_EHLO(arg)

    # LMTP 4.1 - SMTP `HELO` must not be supported
    async def smtp_HELO(self, arg):
        await self.push("500 this is LMTP, use LHLO instead of HELO")

    # LMTP 4.1 - ESMTP `EHLO` must not be supported
    async def smtp_EHLO(self, arg):
        await self.push("500 this is LMTP, use LHLO instead of EHLO")


    async def handle_RCPT(self, server, session, envelope, address, opts):
        try:
            addr = validate_email(
                address,
                allow_smtputf8 = True,
                check_deliverability = False,
            )

            if addr['email'] not in self.factory.addresses:
                return (
                    "553 5.1.0 no configuration for address <{}>"
                        .format(addr['email'])
                )

            envelope.rcpt_tos.append(addr['email'])
            return "250 OK"

        except EmailNotValidError as err:
            return "553 5.1.3 invalid address <{}>".format(address)


    async def handle_DATA(self, server, session, envelope):
        return '250 OK good!'


class LMTPFactory(object):
    def __init__(self, addresses):
        self.addresses = addresses

    def __call__(self):
        return LMTP(
            self,
            enable_SMTPUTF8 = True,
        )
