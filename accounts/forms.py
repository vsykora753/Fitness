from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from .models import AboutPage

User = get_user_model()

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label='Email',
        help_text='Zadejte platnou e-mailovou adresu. Slouží jako přihlašovací jméno.'
    )
    
    class Meta:
        model = User
        fields = ['email', 'password1', 'password2', 'first_name', 'last_name', 'phone']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Přidání CSS tříd a atributů pro všechna pole
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'form-control',
                'placeholder': field.label
            })
    
    def clean_email(self):
        """Ověření, že email je jedinečný."""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Tento e-mail je již registrován.')
        return email
    
    def save(self, commit=True):
        """Automaticky nastavit username z emailu a user_type jako CLIENT."""
        user = super().save(commit=False)
        # Username bude email (Django vyžaduje username)
        user.username = self.cleaned_data['email']
        user.email = self.cleaned_data['email']
        user.user_type = 'client'
        if commit:
            user.save()
        return user

class UserLoginForm(AuthenticationForm):
    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email',
            'autofocus': True
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Přidání CSS tříd pro heslo
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Heslo'
        })


class AboutPageForm(forms.ModelForm):
    class Meta:
        model = AboutPage
        fields = ['title', 'content']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].widget.attrs.update({'class': 'form-control'})
        self.fields['content'].widget.attrs.update({'class': 'form-control', 'rows': 12})