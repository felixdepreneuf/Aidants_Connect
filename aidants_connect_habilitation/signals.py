from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.http import HttpRequest
from django.template import loader
from django.urls import reverse

from aidants_connect_habilitation.models import (
    IssuerEmailConfirmation,
    OrganisationRequest,
    email_confirmation_sent,
)


@receiver(email_confirmation_sent, sender=IssuerEmailConfirmation)
def send_email_confirmation(
    request: HttpRequest, confirmation: IssuerEmailConfirmation, **_
):
    confirmation_link = reverse(
        "habilitation_issuer_email_confirmation_confirm",
        kwargs={"issuer_id": confirmation.issuer.issuer_id, "key": confirmation.key},
    )
    confirmation_link = request.build_absolute_uri(confirmation_link)

    context = {"confirmation_link": confirmation_link}
    text_message = loader.render_to_string("signals/email_confirmation.txt", context)
    html_message = loader.render_to_string("signals/email_confirmation.html", context)

    send_mail(
        from_email=settings.EMAIL_CONFIRMATION_EXPIRE_DAYS_EMAIL_FROM,
        recipient_list=[confirmation.issuer.email],
        subject=settings.EMAIL_CONFIRMATION_EXPIRE_DAYS_EMAIL_SUBJECT,
        message=text_message,
        html_message=html_message,
    )


@receiver(post_save, sender=OrganisationRequest)
def notify_issuer_request_submitted(instance: OrganisationRequest, created: bool, **_):
    if not created:
        return

    context = {
        "url": f"https://{settings.HOST}{instance.get_absolute_url()}",
        "organisation": instance,
    }
    text_message = loader.render_to_string(
        "email/organisation_request_cration.txt", context
    )
    html_message = loader.render_to_string(
        "email/organisation_request_cration.html", context
    )

    send_mail(
        from_email=settings.EMAIL_ORGANISATION_REQUEST_CRATION_FROM,
        recipient_list=[instance.issuer.email],
        subject=settings.EMAIL_ORGANISATION_REQUEST_CRATION_SUBJECT,
        message=text_message,
        html_message=html_message,
    )
