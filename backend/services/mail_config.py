from fastapi_mail import ConnectionConfig
import os

conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME", "your_gmail@gmail.com"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", "your_app_password"),
    MAIL_FROM=os.getenv("MAIL_FROM", "your_gmail@gmail.com"),
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)
