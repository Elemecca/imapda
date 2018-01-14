import base64
import email.utils
import os

from aiosmtpd.smtp import SMTP
from email_validator import validate_email, EmailNotValidError

from imapda import __version__



class LMTP(SMTP):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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



class LMTPHandler(object):
    def __init__(self, factory):
        self.factory = factory


    # validate and normalize sender address
    async def handle_MAIL(self, server, session, envelope, address, opts):
        envelope.mail_options.extend(opts)

        try:
            addr = validate_email(
                address,
                allow_smtputf8 = False,
                check_deliverability = False,
            )

            envelope.mail_from = addr['email']
            return "250 OK"

        except EmailNotValidError as err:
            return "501 5.1.7 invalid address <{}>".format(address)


    # validate and normalize recipient addresses
    async def handle_RCPT(self, server, session, envelope, address, opts):
        try:
            addr = validate_email(
                address,
                allow_smtputf8 = False,
                check_deliverability = False,
            )

            if addr['email'] not in self.factory.addresses:
                return (
                    "501 5.1.0 no configuration for address <{}>"
                        .format(addr['email'])
                )

            envelope.rcpt_tos.append(addr['email'])
            return "250 OK"

        except EmailNotValidError as err:
            return "501 5.1.3 invalid address <{}>".format(address)


    async def handle_DATA(self, server, session, envelope):
        date = email.utils.formatdate(localtime=True)
        msgid = base64.b64encode(os.urandom(9)).decode('us-ascii')

        status = None
        for recipient in envelope.rcpt_tos:
            if status:
                await server.push(status)

            msg = (
                "Delivered-To: {recipient}\r\n"
                "Return-Path: {sender}\r\n"
                "Received: from {peer}\r\n"
                "    by {host} ({ident})\r\n"
                "    with LMTP id {id};\r\n"
                "    {date}\r\n"
            ).format(
                recipient = recipient,
                date = date,
                id = msgid,
                sender = envelope.mail_from,
                peer = session.host_name,
                host = server.hostname,
                ident = server.__ident__,
            ).encode("us-ascii") + envelope.original_content
            print(msg.decode("us-ascii"))

            status = "250 {} <{}> OK".format(msgid, recipient)

        return status



class LMTPFactory(object):
    def __init__(self, addresses):
        self.handler = LMTPHandler(self)
        self.addresses = addresses

    def __call__(self):
        return LMTP(
            self.handler,
            decode_data = False,
            enable_SMTPUTF8 = False,
        )
