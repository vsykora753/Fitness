"""
Společné mixiny pro kontrolu přístupu napříč aplikací.
"""
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect
from django.contrib import messages


class InstructorRequiredMixin(UserPassesTestMixin):
    """
    Mixin který zajistí, že pouze instruktor má přístup k view.
    Použití: class MyView(InstructorRequiredMixin, ListView): ...
    """
    def test_func(self):
        return self.request.user.is_authenticated and getattr(self.request.user, 'user_type', None) == 'instructor'
    
    def handle_no_permission(self):
        messages.error(self.request, "K této stránce nemáte přístup.")
        return redirect('about')


class ClientRequiredMixin(UserPassesTestMixin):
    """
    Mixin který zajistí, že pouze klient má přístup k view.
    """
    def test_func(self):
        return self.request.user.is_authenticated and getattr(self.request.user, 'user_type', None) == 'client'
    
    def handle_no_permission(self):
        messages.error(self.request, "K této stránce nemáte přístup.")
        return redirect('about')
