from django.urls import path
from . import views
from .auth_views import CustomLoginView
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from .forms import UserLoginForm

app_name = 'accounts'

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(
    template_name='accounts/logout.html'
), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    # Změna hesla
    path('password/change/', auth_views.PasswordChangeView.as_view(
        template_name='accounts/password_change.html',
        success_url=reverse_lazy('accounts:password_change_done')
    ), name='password_change'),
    path('password/change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='accounts/password_change_done.html'
    ), name='password_change_done'),
    path('instructor/dashboard/', views.InstructorDashboardView.as_view(), name='instructor_dashboard'),
    path('client/dashboard/', views.ClientDashboardView.as_view(), name='client_dashboard'),
    # Editace stránky O mně (pouze instruktor)
    path('about/edit/', views.AboutEditView.as_view(), name='about_edit'),
]