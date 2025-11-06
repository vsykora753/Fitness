from django.shortcuts import render, redirect
from django.contrib.auth import views as auth_views
from .forms import UserLoginForm

class CustomLoginView(auth_views.LoginView):
    """Vlastní LoginView, který po přihlášení přesměruje podle typu uživatele."""
    template_name = 'accounts/login.html'
    authentication_form = UserLoginForm
    
    def get_success_url(self):
        """Přesměrování podle typu uživatele."""
        user = self.request.user
        if user.is_authenticated:
            if user.user_type == 'instructor':
                return '/accounts/instructor/dashboard/'
            elif user.user_type == 'client':
                return '/accounts/client/dashboard/'
        # Fallback na stránku O mě
        return '/o-me/'
