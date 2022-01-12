from django.contrib.admin import ModelAdmin
from django.conf import settings

from aidants_connect.admin import admin_site, VisibleToAdminMetier
from aidants_connect_habilitation.models import Issuer, OrganisationRequest


class IssuerAdmin(VisibleToAdminMetier, ModelAdmin):
    list_display = (
        "email",
        "last_name",
        "first_name",
        "phone",
        "id",
    )


class OrganisationRequestAdmin(VisibleToAdminMetier, ModelAdmin):
    raw_id_fields = ("issuer",)


if settings.AC_HABILITATION_FORM_ENABLED:
    admin_site.register(Issuer, IssuerAdmin)
    admin_site.register(OrganisationRequest, OrganisationRequestAdmin)
