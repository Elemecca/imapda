IMAP Delivery Agent
===================

`imapda` is a simple [LMTP] server that delivers messages to an [IMAP]
mailbox via the [APPEND] command. It's useful when your mail system
needs to reliably deliver messages to a third-party mailbox without
going through the normal SMTP delivery process, such as for archiving
messages that may be spam.

[LMTP]: https://tools.ietf.org/html/rfc2033
[IMAP]: https://tools.ietf.org/html/rfc3501
[APPEND]: https://tools.ietf.org/html/rfc3501#section-6.3.11
