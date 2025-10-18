from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class EmailBackend(ModelBackend):
    """
    Authenticate users using their email instead of username.
    Compatible with Django + Wagtail admin login.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        # Allow both "username" or "email" as the login field
        email = kwargs.get("email") or username
        if not email or not password:
            return None

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return None

        # Check password and user status
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
