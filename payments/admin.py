from django.contrib import admin
from .models import Payment, TopUp


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
	list_display = ("id", "client", "instructor", "amount", "status", "created_at")
	list_filter = ("status", "created_at")
	search_fields = ("client__username", "client__first_name", "client__last_name", "instructor__username")


@admin.register(TopUp)
class TopUpAdmin(admin.ModelAdmin):
	list_display = ("id", "user", "amount", "variable_symbol", "status", "created_at")
	list_filter = ("status", "created_at")
	search_fields = ("user__username", "user__first_name", "user__last_name", "variable_symbol")
