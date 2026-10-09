"""Sign-in emails (ADR-0014). The only thing Chit ever emails is a one-time code; the message carries no household or child data.

CHIT_MAIL=console (default)  keeps messages in memory (tests) and, with CHIT_MAIL_ECHO=1, prints them (local development)
CHIT_MAIL=brevo              sends through Brevo's transactional API over HTTPS (EU provider; BREVO_API_KEY, CHIT_MAIL_FROM)
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass

SUBJECTS = {
    "enrol": "Your Chit code / Dein Chit-Code: {code}",
    "login": "Your Chit sign-in code / Dein Chit-Anmeldecode: {code}",
    "reauth": "Confirm it is you / Bitte bestätigen: {code}",
}
BODY = (
    "Your Chit code is {code}\n"
    "It is valid for 15 minutes and works once. If you did not ask for it, ignore this email: nothing happens without the code.\n\n"
    "Dein Chit-Code lautet {code}\n"
    "Er ist 15 Minuten gültig und nur einmal verwendbar. Wenn du ihn nicht angefordert hast, ignoriere diese E-Mail.\n"
)


class MailError(Exception):
    pass


@dataclass
class Message:
    to: str
    purpose: str
    code: str

    @property
    def subject(self) -> str:
        return SUBJECTS[self.purpose].format(code=self.code)

    @property
    def text(self) -> str:
        return BODY.format(code=self.code)


class ConsoleMailer:
    def __init__(self, echo: bool = False):
        self.outbox: list[Message] = []
        self.echo = echo

    def send_code(self, to: str, purpose: str, code: str) -> None:
        message = Message(to, purpose, code)
        self.outbox.append(message)
        if self.echo:
            print("[mail] to %s: %s" % (to, message.subject))

    def last_code(self, to: str, purpose: "str | None" = None) -> str:
        for message in reversed(self.outbox):
            if message.to.lower() == to.lower() and (purpose is None or message.purpose == purpose):
                return message.code
        raise LookupError("no mail to %s" % to)


class BrevoMailer:
    URL = "https://api.brevo.com/v3/smtp/email"

    def __init__(self, api_key: str, sender: str, sender_name: str = "Chit", timeout: float = 10.0):
        if not api_key or not sender:
            raise ValueError("BREVO_API_KEY and CHIT_MAIL_FROM are required for CHIT_MAIL=brevo")
        self.api_key, self.sender, self.sender_name, self.timeout = api_key, sender, sender_name, timeout

    def send_code(self, to: str, purpose: str, code: str) -> None:
        message = Message(to, purpose, code)
        body = json.dumps({"sender": {"name": self.sender_name, "email": self.sender}, "to": [{"email": to}],
                           "subject": message.subject, "textContent": message.text}).encode("utf-8")
        request = urllib.request.Request(self.URL, data=body, method="POST", headers={
            "api-key": self.api_key, "content-type": "application/json", "accept": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                if response.status >= 300:
                    raise MailError("mail provider answered %d" % response.status)
        except urllib.error.HTTPError as error:
            raise MailError("mail provider answered %d" % error.code) from None
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            raise MailError("mail provider unreachable: %s" % type(error).__name__) from None


def from_env():
    kind = os.environ.get("CHIT_MAIL", "console")
    if kind == "brevo":
        return BrevoMailer(os.environ.get("BREVO_API_KEY", ""), os.environ.get("CHIT_MAIL_FROM", ""),
                           os.environ.get("CHIT_MAIL_FROM_NAME", "Chit"))
    if kind == "console":
        return ConsoleMailer(echo=os.environ.get("CHIT_MAIL_ECHO") == "1")
    raise ValueError("CHIT_MAIL must be 'console' or 'brevo'")
