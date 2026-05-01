import logging
import smtplib
import socket
import threading
from typing import Any
from email.message import EmailMessage
from email.utils import make_msgid

import requests
from flask import current_app

logger = logging.getLogger(__name__)


class _SMTPIPv4FallbackMixin:
    """Fallback to IPv4 when default socket path is unreachable."""

    max_ipv4_attempts = 1

    def _get_socket(self, host, port, timeout):
        try:
            return super()._get_socket(host, port, timeout)
        except OSError as exc:
            # Railway setups with disabled IPv6 egress can fail with Errno 101.
            if getattr(exc, "errno", None) != 101:
                raise

            ipv4_infos = socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM)
            if not ipv4_infos:
                raise

            last_error = exc
            for _, _, _, _, sockaddr in ipv4_infos[: self.max_ipv4_attempts]:
                try:
                    return socket.create_connection(sockaddr, timeout)
                except OSError as ipv4_exc:
                    last_error = ipv4_exc
            raise last_error


class _SMTPPreferIPv4(_SMTPIPv4FallbackMixin, smtplib.SMTP):
    """SMTP client with IPv4 fallback."""


class _SMTPSSLPreferIPv4(_SMTPIPv4FallbackMixin, smtplib.SMTP_SSL):
    """SMTP_SSL client with IPv4 fallback."""


class MailService:
    """Versendet transaktionale Mails via Resend (HTTPS) oder SMTP (best effort)."""

    _RESEND_API_URL = 'https://api.resend.com/emails'

    @staticmethod
    def _send_resend(
        to_recipients: list[str],
        subject: str,
        html: str,
        text: str | None,
        from_email: str,
        reply_to: str,
        tags: dict[str, str] | None,
        api_key: str,
        timeout: int,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            'from': from_email,
            'to': to_recipients,
            'subject': subject,
            'html': html,
            'text': text or 'Diese E-Mail enthaelt eine HTML-Version.',
            'reply_to': reply_to,
        }
        if tags:
            payload['headers'] = {
                f'X-Gourmen-Tag-{key}': str(value) for key, value in tags.items()
            }

        try:
            response = requests.post(
                MailService._RESEND_API_URL,
                json=payload,
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json',
                },
                timeout=timeout,
            )
            if response.ok:
                data = response.json() if response.content else {}
                resend_id = data.get('id')
                message_id = f'resend:{resend_id}' if resend_id else None
                logger.info(
                    "Mail erfolgreich versendet (Resend): id=%s to=%s",
                    resend_id,
                    to_recipients,
                )
                return {'success': True, 'message_id': message_id, 'error': None}

            err_body = response.text[:500] if response.text else ''
            try:
                err_json = response.json()
                detail = err_json.get('message') or err_body
            except ValueError:
                detail = err_body or str(response.status_code)
            logger.error(
                "Resend-Mail fehlgeschlagen: status=%s body=%s",
                response.status_code,
                err_body,
            )
            return {
                'success': False,
                'message_id': None,
                'error': f"resend: {detail}"[:400],
            }
        except requests.RequestException as exc:
            logger.error("Resend-Mail fehlgeschlagen: %s", exc, exc_info=True)
            return {'success': False, 'message_id': None, 'error': str(exc)}

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
        from_email = current_app.config.get('MAIL_FROM_ADDRESS', 'kontakt@gourmen.ch')
        reply_to = current_app.config.get('MAIL_REPLY_TO', from_email)
        resend_key = current_app.config.get('RESEND_API_KEY')
        http_timeout = int(current_app.config.get('MAIL_HTTP_TIMEOUT_SECONDS', 15))

        if not to_recipients:
            return {'success': False, 'message_id': None, 'error': 'no_recipient'}

        if resend_key:
            return MailService._send_resend(
                to_recipients=to_recipients,
                subject=subject,
                html=html,
                text=text,
                from_email=from_email,
                reply_to=reply_to,
                tags=tags,
                api_key=resend_key,
                timeout=http_timeout,
            )

        smtp_host = current_app.config.get('MAIL_SMTP_HOST')
        smtp_port = current_app.config.get('MAIL_SMTP_PORT', 587)
        smtp_username = current_app.config.get('MAIL_SMTP_USERNAME')
        smtp_password = current_app.config.get('MAIL_SMTP_PASSWORD')
        use_tls = current_app.config.get('MAIL_SMTP_USE_TLS', True)
        use_ssl = current_app.config.get('MAIL_SMTP_USE_SSL', False)
        smtp_timeout = int(current_app.config.get('MAIL_SMTP_TIMEOUT_SECONDS', 3))
        max_ipv4_attempts = int(current_app.config.get('MAIL_SMTP_MAX_IPV4_ATTEMPTS', 1))

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

            smtp_client_cls = _SMTPSSLPreferIPv4 if use_ssl else _SMTPPreferIPv4
            smtp_client_cls.max_ipv4_attempts = max(1, max_ipv4_attempts)

            with smtp_client_cls(smtp_host, smtp_port, timeout=smtp_timeout) as server:
                if use_tls and not use_ssl:
                    server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(message)

            message_id = message['Message-ID']

            logger.info("Mail erfolgreich versendet: message_id=%s to=%s", message_id, to_recipients)
            return {'success': True, 'message_id': message_id, 'error': None}
        except Exception as exc:
            logger.error("Mail-Versand fehlgeschlagen: %s", exc, exc_info=True)
            return {'success': False, 'message_id': None, 'error': str(exc)}

    @staticmethod
    def send_async(
        to: str | list[str],
        subject: str,
        html: str,
        text: str | None = None,
        tags: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Dispatch mail in background so request latency stays low."""
        app = current_app._get_current_object()

        def _worker():
            with app.app_context():
                result = MailService.send(
                    to=to,
                    subject=subject,
                    html=html,
                    text=text,
                    tags=tags,
                )
                if not result.get('success'):
                    logger.warning(
                        "Async-Mail fehlgeschlagen: to=%s subject=%s error=%s",
                        to,
                        subject,
                        result.get('error'),
                    )

        threading.Thread(target=_worker, daemon=True).start()
        return {'success': True, 'message_id': None, 'error': None, 'queued': True}
