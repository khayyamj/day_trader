"""Email service for sending notifications via SMTP."""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, Template

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SMTP with retry logic."""

    def __init__(self):
        """Initialize email service with SMTP settings."""
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.email_from = settings.EMAIL_FROM or settings.SMTP_USER
        self.email_to = settings.EMAIL_TO or settings.SMTP_USER

        # Set up Jinja2 template environment
        template_dir = Path(__file__).parent / "templates"
        self.jinja_env = Environment(loader=FileSystemLoader(str(template_dir)))

    def send_email(
        self,
        subject: str,
        html_body: str,
        plain_body: Optional[str] = None,
        to_addresses: Optional[List[str]] = None,
        retry_attempts: int = 3,
        retry_delay: int = 5
    ) -> bool:
        """
        Send an email with HTML and optional plain text content.

        Args:
            subject: Email subject line
            html_body: HTML content of the email
            plain_body: Plain text version (optional, will be stripped from HTML if not provided)
            to_addresses: List of recipient email addresses (defaults to configured EMAIL_TO)
            retry_attempts: Number of retry attempts on failure (default: 3)
            retry_delay: Delay in seconds between retries (default: 5)

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not self.smtp_user or not self.smtp_password:
            logger.error("SMTP credentials not configured")
            return False

        recipients = to_addresses or [self.email_to]
        if not recipients or not any(recipients):
            logger.error("No recipient email addresses configured")
            return False

        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = self.email_from
        message["To"] = ", ".join(recipients)

        # Add plain text part (strip HTML if not provided)
        if plain_body:
            text_part = MIMEText(plain_body, "plain")
            message.attach(text_part)

        # Add HTML part
        html_part = MIMEText(html_body, "html")
        message.attach(html_part)

        # Attempt to send with retries
        import time
        for attempt in range(retry_attempts):
            try:
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                    server.sendmail(self.email_from, recipients, message.as_string())

                logger.info(f"Email sent successfully: {subject} to {recipients}")
                return True

            except smtplib.SMTPAuthenticationError as e:
                logger.error(f"SMTP authentication failed: {e}")
                return False  # Don't retry auth failures

            except smtplib.SMTPException as e:
                logger.warning(f"SMTP error on attempt {attempt + 1}/{retry_attempts}: {e}")
                if attempt < retry_attempts - 1:
                    time.sleep(retry_delay)
                else:
                    logger.error(f"Failed to send email after {retry_attempts} attempts")
                    return False

            except Exception as e:
                logger.error(f"Unexpected error sending email: {e}")
                if attempt < retry_attempts - 1:
                    time.sleep(retry_delay)
                else:
                    return False

        return False

    def render_template(self, template_name: str, context: dict) -> str:
        """
        Render a Jinja2 email template with the given context.

        Args:
            template_name: Name of the template file (e.g., "trade_execution.html")
            context: Dictionary of variables to pass to the template

        Returns:
            str: Rendered HTML string
        """
        try:
            template = self.jinja_env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            logger.error(f"Error rendering template {template_name}: {e}")
            raise


# Global email service instance
email_service = EmailService()
