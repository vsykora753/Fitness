from django import forms
from .models import TimeSlot
from django.utils import timezone
from datetime import datetime


class TimeSlotForm(forms.ModelForm):
    """
    Formulář pro přidání TimeSlot s oddělenými poli pro datum a čas.
    """
    date = forms.DateField(
        label='Datum',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'placeholder': 'Vyberte datum'
        }),
        help_text='Vyberte datum termínu'
    )
    
    time = forms.TimeField(
        label='Čas',
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'form-control',
            'placeholder': 'HH:MM'
        }),
        help_text='Vyberte čas začátku'
    )
    
    class Meta:
        model = TimeSlot
        fields = []  # start_time se vytvoří z date + time
    
    def __init__(self, *args, **kwargs):
        # Pokud editujeme existující TimeSlot, předvyplníme datum a čas
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.start_time:
            self.fields['date'].initial = self.instance.start_time.date()
            self.fields['time'].initial = self.instance.start_time.time()
    
    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        time = cleaned_data.get('time')
        
        if date and time:
            # Spojíme datum a čas do datetime
            start_datetime = datetime.combine(date, time)
            
            # Převedeme na timezone-aware datetime
            if timezone.is_naive(start_datetime):
                start_datetime = timezone.make_aware(start_datetime, timezone.get_current_timezone())
            
            # Kontrola, že čas není v minulosti
            if start_datetime < timezone.now():
                raise forms.ValidationError("Nelze vytvořit termín v minulosti.")
            
            # Uložíme do cleaned_data
            cleaned_data['start_time'] = start_datetime
        elif not date and not time:
            raise forms.ValidationError("Prosím vyplňte datum i čas termínu.")
        elif not date:
            raise forms.ValidationError("Prosím vyplňte datum termínu.")
        elif not time:
            raise forms.ValidationError("Prosím vyplňte čas termínu.")
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        # Nastavíme start_time pouze pokud byl vytvořen v clean()
        if 'start_time' in self.cleaned_data:
            instance.start_time = self.cleaned_data['start_time']
        if commit:
            instance.save()
        return instance
