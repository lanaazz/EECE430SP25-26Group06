from django import forms
from .models import Match, TrainingSession
from django.utils import timezone


class MatchForm(forms.ModelForm):
    date = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={'type': 'datetime-local', 'class': 'form-input'},
            format='%Y-%m-%dT%H:%M'
        ),
        input_formats=['%Y-%m-%dT%H:%M'],
    )

    class Meta:
        model = Match
        fields = ['home_team', 'away_team', 'date', 'location', 'notes']
        widgets = {
            'home_team': forms.Select(attrs={'class': 'form-input'}),
            'away_team': forms.Select(attrs={'class': 'form-input'}),
            'location': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Main Arena'}),
            'notes': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Optional notes...'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        home_team = cleaned_data.get('home_team')
        away_team = cleaned_data.get('away_team')
        date = cleaned_data.get('date')

        if home_team and away_team and home_team == away_team:
            raise forms.ValidationError("Home team and away team cannot be the same.")

        if date and date < timezone.now():
            raise forms.ValidationError("Match date must be in the future.")

        return cleaned_data


class TrainingSessionForm(forms.ModelForm):
    date = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={'type': 'datetime-local', 'class': 'form-input'},
            format='%Y-%m-%dT%H:%M'
        ),
        input_formats=['%Y-%m-%dT%H:%M'],
    )

    class Meta:
        model = TrainingSession
        fields = ['team', 'title', 'date', 'location', 'duration_minutes', 'description']
        widgets = {
            'team': forms.Select(attrs={'class': 'form-input'}),
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Defensive Drills'}),
            'location': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Gym Hall A'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-input', 'min': 15, 'max': 300}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Session details...'}),
        }

    def clean_date(self):
        date = self.cleaned_data.get('date')
        if date and date < timezone.now():
            raise forms.ValidationError("Training date must be in the future.")
        return date
