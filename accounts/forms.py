from django import forms
from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordResetForm
from .models import CustomUser
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth import get_user_model


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'username', 'password1', 'password2', 'employee_id', 'department',
                  'designation', 'contact_number', 'address', 'image')

        def clean(self):
            cleaned_data = super().clean()
            email = cleaned_data.get('email')
            # Validate that the email is unique
            if email and CustomUser.objects.filter(email=email).exists():
                self.add_error('email', 'This email is already in use.')

            return cleaned_data


class CustomUserChangeForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('department', 'designation', 'contact_number', 'address', 'image')


class CustomPasswordResetForm(forms.Form):
    new_password1 = forms.CharField(label='New Password', widget=forms.PasswordInput)
    new_password2 = forms.CharField(label='Confirm New Password', widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')

        if new_password1 and new_password2 and new_password1 != new_password2:
            raise forms.ValidationError("New passwords do not match.")
