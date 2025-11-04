from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, UpdateView, TemplateView
from django.urls import reverse_lazy
from .forms import UserRegisterForm

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
    
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		if self.request.user.user_type != 'instructor':
			return redirect('home')
		return context

class ClientDashboardView(LoginRequiredMixin, TemplateView):
	template_name = 'accounts/client_dashboard.html'
    
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		if self.request.user.user_type != 'client':
			return redirect('home')
		return context
