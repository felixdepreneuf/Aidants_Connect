import logging
from collections import OrderedDict
from typing import Iterable

from django.conf import settings
from django.contrib import messages as django_messages
from django.contrib.auth.decorators import login_required
from django.db.models.functions import Concat
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.timezone import now, timedelta

from aidants_connect_web.decorators import activity_required
from aidants_connect_web.models import Aidant, Autorisation, Journal, Mandat
from aidants_connect_web.views.service import humanize_demarche_names

logging.basicConfig(level=logging.INFO)
log = logging.getLogger()


def _get_mandats_for_usagers_index(aidant):
    return (
        Mandat.objects.prefetch_related("autorisations")
        .filter(organisation=aidant.organisation)
        .exclude(expiration_date__lt=timezone.now() - timedelta(365))
        .exclude(autorisations__revocation_date__lt=timezone.now() - timedelta(365))
        .annotate(
            for_ordering=Concat("usager__preferred_username", "usager__family_name")
        )
        .order_by("for_ordering", "expiration_date")
    )


def _get_usagers_dict_from_mandats(mandats: Iterable[Mandat]) -> dict:
    """
    :return: A dict containing data about the users from input mandates with attributes:

            with_valid_mandate -> OrderedDict[Usager, list[Tuple[str, bool]]

                dictionnary associating the user with the list of its mandate's
                authorizations. Each item of the list is a tuple of two items: the
                the procedure (see aidants_connect.settings.DEMARCHES) covered by the
                authorization (see aidants_aidants_connect_web.models.Autorisation) and
                a boolean indication if the authorisation is soon to be expired.

            without_valid_mandate -> OrderedDict[Usager, bool]

                dict associating users without an active mandate and the boolean
                indicating if the user has no valid autorisations
                (revoked or no autorisations).

            with_valid_mandate_count -> int

                count of items in ``with_valid_mandate``

            without_valid_mandate_count: int

                count of items in ``without_valid_mandate``

            total: int

                total count of both ``with_valid_mandate`` and ``without_valid_mandate``

        Example:
            $ _get_usagers_dict_from_mandats(mandates)
            {
                "with_valid_mandate": {
                    <Usager: Angela Claire Louise DUBOIS>: [
                        ("papiers", False), ("transports", False)
                    ]
                },
                "without_valid_mandate": {<Usager: Karl MARX>: True},
                "with_valid_mandate_count": 1,
                "without_valid_mandate_count": 1,
                "total"2
            }
    """
    usagers = OrderedDict()
    usagers_with_valid_mandate = OrderedDict()
    usagers_without_valid_mandate = OrderedDict()
    delta = settings.MANDAT_EXPIRED_SOON

    for mandat in mandats:
        if mandat.usager not in usagers:
            usagers[mandat.usager] = {"active_mandats": [], "inactive_mandats": []}

        expired = mandat.expiration_date if mandat.expiration_date < now() else False

        expired_soon = (
            mandat.expiration_date
            if mandat.expiration_date - timedelta(days=delta) < now()
            else False
        )

        autorisations = (
            mandat.autorisations.filter(revocation_date=None).all().order_by("pk")
        )

        has_no_autorisations = autorisations.count() == 0

        if expired or has_no_autorisations:
            usagers[mandat.usager]["inactive_mandats"].append(
                (mandat, has_no_autorisations)
            )

        if not expired and not has_no_autorisations:
            for autorisation in autorisations:
                usagers[mandat.usager]["active_mandats"].append(
                    (autorisation.demarche, expired_soon)
                )

    for usager, mandats in usagers.items():
        if len(mandats["active_mandats"]) > 0:
            usagers_with_valid_mandate[usager] = mandats["active_mandats"]
        if len(mandats["inactive_mandats"]) > 0 and len(mandats["active_mandats"]) == 0:
            usager_without_autorisations = True
            for mandat, has_no_autorisations in mandats["inactive_mandats"]:
                if not has_no_autorisations:
                    usager_without_autorisations = False
            usagers_without_valid_mandate[usager] = usager_without_autorisations

    with_valid_mandate_count = len(usagers_with_valid_mandate)
    without_valid_mandate_count = len(usagers_without_valid_mandate)

    return {
        "with_valid_mandate": usagers_with_valid_mandate,
        "without_valid_mandate": usagers_without_valid_mandate,
        "with_valid_mandate_count": with_valid_mandate_count,
        "without_valid_mandate_count": without_valid_mandate_count,
        "total": with_valid_mandate_count + without_valid_mandate_count,
    }


