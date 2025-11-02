from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from bookings.views import HomeView, ContactView, LessonListView

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("kontakt/", ContactView.as_view(), name="contact"),
    path("lekce/", LessonListView.as_view(), name="lessons"),
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("bookings/", include("bookings.urls")),
    path("payments/", include("payments.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
