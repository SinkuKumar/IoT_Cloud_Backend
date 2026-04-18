from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import OpenApiParameter, extend_schema

from .serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
)
from .tokens import email_verification_token, password_reset_token

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_url(request, viewname, uidb64, token):
    """Return an absolute URL for verification/reset links."""
    return request.build_absolute_uri(f"/api/auth/{viewname}/{uidb64}/{token}/")


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


class RegisterView(APIView):
    """
    POST /api/auth/register/
    Creates an inactive user and sends an email verification link.
    """

    permission_classes = [AllowAny]

    @extend_schema(request=RegisterSerializer, responses={201: None})
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Build verification link
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = email_verification_token.make_token(user)
        verify_url = _build_url(request, "verify-email", uid, token)

        send_mail(
            subject="Verify your email address",
            message=(
                f"Hi {user.get_short_name()},\n\n"
                f"Please verify your email by visiting:\n{verify_url}\n\n"
                "This link is valid for 24 hours."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        return Response(
            {
                "detail": "Registration successful. Please check your email to verify your account.",
                "email": user.email,
            },
            status=status.HTTP_201_CREATED,
        )


# ---------------------------------------------------------------------------
# Email verification
# ---------------------------------------------------------------------------


class EmailVerifyView(APIView):
    """
    GET /api/auth/verify-email/<uidb64>/<token>/
    Activates the user account when the link is valid.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        parameters=[
            OpenApiParameter(name="uidb64", type=str, location=OpenApiParameter.PATH),
            OpenApiParameter(name="token", type=str, location=OpenApiParameter.PATH),
        ]
    )
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {"detail": "Invalid verification link."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user.is_active:
            return Response(
                {"detail": "Account is already verified."},
                status=status.HTTP_200_OK,
            )

        if not email_verification_token.check_token(user, token):
            return Response(
                {"detail": "Verification link is invalid or has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.is_active = True
        user.save(update_fields=["is_active"])

        return Response(
            {"detail": "Email verified successfully. You can now log in."},
            status=status.HTTP_200_OK,
        )


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


class LoginView(APIView):
    """
    POST /api/auth/login/
    Authenticates via email or username + password.
    Returns a DRF auth token.
    """

    permission_classes = [AllowAny]

    @extend_schema(request=LoginSerializer)
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)

        return Response(
            {
                "token": token.key,
                "user": {
                    "id": user.pk,
                    "email": user.email,
                    "username": user.username,
                },
            },
            status=status.HTTP_200_OK,
        )


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------


class LogoutView(APIView):
    """
    POST /api/auth/logout/
    Deletes the user's auth token (requires authentication).
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()
        return Response(
            {"detail": "Logged out successfully."}, status=status.HTTP_200_OK
        )


# ---------------------------------------------------------------------------
# Change password
# ---------------------------------------------------------------------------


class ChangePasswordView(APIView):
    """
    POST /api/auth/change-password/
    Requires authentication. Validates old password before updating.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(request=ChangePasswordSerializer)
    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])

        # Rotate the auth token so existing sessions are invalidated
        Token.objects.filter(user=user).delete()
        new_token = Token.objects.create(user=user)

        return Response(
            {
                "detail": "Password updated successfully.",
                "token": new_token.key,
            },
            status=status.HTTP_200_OK,
        )


# ---------------------------------------------------------------------------
# Password reset – request
# ---------------------------------------------------------------------------


class PasswordResetRequestView(APIView):
    """
    POST /api/auth/password-reset/
    Sends a password reset link to the provided email (always 200 to avoid
    leaking whether the email is registered).
    """

    permission_classes = [AllowAny]

    @extend_schema(request=PasswordResetRequestSerializer)
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            # Return generic success to avoid leaking registered emails
            return Response(
                {"detail": "If that email is registered, a reset link has been sent."},
                status=status.HTTP_200_OK,
            )

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = password_reset_token.make_token(user)
        reset_url = _build_url(request, "password-reset-confirm", uid, token)

        send_mail(
            subject="Reset your password",
            message=(
                f"Hi {user.get_short_name()},\n\n"
                f"Reset your password by visiting:\n{reset_url}\n\n"
                "This link is valid for 24 hours. If you did not request a reset, "
                "you can safely ignore this email."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        return Response(
            {"detail": "If that email is registered, a reset link has been sent."},
            status=status.HTTP_200_OK,
        )


# ---------------------------------------------------------------------------
# Password reset – confirm
# ---------------------------------------------------------------------------


class PasswordResetConfirmView(APIView):
    """
    POST /api/auth/password-reset-confirm/<uidb64>/<token>/
    Validates the token and sets the new password.
    """

    permission_classes = [AllowAny]

    @extend_schema(request=PasswordResetConfirmSerializer)
    def post(self, request, uidb64, token):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {"detail": "Invalid reset link."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not password_reset_token.check_token(user, token):
            return Response(
                {"detail": "Reset link is invalid or has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])

        # Invalidate all existing tokens
        Token.objects.filter(user=user).delete()

        return Response(
            {"detail": "Password has been reset successfully. Please log in."},
            status=status.HTTP_200_OK,
        )
