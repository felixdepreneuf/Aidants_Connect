from django.urls import path

from magicauth import views as magicauth_views
from magicauth.urls import urlpatterns as magicauth_urls

from aidants_connect_web.views import (
    FC_as_FS,
    id_provider,
    mandat,
    service,
    espace_aidant,
    espace_responsable,
    usagers,
    datapass,
)

urlpatterns = [
    # service
    path("accounts/login/", magicauth_views.LoginView.as_view(), name="login"),
    path("logout-session/", service.logout_page, name="logout"),
    path("activity_check/", service.activity_check, name="activity_check"),
    # espace aidant : home, organisation
    path("espace-aidant/", espace_aidant.home, name="espace_aidant_home"),
    path(
        "espace-aidant/organisation/",
        espace_aidant.organisation,
        name="espace_aidant_organisation",
    ),
    # usagers
    path("usagers/", usagers.usagers_index, name="usagers"),
    path("usagers/<int:usager_id>/", usagers.usager_details, name="usager_details"),
    path(
        "usagers/<int:usager_id>/autorisations/<int:autorisation_id>/cancel_confirm",
        usagers.confirm_autorisation_cancelation,
        name="confirm_autorisation_cancelation",
    ),
    path(
        "mandats/<int:mandat_id>/cancel_confirm",
        usagers.confirm_mandat_cancelation,
        name="confirm_mandat_cancelation",
    ),
    path(
        "mandats/<int:mandat_id>/visualisation",
        mandat.attestation_visualisation,
        name="mandat_visualisation",
    ),
    # new mandat
    path("creation_mandat/", mandat.new_mandat, name="new_mandat"),
    path(
        "creation_mandat/recapitulatif/",
        mandat.new_mandat_recap,
        name="new_mandat_recap",
    ),
    path("logout-callback/", mandat.new_mandat_recap, name="new_mandat_recap"),
    path(
        "creation_mandat/visualisation/projet/",
        mandat.attestation_projet,
        name="new_attestation_projet",
    ),
    path(
        "creation_mandat/succes/",
        mandat.new_mandat_success,
        name="new_mandat_success",
    ),
    path(
        "creation_mandat/visualisation/final/",
        mandat.attestation_final,
        name="new_attestation_final",
    ),
    path(
        "creation_mandat/qrcode/",
        mandat.attestation_qrcode,
        name="new_attestation_qrcode",
    ),
    # id_provider
    path("authorize/", id_provider.authorize, name="authorize"),
    path("token/", id_provider.token, name="token"),
    path("userinfo/", id_provider.user_info, name="user_info"),
    path("select_demarche/", id_provider.fi_select_demarche, name="fi_select_demarche"),
    path(
        "logout/",
        id_provider.end_session_endpoint,
        name="end_session_endpoint",
    ),
    # Espace responsable structure
    path(
        "espace-responsable/", espace_responsable.home, name="espace_responsable_home"
    ),
    # FC_as_FS
    path("fc_authorize/", FC_as_FS.fc_authorize, name="fc_authorize"),
    path("callback/", FC_as_FS.fc_callback, name="fc_callback"),
    # public_website
    path("", service.home_page, name="home_page"),
    path("stats/", service.statistiques, name="statistiques"),
    path("cgu/", service.cgu, name="cgu"),
    path("mentions-legales/", service.mentions_legales, name="mentions_legales"),
    path("guide_utilisation/", service.guide_utilisation, name="guide_utilisation"),
    path("habilitation", service.habilitation, name="habilitation"),
    path("ressources/", service.ressources, name="ressources"),
    path("accessibilite/", service.accessibilite, name="accessibilite"),
    # # FAQ
    path("faq/", service.faq_generale, name="faq_generale"),
    path("faq/mandat/", service.faq_mandat, name="faq_mandat"),
    path(
        "faq/donnees-personnelles/",
        service.faq_donnees_personnelles,
        name="faq_donnees_personnelles",
    ),
    path(
        "faq/habilitation/",
        service.faq_habilitation,
        name="faq_habilitation",
    ),
    # # Datapass
    path("datapass_receiver/", datapass.receiver, name="datapass_receiver"),
]

urlpatterns.extend(magicauth_urls)
