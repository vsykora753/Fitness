from django.urls import path
from . import views

urlpatterns = [
    path('events/', views.get_events, name='get_events'),
    path('create/<int:time_slot_id>/', views.BookingCreateView.as_view(), name='booking_create'),
]