@login_required
@activity_required
def usagers_index(request):
    aidant = request.user
    mandats = _get_mandats_for_usagers_index(aidant)
    usagers_dict = _get_usagers_dict_from_mandats(mandats)

    return render(
        request,
        "aidants_connect_web/usagers/usagers.html",
        {
            "aidant": aidant,
            "usagers_dict": usagers_dict,
        },
    )


@login_required
@activity_required
def usager_details(request, usager_id):
    aidant = request.user

    usager = aidant.get_usager(usager_id)
    if not usager:
        django_messages.error(request, "Cet usager est introuvable ou inaccessible.")
        return redirect("espace_aidant_home")

    active_mandats = (
        Mandat.objects.prefetch_related("autorisations")
        .filter(organisation=aidant.organisation, usager=usager)
        .active()
    )
    inactive_mandats = (
        Mandat.objects.prefetch_related("autorisations")
        .filter(organisation=aidant.organisation, usager=usager)
        .inactive()
    )

    return render(
        request,
        "aidants_connect_web/usager_details.html",
        {
            "aidant": aidant,
            "usager": usager,
            "active_mandats": active_mandats,
            "inactive_mandats": inactive_mandats,
        },
    )


@login_required
@activity_required
def confirm_autorisation_cancelation(request, usager_id, autorisation_id):
    aidant = request.user
    try:
        autorisation = aidant.get_active_autorisations_for_usager(usager_id).get(
            pk=autorisation_id
        )
    except Autorisation.DoesNotExist:
        django_messages.error(
            request, "Cette autorisation est introuvable ou inaccessible."
        )
        return redirect("espace_aidant_home")

    if request.method == "POST":
        form = request.POST

        if form:
            autorisation.revocation_date = timezone.now()
            autorisation.save(update_fields=["revocation_date"])

            Journal.log_autorisation_cancel(autorisation, aidant)

            return redirect(
                "autorisation_cancelation_success",
                usager_id=usager_id,
                autorisation_id=autorisation_id,
            )

    return render(
        request,
        "aidants_connect_web/mandat_auths_cancellation/"
        "confirm_autorisation_cancelation.html",
        {
            "aidant": aidant,
            "usager": aidant.get_usager(usager_id),
            "autorisation": autorisation,
        },
    )


@login_required
@activity_required
def autorisation_cancelation_success(request, usager_id, autorisation_id):
    aidant: Aidant = request.user

    try:
        authorization = aidant.get_inactive_autorisations_for_usager(usager_id).get(
            pk=autorisation_id
        )
    except Autorisation.DoesNotExist:
        django_messages.error(
            request, "Cette autorisation est introuvable ou inaccessible."
        )
        return redirect("espace_aidant_home")

    if not authorization.is_revoked:
        django_messages.error(request, "Cette autorisation est encore active.")
        return redirect("espace_aidant_home")

    return render(
        request,
        "aidants_connect_web/mandat_auths_cancellation/"
        "authorization_cancellation_success.html",
        {
            "aidant": aidant,
            "humanized_auth": humanize_demarche_names(authorization.demarche),
            "usager": aidant.get_usager(usager_id),
            "authorization": authorization,
        },
    )


@login_required
@activity_required
def autorisation_cancelation_attestation(request, usager_id, autorisation_id):
    aidant: Aidant = request.user
    try:
        autorisation = aidant.get_inactive_autorisations_for_usager(usager_id).get(
            pk=autorisation_id
        )
    except Autorisation.DoesNotExist:
        django_messages.error(
            request, "Cette autorisation est introuvable ou inaccessible."
        )
        return redirect("espace_aidant_home")

    mandat: Mandat = autorisation.mandat

    if not autorisation.is_revoked:
        django_messages.error(request, "Cette autorisation est encore active.")
        return redirect("espace_aidant_home")

    if not autorisation.was_separately_revoked:
        return redirect("mandat_cancellation_attestation", mandat_id=mandat.id)

    user = aidant.get_usager(usager_id)

    return render(
        request,
        "aidants_connect_web/mandat_auths_cancellation/"
        "authorization_cancellation_attestation.html",
        {
            "aidant": aidant,
            "authorization": humanize_demarche_names(autorisation.demarche),
            "user": user,
            "organisation": autorisation.mandat.organisation,
            "creation_date": autorisation.mandat.creation_date.strftime(
                "%d/%m/%Y à %Hh%M"
            ),
            "revocation_date": autorisation.revocation_date.strftime(
                "%d/%m/%Y à %Hh%M"
            ),
        },
    )


