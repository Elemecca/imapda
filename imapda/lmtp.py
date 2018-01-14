
import re

from twisted.mail.smtp import ESMTP


class ESMTPEnhancedStatus(object):
    def extensions(self):
        ext = super(ESMTPEnhancedStatus, self).extensions(self)
        ext['ENHANCEDSTATUSCODES'] = None
        return ext

    __codeRe = re.compile(r'')
    def sendCode(self, code, message=''):
        match = self.__codeRe.match(message)
        if not match:
            message = str(code / 100) + '.0.0  ' + message

        ESMTP.sendCode(self, code, message)

class LMTP(ESMTP):
    # the LHLO command has identical semantics to EHLO
    def do_LHLO(self, rest):
        return ESMTP.do_EHLO(self, rest)

    # an LMTP server must not accept the HELO or EHLO commands
    def do_HELO(self, rest):
        return self.do_UNKNOWN(self, rest)

    # an LMTP server must not accept the HELO or EHLO commands
    def do_EHLO(self, rest):
        return self.do_UNKNOWN(self, rest)

    def _messageHandled(self, resultList):
        for (success, result) in resultList:
            if success:
                self.sendCode(250, 'OK')

