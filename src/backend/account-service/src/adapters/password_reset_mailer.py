import smtplib
from email.message import EmailMessage

from src.config.settings import settings


class PasswordResetDeliveryError(Exception):
    pass


class PasswordResetMailer:
    def send(self, *, email: str, reset_token: str) -> None:
        if (
            not settings.smtp_host
            or not settings.smtp_from
            or not settings.password_reset_url
        ):
            raise PasswordResetDeliveryError(
                "Password reset delivery is not configured"
            )

        message = EmailMessage()
        message["From"] = settings.smtp_from
        message["To"] = email
        message["Subject"] = "Reset your Briefly password"
        message.set_content(
            f"Reset your password: "
            f"{settings.password_reset_url}?token={reset_token}"
        )

        try:
            with smtplib.SMTP(
                settings.smtp_host, settings.smtp_port
            ) as smtp:
                if settings.smtp_use_tls:
                    smtp.starttls()
                if settings.smtp_username:
                    if not settings.smtp_password:
                        raise PasswordResetDeliveryError(
                            "SMTP password is not configured"
                        )
                    smtp.login(
                        settings.smtp_username, settings.smtp_password
                    )
                smtp.send_message(message)
        except (OSError, smtplib.SMTPException) as exc:
            raise PasswordResetDeliveryError(
                "Password reset delivery failed"
            ) from exc
