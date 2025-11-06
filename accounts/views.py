from django.shortcuts import redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, UpdateView, TemplateView
from django.urls import reverse_lazy
from .forms import UserRegisterForm, AboutPageForm
from payments.models import TopUp
from .models import AboutPage

User = get_user_model()

class RegisterView(CreateView):
	model = User
	form_class = UserRegisterForm
	template_name = 'accounts/register.html'
	success_url = reverse_lazy('accounts:login')

class ProfileView(LoginRequiredMixin, UpdateView):
	model = User
	fields = ['first_name', 'last_name', 'email', 'phone', 'bio']
	template_name = 'accounts/profile.html'
	success_url = reverse_lazy('accounts:profile')
    
	def get_object(self):
		return self.request.user

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		# Defaultní instruktor pro dobití kreditu (první nalezený)
		context['default_instructor'] = User.objects.filter(user_type='instructor').first()
		return context

class InstructorDashboardView(LoginRequiredMixin, TemplateView):
	template_name = 'accounts/instructor_dashboard.html'
    
	def dispatch(self, request, *args, **kwargs):
		# Pouze instruktor má přístup na dashboard lektora
		if not request.user.is_authenticated or request.user.user_type != 'instructor':
			return redirect('about')
		return super().dispatch(request, *args, **kwargs)
    
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		# Čekající dobití (globálně pro všechny klienty) - zobrazíme všechna
		context['pending_topups'] = TopUp.objects.filter(status='pending').select_related('user').order_by('created_at')
		return context

class ClientDashboardView(LoginRequiredMixin, TemplateView):
	template_name = 'accounts/client_dashboard.html'
    
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		if self.request.user.user_type != 'client':
			return redirect('about')
		return context


class AboutView(TemplateView):
	template_name = 'about.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		page = AboutPage.get_solo()
		context['about'] = page
		return context


class AboutEditView(LoginRequiredMixin, UpdateView):
	template_name = 'accounts/about_edit.html'
	form_class = AboutPageForm
	success_url = reverse_lazy('about')

	def dispatch(self, request, *args, **kwargs):
		# Pouze instruktor může upravovat stránku O mně
		if not request.user.is_authenticated or not getattr(request.user, 'is_instructor', False):
			return redirect('about')
		return super().dispatch(request, *args, **kwargs)

	def get_object(self):
		# Vytvoří instanci při prvním uložení, pokud ještě neexistuje
		obj = AboutPage.objects.first()
		if obj:
			return obj
		return AboutPage()
