from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class EmailBackend(ModelBackend):
    """
    Autentizační backend, který umožňuje přihlášení pomocí emailu.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Hledáme uživatele podle emailu (username v našem případě obsahuje email)
            user = User.objects.get(email=username)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
