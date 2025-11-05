from django.urls import path
from . import views

urlpatterns = [
    path('create/<int:instructor_id>/', views.PaymentCreateView.as_view(), name='payment_create'),
    path('confirm/<int:payment_id>/', views.PaymentConfirmView.as_view(), name='payment_confirm'),
    path('history/', views.PaymentHistoryView.as_view(), name='payment_history'),
    # Top-up routes
    path('topup/create/', views.TopUpCreateView.as_view(), name='topup_create'),
    path('topup/<int:pk>/', views.TopUpDetailView.as_view(), name='topup_detail'),
    path('topup/history/', views.TopUpHistoryView.as_view(), name='topup_history'),
    path('topup/approve/', views.TopUpApproveListView.as_view(), name='topup_approve_list'),
    path('topup/approve/<int:pk>/', views.TopUpApproveView.as_view(), name='topup_approve'),
]