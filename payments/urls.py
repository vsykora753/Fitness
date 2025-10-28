from django.urls import path
from . import views

urlpatterns = [
    path('create/<int:instructor_id>/', views.PaymentCreateView.as_view(), name='payment_create'),
    path('confirm/<int:payment_id>/', views.PaymentConfirmView.as_view(), name='payment_confirm'),
    path('history/', views.PaymentHistoryView.as_view(), name='payment_history'),
]