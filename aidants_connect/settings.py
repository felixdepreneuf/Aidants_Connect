"""
Django settings for aidants_connect project.

Generated by 'django-admin startproject' using Django 2.2.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import logging
import os
import re
import sys
from datetime import datetime, timedelta
from distutils.util import strtobool
from typing import Optional, Union

import sentry_sdk
from dotenv import load_dotenv
from sentry_sdk.integrations.django import DjangoIntegration

from aidants_connect.postgres_url import turn_psql_url_into_param

load_dotenv(verbose=True)


def getenv_bool(key: str, default: Optional[bool] = None) -> bool:
    """Obtains a boolean value from an environement variable

    Authorized values are casing variants of "true", "yes", "false" and "no" as well as
    0 and 1. Any other valuer will result in an error unless a default value
    is provided.

    If the environment variable does not exist and no default value is provided,
    an error will be thrown

    :param key: The name the the environment variable to load
    :param default: The default value to take if env var does not exist
    """
    var = os.getenv(key, default)

    if var is None:
        raise ValueError(
            f"{key} is not present in environment variables "
            "and no default value was provided"
        )

    if isinstance(var, bool):
        return var

    try:
        return bool(strtobool(var))
    except ValueError:
        if default is not None:
            return default
        else:
            raise ValueError(
                f"{key} does not have a valid boolean value; authorized values are "
                'any casing of ["true", "yes", "false", "no"] as well as 0 and 1.'
            )


HOST = os.environ["HOST"]
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# FC as FI
FC_AS_FI_CALLBACK_URL = os.environ["FC_AS_FI_CALLBACK_URL"]
FC_AS_FI_ID = os.environ["FC_AS_FI_ID"]
HASH_FC_AS_FI_SECRET = os.environ["HASH_FC_AS_FI_SECRET"]
FC_AS_FI_HASH_SALT = os.environ["FC_AS_FI_HASH_SALT"]
FC_AS_FI_LOGOUT_REDIRECT_URI = os.environ["FC_AS_FI_LOGOUT_REDIRECT_URI"]

# FC as FS
FC_AS_FS_BASE_URL = os.environ["FC_AS_FS_BASE_URL"]
FC_AS_FS_ID = os.environ["FC_AS_FS_ID"]
FC_AS_FS_SECRET = os.environ["FC_AS_FS_SECRET"]
FC_AS_FS_CALLBACK_URL = os.environ["FC_AS_FS_CALLBACK_URL"]

FC_CONNECTION_AGE = int(os.environ["FC_CONNECTION_AGE"])

if os.environ.get("FC_AS_FS_TEST_PORT"):
    FC_AS_FS_TEST_PORT = int(os.environ["FC_AS_FS_TEST_PORT"])
else:
    FC_AS_FS_TEST_PORT = 0

GET_PREFERRED_USERNAME_FROM_FC = getenv_bool("GET_PREFERRED_USERNAME_FROM_FC", True)

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("APP_SECRET")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = getenv_bool("DEBUG", False)

# We support a comma-separated list of allowed hosts.
ENV_SEPARATOR = ","
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost").split(ENV_SEPARATOR)

# Init Sentry if the DSN is defined
SENTRY_DSN = os.getenv("SENTRY_DSN", None)

if SENTRY_DSN:
    SENTRY_ENV = os.getenv("SENTRY_ENV", "unknown")
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        environment=SENTRY_ENV,
    )

# Application definition

INSTALLED_APPS = [
    "aidants_connect_overrides",
    "django.contrib.admin",
    "nested_admin",
    "tabbed_admin",
    "magicauth",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "admin_honeypot",
    "django_otp",
    "django_otp.plugins.otp_static",
    "django_otp.plugins.otp_totp",
    "django_celery_beat",
    "django_extensions",
    "import_export",
    "phonenumber_field",
    "aidants_connect",
    "aidants_connect_web",
    "aidants_connect_habilitation",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.contrib.sites.middleware.CurrentSiteMiddleware",
    "django_referrer_policy.middleware.ReferrerPolicyMiddleware",
    "csp.middleware.CSPMiddleware",
    "django_otp.middleware.OTPMiddleware",
]

# Add debug toolbar
if DEBUG and "test" not in sys.argv:
    INSTALLED_APPS.append("debug_toolbar")
    MIDDLEWARE.append("debug_toolbar.middleware.DebugToolbarMiddleware")
    INTERNAL_IPS = ["127.0.0.1"] + ALLOWED_HOSTS

ROOT_URLCONF = "aidants_connect.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "aidants_connect.common.context_processors.settings_variables",
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

WSGI_APPLICATION = "aidants_connect.wsgi.application"

# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

postgres_url = os.getenv("POSTGRESQL_URL")
if postgres_url:
    environment_info = turn_psql_url_into_param(postgres_url)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": environment_info.get("db_name"),
            "USER": environment_info.get("db_user"),
            "PASSWORD": environment_info.get("db_password"),
            "HOST": environment_info.get("db_host"),
            "PORT": environment_info.get("db_port"),
        }
    }

    ssl_option = environment_info.get("sslmode")

else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DATABASE_NAME"),
            "USER": os.getenv("DATABASE_USER"),
            "PASSWORD": os.getenv("DATABASE_PASSWORD"),
            "HOST": os.getenv("DATABASE_HOST"),
            "PORT": os.getenv("DATABASE_PORT"),
        }
    }

    ssl_option = os.getenv("DATABASE_SSL")

if ssl_option:
    DATABASES["default"]["OPTIONS"] = {"sslmode": ssl_option}

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = "fr"

TIME_ZONE = "Europe/Paris"

USE_I18N = True

USE_L10N = True

USE_TZ = True

LOCALE_PATHS = [os.path.join(BASE_DIR, "locale")]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_ROOT = "staticfiles"
STATIC_URL = "/static/"
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "aidants_connect/common/static"),
]

LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "home_page"
ACTIVITY_CHECK_URL = "activity_check"
ACTIVITY_CHECK_THRESHOLD = int(os.getenv("ACTIVITY_CHECK_THRESHOLD"))
ACTIVITY_CHECK_DURATION = timedelta(minutes=ACTIVITY_CHECK_THRESHOLD)

AUTH_USER_MODEL = "aidants_connect_web.Aidant"

DEMARCHES = {
    "papiers": {
        "titre": "Papiers - Citoyenneté",
        "titre_court": "Papiers",
        "description": "État-civil, Passeport, Élections, Papiers à conserver, Carte d'identité…",
        "service_exemples": ["ANTS", "Défenseur des droits"],
        "icon": "/static/images/icons/papiers.svg",
    },
    "famille": {
        "titre": "Famille",
        "titre_court": "Famille",
        "description": "Allocations familiales, Naissance, Mariage, Pacs, Scolarité…",
        "service_exemples": ["CAF", "ameli.fr", "EduConnect"],
        "icon": "/static/images/icons/famille.svg",
    },
    "social": {
        "titre": "Social - Santé",
        "titre_court": "Social",
        "description": "Carte vitale, Chômage, Handicap, RSA, Personnes âgées…",
        "service_exemples": ["ameli.fr", "MSA", "RSI"],
        "icon": "/static/images/icons/social.svg",
    },
    "travail": {
        "titre": "Travail",
        "titre_court": "Travail",
        "description": "CDD, Concours, Retraite, Démission, Période d'essai…",
        "service_exemples": ["Pôle emploi", "Mon compte formation", "info-retraite.fr"],
        "icon": "/static/images/icons/travail.svg",
    },
    "logement": {
        "titre": "Logement",
        "titre_court": "Logement",
        "description": "Allocations logement, Permis de construire, Logement social, Fin de bail…",
        "service_exemples": ["CAF", "Enedis"],
        "icon": "/static/images/icons/logement.svg",
    },
    "transports": {
        "titre": "Transports",
        "titre_court": "Transports",
        "description": "Carte grise, Permis de conduire, Contrôle technique, Infractions…",
        "service_exemples": ["ANTS", "ANTAI", "Crit'air"],
        "icon": "/static/images/icons/transports.svg",
    },
    "argent": {
        "titre": "Argent",
        "titre_court": "Argent",
        "description": "Crédit immobilier, Impôts, Consommation, Livret A, Assurance, "
        "Surendettement…",
        "service_exemples": ["Impots.gouv", "Timbres fiscaux", "Banque"],
        "icon": "/static/images/icons/argent.svg",
    },
    "justice": {
        "titre": "Justice",
        "titre_court": "Justice",
        "description": "Casier judiciaire, Plainte, Aide juridictionnelle, Saisie…",
        "service_exemples": ["Télérecours citoyens"],
        "icon": "/static/images/icons/justice.svg",
    },
    "etranger": {
        "titre": "Étranger",
        "titre_court": "Étranger",
        "description": "Titres de séjour, Attestation d’accueil, Regroupement familial…",
        "service_exemples": ["OFPRA"],
        "icon": "/static/images/icons/etranger.svg",
    },
    "loisirs": {
        "titre": "Loisirs",
        "titre_court": "Loisirs",
        "description": "Animaux, Permis bateau, Tourisme, Permis de chasser…",
        "service_exemples": ["Ariane"],
        "icon": "/static/images/icons/loisirs.svg",
    },
}

# CGU
CGU_CURRENT_VERSION = "0.2"

MANDAT_TEMPLATE_DIR = "aidants_connect_web/mandat_templates"
MANDAT_TEMPLATE_CURRENT_FILE = "20210308_mandat.html"
MANDAT_TEMPLATE_PATH = os.path.join(MANDAT_TEMPLATE_DIR, MANDAT_TEMPLATE_CURRENT_FILE)
ATTESTATION_SALT = os.getenv("ATTESTATION_SALT", "")

# Magic Auth
MAGICAUTH_EMAIL_FIELD = "email"
MAGICAUTH_FROM_EMAIL = os.getenv("MAGICAUTH_FROM_EMAIL")
MAGICAUTH_LOGGED_IN_REDIRECT_URL_NAME = "espace_aidant_home"
MAGICAUTH_LOGIN_VIEW_TEMPLATE = "login/login.html"
MAGICAUTH_EMAIL_SENT_VIEW_TEMPLATE = "login/email_sent.html"
MAGICAUTH_EMAIL_HTML_TEMPLATE = "login/email_template.html"
MAGICAUTH_EMAIL_TEXT_TEMPLATE = "login/email_template.txt"
MAGICAUTH_WAIT_VIEW_TEMPLATE = "login/wait.html"
MAGICAUTH_ENABLE_2FA = True

# https://github.com/betagouv/django-magicauth/blob/8a8143388bb15fad2823528201e22a31817da243/magicauth/settings.py#L54  # noqa
MAGICAUTH_TOKEN_DURATION_SECONDS = int(
    os.getenv("MAGICAUTH_TOKEN_DURATION_SECONDS", 5 * 60)
)

# TOTP
OTP_TOTP_ISSUER = os.getenv("OTP_TOTP_ISSUER", "Aidants Connect")
LOWER_TOTP_TOLERANCE_ON_LOGIN = getenv_bool("LOWER_TOTP_TOLERANCE_ON_LOGIN", True)

# Emails
EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend"
)

## if file based email backend is used (debug)
EMAIL_FILE_PATH = os.path.dirname(os.path.abspath(__file__)) + "/tmp_email_as_file"
## if smtp backend is used
EMAIL_HOST = os.getenv("EMAIL_HOST", None)
EMAIL_PORT = os.getenv("EMAIL_PORT", None)
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", None)
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", None)
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", None)
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", None)

## if email backend is aidants_connect_web.mail.ForceSpecificSenderBackend
EMAIL_EXTRA_HEADERS = os.getenv("EMAIL_EXTRA_HEADERS", None)
EMAIL_SENDER = os.getenv("EMAIL_SENDER", os.getenv("ADMIN_EMAIL"))

## Emails from the server
SERVER_EMAIL = os.getenv("SERVER_EMAIL", os.getenv("ADMIN_EMAIL"))
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", SERVER_EMAIL)
ADMIN_HONEYPOT_EMAIL_ADMINS = os.getenv("ADMIN_HONEYPOT_EMAIL_ADMINS", SERVER_EMAIL)

# Security headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
REFERRER_POLICY = "strict-origin"

STIMULUS_JS_URL = "https://unpkg.com/stimulus@2.0.0/dist/stimulus.umd.js"

# Content security policy
CSP_DEFAULT_SRC = ("'self'",)
CSP_CONNECT_SRC = ("'self'",)
CSP_IMG_SRC = (
    "'self'",
    "https://www.service-public.fr/resources/v-5cf79a7acf/web/css/img/png/",
)
CSP_SCRIPT_SRC = (
    "'self'",
    STIMULUS_JS_URL,
    "'sha256-FUfFEwUd+ObSebyGDfkxyV7KwtyvBBwsE/VxIOfPD68='",  # tabbed_admin
    "'sha256-p0nVvBQQOY8PrKj8/JWPCKOJU8Iso8I6LIVer817o64='",  # main.html
    "'sha256-ARvyo8AJ91wUvPfVqP2FfHuIHZJN3xaLI7Vgj2tQx18='",  # wait.html
    "'sha256-mXH/smf1qtriC8hr62Qt2dvp/StB/Ixr4xmBRvkCz0U='",  # main-habilitation.html
    "https://cdn.jsdelivr.net/npm/chart.js@3.7.1/dist/chart.min.js",
    "'sha256-oOHki3o/lOkQD0J+jC75068TFqQoV40dYK6wrkIXI1c='",  # statistiques.html
    "https://cdnjs.cloudflare.com/ajax/libs/chartjs-plugin-datalabels/2.0.0/chartjs-plugin-datalabels.min.js",
)

CSP_STYLE_SRC = ("'self'",)
CSP_OBJECT_SRC = ("'none'",)
CSP_FRAME_SRC = (
    "https://www.youtube.com/embed/hATrqHG4zYQ",
    "https://www.youtube.com/embed/WTHj_kQXnzs",
    "https://www.youtube.com/embed/ihsm-36I-fE",
)

# Admin Page settings
ADMIN_URL = os.getenv("ADMIN_URL")
ADMINS = [(os.getenv("ADMIN_NAME"), os.getenv("ADMIN_EMAIL"))]

# Sessions
SESSION_COOKIE_AGE = int(
    os.getenv("SESSION_COOKIE_AGE", 86400)
)  # default: 24 hours, in seconds
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# Cookie security
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = getenv_bool("SESSION_COOKIE_SECURE", True)
CSRF_COOKIE_SECURE = getenv_bool("CSRF_COOKIE_SECURE", True)

# SSL security
SECURE_SSL_REDIRECT = getenv_bool("SECURE_SSL_REDIRECT", True)
SECURE_HSTS_SECONDS = os.getenv("SECURE_HSTS_SECONDS")

# django_OTP_throttling
OTP_TOTP_THROTTLE_FACTOR = int(os.getenv("OTP_TOTP_THROTTLE_FACTOR", 1))

# Functional tests behaviour
HEADLESS_FUNCTIONAL_TESTS = getenv_bool("HEADLESS_FUNCTIONAL_TESTS", True)

# Disable logging in tests
if "test" in sys.argv:
    logging.disable(logging.CRITICAL)
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": True,
        "handlers": {
            "file": {
                "level": "DEBUG",
                "class": "logging.NullHandler",
            },
        },
    }

BYPASS_FIRST_LIVESERVER_CONNECTION = getenv_bool(
    "BYPASS_FIRST_LIVESERVER_CONNECTION", False
)

# Celery settings
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
JSON_CONTENT_TYPE = "application/json"
JSON_SERIALIZER = "json"

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_RESULT_SERIALIZER = JSON_SERIALIZER
CELERY_TASK_SERIALIZER = JSON_SERIALIZER
CELERY_ACCEPT_CONTENT = [JSON_CONTENT_TYPE]

# COVID-19 changes
ETAT_URGENCE_2020_LAST_DAY = datetime.strptime(
    os.getenv("ETAT_URGENCE_2020_LAST_DAY"), "%d/%m/%Y %H:%M:%S %z"
)

# Staff Organisation name
STAFF_ORGANISATION_NAME = "BetaGouv"

# Tabbed Admin
TABBED_ADMIN_USE_JQUERY_UI = True

# Shell Plus
SHELL_PLUS_IMPORTS = [
    "from datetime import datetime, timedelta",
]

# Datapass
DATAPASS_KEY = os.getenv("DATAPASS_KEY", None)
DATAPASS_FROM_EMAIL = os.getenv("DATAPASS_FROM_EMAIL", None)
DATAPASS_TO_EMAIL = os.getenv("DATAPASS_TO_EMAIL", None)
DATAPASS_CODE_FOR_ID_GENERATOR = "datapassid"

AC_HABILITATION_FORM_ENABLED = getenv_bool("AC_HABILITATION_FORM_ENABLED", False)
AC_IMPORT_HABILITATION_REQUESTS = getenv_bool("AC_IMPORT_HABILITATION_REQUESTS", False)

SUPPORT_EMAIL = "connexion@aidantsconnect.beta.gouv.fr"

MANDAT_EXPIRED_SOON = 30
MANDAT_EXPIRED_SOON_EMAIL_SUBJECT = os.getenv(
    "MANDAT_EXPIRED_SOON_EMAIL_SUBJECT", "Ces mandats vont bientôt expirer"
)
MANDAT_EXPIRED_SOON_EMAIL_FROM = os.getenv(
    "MANDAT_EXPIRED_SOON_EMAIL_FROM", SUPPORT_EMAIL
)

WORKERS_NO_TOTP_NOTIFY_EMAIL_SUBJECT = os.getenv(
    "WORKERS_NO_TOTP_NOTIFY_EMAIL_SUBJECT", ""
)
WORKERS_NO_TOTP_NOTIFY_EMAIL_FROM = os.getenv(
    "WORKERS_NO_TOTP_NOTIFY_EMAIL_FROM", SUPPORT_EMAIL
)

PHONENUMBER_DEFAULT_REGION = os.getenv("PHONENUMBER_DEFAULT_REGION", "FR")

AIDANTS__ORGANISATIONS_CHANGED_EMAIL_SUBJECT = os.getenv(
    "AIDANTS__ORGANISATIONS_CHANGED_EMAIL_SUBJECT",
    "La liste des organisations dont vous faites partie a changé",
)
AIDANTS__ORGANISATIONS_CHANGED_EMAIL_FROM = os.getenv(
    "AIDANTS__ORGANISATIONS_CHANGED_EMAIL_FROM", SUPPORT_EMAIL
)

default = "3"
val = os.getenv("EMAIL_CONFIRMATION_EXPIRE_DAYS", default)
EMAIL_CONFIRMATION_EXPIRE_DAYS = int(val) if val.isnumeric() else default

EMAIL_CONFIRMATION_EXPIRE_DAYS_EMAIL_FROM = os.getenv(
    "EMAIL_CONFIRMATION_EXPIRE_DAYS_EMAIL_FROM", SUPPORT_EMAIL
)

EMAIL_CONFIRMATION_EXPIRE_DAYS_EMAIL_SUBJECT = os.getenv(
    "EMAIL_CONFIRMATION_EXPIRE_DAYS_EMAIL_SUBJECT",
    "Merci de confirmer votre adresse email pour le processus d'habilitation "
    "Aidant Connect.",
)

EMAIL_CONFIRMATION_SUPPORT_CONTACT_EMAIL = os.getenv(
    "EMAIL_CONFIRMATION_SUPPORT_CONTACT_EMAIL", SUPPORT_EMAIL
)

EMAIL_CONFIRMATION_SUPPORT_CONTACT_SUBJECT = os.getenv(
    "EMAIL_CONFIRMATION_SUPPORT_CONTACT_SUBJECT",
    "Je ne reçois pas les emails de confirmation de mon adresse email",
)

EMAIL_CONFIRMATION_SUPPORT_CONTACT_BODY = os.getenv(
    "EMAIL_CONFIRMATION_SUPPORT_CONTACT_BODY",
    """Bonjour,

    Je vous contacte car je ne reçois pas les emails de confirmation de mon adresse email.""",
)

EMAIL_ORGANISATION_REQUEST_FROM = os.getenv(
    "EMAIL_ORGANISATION_REQUEST_FROM", SUPPORT_EMAIL
)

EMAIL_HABILITATION_ISSUER_EMAIL_ALREADY_EXISTS_SUBJECT = os.getenv(
    "EMAIL_HABILITATION_ISSUER_EMAIL_ALREADY_EXISTS_SUBJECT",
    "Aidants Connect - Rappel de votre profil demandeur",
)

EMAIL_ORGANISATION_REQUEST_CREATION_SUBJECT = os.getenv(
    "EMAIL_ORGANISATION_REQUEST_CREATION_SUBJECT",
    "Aidants Connect - Votre demande d’habilitation a été créée",
)

EMAIL_ORGANISATION_REQUEST_SUBMISSION_SUBJECT = os.getenv(
    "EMAIL_ORGANISATION_REQUEST_CREATION_SUBJECT",
    "Aidants Connect - Votre demande d’habilitation a été soumise",
)

EMAIL_ORGANISATION_REQUEST_MODIFICATION_SUBJECT = os.getenv(
    "EMAIL_ORGANISATION_REQUEST_MODIFICATION_SUBJECT",
    "Aidants Connect - Votre demande d’habilitation a été modifiée",
)

EMAIL_NEW_MESSAGE_RECEIVED_SUBJECT = os.getenv(
    "EMAIL_NEW_MESSAGE_RECEIVED_SUBJECT",
    "Aidants Connect - Vous avez reçu un nouveau message de l’équipe Aidants Connect",
)

PIX_METABASE_USER = os.getenv("PIX_METABASE_USER")
PIX_METABASE_PASSWORD = os.getenv("PIX_METABASE_PASSWORD")
PIX_METABASE_CARD_ID = os.getenv("PIX_METABASE_CARD_ID")

GOUV_ADDRESS_SEARCH_API_BASE_URL = os.getenv(
    "GOUV_ADDRESS_SEARCH_API_BASE_URL", "https://api-adresse.data.gouv.fr/search/"
)
GOUV_ADDRESS_SEARCH_API_DISABLED = getenv_bool("GOUV_ADDRESS_SEARCH_API_DISABLED", True)

if not GOUV_ADDRESS_SEARCH_API_DISABLED:
    CSP_CONNECT_SRC = (*CSP_CONNECT_SRC, GOUV_ADDRESS_SEARCH_API_BASE_URL)
    CSP_SCRIPT_SRC = (
        *CSP_SCRIPT_SRC,
        "https://cdn.jsdelivr.net/npm/@tarekraafat/autocomplete.js@10.2.7/dist/autoComplete.min.js",
    )

MATOMO_INSTANCE_URL = os.getenv("MATOMO_INSTANCE_URL")
MATOMO_INSTANCE_SITE_ID = os.getenv("MATOMO_INSTANCE_SITE_ID")
