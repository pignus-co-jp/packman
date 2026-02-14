import ssl
import smtplib
from email.message import EmailMessage


def send_email(
        host: str,
        username: str,
        password: str,
        msg: EmailMessage,
        port: int = 465,
        context: ssl.SSLContext = ssl.create_default_context()
):
    try:
        with smtplib.SMTP_SSL(host=host, port=port, context=context, timeout=60) as smtp:
            smtp.login(user=username, password=password)
            smtp.send_message(msg)
    except Exception as ex:
        print(ex)
        return False
    return True