@login_required
@activity_required
def confirm_mandat_cancelation(request, mandat_id):
    aidant: Aidant = request.user
    try:
        mandat = Mandat.objects.get(pk=mandat_id, organisation=aidant.organisation)
    except Mandat.DoesNotExist:
        django_messages.error(request, "Ce mandat est introuvable ou inaccessible.")
        return redirect("espace_aidant_home")

    usager = mandat.usager
    remaining_autorisations = []

    if mandat.is_active:
        for autorisation in mandat.autorisations.filter(revocation_date=None):
            remaining_autorisations.append(
                humanize_demarche_names(autorisation.demarche)
            )

        if request.method == "POST":
            if request.POST:
                autorisation_in_mandat = Autorisation.objects.filter(mandat=mandat)
                for autorisation in autorisation_in_mandat:
                    if not autorisation.revocation_date:
                        autorisation.revocation_date = (
                            autorisation.revocation_date
                        ) = timezone.now()
                        autorisation.save(update_fields=["revocation_date"])
                        Journal.log_autorisation_cancel(autorisation, aidant)
                Journal.log_mandat_cancel(mandat, aidant)
                return redirect("mandat_cancelation_success", mandat_id=mandat.id)
            else:
                return render(
                    request,
                    "aidants_connect_web/mandat_auths_cancellation/"
                    "confirm_mandat_cancellation.html",
                    {
                        "aidant": aidant,
                        "usager_name": usager.get_full_name(),
                        "usager_id": usager.id,
                        "mandat": mandat,
                        "remaining_autorisations": remaining_autorisations,
                        "error": "Une erreur s'est produite lors "
                        "de la révocation du mandat",
                    },
                )

    return render(
        request,
        "aidants_connect_web/mandat_auths_cancellation/"
        "confirm_mandat_cancellation.html",
        {
            "aidant": aidant,
            "usager_name": usager.get_full_name(),
            "usager_id": usager.id,
            "mandat": mandat,
            "remaining_autorisations": remaining_autorisations,
        },
    )


@login_required
@activity_required
def mandat_cancelation_success(request, mandat_id: int):
    aidant: Aidant = request.user
    try:
        mandate = Mandat.objects.get(pk=mandat_id, organisation=aidant.organisation)
    except Mandat.DoesNotExist:
        django_messages.error(request, "Ce mandat est introuvable ou inaccessible.")
        return redirect("espace_aidant_home")
    user = mandate.usager
    if mandate.is_active:
        django_messages.error(request, "Ce mandat est toujours actif.")
        return redirect("usager_details", usager_id=user.id)

    return render(
        request,
        "aidants_connect_web/mandat_auths_cancellation/"
        "mandat_cancellation_success.html",
        {
            "aidant": aidant,
            "mandat": mandate,
            "usager": user,
        },
    )


@login_required
@activity_required
def mandat_cancellation_attestation(request, mandat_id):
    organisation = request.user.organisation
    try:
        mandat = Mandat.objects.get(pk=mandat_id, organisation=organisation)
        if not mandat.was_explicitly_revoked:
            return redirect("espace_aidant_home")

    except Mandat.DoesNotExist:
        django_messages.error(request, "Ce mandat est introuvable ou inaccessible.")
        return redirect("espace_aidant_home")
    usager = mandat.usager

    return render(
        request,
        "aidants_connect_web/mandat_auths_cancellation/"
        "mandat_cancellation_attestation.html",
        {
            "organisation": organisation,
            "usager_name": usager.get_full_name(),
            "mandat": mandat,
            "creation_date": mandat.creation_date.strftime("%d/%m/%Y à %Hh%M"),
            "revocation_date": mandat.revocation_date.strftime("%d/%m/%Y à %Hh%M"),
        },
    )
