from django import forms
from wagtail.users.forms import UserCreationForm, UserEditForm

from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    phone_number = forms.CharField(required=False, max_length=15, label="Phone number")

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ("email", "first_name", "last_name", "phone_number")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.phone_number = self.cleaned_data.get("phone_number", "")
        if commit:
            user.save()
        return user


class CustomUserEditForm(UserEditForm):
    phone_number = forms.CharField(required=False, max_length=15, label="Phone number")

    class Meta(UserEditForm.Meta):
        model = CustomUser
        fields = ("email", "first_name", "last_name", "phone_number", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.phone_number = self.cleaned_data.get("phone_number", "")
        if commit:
            user.save()
        return user




