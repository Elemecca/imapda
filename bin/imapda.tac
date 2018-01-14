from twisted.application.service import Application
from twisted.application.internet import TCPServer
from twisted.application import strports

from twisted.mail.smtp import SMTPFactory
from imapda.lmtp import LMTP

application = Application("IMAP-DA")

lmtpPort = "unix:lmtp"
lmtpFactory = SMTPFactory()
lmtpFactory.protocol = LMTP
lmtpService = strports.service(lmtpPort, lmtpFactory)
lmtpService.setServiceParent(application)
