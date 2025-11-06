from django.http import JsonResponse
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import TimeSlot, Booking, Lesson, Category
from .forms import TimeSlotForm
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.views import View
from datetime import datetime
from accounts.mixins import InstructorRequiredMixin

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

class ContactView(TemplateView):
    template_name = 'contact.html'

class LessonListView(ListView):
    model = Lesson
    template_name = 'lessons.html'
    context_object_name = 'lessons'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Získáme všechny time_sloty pro aktuální měsíc
        current_date = timezone.now()
        start_of_month = current_date.replace(day=1)
        next_month = current_date.replace(day=1) + timezone.timedelta(days=32)
        end_of_month = next_month.replace(day=1) - timezone.timedelta(days=1)
        
        # Získáme pouze budoucí sloty v daném měsíci
        now = timezone.now()
        time_slots = TimeSlot.objects.filter(
            start_time__gte=max(start_of_month, now),
            start_time__lte=end_of_month
        ).select_related('lesson', 'lesson__instructor').order_by('start_time')

        # Klíčujeme podle YYYY-MM-DD
        lessons_by_day = {}
        for slot in time_slots:
            day_key = slot.start_time.strftime('%Y-%m-%d')
            if day_key not in lessons_by_day:
                lessons_by_day[day_key] = []

            booked_count = Booking.objects.filter(
                time_slot=slot,
                status='confirmed'
            ).count()
            available_spots = slot.lesson.capacity - booked_count

            lessons_by_day[day_key].append({
                'id': slot.lesson.id,
                'title': slot.lesson.title,
                'time': slot.start_time.strftime('%H:%M'),
                'duration': slot.lesson.duration,
                'price': float(slot.lesson.price),
                'available_spots': available_spots,
                'capacity': slot.lesson.capacity,
                'instructor': slot.lesson.instructor.get_full_name(),
                'category': slot.lesson.category.slug if slot.lesson.category else 'other',
                'location': slot.lesson.location
            })
        
        # Kategorie pro ouška - načteme z databáze
        categories = [(cat.slug, cat.name) for cat in Category.objects.all().order_by('order', 'name')]

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
    success_url = reverse_lazy('accounts:client_dashboard')

    def get_form(self, form_class=None):
        """Předvyplníme instance formu hodnotami, které nejsou ve formuláři,
        aby prošla modelová validace (clean), která time_slot vyžaduje."""
        form = super().get_form(form_class)
        time_slot_id = self.kwargs.get('time_slot_id')
        if time_slot_id:
            form.instance.time_slot = get_object_or_404(TimeSlot, id=time_slot_id)
        form.instance.client = self.request.user
        return form

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

class BookingCancelView(LoginRequiredMixin, View):
    def post(self, request, booking_id):
        booking = get_object_or_404(Booking, id=booking_id, client=request.user)
        
        if not booking.can_cancel():
            messages.error(request, "Rezervaci nelze zrušit méně než 2 hodiny před začátkem lekce nebo je již zrušená.")
            return redirect('accounts:client_dashboard')
        
        try:
            booking.cancel()
            messages.success(request, f"Rezervace byla úspěšně zrušena. Kredit {booking.time_slot.lesson.price} Kč byl vrácen na váš účet.")
        except Exception as e:
            messages.error(request, f"Chyba při rušení rezervace: {str(e)}")
        
        return redirect('accounts:client_dashboard')


# ===== INSTRUCTOR VIEWS =====
# InstructorRequiredMixin je nyní importován z accounts.mixins


class InstructorLessonListView(InstructorRequiredMixin, ListView):
    """Seznam všech lekcí daného lektora."""
    model = Lesson
    template_name = 'bookings/instructor_lesson_list.html'
    context_object_name = 'lessons'
    
    def get_queryset(self):
        return Lesson.objects.filter(instructor=self.request.user).order_by('-date', '-start_time')


class LessonCreateView(InstructorRequiredMixin, CreateView):
    """Vytvoření nové lekce lektorem."""
    model = Lesson
    template_name = 'bookings/lesson_form.html'
    fields = ['title', 'description', 'category', 'price', 'duration', 'capacity', 'date', 'start_time', 'location']
    success_url = reverse_lazy('bookings:instructor_lessons')
    
    def form_valid(self, form):
        # Uložíme lekci pod přihlášeného lektora
        form.instance.instructor = self.request.user
        response = super().form_valid(form)

        # Po vytvoření lekce automaticky vytvoříme první TimeSlot
        # podle zadaného datumu a času z modelu Lesson (aby se objevila v kalendáři).
        lesson = self.object
        try:
            start_dt = datetime.combine(lesson.date, lesson.start_time)
            if timezone.is_naive(start_dt):
                start_dt = timezone.make_aware(start_dt, timezone.get_current_timezone())

            # Pokud pro daný lesson+čas už slot existuje, nevytvářej duplicitně
            exists = TimeSlot.objects.filter(lesson=lesson, start_time=start_dt).exists()
            if not exists:
                TimeSlot.objects.create(lesson=lesson, start_time=start_dt, is_available=True)
        except Exception as e:
            # Nezablokovat uložení lekce kvůli TimeSlotu, ale informovat uživatele
            messages.warning(self.request, f"Lekce byla vytvořena, ale nepodařilo se automaticky vytvořit termín: {e}")

        messages.success(self.request, f"Lekce '{lesson.title}' byla úspěšně vytvořena.")
        return response


