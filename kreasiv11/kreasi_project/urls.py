from django.contrib import admin
from django.urls import path
from portal import views

# Pemetaan URL ke function-based views. Endpoint API dipisah agar frontend tetap
# menggunakan layout/renderer lama sementara data dan autentikasi diproses Django.
urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("", views.index, name="index"),
    path("api/session/", views.session_info, name="api_session"),
    path("api/auth/login/", views.login_view, name="api_login"),
    path("api/auth/logout/", views.logout_view, name="api_logout"),
    path("api/state/", views.state_view, name="api_state"),
    path("api/documents/upload/", views.document_upload, name="api_document_upload"),
    path("api/documents/<uuid:document_id>/", views.document_detail, name="api_document_detail"),
    path("api/documents/<uuid:document_id>/delete/", views.document_delete, name="api_document_delete"),
]
