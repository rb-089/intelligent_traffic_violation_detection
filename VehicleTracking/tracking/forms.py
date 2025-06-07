from django import forms
from .models import IncidentReport

class IncidentReportForm(forms.ModelForm):
    class Meta:
        model = IncidentReport
        fields = ['name', 'email', 'location', 'description', 'photos']
        widgets = {
            'location': forms.TextInput(attrs={'readonly': 'readonly'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }
