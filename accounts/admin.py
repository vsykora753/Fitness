from django.contrib import admin
from .models import AboutPage, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
	list_display = ("username", "first_name", "last_name", "user_type", "credits")
	list_filter = ("user_type",)
	search_fields = ("username", "first_name", "last_name", "email")


@admin.register(AboutPage)
class AboutPageAdmin(admin.ModelAdmin):
	list_display = ("title", "updated_at")
