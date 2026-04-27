import logging
import smtplib
from typing import Any
from email.message import EmailMessage
from email.utils import make_msgid
from flask import current_app

logger = logging.getLogger(__name__)


class MailService:
    """Versendet transaktionale Mails via SMTP (best effort)."""

    @staticmethod
    def send(
        to: str | list[str],
        subject: str,
        html: str,
        text: str | None = None,
        tags: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Sendet eine Mail und gibt ein strukturiertes Resultat zurück."""
        to_recipients = [to] if isinstance(to, str) else to
        smtp_host = current_app.config.get('MAIL_SMTP_HOST')
        smtp_port = current_app.config.get('MAIL_SMTP_PORT', 587)
        smtp_username = current_app.config.get('MAIL_SMTP_USERNAME')
        smtp_password = current_app.config.get('MAIL_SMTP_PASSWORD')
        use_tls = current_app.config.get('MAIL_SMTP_USE_TLS', True)
        from_email = current_app.config.get('MAIL_FROM_ADDRESS', 'kontakt@gourmen.ch')
        reply_to = current_app.config.get('MAIL_REPLY_TO', from_email)

        if not to_recipients:
            return {'success': False, 'message_id': None, 'error': 'no_recipient'}

        if not smtp_host:
            logger.warning(
                "SMTP-Host fehlt. Mailversand wird uebersprungen. to=%s subject=%s",
                to_recipients,
                subject,
            )
            return {'success': True, 'message_id': None, 'error': 'smtp_host_missing'}

        if not smtp_username or not smtp_password:
            logger.warning(
                "SMTP-Zugang fehlt. Test-Modus aktiv, Mail wird nur geloggt. "
                "to=%s subject=%s",
                to_recipients,
                subject,
            )
            return {'success': True, 'message_id': None, 'error': None}

        try:
            message = EmailMessage()
            message['From'] = from_email
            message['To'] = ', '.join(to_recipients)
            message['Subject'] = subject
            message['Reply-To'] = reply_to
            message['Message-ID'] = make_msgid(domain=from_email.split('@')[-1])
            if tags:
                for key, value in tags.items():
                    message[f'X-Gourmen-Tag-{key}'] = str(value)

            message.set_content(text or 'Diese E-Mail enthaelt eine HTML-Version.')
            message.add_alternative(html, subtype='html')

            with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
                if use_tls:
                    server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(message)

            message_id = message['Message-ID']

            logger.info("Mail erfolgreich versendet: message_id=%s to=%s", message_id, to_recipients)
            return {'success': True, 'message_id': message_id, 'error': None}
        except Exception as exc:
            logger.error("Mail-Versand fehlgeschlagen: %s", exc, exc_info=True)
            return {'success': False, 'message_id': None, 'error': str(exc)}
