"""Ephemeral SMTP delivery for validated contact requests."""

from __future__ import annotations

import smtplib
import ssl
from email.message import EmailMessage
from typing import Any


class MailConfigurationError(RuntimeError):
    pass


def send_contact(config: dict[str, Any], name: str, email: str, subject: str, message: str) -> None:
    required = ("SMTP_HOST", "CONTACT_RECIPIENT", "CONTACT_SENDER")
    missing = [key for key in required if not config.get(key)]
    if missing:
        raise MailConfigurationError("contact delivery is not configured")
    outgoing = EmailMessage()
    outgoing["Subject"] = f"Project Simulation: {subject}"
    outgoing["From"] = config["CONTACT_SENDER"]
    outgoing["To"] = config["CONTACT_RECIPIENT"]
    outgoing["Reply-To"] = email
    outgoing.set_content(f"From: {name}\n\n{message}")
    with smtplib.SMTP(config["SMTP_HOST"], int(config["SMTP_PORT"]), timeout=8) as server:
        if config.get("SMTP_USE_TLS"):
            server.starttls(context=ssl.create_default_context())
        if config.get("SMTP_USERNAME"):
            server.login(config["SMTP_USERNAME"], config.get("SMTP_PASSWORD", ""))
        server.send_message(outgoing)