class LessonUpdateView(InstructorRequiredMixin, UpdateView):
    """Editace existující lekce lektorem."""
    model = Lesson
    template_name = 'bookings/lesson_form.html'
    fields = ['title', 'description', 'category', 'price', 'duration', 'capacity', 'date', 'start_time', 'location']
    success_url = reverse_lazy('bookings:instructor_lessons')
    
    def get_queryset(self):
        # Lektor může editovat pouze své vlastní lekce
        return Lesson.objects.filter(instructor=self.request.user)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        lesson = self.object
        try:
            new_start = datetime.combine(lesson.date, lesson.start_time)
            if timezone.is_naive(new_start):
                new_start = timezone.make_aware(new_start, timezone.get_current_timezone())

            # Zkusíme upravit první existující slot pro tuto lekci
            slot = TimeSlot.objects.filter(lesson=lesson).order_by('start_time').first()
            if slot:
                slot.start_time = new_start
                slot.is_available = True
                slot.save()
            else:
                TimeSlot.objects.create(lesson=lesson, start_time=new_start, is_available=True)
        except Exception as e:
            messages.warning(self.request, f"Lekce byla aktualizována, ale nepodařilo se upravit/vytvořit termín: {e}")

        messages.success(self.request, f"Lekce '{lesson.title}' byla úspěšně aktualizována.")
        return response


class LessonDeleteView(InstructorRequiredMixin, DeleteView):
    """Smazání lekce lektorem."""
    model = Lesson
    template_name = 'bookings/lesson_confirm_delete.html'
    success_url = reverse_lazy('bookings:instructor_lessons')
    
    def get_queryset(self):
        # Lektor může mazat pouze své vlastní lekce
        return Lesson.objects.filter(instructor=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        lesson = self.get_object()
        messages.success(request, f"Lekce '{lesson.title}' byla úspěšně smazána.")
        return super().delete(request, *args, **kwargs)


class InstructorLessonDetailView(InstructorRequiredMixin, DetailView):
    """Detail lekce s přehledem přihlášených klientů."""
    model = Lesson
    template_name = 'bookings/instructor_lesson_detail.html'
    context_object_name = 'lesson'
    
    def get_queryset(self):
        return Lesson.objects.filter(instructor=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lesson = self.object
        
        # Všechny časové sloty pro tuto lekci
        time_slots = TimeSlot.objects.filter(lesson=lesson).order_by('start_time')
        context['time_slots'] = time_slots
        
        # Všechny potvrzené rezervace pro tuto lekci
        bookings = Booking.objects.filter(
            time_slot__lesson=lesson,
            status='confirmed'
        ).select_related('client', 'time_slot').order_by('time_slot__start_time')
        context['bookings'] = bookings
        
        # Statistiky
        context['total_bookings'] = bookings.count()
        context['total_slots'] = time_slots.count()
        
        # Informace o kreditech klientů
        from payments.models import TopUp
        clients = set(booking.client for booking in bookings)
        client_info = {}
        total_pending_amount = 0
        for client in clients:
            # Kredit klienta
            credit_balance = getattr(client, 'credits', 0)
            
            # Čekající dobití
            pending_topups = TopUp.objects.filter(
                user=client,
                status='pending'
            ).order_by('-created_at')
            
            pending_sum = sum(topup.amount for topup in pending_topups)
            total_pending_amount += pending_sum
            
            client_info[client.id] = {
                'client': client,
                'credits': credit_balance,
                'pending_topups': pending_topups,
                'pending_total': pending_sum
            }
        
        context['client_info'] = client_info
        context['total_pending_topups'] = total_pending_amount
        
        return context


class TimeSlotCreateView(InstructorRequiredMixin, CreateView):
    """Přidání časového slotu k lekci."""
    model = TimeSlot
    template_name = 'bookings/timeslot_form.html'
    form_class = TimeSlotForm
    
    def dispatch(self, request, *args, **kwargs):
        # Ověříme, že lekce existuje a patří lektorovi
        self.lesson = get_object_or_404(Lesson, pk=self.kwargs['lesson_id'], instructor=request.user)
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lesson'] = self.lesson
        return context
    
    def form_valid(self, form):
        form.instance.lesson = self.lesson
        messages.success(self.request, f"Nový termín byl přidán k lekci '{self.lesson.title}'.")
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('bookings:instructor_lesson_detail', kwargs={'pk': self.lesson.pk})


class TimeSlotDeleteView(InstructorRequiredMixin, DeleteView):
    """Smazání časového slotu."""
    model = TimeSlot
    template_name = 'bookings/timeslot_confirm_delete.html'
    
    def get_queryset(self):
        # Lektor může mazat pouze sloty svých vlastních lekcí
        return TimeSlot.objects.filter(lesson__instructor=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        slot = self.get_object()
        # Zkontrolujeme, zda nejsou na tento slot rezervace
        bookings_count = Booking.objects.filter(time_slot=slot, status='confirmed').count()
        if bookings_count > 0:
            messages.error(request, f"Nelze smazat termín, protože má {bookings_count} aktivních rezervací.")
            return redirect('bookings:instructor_lesson_detail', pk=slot.lesson.pk)
        
        lesson_pk = slot.lesson.pk
        messages.success(request, f"Termín {slot.start_time.strftime('%d.%m.%Y %H:%M')} byl úspěšně smazán.")
        self.object = slot
        self.object.delete()
        return redirect('bookings:instructor_lesson_detail', pk=lesson_pk)
    
    def get_success_url(self):
        return reverse_lazy('bookings:instructor_lesson_detail', kwargs={'pk': self.object.lesson.pk})
