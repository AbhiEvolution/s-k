import smtplib

import pytest

from app.channels import email as email_channel
from app.core.config import Settings


def settings(**overrides):
    return Settings(database_url="sqlite://", smtp_host="smtp.test", smtp_port=2525, **overrides)


class FakeSMTP:
    instances = []

    def __init__(self, host, port, **kwargs):
        self.host, self.port, self.calls, self.sent = host, port, [], []
        FakeSMTP.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def starttls(self, **kwargs):
        self.calls.append("starttls")

    def login(self, user, password):
        self.calls.append(("login", user))

    def send_message(self, message):
        self.sent.append(message)


@pytest.fixture(autouse=True)
def fake_smtp(monkeypatch):
    FakeSMTP.instances.clear()
    monkeypatch.setattr(email_channel.smtplib, "SMTP", FakeSMTP)
    monkeypatch.setattr(email_channel.smtplib, "SMTP_SSL", FakeSMTP)


def test_message_has_the_expected_headers_and_body():
    email_channel.send_email("a@example.com", "Hello", "Body text", settings(smtp_from="clinic@x.org"))
    (server,) = FakeSMTP.instances
    assert (server.host, server.port) == ("smtp.test", 2525)
    message = server.sent[0]
    assert message["To"] == "a@example.com" and message["From"] == "clinic@x.org"
    assert message["Subject"] == "Hello" and "Body text" in message.get_content()


def test_newlines_in_the_subject_cannot_inject_headers():
    email_channel.send_email("a@example.com", "Hi\r\nBcc: attacker@example.com", "x", settings())
    message = FakeSMTP.instances[0].sent[0]
    assert message["Bcc"] is None
    assert "\n" not in message["Subject"]


def test_starttls_and_login_only_when_configured():
    email_channel.send_email("a@example.com", "s", "b", settings(smtp_security="starttls", smtp_username="u", smtp_password="p"))
    assert FakeSMTP.instances[0].calls == ["starttls", ("login", "u")]

    FakeSMTP.instances.clear()
    email_channel.send_email("a@example.com", "s", "b", settings())
    assert FakeSMTP.instances[0].calls == []


def test_smtp_errors_propagate_so_the_consumer_can_retry(monkeypatch):
    class Refusing(FakeSMTP):
        def send_message(self, message):
            raise smtplib.SMTPServerDisconnected("gone")

    monkeypatch.setattr(email_channel.smtplib, "SMTP", Refusing)
    with pytest.raises(smtplib.SMTPServerDisconnected):
        email_channel.send_email("a@example.com", "s", "b", settings())
