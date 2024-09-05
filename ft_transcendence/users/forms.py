from .models import User
from django import forms
class UserSettingsForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'twoFaEnable', 'avatar', 'is_subscribe']
