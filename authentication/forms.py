from django import forms
from wagtail.users.forms import UserCreationForm, UserEditForm
from django.core.exceptions import ValidationError
import re

from .models import CustomUser, UserProfile


class CustomUserCreationForm(UserCreationForm):
    phone_number = forms.CharField(required=False, max_length=15, label="Phone number")
    branch = forms.CharField(required=False, max_length=100, label="Branch")
    route = forms.CharField(required=False, max_length=100, label="Route")
    code = forms.CharField(required=False, max_length=50, label="Code")
    designation = forms.CharField(required=False, max_length=100, label="Designation")

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ("email", "first_name", "last_name", "phone_number")

    def clean_first_name(self):
        """Validate that first_name contains only letters"""
        first_name = self.cleaned_data.get('first_name', '').strip()
        if first_name:
            if not re.match(r'^[a-zA-Z]+$', first_name):
                raise ValidationError('First name must contain only letters (a-z, A-Z).')
        return first_name

    def clean_last_name(self):
        """Validate that last_name contains only letters"""
        last_name = self.cleaned_data.get('last_name', '').strip()
        if last_name:
            if not re.match(r'^[a-zA-Z]+$', last_name):
                raise ValidationError('Last name must contain only letters (a-z, A-Z).')
        return last_name

    def clean_phone_number(self):
        """Validate mobile number - must be exactly 10 digits"""
        phone_number = self.cleaned_data.get('phone_number', '').strip()
        if phone_number:
            # Remove any spaces, dashes, or other characters
            phone_number = re.sub(r'[\s\-\(\)]', '', phone_number)
            # Check if it contains only digits
            if not phone_number.isdigit():
                raise ValidationError('Mobile number must contain only digits.')
            # Check if it's exactly 10 digits
            if len(phone_number) != 10:
                raise ValidationError('Mobile number must be exactly 10 digits.')
        return phone_number

    def save(self, commit=True):
        user = super().save(commit=False)
        user.phone_number = self.cleaned_data.get("phone_number", "")
        if commit:
            user.save()
            # Update profile with additional fields
            if hasattr(user, 'profile'):
                profile = user.profile
                profile.phone_number = self.cleaned_data.get("phone_number", "")
                profile.branch = self.cleaned_data.get("branch", "")
                profile.route = self.cleaned_data.get("route", "")
                profile.code = self.cleaned_data.get("code", "")
                profile.designation = self.cleaned_data.get("designation", "")
                profile.save()
        return user


class CustomUserEditForm(UserEditForm):
    phone_number = forms.CharField(required=False, max_length=15, label="Phone number")
    branch = forms.CharField(required=False, max_length=100, label="Branch")
    route = forms.CharField(required=False, max_length=100, label="Route")
    code = forms.CharField(required=False, max_length=50, label="Code")
    designation = forms.CharField(required=False, max_length=100, label="Designation")

    class Meta(UserEditForm.Meta):
        model = CustomUser
        fields = ("email", "first_name", "last_name", "phone_number", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")

    def clean_first_name(self):
        """Validate that first_name contains only letters"""
        first_name = self.cleaned_data.get('first_name', '').strip()
        if first_name:
            if not re.match(r'^[a-zA-Z]+$', first_name):
                raise ValidationError('First name must contain only letters (a-z, A-Z).')
        return first_name

    def clean_last_name(self):
        """Validate that last_name contains only letters"""
        last_name = self.cleaned_data.get('last_name', '').strip()
        if last_name:
            if not re.match(r'^[a-zA-Z]+$', last_name):
                raise ValidationError('Last name must contain only letters (a-z, A-Z).')
        return last_name

    def clean_phone_number(self):
        """Validate mobile number - must be exactly 10 digits"""
        phone_number = self.cleaned_data.get('phone_number', '').strip()
        if phone_number:
            # Remove any spaces, dashes, or other characters
            phone_number = re.sub(r'[\s\-\(\)]', '', phone_number)
            # Check if it contains only digits
            if not phone_number.isdigit():
                raise ValidationError('Mobile number must contain only digits.')
            # Check if it's exactly 10 digits
            if len(phone_number) != 10:
                raise ValidationError('Mobile number must be exactly 10 digits.')
        return phone_number

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-populate profile fields if editing existing user
        if self.instance and self.instance.pk and hasattr(self.instance, 'profile'):
            profile = self.instance.profile
            self.fields['phone_number'].initial = profile.phone_number or self.instance.phone_number
            self.fields['branch'].initial = profile.branch
            self.fields['route'].initial = profile.route
            self.fields['code'].initial = profile.code
            self.fields['designation'].initial = profile.designation

    def save(self, commit=True):
        user = super().save(commit=False)
        user.phone_number = self.cleaned_data.get("phone_number", "")
        if commit:
            user.save()
            # Update profile with additional fields
            if hasattr(user, 'profile'):
                profile = user.profile
                profile.phone_number = self.cleaned_data.get("phone_number", "")
                profile.branch = self.cleaned_data.get("branch", "")
                profile.route = self.cleaned_data.get("route", "")
                profile.code = self.cleaned_data.get("code", "")
                profile.designation = self.cleaned_data.get("designation", "")
                profile.save()
        return user





