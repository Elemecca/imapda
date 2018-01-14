import argparse
import asyncio
from configparser import ConfigParser
from contextlib import suppress
import logging
import logging.config
import os
import signal
import sys

from email_validator import validate_email, EmailNotValidError

from imapda import __version__
from imapda.lmtp import LMTPFactory

log = logging.getLogger('main')

def main():
    logging.basicConfig(
            level = logging.INFO,
            format = '%(asctime)s %(levelname)s[%(name)s]: %(message)s',
        )

    # set the log level for aiosmtpd to warning
    # they spam a bunch of stuff at info that should be debug
    logging.config.dictConfig({
        'version': 1,
        'incremental': True,
        'loggers': {
            'mail.log': {'level': logging.WARNING},
        },
    })


    cli = argparse.ArgumentParser(
        description = "LMTP IMAP Delivery Agent",
    )

    cli.add_argument(
        '-f', '--config-file',
        default = '/etc/imapda.conf',
        help = "load an alternative configuration file",
    )

    args = cli.parse_args()

    log.info('imapda %s starting', __version__)


    config_file = os.path.abspath(args.config_file)
    config = ConfigParser()
    try:
        with open(config_file, 'rt', encoding='utf-8') as reader:
            config.read_file(reader)
    except OSError as caught:
        log.error(
            "can't read config file %s: %s\n",
            config_file,
            caught.strerror
        )
        sys.exit(1)

    log.info("loaded config file %s", config_file)


    # validate and normalize address config sections
    addresses = []
    addr_fail = False
    for section in config.sections():
        if '@' not in section:
            continue

        try:
            addr = validate_email(
                section,
                allow_smtputf8 = False,
                check_deliverability = False,
            )
        except EmailNotValidError as err:
            log.error("invalid address in config: %s", section)
            addr_fail = True
            continue

        addresses.append(addr['email'])

    if addr_fail:
        sys.exit(2)

    factory = LMTPFactory(addresses=addresses)


    loop = asyncio.get_event_loop()

    # signal handlers aren't supported on Windows
    with suppress(NotImplementedError):
        loop.add_signal_handler(signal.SIGINT, loop.stop)
        loop.add_signal_handler(signal.SIGTERM, loop.stop)


    proto = config['server'].get('protocol', 'tcp')

    if 'tcp' == proto:
        host = config['server'].get('host', '127.0.0.1')
        port = config['server'].get('port', 8025)

        try:
            server = loop.run_until_complete(
                loop.create_server(factory, host, int(port))
            )
        except Exception as caught:
            log.error(
                "can't bind to TCP port %s:%s: %s",
                host, port,
                getattr(caught, 'strerror', str(caught)),
            )
            sys.exit(2)

        log.info("listening on TCP port %s:%s", host, port)

    elif 'unix' == proto:
        path = config['server'].get('path')
        if path is None:
            log.error("path is required when protocol=unix")
            sys.exit(1)

        path = os.path.abspath(path)
        try:
            server = loop.run_until_complete(
                loop.create_unix_server(factory, path=path)
            )
        except Exception as caught:
            log.error(
                "can't bind to UNIX socket %s: %s",
                path,
                getattr(caught, 'strerror', str(caught)),
            )
            sys.exit(2)

        log.info("listening on UNIX socket %s", path)

    else:
        log.info("unsupported protocol %s", proto)
        sys.exit(1)


    with suppress(KeyboardInterrupt):
        loop.run_forever()

    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()
