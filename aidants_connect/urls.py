import sys

from django.conf import settings
from django.urls import include, path

from aidants_connect import views
from aidants_connect_web.admin import admin_site

urlpatterns = [
    path("favicon.ico", views.favicon),
    path(settings.ADMIN_URL, admin_site.urls),
    path("admin/", include("admin_honeypot.urls", namespace="admin_honeypot")),
    path("", include("aidants_connect_web.urls")),
    path("habilitation/", include("aidants_connect_habilitation.urls")),
]

if settings.DEBUG and "test" not in sys.argv:
    import debug_toolbar

    urlpatterns.append(path("__debug__/", include(debug_toolbar.urls)))
