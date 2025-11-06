from django.contrib import admin
from .models import Category, Lesson, TimeSlot, Booking


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'order')
    list_editable = ('order',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'instructor', 'category', 'date', 'start_time', 'location', 'price', 'capacity')
    list_filter = ('category', 'instructor', 'date')
    search_fields = ('title', 'description', 'location')
    date_hierarchy = 'date'


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('lesson', 'start_time', 'is_available')
    list_filter = ('is_available', 'start_time')
    search_fields = ('lesson__title',)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('client', 'time_slot', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('client__username', 'client__first_name', 'client__last_name', 'time_slot__lesson__title')
