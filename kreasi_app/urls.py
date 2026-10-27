"""URL untuk halaman KREASI dan endpoint penyimpanan."""
from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("api/state/", views.state_api, name="state-api"),
    path("api/session/", views.session_api, name="session-api"),
    path("api/session/logout/", views.session_logout_api, name="session-logout-api"),
    path("api/documents/", views.document_api, name="document-create-api"),
    path("api/documents/<str:document_id>/", views.document_api, name="document-api"),
]
