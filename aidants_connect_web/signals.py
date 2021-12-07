from django.contrib.auth.signals import user_logged_in
from django.core.mail import send_mail
from django.dispatch import receiver
from django.conf import settings
from django.template import loader

from django_otp.plugins.otp_totp.models import TOTPDevice

from aidants_connect_web.models import Aidant, Journal, aidants__organisations_changed


@receiver(user_logged_in)
def log_connection_on_login(sender, user: Aidant, request, **kwargs):
    Journal.log_connection(user)


@receiver(user_logged_in)
def lower_totp_tolerance_on_login(sender, user: Aidant, request, **kwargs):
    if not settings.LOWER_TOTP_TOLERANCE_ON_LOGIN:
        return

    for device in TOTPDevice.objects.filter(
        user=user, tolerance__gte=2, confirmed=True
    ):
        device.tolerance = 1
        device.save()


@receiver(aidants__organisations_changed)
def send_mail_aidant__organisations_changed(instance: Aidant, diff: dict, **_):
    context = {"aidant": instance, **diff}
    text_message = loader.render_to_string(
        "signals/aidant__organisations_changed.txt", context
    )
    html_message = loader.render_to_string(
        "signals/aidant__organisations_changed.html", context
    )

    send_mail(
        from_email=settings.AIDANTS__ORGANISATIONS_CHANGED_EMAIL_FROM,
        recipient_list=[instance.email],
        subject=settings.AIDANTS__ORGANISATIONS_CHANGED_EMAIL_SUBJECT,
        message=text_message,
        html_message=html_message,
    )
