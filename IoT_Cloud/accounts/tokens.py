from django.contrib.auth.tokens import PasswordResetTokenGenerator


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    """
    Token generator for email verification links.
    Includes is_active in the hash so the token is invalidated after the
    user activates their account (single-use).
    """

    def _make_hash_value(self, user, timestamp):
        return (
            str(user.pk)
            + str(timestamp)
            + str(user.is_active)
            + str(user.email)
        )


email_verification_token = EmailVerificationTokenGenerator()

# Django's built-in PasswordResetTokenGenerator is used directly for
# password-reset flows (it already hashes last_login + password).
password_reset_token = PasswordResetTokenGenerator()
