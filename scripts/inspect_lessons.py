import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE','reservations.settings')
django.setup()
from django.utils import timezone
from bookings.models import Lesson
from bookings.models import Booking
current_date = timezone.now()
start_of_month = current_date.replace(day=1)
next_month = current_date.replace(day=1) + timezone.timedelta(days=32)
end_of_month = next_month.replace(day=1) - timezone.timedelta(days=1)
print('start_of_month', start_of_month.date(), 'end_of_month', end_of_month.date())
lessons = Lesson.objects.filter(date__range=(start_of_month.date(), end_of_month.date())).select_related('instructor')
print('lessons count', lessons.count())
lessons_by_day = {}
for lesson in lessons:
    day = lesson.date.day
    lessons_by_day.setdefault(day,[]).append({'id':lesson.id,'title':lesson.title,'time':lesson.start_time.strftime('%H:%M'),'category':lesson.category})
print('keys types sample:', type(list(lessons_by_day.keys())[0]) if lessons_by_day else 'no keys')
from pprint import pprint
pprint({k:lessons_by_day[k] for k in sorted(lessons_by_day)[:6]})
import json
print('serialized sample:', json.dumps(lessons_by_day)[:400])
