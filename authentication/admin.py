from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django import forms

from .models import CustomUser, UserProfile, OTP


class CustomUserCreationForm(forms.ModelForm):
    """Form for creating new users in Django admin with phone number."""
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Password confirmation", widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ("email", "first_name", "last_name", "phone_number")

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class CustomUserChangeForm(forms.ModelForm):
    """Form for updating users in Django admin."""

    class Meta:
        model = CustomUser
        fields = ("email", "first_name", "last_name", "phone_number", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser

    list_display = ("email", "first_name", "last_name", "phone_number", "is_staff", "is_active")
    list_filter = ("is_staff", "is_active", "is_superuser", "groups")
    ordering = ("email",)
    search_fields = ("email", "username", "first_name", "last_name", "phone_number", 
                     "profile__phone_number", "profile__branch", "profile__route", 
                     "profile__code", "profile__designation")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "phone_number")} ),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")} ),
        ("Important dates", {"fields": ("last_login", "date_joined")} ),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "first_name", "last_name", "phone_number", "password1", "password2", "is_active", "is_staff", "is_superuser", "groups")
        }),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'branch', 'route', 'code', 'designation')
    list_filter = ('branch', 'designation')
    search_fields = ('user__email', 'user__username', 'user__first_name', 'user__last_name', 
                     'phone_number', 'branch', 'route', 'code', 'designation')
    raw_id_fields = ('user',)


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'otp_code', 'otp_type', 'contact_info', 'created_at', 'expires_at', 'is_used', 'attempts')
    list_filter = ('otp_type', 'is_used', 'created_at')
    search_fields = ('user__email', 'contact_info', 'otp_code')
    readonly_fields = ('otp_code', 'created_at', 'expires_at')
    raw_id_fields = ('user',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
