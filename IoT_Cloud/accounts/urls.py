from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from .views import (
    ChangePasswordView,
    EmailVerifyView,
    LoginView,
    LogoutView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    RegisterView,
)

app_name = "accounts"

urlpatterns = [
    # Registration & verification
    path("register/", RegisterView.as_view(), name="register"),
    path(
        "verify-email/<str:uidb64>/<str:token>/",
        EmailVerifyView.as_view(),
        name="verify-email",
    ),

    # Session management
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),

    # Password management
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("password-reset/", PasswordResetRequestView.as_view(), name="password-reset"),
    path(
        "password-reset-confirm/<str:uidb64>/<str:token>/",
        PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
]
