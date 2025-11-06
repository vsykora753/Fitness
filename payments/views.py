from django.views.generic import CreateView, DetailView, ListView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth import get_user_model
from .models import Payment, TopUp
from accounts.mixins import InstructorRequiredMixin

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


class TopUpCreateView(LoginRequiredMixin, CreateView):
	model = TopUp
	fields = ['amount']
	template_name = 'payments/topup_create.html'

	def form_valid(self, form):
		form.instance.user = self.request.user
		# VS a message se doplní v modelu v save()
		response = super().form_valid(form)
		return response

	def get_success_url(self):
		return reverse_lazy('topup_detail', kwargs={'pk': self.object.pk})


class TopUpDetailView(LoginRequiredMixin, DetailView):
	model = TopUp
	template_name = 'payments/topup_detail.html'

	def get_queryset(self):
		return TopUp.objects.filter(user=self.request.user)


class TopUpHistoryView(LoginRequiredMixin, ListView):
	model = TopUp
	template_name = 'payments/topup_history.html'
	context_object_name = 'topups'

	def get_queryset(self):
		return TopUp.objects.filter(user=self.request.user).order_by('-created_at')


class TopUpApproveListView(LoginRequiredMixin, InstructorRequiredMixin, ListView):
	model = TopUp
	template_name = 'payments/topup_approve_list.html'
	context_object_name = 'topups'

	def get_queryset(self):
		return TopUp.objects.filter(status='pending').order_by('created_at')


class TopUpApproveView(LoginRequiredMixin, InstructorRequiredMixin, UpdateView):
	model = TopUp
	fields = []
	template_name = 'payments/topup_approve.html'

	def form_valid(self, form):
		form.instance.status = 'confirmed'
		messages.success(self.request, 'Dobití bylo potvrzeno a kredit připsán.')
		return super().form_valid(form)

	def get_success_url(self):
		return reverse_lazy('topup_approve_list')
