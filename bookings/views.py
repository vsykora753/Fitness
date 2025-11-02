from django.shortcuts import render
from django.http import JsonResponse
from django.views.generic import TemplateView, ListView, DetailView
from .models import TimeSlot, Booking, Lesson
from django.utils import timezone
from django.views.generic.edit import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django.contrib import messages

class CalendarView(TemplateView):
    template_name = 'bookings/calendar.html'

def get_events(request):
    start = request.GET.get('start')
    end = request.GET.get('end')
    
    time_slots = TimeSlot.objects.filter(
        start_time__gte=timezone.now()
    ).select_related('lesson', 'lesson__instructor')
    
    events = []
    for slot in time_slots:
        booked_count = Booking.objects.filter(
            time_slot=slot,
            status='confirmed'
        ).count()
        
        available_spots = slot.lesson.capacity - booked_count
        
        events.append({
            'id': slot.id,
            'title': slot.lesson.title,
            'start': slot.start_time.isoformat(),
            'end': (slot.start_time + timezone.timedelta(minutes=slot.lesson.duration)).isoformat(),
            'extendedProps': {
                'instructor': slot.lesson.instructor.get_full_name(),
                'duration': slot.lesson.duration,
                'price': float(slot.lesson.price),
                'capacity': slot.lesson.capacity,
                'availableSpots': available_spots,
                'description': slot.lesson.description,
                'isAvailable': slot.is_available and available_spots > 0,
                'timeSlotId': slot.id,
            }
        })
    
    return JsonResponse(events, safe=False)

class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated and self.request.user.is_instructor:
            context['instructor'] = self.request.user
        return context

class ContactView(TemplateView):
    template_name = 'contact.html'

class LessonListView(ListView):
    model = Lesson
    template_name = 'lessons.html'
    context_object_name = 'lessons'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Získáme všechny lekce pro aktuální měsíc
        current_date = timezone.now()
        start_of_month = current_date.replace(day=1)
        next_month = current_date.replace(day=1) + timezone.timedelta(days=32)
        end_of_month = next_month.replace(day=1) - timezone.timedelta(days=1)
        
        lessons = Lesson.objects.filter(
            date__range=(start_of_month.date(), end_of_month.date())
        ).select_related('instructor')
        
        # Vytvoříme slovník pro každý den v měsíci
        lessons_by_day = {}
        for lesson in lessons:
            day = lesson.date.day
            if day not in lessons_by_day:
                lessons_by_day[day] = []
            
            # Zjistíme počet obsazených míst
            booked_count = Booking.objects.filter(
                time_slot__lesson=lesson,
                status='confirmed'
            ).count()
            available_spots = lesson.capacity - booked_count
            
            lessons_by_day[day].append({
                'id': lesson.id,
                'title': lesson.title,
                'time': lesson.start_time.strftime('%H:%M'),
                'duration': lesson.duration,
                'price': float(lesson.price),
                'available_spots': available_spots,
                'instructor': lesson.instructor.get_full_name(),
                'category': lesson.category,
                'location': lesson.location
            })
        
        # Kategorie pro ouška (z definice v modelu)
        try:
            categories = list(Lesson.LESSON_CATEGORIES)
        except Exception:
            categories = []

        context['lessons_by_day'] = lessons_by_day
        context['current_month'] = current_date.month
        context['current_year'] = current_date.year
        context['categories'] = categories
        return context

class LessonDetailView(DetailView):
    model = Lesson
    template_name = 'lessons_detail.html'
    context_object_name = 'lesson'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Získáme budoucí časové sloty pro tuto lekci
        context['time_slots'] = TimeSlot.objects.filter(
            lesson=self.object,
            start_time__gte=timezone.now()
        ).order_by('start_time')
        return context

class BookingCreateView(LoginRequiredMixin, CreateView):
    model = Booking
    fields = []
    template_name = 'bookings/booking_create.html'
    success_url = reverse_lazy('client_dashboard')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        time_slot_id = self.kwargs.get('time_slot_id')
        context['time_slot'] = get_object_or_404(TimeSlot, id=time_slot_id)
        return context

    def form_valid(self, form):
        time_slot_id = self.kwargs.get('time_slot_id')
        time_slot = get_object_or_404(TimeSlot, id=time_slot_id)
    
        if not time_slot.is_available:
            messages.error(self.request, "Tento termín již není dostupný.")
            return self.form_invalid(form)
    
        if self.request.user.credits < time_slot.lesson.price:
            messages.error(self.request, "Nemáte dostatek kreditů pro tuto rezervaci.")
            return self.form_invalid(form)
    
        form.instance.client = self.request.user
        form.instance.time_slot = time_slot
        form.instance.status = 'confirmed'
    
        return super().form_valid(form)
