from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    # API a události
    path('events/', views.get_events, name='get_events'),
    
    # Veřejné zobrazení lekce
    path('lesson/<int:pk>/', views.LessonDetailView.as_view(), name='lesson_detail'),
    
    # Rezervace (klienti)
    path('create/<int:time_slot_id>/', views.BookingCreateView.as_view(), name='booking_create'),
    path('cancel/<int:booking_id>/', views.BookingCancelView.as_view(), name='booking_cancel'),
    
    # Instruktoři - správa lekcí
    path('instructor/lessons/', views.InstructorLessonListView.as_view(), name='instructor_lessons'),
    path('instructor/lesson/create/', views.LessonCreateView.as_view(), name='lesson_create'),
    path('instructor/lesson/<int:pk>/edit/', views.LessonUpdateView.as_view(), name='lesson_edit'),
    path('instructor/lesson/<int:pk>/delete/', views.LessonDeleteView.as_view(), name='lesson_delete'),
    path('instructor/lesson/<int:pk>/', views.InstructorLessonDetailView.as_view(), name='instructor_lesson_detail'),
    
    # Instruktoři - správa termínů
    path('instructor/lesson/<int:lesson_id>/timeslot/add/', views.TimeSlotCreateView.as_view(), name='timeslot_add'),
    path('instructor/timeslot/<int:pk>/delete/', views.TimeSlotDeleteView.as_view(), name='timeslot_delete'),
]