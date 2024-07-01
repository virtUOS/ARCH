from django.conf import settings
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives
import logging

file_logger = logging.getLogger('ARCH_file_logger')


def send_email(
        to_email,
        subject,
        html_message,
        from_email=settings.DEFAULT_FROM_EMAIL, ) -> bool:
    """
    Sends an email to a user and returns True if successful, False otherwise.
    """

    try:
        subject = subject
        html_message = html_message
        plain_message = strip_tags(html_message)
        from_email = from_email
        to_email = to_email

        email = EmailMultiAlternatives(subject, plain_message, from_email, [to_email])
        email.attach_alternative(html_message, "text/html")
        email.send()
        return True
    except Exception as e:
        file_logger.error(e)
        return False
