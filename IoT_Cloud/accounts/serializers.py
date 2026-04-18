from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True, label="Confirm password")

    class Meta:
        model = User
        fields = ("email", "username", "password", "password2")
        extra_kwargs = {"username": {"required": False, "allow_null": True}}

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password2"):
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def validate_username(self, value):
        if value and User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

class LoginSerializer(serializers.Serializer):
    login = serializers.CharField(
        help_text="Email address or username"
    )
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        login = attrs.get("login")
        password = attrs.get("password")

        user = authenticate(
            request=self.context.get("request"),
            username=login,  # backend accepts email or username via `username` kwarg
            password=password,
        )

        if not user:
            raise serializers.ValidationError("Invalid credentials. Please try again.")

        if not user.is_active:
            raise serializers.ValidationError(
                "Account is not activated. Please verify your email first."
            )

        attrs["user"] = user
        return attrs


# ---------------------------------------------------------------------------
# Email verification
# ---------------------------------------------------------------------------

class EmailVerifySerializer(serializers.Serializer):
    uidb64 = serializers.CharField()
    token = serializers.CharField()


# ---------------------------------------------------------------------------
# Change password (authenticated)
# ---------------------------------------------------------------------------

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password2 = serializers.CharField(write_only=True, label="Confirm new password")

    def validate(self, attrs):
        if attrs["new_password"] != attrs.pop("new_password2"):
            raise serializers.ValidationError({"new_password": "Passwords do not match."})
        return attrs

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value


# ---------------------------------------------------------------------------
# Password reset – request
# ---------------------------------------------------------------------------

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        # Always return a success response (don't leak whether email exists)
        return value


# ---------------------------------------------------------------------------
# Password reset – confirm
# ---------------------------------------------------------------------------

class PasswordResetConfirmSerializer(serializers.Serializer):
    uidb64 = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password2 = serializers.CharField(write_only=True, label="Confirm new password")

    def validate(self, attrs):
        if attrs["new_password"] != attrs.pop("new_password2"):
            raise serializers.ValidationError({"new_password": "Passwords do not match."})
        return attrs
