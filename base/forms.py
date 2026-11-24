from django import forms

from .models import BasicInformation


class ProfessionalDocumentsUploadForm(forms.ModelForm):
    class Meta:
        model = BasicInformation
        fields = ('resume_pdf', 'cv_pdf')
        widgets = {
            'resume_pdf': forms.FileInput(attrs={'accept': '.pdf,application/pdf'}),
            'cv_pdf': forms.FileInput(attrs={'accept': '.pdf,application/pdf'}),
        }
