from django.shortcuts import render

# Create your views here.
from django.views.generic import CreateView, DetailView, ListView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth import get_user_model
from .models import Payment
from decimal import Decimal

User = get_user_model()

class PaymentCreateView(LoginRequiredMixin, CreateView):
	model = Payment
	fields = ['amount']
	template_name = 'payments/payment_create.html'
	success_url = reverse_lazy('payment_history')

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		instructor_id = self.kwargs.get('instructor_id')
		context['instructor'] = get_object_or_404(User, id=instructor_id, user_type='instructor')
		return context

	def form_valid(self, form):
		form.instance.client = self.request.user
		form.instance.instructor = get_object_or_404(
			User,
			id=self.kwargs.get('instructor_id'),
			user_type='instructor'
		)
		return super().form_valid(form)

class PaymentConfirmView(LoginRequiredMixin, UpdateView):
	model = Payment
	fields = []
	template_name = 'payments/payment_confirm.html'
	success_url = reverse_lazy('payment_history')
	pk_url_kwarg = 'payment_id'

	def get_queryset(self):
		return Payment.objects.filter(instructor=self.request.user, status='pending')

	def form_valid(self, form):
		form.instance.status = 'confirmed'
		messages.success(self.request, 'Platba byla úspěšně potvrzena.')
		return super().form_valid(form)

class PaymentHistoryView(LoginRequiredMixin, ListView):
	model = Payment
	template_name = 'payments/payment_history.html'
	context_object_name = 'payments'

	def get_queryset(self):
		if self.request.user.user_type == 'instructor':
			return Payment.objects.filter(instructor=self.request.user).order_by('-created_at')
		return Payment.objects.filter(client=self.request.user).order_by('-created_at')

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['user_type'] = self.request.user.user_type
		return context
